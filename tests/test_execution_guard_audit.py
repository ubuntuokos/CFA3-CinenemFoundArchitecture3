"""Mutation-audit gate regression tests; synthetic only, no real authority."""
import copy
import hashlib
import hmac
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_execution_guard_audit import SCHEMA, AuditBlocked, canonical_bytes, verify_audit_receipt
from check_execution_rule_evidence import request_digest

KEY = b"synthetic-independent-audit-test-key".ljust(32, b"_")
NOW = 1000.0

def task():
    return {
        "task_id": "synthetic-audit-task", "nonce": "synthetic-nonce-12345678",
        "operation": "REPOSITORY_WRITE", "main_sha": "a"*40, "head_sha": "b"*40,
        "branch": "guard/example", "target": "scripts/execution_guard.py",
        "scope_targets": ["scripts/execution_guard.py"],
        "expires_at": NOW + 100, "max_calls": 2, "max_units": 2,
    }

def issued(t, phase, previous=None):
    out = {
        "schema": SCHEMA, "task_sha256": request_digest(t),
        "task_id": t["task_id"], "nonce": t["nonce"],
        "operation": t["operation"], "main_sha": t["main_sha"],
        "phase": phase, "event_id": "synthetic-event-" + phase.lower(),
        "store_id": "isolated-test-audit-store",
        "sequence": 4 if previous else 3,
        "previous_receipt_sha256": previous["sha256"] if previous else None,
        "durably_committed": True, "issued_at": NOW - 1,
    }
    out["signature"] = hmac.new(KEY, canonical_bytes(out), hashlib.sha256).hexdigest()
    return out

def signed_again(row):
    row["signature"] = hmac.new(KEY, canonical_bytes(
        {k: v for k, v in row.items() if k != "signature"}),
        hashlib.sha256).hexdigest()
    return row

