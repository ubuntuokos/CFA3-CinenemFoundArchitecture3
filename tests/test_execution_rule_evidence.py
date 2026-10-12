"""Rule-by-rule evidence receipts; tests use synthetic keys, NEVER real authority."""
import copy
import io
import hashlib
import hmac
from pathlib import Path
import sys
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from execution_guard import load, GOV, LEDGER, CATALOG
from check_execution_rule_evidence import (
    RuleEvidenceBlocked, SCHEMA, bytes_canonical, expected_rules,
    request_digest, verify_rule_receipts, EVIDENCE_SCHEMA
)

KEY = b"t" * 32
NOW = 10000.0

def task():
    return {
        "task_id": "synthetic-only", "main_sha": "a" * 40,
        "expires_at": NOW + 100,
        "source_hashes": {GOV: hashlib.sha256((ROOT / GOV).read_bytes()).hexdigest()}
    }

def evidence_bytes(receipt):
    fields = ("rule_id", "code", "task_sha256", "governance_sha256",
              "main_sha", "gate_id", "verdict", "checked_at")
    body = {field: receipt[field] for field in fields}
    body["schema"] = EVIDENCE_SCHEMA
    body["evaluator_sha256"] = hashlib.sha256(
        b"SYNTHETIC-UNIT-TEST-EVALUATOR-ONLY"
    ).hexdigest()
    return bytes_canonical(body)

def receipts(task_contract, governance):
    out = []
    for ident, code in expected_rules(governance).items():
        row = {
            "schema": SCHEMA, "rule_id": ident, "code": code,
            "gate_id": "CFA3-RULE-GATE-" + ident,
            "task_sha256": request_digest(task_contract),
            "governance_sha256": task_contract["source_hashes"][GOV],
            "main_sha": task_contract["main_sha"], "verdict": "PASS",
            "checked_at": NOW - 1, "expires_at": NOW + 10
        }
        row["evidence_sha256"] = hashlib.sha256(evidence_bytes(row)).hexdigest()
        row["signature"] = hmac.new(
            KEY, bytes_canonical(row), hashlib.sha256).hexdigest()
        out.append(row)
    return out

class RuleReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.governance = load(ROOT, GOV)
        reference = receipts(task(), cls.governance)
        cls.content_store = {
            row["rule_id"]: evidence_bytes(row) for row in reference
        }

    def resolver(self, ident, digest):
        return self.content_store.get(ident)

    def check(self, bundle, task_contract=None, governance=None, secret=KEY, resolver=None):
        return verify_rule_receipts(
            task() if task_contract is None else task_contract,
            bundle, self.governance if governance is None else governance, secret,
            now=NOW, evidence_resolver=self.resolver if resolver is None else resolver)

    def test_only_full_24_source_bound_receipts_pass_structurally(self):
        self.assertEqual(83, len(expected_rules(self.governance)))
        self.assertTrue(self.check(receipts(task(), self.governance)))

    def test_every_missing_individual_rule_blocks(self):
        valid = receipts(task(), self.governance)
        for index in range(83):
            with self.subTest(rule=valid[index]["rule_id"]), self.assertRaises(RuleEvidenceBlocked):
                self.check(valid[:index] + valid[index + 1:])

    def test_every_negative_individual_verdict_blocks(self):
        valid = receipts(task(), self.governance)
        for index in range(83):
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

    def test_missing_content_resolver_fails_before_admission(self):
        valid = receipts(task(), self.governance)
        with self.assertRaises(RuleEvidenceBlocked):
            verify_rule_receipts(task(), valid, self.governance, KEY, now=NOW)

    def test_missing_or_wrong_evidence_bytes_fail(self):
        valid = receipts(task(), self.governance)
        for value in (None, b"", b"not-a-json-document", b"{}", b"\x00"*131073):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(RuleEvidenceBlocked):
                self.check(valid, resolver=lambda *_: value)

    def test_cross_rule_evidence_substitution_fails_for_every_rule(self):
        valid = receipts(task(), self.governance)
        order = list(self.content_store)
        for i, ident in enumerate(order):
            altered = dict(self.content_store)
            altered[ident] = self.content_store[order[(i + 1) % len(order)]]
            with self.subTest(rule=ident), self.assertRaises(RuleEvidenceBlocked):
                self.check(valid, resolver=lambda name, digest: altered.get(name))

    def test_signed_matching_digest_with_wrong_content_binding_fails(self):
        valid = receipts(task(), self.governance)
        forged = copy.deepcopy(valid)
        wrong_body = copy.deepcopy(__import__("json").loads(evidence_bytes(forged[0])))
        wrong_body["rule_id"] = "AI-99"
        raw = bytes_canonical(wrong_body)
        forged[0]["evidence_sha256"] = hashlib.sha256(raw).hexdigest()
        forged[0]["signature"] = hmac.new(KEY, bytes_canonical(
            {k:v for k,v in forged[0].items() if k!="signature"}
        ), hashlib.sha256).hexdigest()
        altered = dict(self.content_store)
        altered[forged[0]["rule_id"]] = raw
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(forged, resolver=lambda name, digest: altered.get(name))

    def test_evidence_provider_exception_is_denied(self):
        valid = receipts(task(), self.governance)
        def unavailable(*_):
            raise OSError("protected evidence store unavailable")
        with self.assertRaises(RuleEvidenceBlocked):
            self.check(valid, resolver=unavailable)


    def test_bootstrap_reports_24_individual_rules_without_runtime_admission(self):
        from check_execution_rule_evidence import bootstrap_rule_report
        catalog = load(ROOT, CATALOG)
        matrix, issues = bootstrap_rule_report(self.governance, catalog)
        self.assertEqual([], issues)
        self.assertEqual(83, len(matrix))
        self.assertEqual(sorted(expected_rules(self.governance)), [row[0] for row in matrix])
        self.assertEqual({"PENDING_RUNTIME_GATE_AND_PROOF"}, {row[2] for row in matrix})
        self.assertFalse(catalog["coverage_complete"])
        self.assertFalse(catalog["independent_evidence_verified"])

    def test_bootstrap_never_requires_untriggered_runtime_incident(self):
        """Without an observed blocker, a current rule stays pending, not failed."""
        from check_execution_rule_evidence import bootstrap_main
        output = io.StringIO()
        with patch("sys.argv", ["check_execution_rule_evidence.py", "--bootstrap-report"]), \
                patch("check_execution_rule_evidence.verify_rule_receipts",
                      side_effect=AssertionError("runtime receipt called from bootstrap")), \
                patch("check_execution_rule_evidence.verify_evidence_bytes",
                      side_effect=AssertionError("runtime evidence called from bootstrap")), \
                redirect_stdout(output):
            self.assertEqual(0, bootstrap_main())
        rendered = output.getvalue()
        self.assertEqual(83, rendered.count("CFA3_RULE:"))
        self.assertIn("conditional runtime events are NOT required by bootstrap", rendered)
        self.assertIn("NOT execution authorization", rendered)

    def test_bootstrap_each_rule_code_presence_and_status_are_checked(self):
        from check_execution_rule_evidence import bootstrap_rule_report
        catalog = load(ROOT, CATALOG)
        for ident in expected_rules(self.governance):
            changed = copy.deepcopy(catalog)
            changed["rules"][ident]["code"] += "_CHANGED"
            with self.subTest(rule=ident, field="code"):
                self.assertTrue(bootstrap_rule_report(self.governance, changed)[1])
            changed = copy.deepcopy(catalog)
            del changed["rules"][ident]
            with self.subTest(rule=ident, field="missing"):
                self.assertTrue(bootstrap_rule_report(self.governance, changed)[1])
            changed = copy.deepcopy(catalog)
            changed["rules"][ident]["status"] = "AUTO_PASS"
            with self.subTest(rule=ident, field="status"):
                self.assertTrue(bootstrap_rule_report(self.governance, changed)[1])

    def test_bootstrap_rejects_false_coverage_and_restoration_drift(self):
        from check_execution_rule_evidence import bootstrap_rule_report
        catalog = load(ROOT, CATALOG)
        for change in ({"coverage_complete": True},
                       {"independent_evidence_verified": True}):
            altered = copy.deepcopy(catalog)
            altered.update(change)
            with self.subTest(change=change):
                self.assertTrue(bootstrap_rule_report(self.governance, altered)[1])
        altered = copy.deepcopy(catalog)
        for row in altered["rules"].values():
            row["status"] = "VERIFIED_GATE"
        self.assertTrue(bootstrap_rule_report(self.governance, altered)[1])
        for field, value in (
            ("source_count", 77), ("mapped_existing", 21),
            ("admitted_new", 55), ("excluded_for_conflict", 1),
            ("active_count", 24), ("all_source_rules_accounted_for", False)):
            altered = copy.deepcopy(catalog)
            altered["owner_historical_reconciliation"][field] = value
            with self.subTest(field=field):
                self.assertTrue(bootstrap_rule_report(self.governance, altered)[1])

if __name__ == "__main__":
    unittest.main()
