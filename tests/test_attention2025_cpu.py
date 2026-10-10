import math
import unittest

try:
    import torch
except ImportError:
    torch = None

from cfa3_cram.attention2025 import credibility_sdpa_cpu, AttentionBackendUnavailable


@unittest.skipUnless(torch is not None, 'PyTorch CPU not installed: NOT_VERIFIED')
class Attention2025CPUTests(unittest.TestCase):
    def setUp(self):
        self.q = torch.zeros(1, 1, 1, 2)
        self.k = torch.zeros(1, 1, 2, 2)
        self.v = torch.tensor([[[[1.0], [100.0]]]])

    def test_lower_credibility_reduces_untrusted_attention(self):
        baseline = credibility_sdpa_cpu(self.q, self.k, self.v, (0.0, 0.0))
        penalized = credibility_sdpa_cpu(self.q, self.k, self.v, (0.0, math.log(0.001)))
        self.assertAlmostEqual(baseline.item(), 50.5, places=4)
        self.assertLess(penalized.item(), 2)
        self.assertGreater(penalized.item(), 1)

    def test_no_implicit_dtype_cast_or_gpu_path(self):
        with self.assertRaises(ValueError):
            credibility_sdpa_cpu(self.q.double(), self.k, self.v, (0, 0))
        with self.assertRaises(AttentionBackendUnavailable):
            credibility_sdpa_cpu(self.q.to('meta'), self.k, self.v, (0, 0))

    def test_incompatible_shapes_rejected(self):
        with self.assertRaises(ValueError):
            credibility_sdpa_cpu(self.q, self.k[:, :, :1], self.v, (0, 0))

    def test_bad_logbias_rejected(self):
        for values in ((0,), (0, 1), (0, float('nan')), (0, float('inf')), (0, True)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                credibility_sdpa_cpu(self.q, self.k, self.v, values)

    def test_nonfinite_tensors_rejected(self):
        bad_q = self.q.clone()
        bad_q[0, 0, 0, 0] = float('nan')
        with self.assertRaises(ValueError):
            credibility_sdpa_cpu(bad_q, self.k, self.v, (0, 0))

    def test_causal_future_token_is_masked(self):
        q = torch.zeros(1, 1, 2, 1)
        k = torch.zeros(1, 1, 2, 1)
        v = torch.tensor([[[[1.0], [11.0]]]])
        result = credibility_sdpa_cpu(q, k, v, (0, 0), causal=True)
        self.assertAlmostEqual(result[0, 0, 0, 0].item(), 1.0)
        self.assertAlmostEqual(result[0, 0, 1, 0].item(), 6.0)

    def test_causal_cross_attention_rejected(self):
        with self.assertRaises(ValueError):
            credibility_sdpa_cpu(self.q, self.k, self.v, (0, 0), causal=True)

    def test_repeatable_and_finite(self):
        a = credibility_sdpa_cpu(self.q, self.k, self.v, (0, -2))
        b = credibility_sdpa_cpu(self.q, self.k, self.v, (0, -2))
        self.assertTrue(torch.equal(a, b))
        self.assertTrue(bool(torch.isfinite(a).all()))


if __name__ == '__main__':
    unittest.main()