class AuditProofTests(unittest.TestCase):
    def check(self, t, row, phase="RESERVED", previous=None, key=KEY):
        return verify_audit_receipt(t, row, key, phase, previous=previous, now=NOW)

    def test_positive_synthetic_reserved_verified_chain(self):
        t = task()
        first = self.check(t, issued(t, "RESERVED"))
        self.assertEqual("VERIFIED", self.check(
            t, issued(t, "VERIFIED", first), "VERIFIED", first)["phase"])

    def test_positive_synthetic_reserved_failed_chain(self):
        t = task()
        first = self.check(t, issued(t, "RESERVED"))
        self.assertEqual("FAILED", self.check(
            t, issued(t, "FAILED", first), "FAILED", first)["phase"])

    def test_dev01_expired_task_records_only_bounded_signed_failed(self):
        t = dict(task(), expires_at=NOW + 3)
        first = verify_audit_receipt(
            t, issued(t, "RESERVED"), KEY, "RESERVED", now=NOW)
        failed = issued(t, "FAILED", first)
        failed["issued_at"] = NOW + 4
        signed_again(failed)
        result = verify_audit_receipt(
            t, failed, KEY, "FAILED", previous=first, now=NOW + 4)
        self.assertEqual("FAILED", result["phase"])

        # A completed operation, an initial reservation, a replayed pre-expiry
        # acknowledgement and an unchained FAILED are never accepted.
        verified = issued(t, "VERIFIED", first)
        verified["issued_at"] = NOW + 4
        signed_again(verified)
        with self.assertRaisesRegex(AuditBlocked, "timestamp"):
            verify_audit_receipt(
                t, verified, KEY, "VERIFIED", previous=first, now=NOW + 4)
        reserved = issued(t, "RESERVED")
        reserved["issued_at"] = NOW + 4
        signed_again(reserved)
        with self.assertRaisesRegex(AuditBlocked, "timestamp"):
            verify_audit_receipt(t, reserved, KEY, "RESERVED", now=NOW + 4)
        with self.assertRaises(AuditBlocked):
            verify_audit_receipt(t, failed, KEY, "FAILED", now=NOW + 4)
        old_event = issued(t, "FAILED", first)
        old_event["issued_at"] = NOW + 2
        signed_again(old_event)
        with self.assertRaisesRegex(AuditBlocked, "timestamp"):
            verify_audit_receipt(
                t, old_event, KEY, "FAILED", previous=first, now=NOW + 4)

        too_late = copy.deepcopy(failed)
        too_late["issued_at"] = NOW + 65
        signed_again(too_late)
        with self.assertRaisesRegex(AuditBlocked, "timestamp"):
            verify_audit_receipt(
                t, too_late, KEY, "FAILED", previous=first, now=NOW + 65)
        changed_chain = copy.deepcopy(failed)
        changed_chain["previous_receipt_sha256"] = "0" * 64
        signed_again(changed_chain)
        with self.assertRaisesRegex(AuditBlocked, "chain"):
            verify_audit_receipt(
                t, changed_chain, KEY, "FAILED", previous=first, now=NOW + 4)
        changed_sig = dict(failed, signature="0" * 64)
        with self.assertRaisesRegex(AuditBlocked, "signature"):
            verify_audit_receipt(
                t, changed_sig, KEY, "FAILED", previous=first, now=NOW + 4)

    def test_missing_or_noop_ack_is_denied(self):
        for value in (None, True, {}, []):
            with self.subTest(value=value), self.assertRaises(AuditBlocked):
                self.check(task(), value)

    def test_weak_wrong_or_missing_audit_key_denied(self):
        for key in (None, "", b"", b"weak", b"x"*32):
            with self.subTest(key=key), self.assertRaises(AuditBlocked):
                self.check(task(), issued(task(), "RESERVED"), key=key)

    def test_every_task_binding_is_exact_and_signed(self):
        t = task()
        receipt = issued(t, "RESERVED")
        for key, value in (
            ("task_id", "other"), ("nonce", "new-one"),
            ("operation", "WORKFLOW_START"), ("main_sha", "c"*40),
            ("head_sha", "c"*40), ("branch", "guard/other"),
            ("target", "docs/out.md"), ("scope_targets", ["docs/out.md"]),
            ("max_calls", 3), ("max_units", 3), ("expires_at", NOW + 60),
        ):
            forged_task = copy.deepcopy(t)
            forged_task[key] = value
            with self.subTest(key=key), self.assertRaises(AuditBlocked):
                self.check(forged_task, receipt)

    def test_tampered_receipt_and_false_durable_ack_denied(self):
        t = task()
        for key, value in (
            ("phase", "FAILED"), ("sequence", 0),
            ("event_id", "short"), ("store_id", "short"),
            ("durably_committed", False), ("issued_at", NOW+1),
            ("previous_receipt_sha256", "a"*64),
        ):
            modified = issued(t, "RESERVED")
            modified[key] = value
            with self.subTest(key=key), self.assertRaises(AuditBlocked):
                self.check(t, modified)

    def test_unexpected_second_event_without_initial_ack_denied(self):
        t = task()
        with self.assertRaises(AuditBlocked):
            self.check(t, issued(t, "VERIFIED"), "VERIFIED")

    def test_resigned_but_disconnected_chain_is_denied(self):
        t = task()
        first = self.check(t, issued(t, "RESERVED"))
        for key, value in (
            ("previous_receipt_sha256", "0"*64),
            ("sequence", 2), ("store_id", "other-store"),
            ("event_id", first["event_id"]),
        ):
            altered = issued(t, "VERIFIED", first)
            signed_again(dict(altered, **{key: value}))
            altered[key] = value
            signed_again(altered)
            with self.subTest(key=key), self.assertRaises(AuditBlocked):
                self.check(t, altered, "VERIFIED", first)

    def test_stale_or_future_signed_receipt_denied(self):
        t = task()
        for timestamp in (NOW - 61, NOW + 1):
            altered = issued(t, "RESERVED")
            altered["issued_at"] = timestamp
            signed_again(altered)
            with self.subTest(timestamp=timestamp), self.assertRaises(AuditBlocked):
                self.check(t, altered)

    def test_full_gateway_denies_noop_audit_before_executor(self):
        from execution_guard import (
            guarded_execute, Blocked, canonical_bytes as guard_bytes, load, GOV,
        )
        from test_execution_guard import sample
        from test_execution_rule_evidence import receipts, evidence_bytes, KEY as RULE_KEY
        sample_task = sample()
        task_key = b"synthetic-separate-task-signature".ljust(32, b"_")
        sample_task["signature"] = hmac.new(
            task_key, guard_bytes(sample_task), hashlib.sha256).hexdigest()
        emitted = receipts(sample_task, load(ROOT, GOV))
        evidence_store = {x["rule_id"]: evidence_bytes(x) for x in emitted}
        admission = {
            "current_83_rule_inventory_verified": True,
            "current_83_rule_gates_verified": True,
            "current_83_conflicts_resolved": True,
            "independent_proof_verified": True,
        }
        live_state = {
            "main_current": True, "head_current": True, "no_overlap": True,
            "checks_passed": True, "review_threads_clear": True,
            "owner_scope_approved": True, "owner_grant_signature_verified": True,
            "main_ruleset_verified": True, "privileged_bypass_actors_verified": True,
            "actual_main_sha": sample_task["main_sha"],
        }
        preflight = {
            "source_verified": True, "scope_verified": True,
            "resource_verified": True, "output_contract_verified": True,
        }
        called = []
        with tempfile.TemporaryDirectory() as tmp, patch(
                "execution_guard.policy_issues", return_value=[]), patch(
                "execution_guard.trusted_runtime_issues", return_value=[]), patch(
                "check_execution_rule_evidence.time.time", return_value=10000.0):
            with self.assertRaises(Blocked):
                guarded_execute(
                    sample_task, root=ROOT, secret=task_key,
                    admission=lambda _: admission, live_state=lambda _: live_state,
                    preflight=lambda _: preflight, executor=lambda _: called.append(True),
                    verify_result=lambda *_: True, audit=lambda *_: None,
                    state_dir=tmp, rule_attester=lambda _: emitted,
                    rule_attestation_secret=RULE_KEY,
                    rule_evidence_resolver=lambda name, _: evidence_store.get(name),
                    audit_attestation_secret=KEY,
                )
        self.assertEqual([], called)

if __name__ == "__main__":
    unittest.main()
