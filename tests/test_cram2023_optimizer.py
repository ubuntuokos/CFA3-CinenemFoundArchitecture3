"""Real CPU-only PyTorch tests; without torch these tests SKIP, never PASS."""
import math
import unittest

try:
    import torch
except ImportError:
    torch = None

from cfa3_cram import TopkCrAM2023CPU, UPSTREAM_COMMIT


@unittest.skipUnless(torch is not None, "NOT_RUN: optional PyTorch CPU backend absent")
class CrAM2023CPUTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(73)
        self.model = torch.nn.Linear(4, 2, bias=True)
        self.x = torch.arange(20, dtype=torch.float32).reshape(5, 4) / 20
        self.y = torch.ones(5, 2)

    def make_closure(self):
        def closure():
            loss = torch.nn.functional.mse_loss(self.model(self.x), self.y)
            loss.backward()
            return loss
        return closure

    def test_source_pin(self):
        self.assertEqual(len(UPSTREAM_COMMIT), 40)

    def test_real_cpu_parameter_update(self):
        opt = TopkCrAM2023CPU(self.model.parameters(), lr=0.1, sparsities=(0.5,), seed=11)
        before = [p.detach().clone() for p in self.model.parameters()]
        opt.zero_grad()
        self.make_closure()()
        result = opt.step(self.make_closure())
        self.assertTrue(math.isfinite(result.item()))
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, self.model.parameters())))
        self.assertEqual(opt.last_sparsity, 0.5)

    def test_reference_sgd_when_zero_rho_zero_sparsity_no_plus(self):
        duplicate = torch.nn.Linear(4, 2)
        duplicate.load_state_dict(self.model.state_dict())
        opt = TopkCrAM2023CPU(self.model.parameters(), lr=0.1, rho=0.0, sparsities=(0.0,), plus_version=False)
        sgd = torch.optim.SGD(duplicate.parameters(), lr=0.1)
        opt.zero_grad(); self.make_closure()()
        opt.step(self.make_closure())
        sgd.zero_grad()
        loss = torch.nn.functional.mse_loss(duplicate(self.x), self.y)
        loss.backward(); sgd.step()
        for a, b in zip(self.model.parameters(), duplicate.parameters()):
            self.assertTrue(torch.allclose(a, b, atol=1e-7, rtol=1e-6))

    def test_sparse_weights_seen_inside_closure(self):
        opt = TopkCrAM2023CPU(self.model.parameters(), lr=0.05, sparsities=(0.7,))
        seen = []
        def closure():
            seen.append(int((self.model.weight.detach() == 0).sum().item()))
            return self.make_closure()()
        opt.zero_grad(); self.make_closure()()
        opt.step(closure)
        self.assertGreater(seen[0], 0)

    def test_failed_closure_restores_parameters_and_gradients(self):
        opt = TopkCrAM2023CPU(self.model.parameters(), lr=0.1, sparsities=(0.7,))
        opt.zero_grad(); self.make_closure()()
        before = [p.detach().clone() for p in self.model.parameters()]
        grads = [p.grad.detach().clone() for p in self.model.parameters()]
        def exploding():
            _ = self.make_closure()()
            raise RuntimeError("fixture simulated failure")
        with self.assertRaisesRegex(RuntimeError, "simulated failure"):
            opt.step(exploding)
        for p, old, grad in zip(self.model.parameters(), before, grads):
            self.assertTrue(torch.equal(p, old))
            self.assertTrue(torch.equal(p.grad, grad))
        self.assertIsNone(opt.last_sparsity)

    def test_invalid_ranges_fail_closed(self):
        for k in (-0.1, 1.0, float("nan")):
            with self.subTest(k=k), self.assertRaises(ValueError):
                TopkCrAM2023CPU(self.model.parameters(), sparsities=(k,))
        with self.assertRaises(ValueError):
            TopkCrAM2023CPU(self.model.parameters(), rho=-1)

    def test_no_silent_cuda_backend(self):
        with self.assertRaises(Exception):
            TopkCrAM2023CPU([torch.nn.Parameter(torch.empty(2, 2, device="meta"))])

    def test_missing_clean_gradients_rejected(self):
        opt = TopkCrAM2023CPU(self.model.parameters())
        with self.assertRaisesRegex(ValueError, "clean backward"):
            opt.step(self.make_closure())


    def test_failed_base_optimizer_update_restores_weights(self):
        opt = TopkCrAM2023CPU(self.model.parameters(), lr=0.1, sparsities=(0.5,))
        opt.zero_grad(); self.make_closure()()
        before = [p.detach().clone() for p in self.model.parameters()]
        actual_step = opt.base_optimizer.step
        def partial_then_fail(*args, **kwargs):
            actual_step(*args, **kwargs)
            raise RuntimeError("simulated update failure")
        opt.base_optimizer.step = partial_then_fail
        with self.assertRaisesRegex(RuntimeError, "update failure"):
            opt.step(self.make_closure())
        for p, old in zip(self.model.parameters(), before):
            self.assertTrue(torch.equal(p, old))

    def test_checkpoint_restores_rng_for_repeatable_choice(self):
        first = TopkCrAM2023CPU(self.model.parameters(), sparsities=(0.2, 0.5, 0.8), seed=42)
        first.zero_grad(); self.make_closure()()
        first.step(self.make_closure())
        snapshot = first.state_dict()
        duplicate = torch.nn.Linear(4, 2)
        duplicate.load_state_dict(self.model.state_dict())
        second = TopkCrAM2023CPU(duplicate.parameters(), sparsities=(0.2, 0.5, 0.8), seed=1)
        second.load_state_dict(snapshot)
        first.zero_grad(); self.make_closure()()
        first.step(self.make_closure())
        second.zero_grad()
        def other_closure():
            loss = torch.nn.functional.mse_loss(duplicate(self.x), self.y)
            loss.backward()
            return loss
        other_closure(); second.step(other_closure)
        self.assertEqual(first.last_sparsity, second.last_sparsity)
        for a, b in zip(self.model.parameters(), duplicate.parameters()):
            self.assertTrue(torch.allclose(a, b, atol=1e-6))

    def test_reject_checkpoint_different_source_revision(self):
        opt = TopkCrAM2023CPU(self.model.parameters())
        bad = opt.state_dict()
        bad["source_commit"] = "unverified"
        with self.assertRaisesRegex(ValueError, "source revision"):
            opt.load_state_dict(bad)


if __name__ == "__main__":
    unittest.main()
