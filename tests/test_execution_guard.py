"""Negative-path guard tests; NOT full CFA3 admission or physical-host proof."""
import hashlib
import hmac
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from execution_guard import (Blocked, GOV, LEDGER, CATALOG, canonical_bytes,
                             check_task, guarded_execute, load, local_path,
                             policy_issues, verify_signature)

def sample():
    sources = [GOV, LEDGER, CATALOG]
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

if __name__ == "__main__":
    unittest.main()
