"""Negative-path guard tests; NOT full CFA3 admission or physical-host proof."""
import hashlib
import copy
import tempfile
from unittest.mock import patch
import hmac
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from execution_guard import (Blocked, GOV, LEDGER, CATALOG, canonical_bytes,
                             check_task, guarded_execute, load, local_path,
                             policy_issues, verify_signature, _reserve,
                             validate_current_rule_map)

def sample():
    sources = [GOV, LEDGER, CATALOG, "AGENTS.md"] + load(ROOT, CATALOG)["policy_files"]
    return {"task_id": "synthetic-test", "nonce": "single",
            "operation": "ARTIFACT_EXPORT", "target": "docs/out.txt",
            "scope_targets": ["docs/out.txt"], "main_sha": "a" * 40,
            "expires_at": time.time() + 120, "expected_outputs": 2,
            "units": 1, "max_calls": 2, "max_units": 2,
            "source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                              for p in sources}}

class GuardTests(unittest.TestCase):
    def test_all_known_dev_ai_rules_mapped(self):
        gov, catalog = load(ROOT, GOV), load(ROOT, CATALOG)
        expected = {r["id"] for section in ("development_rules", "ai_behavior_rules")
                    for r in gov[section]}
        self.assertEqual(24, len(expected))
        self.assertEqual(expected, set(catalog["rules"]))

    def test_unreviewed_historical_rules_block(self):
        self.assertTrue(any("historical rule inventory" in s for s in policy_issues(ROOT)))

    def test_signature_required_and_tampering_fails(self):
        t, key = sample(), b"x" * 32
        with self.assertRaises(Blocked):
            verify_signature(t, key)
        with self.assertRaises(Blocked):
            verify_signature(t, None)
        t["signature"] = hmac.new(key, canonical_bytes(t), hashlib.sha256).hexdigest()
        verify_signature(t, key)
        t["expected_outputs"] = 1
        with self.assertRaises(Blocked):
            verify_signature(t, key)

    def test_path_and_scope_denials(self):
        for name in ("../foo", "/tmp/foo", r"foo\bar"):
            with self.assertRaises(Blocked):
                local_path(ROOT, name)
        t = sample()
        t["target"] = "docs/other.txt"
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_direct_main_and_legacy_mutation_denied(self):
        t = sample()
        t["operation"] = "REPOSITORY_WRITE"
        t["branch"] = "main"
        t["head_sha"] = "b" * 40
        with self.assertRaises(Blocked):
            check_task(ROOT, t)
        t["branch"], t["target"], t["scope_targets"] = "guard/example", "legacy/x", ["legacy/x"]
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_expiration_and_source_drift_denied(self):
        t = sample()
        t["expires_at"] = 1
        with self.assertRaises(Blocked):
            check_task(ROOT, t)
        t = sample()
        t["source_hashes"][GOV] = "0" * 64
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_gui_without_accepted_design_denied(self):
        t = sample()
        t["operation"] = "GUI_RENDER"
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_false_physical_pass_denied(self):
        t = sample()
        t["claims_physical_pass"] = True
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_incomplete_governance_never_invokes_executor(self):
        calls = []
        with self.assertRaises(Blocked):
            guarded_execute(sample(), root=ROOT, secret=b"x" * 32,
                            live_state=lambda _: {},
                            executor=lambda _: calls.append(True),
                            verify_result=lambda *_: True, state_dir=ROOT / "tests")
        self.assertEqual([], calls)

    def test_quota_contract_bound_across_all_authorizations(self):
        with tempfile.TemporaryDirectory() as location:
            t = sample()
            _reserve(location, t)
            with self.assertRaises(Blocked):
                _reserve(location, dict(t, nonce="next", max_units=999))
            with self.assertRaises(Blocked):
                _reserve(location, dict(t, nonce="next", scope_targets=["docs/out.txt", "docs/new.txt"]))

    def test_cross_task_nonce_replay_forbidden(self):
        with tempfile.TemporaryDirectory() as location:
            t = sample()
            _reserve(location, t)
            with self.assertRaises(Blocked):
                _reserve(location, dict(t, task_id="different"))

    def test_exhaustion_and_replay_forbidden(self):
        with tempfile.TemporaryDirectory() as location:
            t = sample()
            _reserve(location, t)
            with self.assertRaises(Blocked):
                _reserve(location, t)
            _reserve(location, dict(t, nonce="second"))
            with self.assertRaises(Blocked):
                _reserve(location, dict(t, nonce="third"))

    def test_workflow_missing_approval_and_head_denied(self):
        t = sample()
        t["operation"], t["branch"] = "WORKFLOW_START", "guard/branch"
        with self.assertRaises(Blocked):
            check_task(ROOT, t)
        t["head_sha"] = "b" * 40
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_nan_and_noncanonical_paths_denied(self):
        for name in ("docs//out.txt", "docs/./out.txt", "docs/out.txt/"):
            with self.assertRaises(Blocked):
                local_path(ROOT, name)
        t = sample()
        t["expires_at"] = float("nan")
        with self.assertRaises(Blocked):
            check_task(ROOT, t)

    def test_preflight_failure_consumes_no_quota(self):
        t, key = sample(), b"x" * 32
        t["signature"] = hmac.new(key, canonical_bytes(t), hashlib.sha256).hexdigest()
        ok = dict(complete_rule_inventory=True, rule_gates_verified=True,
                  all_conflicts_resolved=True, independent_proof_verified=True)
        state = dict(main_current=True, head_current=True, no_overlap=True,
                     checks_passed=True, review_threads_clear=True,
                     owner_scope_approved=True, main_ruleset_verified=True,
                     privileged_bypass_actors_verified=True,
                     actual_main_sha=t["main_sha"])
        called = []
        with tempfile.TemporaryDirectory() as location:
            with patch("execution_guard.policy_issues", return_value=[]):
                with self.assertRaises(Blocked):
                    guarded_execute(t, root=ROOT, secret=key,
                                    admission=lambda _: ok, live_state=lambda _: state,
                                    preflight=lambda _: {}, executor=lambda _: called.append(True),
                                    verify_result=lambda *_: True, audit=lambda *_: None,
                                    state_dir=location)
            self.assertEqual([], called)
            self.assertFalse((Path(location) / "receipts.json").exists())

    def test_full_legacy_tree_is_explicitly_pending_rule_review(self):
        frozen = load(ROOT, "canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json")
        self.assertEqual("UNREVIEWED_RULE_APPLICABILITY", frozen["review_status_default"])
        self.assertEqual(3159, len(frozen["files"]))
        self.assertTrue(any("historical rule inventory incomplete" in x
                            for x in policy_issues(ROOT)))

    def test_policy_surface_contains_all_current_leaf_fields(self):
        from check_guard_policy_surface import validate_snapshot
        manifest = load(ROOT, "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json")
        self.assertFalse(manifest["semantic_rule_admission"])
        self.assertEqual([], validate_snapshot(manifest, ROOT))

    def test_rule_catalog_exact_code_and_status_must_match_authority(self):
        gov = load(ROOT, GOV)
        catalog = load(ROOT, CATALOG)
        self.assertEqual([], validate_current_rule_map(gov, catalog))
        for ident in catalog["rules"]:
            bad = copy.deepcopy(catalog)
            bad["rules"][ident]["code"] += "_TAMPERED"
            with self.subTest(rule=ident, mutation="code"):
                self.assertTrue(validate_current_rule_map(gov, bad))
            bad = copy.deepcopy(catalog)
            bad["rules"][ident]["status"] = "UNKNOWN_AUTOPASS"
            with self.subTest(rule=ident, mutation="status"):
                self.assertTrue(validate_current_rule_map(gov, bad))
            bad = copy.deepcopy(catalog)
            del bad["rules"][ident]
            with self.subTest(rule=ident, mutation="omitted"):
                self.assertTrue(validate_current_rule_map(gov, bad))
        bad = copy.deepcopy(catalog)
        bad["rules"]["DEV-99"] = {"code": "IMAGINARY", "status": "VERIFIED_GATE"}
        self.assertTrue(validate_current_rule_map(gov, bad))

    def test_modified_canonical_governance_rule_code_detected(self):
        gov, catalog = load(ROOT, GOV), load(ROOT, CATALOG)
        for section in ("development_rules", "ai_behavior_rules"):
            for i in range(12):
                broken = copy.deepcopy(gov)
                broken[section][i]["code"] = "REPLACED_WITH_AN_ASSUMPTION"
                with self.subTest(section=section, index=i):
                    self.assertTrue(validate_current_rule_map(broken, catalog))

if __name__ == "__main__":
    unittest.main()
