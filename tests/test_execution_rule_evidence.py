"""Rule-by-rule evidence receipts; tests use synthetic keys, NEVER real authority."""
import copy
import hashlib
import hmac
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from execution_guard import load, GOV, LEDGER, CATALOG
from check_execution_rule_evidence import (
    RuleEvidenceBlocked, SCHEMA, bytes_canonical, expected_rules,
    request_digest, verify_rule_receipts
)

KEY = b"t" * 32
NOW = 10000.0

def task():
    return {
        "task_id": "synthetic-only", "main_sha": "a" * 40,
        "expires_at": NOW + 100,
        "source_hashes": {GOV: hashlib.sha256((ROOT / GOV).read_bytes()).hexdigest()}
    }

def receipts(task_contract, governance):
    out = []
    for ident, code in expected_rules(governance).items():
        row = {
            "schema": SCHEMA, "rule_id": ident, "code": code,
            "gate_id": "CFA3-RULE-GATE-" + ident,
            "task_sha256": request_digest(task_contract),
            "governance_sha256": task_contract["source_hashes"][GOV],
            "main_sha": task_contract["main_sha"], "verdict": "PASS",
            "checked_at": NOW - 1, "expires_at": NOW + 10,
            "evidence_sha256": hashlib.sha256(ident.encode()).hexdigest()
        }
        row["signature"] = hmac.new(
            KEY, bytes_canonical(row), hashlib.sha256).hexdigest()
        out.append(row)
    return out

class RuleReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.governance = load(ROOT, GOV)

    def check(self, bundle, task_contract=None, governance=None, secret=KEY):
        return verify_rule_receipts(
            task() if task_contract is None else task_contract,
            bundle, self.governance if governance is None else governance, secret, now=NOW)

    def test_only_full_24_source_bound_receipts_pass_structurally(self):
        self.assertEqual(24, len(expected_rules(self.governance)))
        self.assertTrue(self.check(receipts(task(), self.governance)))

    def test_every_missing_individual_rule_blocks(self):
        valid = receipts(task(), self.governance)
        for index in range(24):
            with self.subTest(rule=valid[index]["rule_id"]), self.assertRaises(RuleEvidenceBlocked):
                self.check(valid[:index] + valid[index + 1:])

    def test_every_negative_individual_verdict_blocks(self):
        valid = receipts(task(), self.governance)
        for index in range(24):
            tampered = copy.deepcopy(valid)
            tampered[index]["verdict"] = "PENDING"
            with self.subTest(rule=valid[index]["rule_id"]), self.assertRaises(RuleEvidenceBlocked):
                self.check(tampered)

    def test_duplicate_or_unknown_receipt_blocks(self):
        valid = receipts(task(), self.governance)
        duplicated = valid[:23] + [copy.deepcopy(valid[0])]
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(duplicated)
        wrong = copy.deepcopy(valid)
        wrong[0]["rule_id"] = "DEV-99"
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(wrong)

    def test_drifted_task_or_policy_blocks(self):
        valid = receipts(task(), self.governance)
        changed = dict(task(), main_sha="b" * 40)
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, task_contract=changed)
        changed = copy.deepcopy(task())
        changed["source_hashes"][GOV] = "0" * 64
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, task_contract=changed)

    def test_tampered_signature_and_other_signing_key_block(self):
        valid = receipts(task(), self.governance)
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, secret=b"x" * 32)
        tampered = copy.deepcopy(valid)
        tampered[7]["gate_id"] = "MADE_UP_GATE"
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(tampered)
        tampered = copy.deepcopy(valid)
        tampered[7]["evidence_sha256"] = "0" * 64
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(tampered)

    def test_expired_future_and_nonfinite_receipts_block(self):
        valid = receipts(task(), self.governance)
        for field, value in (("checked_at", NOW+1), ("checked_at", NOW-100),
                             ("checked_at", float("nan")), ("expires_at", NOW),
                             ("expires_at", NOW+1000)):
            bad = copy.deepcopy(valid)
            bad[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuleEvidenceBlocked):
                self.check(bad)

    def test_canonical_rule_removed_or_renamed_blocks(self):
        valid = receipts(task(), self.governance)
        governance = copy.deepcopy(self.governance)
        governance["ai_behavior_rules"].pop()
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, governance=governance)
        governance = copy.deepcopy(self.governance)
        governance["development_rules"][0]["code"] = "ALTERED"
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, governance=governance)

    def test_missing_or_untrusted_secret_blocks(self):
        valid = receipts(task(), self.governance)
        for key in (None, b"", b"bad", "notbytes"):
            with self.subTest(key=key), self.assertRaises(RuleEvidenceBlocked):
                self.check(valid, secret=key)

    def test_receipt_not_global_admission(self):
        ledger = load(ROOT, LEDGER)
        catalog = load(ROOT, CATALOG)
        self.assertFalse(ledger["inventory_complete"])
        self.assertFalse(catalog["coverage_complete"])
        self.assertFalse(catalog["independent_evidence_verified"])

if __name__ == "__main__":
    unittest.main()
