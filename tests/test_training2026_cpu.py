import unittest

try:
    import torch
except ImportError:
    torch = None

from cfa3_cram.training2026 import IsolatedLowRankExpert2026CPU, propose_adaptive_rank


class RankProposalTests(unittest.TestCase):
    def test_gap_zero_and_one_bounded(self):
        self.assertEqual(propose_adaptive_rank(0, min_rank=1, max_rank=4), 1)
        self.assertEqual(propose_adaptive_rank(1, min_rank=1, max_rank=4), 4)

    def test_invalid_gap_or_rank_rejected(self):
        for gap in (-0.1, 1.2, float('nan'), True):
            with self.assertRaises(ValueError): propose_adaptive_rank(gap)
        with self.assertRaises(ValueError): propose_adaptive_rank(0.5, min_rank=4, max_rank=2)


@unittest.skipUnless(torch is not None, 'CPU PyTorch unavailable: NOT_VERIFIED')
class Training2026Tests(unittest.TestCase):
    def make_expert(self, identity='expert-1', gap=0, seed=42):
        return IsolatedLowRankExpert2026CPU(input_dim=2, output_dim=1,
            model_revision='model:v1', projection_id='projection:v1', expert_id=identity,
            min_rank=1, max_rank=1, rank_gap=gap, seed=seed)

    def setUp(self):
        self.x = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
        self.y = self.x[:, :1] * 2.0

    def test_training_reduces_residual_loss(self):
        expert = self.make_expert()
        initial = torch.nn.functional.mse_loss(expert.forward(self.x), self.y).item()
        trained = expert.fit(self.x, self.y, steps=100, lr=0.1)
        actual = torch.nn.functional.mse_loss(expert.forward(self.x), self.y).item()
        self.assertLess(actual, initial / 20)
        self.assertGreaterEqual(trained, 0)

    def test_previous_expert_weights_do_not_change(self):
        old = self.make_expert('old')
        old.fit(self.x, self.y, steps=20, lr=0.1)
        snapshot = old.checkpoint()
        new = self.make_expert('new', seed=1)
        new.fit(self.x, self.y * 0.5, steps=20, lr=0.1,
                orthogonality_refs=(old.a.detach() @ old.b.detach(),), orthogonality_weight=0.01)
        self.assertTrue(torch.equal(old.a, snapshot['a']))
        self.assertTrue(torch.equal(old.b, snapshot['b']))

    def test_checkpoint_restore_isolation_and_revision(self):
        old = self.make_expert('old')
        original = old.checkpoint()
        old.fit(self.x, self.y, steps=5)
        old.restore(original)
        self.assertTrue(torch.equal(old.a, original['a']))
        self.assertTrue(torch.equal(old.b, original['b']))
        bad = dict(original, model_revision='wrong')
        with self.assertRaises(ValueError): old.restore(bad)

    def test_nonfinite_inputs_rejected_before_mutation(self):
        expert = self.make_expert()
        original = expert.checkpoint()
        bad = self.x.clone()
        bad[0, 0] = float('nan')
        with self.assertRaises(ValueError): expert.fit(bad, self.y)
        self.assertTrue(torch.equal(expert.a, original['a']))
        with self.assertRaises(ValueError): expert.fit(self.x, self.y * float('inf'))

    def test_missing_model_or_rank_excess_rejected(self):
        with self.assertRaises(ValueError):
            IsolatedLowRankExpert2026CPU(input_dim=2, output_dim=1, model_revision='', projection_id='p', expert_id='e',rank_gap=0)
        with self.assertRaises(ValueError):
            IsolatedLowRankExpert2026CPU(input_dim=2, output_dim=1, model_revision='m',projection_id='p',expert_id='e',rank_gap=1, max_rank=8)

    def test_orthogonality_bad_ref_rejected(self):
        expert = self.make_expert()
        with self.assertRaises(ValueError):
            expert.fit(self.x, self.y, orthogonality_refs=(torch.zeros(2, 2),))

    def test_loss_overflow_restores_checkpoint(self):
        expert = self.make_expert()
        before = expert.checkpoint()
        huge = torch.full_like(self.y, 1e30)
        with self.assertRaises(ValueError):
            expert.fit(self.x, huge, steps=2)
        self.assertTrue(torch.equal(expert.a, before['a']))
        self.assertTrue(torch.equal(expert.b, before['b']))


if __name__ == '__main__':
    unittest.main()
