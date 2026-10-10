"""CFA3 source lifecycle lookup: no silent duplicate/decision overwrite."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_lifecycle import evaluate, normalize_url, validate_index

BASE = {
    "schema": "cfa3.source-lifecycle-index.v1",
    "complete": True,
    "source_records": [{
        "source_id": "s-001",
        "canonical_url": "https://github.com/Example/Project",
        "aliases": ["https://github.com/Old/Project"],
        "prior_decision": {"decision_id": "DEC-1", "revision": 2, "outcome": "REFERENCE_ONLY"},
        "observed_revision": "abc123",
        "support_status": "SUPPORTED",
        "rights": {"verified": False, "may_modify_and_distribute": False}
    }]
}
OBS = {"verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
       "evidence_ref": "upstream-check/example-001",
       "checked_at": "2026-10-09T10:00:00Z",
       "observed_revision": "abc123", "support_status": "SUPPORTED"}

class SourceLifecycleTests(unittest.TestCase):
    def test_github_alias_and_tracking_do_not_make_duplicate(self):
        self.assertEqual(normalize_url("http://WWW.github.com/Example/Project.git/?utm_source=x"),
                         normalize_url("https://github.com/example/project"))
        self.assertEqual(evaluate("https://github.com/OLD/PROJECT?fbclid=xx", BASE, OBS)["disposition"],
                         "REUSE_PRIOR_DECISION")

    def test_nontracking_query_values_are_distinct(self):
        self.assertNotEqual(normalize_url("https://example.com/topic?tag=1"),
                            normalize_url("https://example.com/topic?tag=2"))

    def test_prior_decision_is_not_reinterpreted(self):
        snapshot = copy.deepcopy(BASE)
        observed = evaluate("https://github.com/example/project", BASE, OBS)
        self.assertEqual(observed["prior_decision"], snapshot["source_records"][0]["prior_decision"])
        self.assertFalse(observed["prior_decision_overwritten"])
        self.assertEqual(BASE, snapshot)

    def test_without_fresh_evidence_requires_change_check(self):
        self.assertEqual(evaluate("https://github.com/example/project", BASE)["disposition"],
                         "CHANGE_CHECK_REQUIRED")

    def test_unchanged_uses_previous_decision(self):
        self.assertEqual(evaluate("https://github.com/example/project", BASE, OBS)["disposition"],
                         "REUSE_PRIOR_DECISION")

    def test_changed_version_is_append_only_review(self):
        ob = dict(OBS, observed_revision="def456")
        result = evaluate("https://github.com/example/project", BASE, ob)
        self.assertEqual(result["disposition"], "CHANGE_REVIEW_REQUIRED")
        self.assertEqual(result["prior_decision"]["revision"], 2)

    def test_move_is_not_new_source(self):
        ob = dict(OBS, event="RELOCATED", previous_source_id="s-001")
        result = evaluate("https://github.com/NewOrg/Project", BASE, ob)
        self.assertEqual(result["disposition"], "RELOCATION_REVIEW_REQUIRED")
        self.assertEqual(result["source_id"], "s-001")

    def test_unsupported_source_with_verified_reuse_rights(self):
        ob = dict(OBS, support_status="UNMAINTAINED",
                  rights={"verified": True, "may_modify_and_distribute": True})
        result = evaluate("https://github.com/example/project", BASE, ob)
        self.assertEqual(result["disposition"], "REPLACEMENT_PLAN_REQUIRED")
        self.assertEqual(result["replacement_strategy"], "MODERNIZE_AND_ADAPT_TO_CFA3_AFTER_RIGHTS_REVIEW")

    def test_unsupported_source_without_rights_requires_native(self):
        ob = dict(OBS, support_status="UNMAINTAINED")
        result = evaluate("https://github.com/example/project", BASE, ob)
        self.assertEqual(result["replacement_strategy"], "INDEPENDENT_CFA3_REPLACEMENT_NO_CODE_IMPORT")

    def test_unverified_change_blocked(self):
        ob = dict(OBS, verification="ASSUMED", observed_revision="def456")
        self.assertEqual(evaluate("https://github.com/example/project", BASE, ob)["disposition"],
                         "BLOCKED_UNVERIFIED_OBSERVATION")

    def test_new_source_only_after_index_complete(self):
        self.assertEqual(evaluate("https://example.org/new", BASE)["disposition"],
                         "NEW_SOURCE_ANALYSIS_ALLOWED")
        incomplete = dict(BASE, complete=False)
        self.assertEqual(evaluate("https://example.org/new", incomplete)["disposition"],
                         "BLOCKED_INDEX_INCOMPLETE")

    def test_empty_bootstrap_index_never_certifies_new(self):
        from source_lifecycle import DEFAULT_INDEX
        import json
        current = json.loads(DEFAULT_INDEX.read_text(encoding="utf-8"))
        self.assertFalse(current["complete"])
        self.assertEqual(evaluate("https://github.com/any/new", current)["disposition"],
                         "BLOCKED_INDEX_INCOMPLETE")

    def test_alias_collision_blocks_all_processing(self):
        conflicting = copy.deepcopy(BASE)
        other = copy.deepcopy(conflicting["source_records"][0])
        other["source_id"] = "s-002"
        other["canonical_url"] = "https://github.com/old/project"
        other["aliases"] = []
        conflicting["source_records"].append(other)
        self.assertEqual(evaluate("https://github.com/example/project", conflicting)["disposition"],
                         "BLOCKED_INDEX_CONFLICT")

    def test_missing_or_invalid_index_blocks(self):
        self.assertEqual(evaluate("https://github.com/example/project", {"complete": True})["disposition"],
                         "BLOCKED_INDEX_CONFLICT")

    def test_no_credential_urls(self):
        self.assertRaises(ValueError, normalize_url, "https://secret:password@github.com/example/project")

    def test_does_not_register_or_admit_automatically(self):
        for observation in (None, OBS, dict(OBS, observed_revision="update")):
            result = evaluate("https://github.com/example/project", BASE, observation)
            self.assertFalse(result["automatic_code_import"])
            self.assertFalse(result["automatic_donor_registration"])

if __name__ == "__main__":
    unittest.main()
