import math
import unittest

from cfa3_cram.reliability2025 import Evidence, SourceTokenSpan, attention_log_bias, temporary_attention_pre_hook
from cfa3_cram.continual2026 import Expert, rank_existing_experts

DIGEST = "sha256:" + "a" * 64


class CrAM2025PolicyTests(unittest.TestCase):
    def test_cpu_attention_bias_with_assessed_evidence(self):
        records = [Evidence("a", DIGEST, 1.0, "assessor:v1"), Evidence("b", DIGEST, 0.1, "assessor:v1")]
        bias = attention_log_bias(records, [SourceTokenSpan("a", 0, 2), SourceTokenSpan("b", 3, 5)], 6)
        self.assertEqual(bias[:2], (0.0, 0.0))
        self.assertAlmostEqual(bias[3], math.log(0.1))
        self.assertEqual(bias[2], 0.0)
        self.assertEqual(bias[5], 0.0)

    def test_untrusted_sources_get_finite_floor(self):
        e = Evidence("a", DIGEST, 0.0, "assessor")
        self.assertAlmostEqual(attention_log_bias([e], [SourceTokenSpan("a", 0, 1)], 1)[0], math.log(0.001))

    def test_wrong_digest_or_assessor_rejected(self):
        for dig, assessor in [("wrong", "x"), (DIGEST, "")]:
            with self.assertRaises(ValueError): Evidence("a", dig, 0.9, assessor)

    def test_nonfinite_credibility_rejected(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1, True):
            with self.assertRaises(ValueError): Evidence("a", DIGEST, value, "assessor")

    def test_overlap_rejected(self):
        e = Evidence("a", DIGEST, 0.5, "assessor")
        with self.assertRaises(ValueError): attention_log_bias([e], [SourceTokenSpan("a", 0, 2), SourceTokenSpan("a", 1, 3)], 3)

    def test_ambiguous_or_unrepresented_evidence_rejected(self):
        e = Evidence("a", DIGEST, 0.5, "assessor")
        with self.assertRaises(ValueError): attention_log_bias([e, e], [SourceTokenSpan("a", 0, 1)], 1)
        with self.assertRaises(ValueError): attention_log_bias([e], [], 1)
        with self.assertRaises(ValueError): attention_log_bias([e], [SourceTokenSpan("unknown", 0, 1)], 1)

    def test_hook_cleaned_on_exception(self):
        class Module:
            def __init__(self): self.hooks = []
            def register_forward_pre_hook(self, hook, *, with_kwargs):
                self.hooks.append(hook)
                class Handle:
                    def remove(inner): self.hooks.remove(hook)
                return Handle()
        m = Module()
        with self.assertRaisesRegex(RuntimeError, "inference failed"):
            with temporary_attention_pre_hook(m, object()):
                self.assertEqual(len(m.hooks), 1)
                raise RuntimeError("inference failed")
        self.assertEqual(m.hooks, [])


class CrAM2026ExpertTests(unittest.TestCase):
    def expert(self, identity, vec, revision="m:v1"):
        return Expert(identity, revision, "projection:1", DIGEST, tuple(vec))

    def test_select_existing_expert_inside_one_model(self):
        match = rank_existing_experts((1, 0), [self.expert("e1", (1, 0)), self.expert("e2", (0, 1))], model_revision="m:v1", projection_id="projection:1")
        self.assertEqual(match.expert_id, "e1")
        self.assertFalse(match.needs_new_expert_review)

    def test_no_match_requests_review_not_automatic_expansion(self):
        match = rank_existing_experts((1, 0), [self.expert("e2", (0, 1))], model_revision="m:v1", projection_id="projection:1")
        self.assertIsNone(match.expert_id)
        self.assertTrue(match.needs_new_expert_review)

    def test_empty_expert_registry_requests_review(self):
        self.assertTrue(rank_existing_experts((1,), [], model_revision="m:v1", projection_id="projection:1").needs_new_expert_review)

    def test_conflicting_model_or_projection_rejected(self):
        with self.assertRaises(ValueError):
            rank_existing_experts((1, 0), [self.expert("e", (1, 0), "m:v2")], model_revision="m:v1", projection_id="projection:1")

    def test_duplicate_expert_rejected(self):
        e = self.expert("e", (1, 0))
        with self.assertRaises(ValueError):
            rank_existing_experts((1, 0), [e, e], model_revision="m:v1", projection_id="projection:1")

    def test_zero_or_nonfinite_vectors_rejected(self):
        with self.assertRaises(ValueError): self.expert("e", (0, 0))
        with self.assertRaises(ValueError): self.expert("e", (float("inf"), 1))
        with self.assertRaises(ValueError):
            rank_existing_experts((float("nan"), 0), [], model_revision="m:v1", projection_id="projection:1")

    def test_dimension_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            rank_existing_experts((1, 0, 0), [self.expert("e", (1, 0))], model_revision="m:v1", projection_id="projection:1")


if __name__ == "__main__": unittest.main()
