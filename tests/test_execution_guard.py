"""Negative-path guard tests; NOT full CFA3 admission or physical-host proof."""
import hashlib
import copy
import json
import os
import stat
import shutil
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
                             validate_current_rule_map, GUARD_SOURCE_BINDINGS,
                             trusted_runtime_issues)

def sample():
    sources = sorted(GUARD_SOURCE_BINDINGS.union(load(ROOT, CATALOG)["policy_files"]))
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
        self.assertTrue(expected.issubset(set(catalog["rules"])))
        self.assertEqual(83,len(catalog["rules"]))

    def test_78_owner_rules_active_with_24_original_unmodified(self):
        catalog=load(ROOT,CATALOG)
        self.assertEqual(83,len(catalog["rules"]))
        restored=catalog["owner_historical_reconciliation"]
        self.assertEqual(78,restored["source_count"])
        self.assertEqual(22,restored["mapped_existing"])
        self.assertEqual(56,restored["admitted_new"])
        self.assertEqual(0,restored["excluded_for_conflict"])
        self.assertEqual([],policy_issues(ROOT,require_prior_runtime_proofs=False))
        self.assertTrue(policy_issues(ROOT))
        
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

    def test_dev01_late_live_blocker_stops_executor_and_records_failure(self):
        """One rule only: never execute after preflight/live-state drift."""
        from check_execution_guard_audit import verify_audit_receipt
        from test_execution_guard_audit import issued, KEY as AUDIT_KEY
        from test_execution_rule_evidence import (
            receipts, evidence_bytes, KEY as RULE_KEY, NOW as RULE_NOW,
        )
        task_key = b"synthetic-dev01-owner-task-signature-key".ljust(32, b"_")
        admission = {
            "current_83_rule_inventory_verified": True,
            "current_83_rule_gates_verified": True,
            "current_83_conflicts_resolved": True,
            "independent_proof_verified": True,
        }
        preflight = {
            "source_verified": True, "scope_verified": True,
            "resource_verified": True, "output_contract_verified": True,
        }
        for failure in ("main", "head", "checks", "overlap", "review",
                        "ruleset", "read_error"):
            with self.subTest(late_blocker=failure):
                t = sample()
                t["operation"] = "REPOSITORY_WRITE"
                t["branch"] = "guard/dev01"
                t["head_sha"] = "b" * 40
                t["signature"] = hmac.new(
                    task_key, canonical_bytes(t), hashlib.sha256).hexdigest()
                issued_rules = receipts(t, load(ROOT, GOV))
                store = {r["rule_id"]: evidence_bytes(r) for r in issued_rules}
                good = {
                    "main_current": True, "head_current": True, "no_overlap": True,
                    "checks_passed": True, "review_threads_clear": True,
                    "owner_scope_approved": True,
                    "owner_grant_signature_verified": True,
                    "main_ruleset_verified": True,
                    "privileged_bypass_actors_verified": True,
                    "actual_main_sha": t["main_sha"],
                    "actual_head_sha": t["head_sha"],
                }
                observed, executed, audit_phases = [], [], []
                def state(_):
                    observed.append(True)
                    if len(observed) == 1:
                        return dict(good)
                    if failure == "read_error":
                        raise OSError("trusted GitHub state became unavailable")
                    changed = dict(good)
                    name = {
                        "main": "actual_main_sha",
                        "head": "actual_head_sha",
                        "checks": "checks_passed",
                        "overlap": "no_overlap",
                        "review": "review_threads_clear",
                        "ruleset": "main_ruleset_verified",
                    }[failure]
                    changed[name] = "c" * 40 if name.startswith("actual_") else False
                    return changed

                with (tempfile.TemporaryDirectory() as location,
                      patch("execution_guard.policy_issues", return_value=[]),
                      patch("execution_guard.trusted_runtime_issues", return_value=[]),
                      patch("test_execution_guard_audit.NOW", RULE_NOW),
                      patch("check_execution_rule_evidence.time.time",
                            return_value=RULE_NOW)):
                    reserved = issued(t, "RESERVED")
                    first = verify_audit_receipt(
                        t, reserved, AUDIT_KEY, "RESERVED", now=RULE_NOW)
                    failed = issued(t, "FAILED", first)
                    def audit(_, phase):
                        audit_phases.append(phase)
                        return {"RESERVED": reserved, "FAILED": failed}[phase]

                    with self.assertRaises(Blocked):
                        guarded_execute(
                            t, root=ROOT, secret=task_key,
                            admission=lambda _: admission,
                            live_state=state,
                            preflight=lambda _: preflight,
                            executor=lambda _: executed.append(True),
                            verify_result=lambda *_: True, audit=audit,
                            state_dir=location, rule_attester=lambda _: issued_rules,
                            rule_attestation_secret=RULE_KEY,
                            rule_evidence_resolver=lambda rid, _: store.get(rid),
                            audit_attestation_secret=AUDIT_KEY,
                        )
                self.assertEqual(2, len(observed))
                self.assertEqual(["RESERVED", "FAILED"], audit_phases)
                self.assertEqual([], executed)

    def test_dev01_expired_rule_proof_and_task_after_reservation(self):
        """After RESERVE, expiry of either rule proof or task must STOP."""
        from check_execution_guard_audit import verify_audit_receipt
        from test_execution_guard_audit import (
            issued, signed_again, KEY as AUDIT_KEY,
        )
        from test_execution_rule_evidence import (
            receipts, evidence_bytes, KEY as RULE_KEY, NOW as RULE_NOW,
        )
        signing_key = b"synthetic-dev01-owner-task-signature-key".ljust(32, b"_")
        for failure in ("rule_receipts_expired", "task_expired"):
            with self.subTest(failure=failure):
                t = sample()
                t["operation"] = "REPOSITORY_WRITE"
                t["branch"], t["head_sha"] = "guard/dev01", "b" * 40
                if failure == "task_expired":
                    t["expires_at"] = RULE_NOW + 12
                t["signature"] = hmac.new(
                    signing_key, canonical_bytes(t), hashlib.sha256).hexdigest()
                proofs = receipts(t, load(ROOT, GOV))
                store = {r["rule_id"]: evidence_bytes(r) for r in proofs}
                live_ok = {
                    "main_current": True, "head_current": True, "no_overlap": True,
                    "checks_passed": True, "review_threads_clear": True,
                    "owner_scope_approved": True, "owner_grant_signature_verified": True,
                    "main_ruleset_verified": True,
                    "privileged_bypass_actors_verified": True,
                    "actual_main_sha": t["main_sha"],
                    "actual_head_sha": t["head_sha"],
                }
                admission = {
                    "current_83_rule_inventory_verified": True,
                    "current_83_rule_gates_verified": True,
                    "current_83_conflicts_resolved": True,
                    "independent_proof_verified": True,
                }
                preflight = {
                    "source_verified": True, "scope_verified": True,
                    "resource_verified": True, "output_contract_verified": True,
                }
                clock = {"now": RULE_NOW}
                seen, executed, phases = [], [], []
                def live(_):
                    seen.append(True)
                    if failure == "rule_receipts_expired" and len(seen) == 2:
                        clock["now"] = RULE_NOW + 11
                    return dict(live_ok)

                with (tempfile.TemporaryDirectory() as location,
                      patch("execution_guard.policy_issues", return_value=[]),
                      patch("execution_guard.trusted_runtime_issues", return_value=[]),
                      patch("test_execution_guard_audit.NOW", RULE_NOW),
                      patch("check_execution_rule_evidence.time.time",
                            side_effect=lambda: clock["now"])):
                    reserved = issued(t, "RESERVED")
                    first = verify_audit_receipt(
                        t, reserved, AUDIT_KEY, "RESERVED", now=RULE_NOW)
                    def audit(_, phase):
                        phases.append(phase)
                        if phase == "RESERVED":
                            return reserved
                        failed = issued(t, "FAILED", first)
                        if failure == "task_expired":
                            failed["issued_at"] = clock["now"]
                            signed_again(failed)
                        return failed

                    def verified_audit(*args, **kwargs):
                        result = verify_audit_receipt(*args, **kwargs)
                        # Expire only after the RESERVED receipt was accepted.
                        if failure == "task_expired" and args[3] == "RESERVED":
                            clock["now"] = RULE_NOW + 13
                        return result

                    with (patch("check_execution_guard_audit.verify_audit_receipt",
                                side_effect=verified_audit),
                          self.assertRaisesRegex(
                              Blocked,
                              "late rule proof invalid" if failure ==
                              "rule_receipts_expired" else "expired task authorization")):
                        guarded_execute(
                            t, root=ROOT, secret=signing_key,
                            admission=lambda _: admission, live_state=live,
                            preflight=lambda _: preflight,
                            executor=lambda _: executed.append(True),
                            verify_result=lambda *_: True, audit=audit,
                            state_dir=location, rule_attester=lambda _: proofs,
                            rule_attestation_secret=RULE_KEY,
                            rule_evidence_resolver=lambda rid, _: store.get(rid),
                            audit_attestation_secret=AUDIT_KEY,
                        )
                self.assertEqual([], executed)
                self.assertEqual(["RESERVED", "FAILED"], phases)
                self.assertEqual(1 if failure == "task_expired" else 2, len(seen))

    def test_dev01_rule_resolver_drift_rechecked_after_evidence(self):
        """Live PR overlap arising during 83 evidence reads must stop mutation."""
        from check_execution_guard_audit import verify_audit_receipt
        from test_execution_guard_audit import issued, KEY as AUDIT_KEY
        from test_execution_rule_evidence import (
            receipts, evidence_bytes, KEY as RULE_KEY, NOW as RULE_NOW,
        )
        t = sample()
        t["operation"] = "REPOSITORY_WRITE"
        t["branch"], t["head_sha"] = "guard/dev01", "b" * 40
        task_key = b"synthetic-dev01-owner-task-signature-key".ljust(32, b"_")
        t["signature"] = hmac.new(
            task_key, canonical_bytes(t), hashlib.sha256).hexdigest()
        bundle = receipts(t, load(ROOT, GOV))
        store = {r["rule_id"]: evidence_bytes(r) for r in bundle}
        evidence_calls, live_calls, phases, executed = [], [], [], []
        drift = {"overlap": False}

        def resolver(ident, digest):
            evidence_calls.append(ident)
            # Start a conflicting PR exactly when the second 83-rule
            # revalidation begins, after the previous live authorization.
            if len(evidence_calls) == len(bundle) + 1:
                drift["overlap"] = True
            return store.get(ident)

        def live(_):
            live_calls.append(True)
            return {
                "main_current": True, "head_current": True,
                "no_overlap": not drift["overlap"],
                "checks_passed": True, "review_threads_clear": True,
                "owner_scope_approved": True,
                "owner_grant_signature_verified": True,
                "main_ruleset_verified": True,
                "privileged_bypass_actors_verified": True,
                "actual_main_sha": t["main_sha"],
                "actual_head_sha": t["head_sha"],
            }

        admission = {
            "current_83_rule_inventory_verified": True,
            "current_83_rule_gates_verified": True,
            "current_83_conflicts_resolved": True,
            "independent_proof_verified": True,
        }
        preflight = {
            "source_verified": True, "scope_verified": True,
            "resource_verified": True, "output_contract_verified": True,
        }
        with (tempfile.TemporaryDirectory() as location,
              patch("execution_guard.policy_issues", return_value=[]),
              patch("execution_guard.trusted_runtime_issues", return_value=[]),
              patch("test_execution_guard_audit.NOW", RULE_NOW),
              patch("check_execution_rule_evidence.time.time",
                    return_value=RULE_NOW)):
            reserved = issued(t, "RESERVED")
            first = verify_audit_receipt(
                t, reserved, AUDIT_KEY, "RESERVED", now=RULE_NOW)
            failed = issued(t, "FAILED", first)

            def audit(_, phase):
                phases.append(phase)
                return {"RESERVED": reserved, "FAILED": failed}[phase]

            with self.assertRaisesRegex(
                    Blocked, "fresh exact-state authorization failed"):
                guarded_execute(
                    t, root=ROOT, secret=task_key, admission=lambda _: admission,
                    live_state=live, preflight=lambda _: preflight,
                    executor=lambda _: executed.append(True),
                    verify_result=lambda *_: True, audit=audit,
                    state_dir=location, rule_attester=lambda _: bundle,
                    rule_attestation_secret=RULE_KEY,
                    rule_evidence_resolver=resolver,
                    audit_attestation_secret=AUDIT_KEY,
                )
        self.assertEqual(3, len(live_calls))
        self.assertEqual(2 * len(bundle), len(evidence_calls))
        self.assertEqual(["RESERVED", "FAILED"], phases)
        self.assertEqual([], executed)

    def test_dev01_rule_expiry_during_final_live_snapshot(self):
        """A slow final GitHub read must not authorize expired PASS receipts."""
        from check_execution_guard_audit import verify_audit_receipt
        from test_execution_guard_audit import issued, KEY as AUDIT_KEY
        from test_execution_rule_evidence import (
            receipts, evidence_bytes, KEY as RULE_KEY, NOW as RULE_NOW,
        )
        t = sample()
        t["operation"] = "REPOSITORY_WRITE"
        t["branch"], t["head_sha"] = "guard/dev01", "b" * 40
        key = b"synthetic-dev01-owner-task-signature-key".ljust(32, b"_")
        t["signature"] = hmac.new(
            key, canonical_bytes(t), hashlib.sha256).hexdigest()
        bundle = receipts(t, load(ROOT, GOV))
        store = {r["rule_id"]: evidence_bytes(r) for r in bundle}
        clock = {"now": RULE_NOW}
        live_calls, executed, phases = [], [], []

        def live(_):
            live_calls.append(True)
            if len(live_calls) == 3:
                # Expire the signed rule receipts during the final GitHub
                # network snapshot, after the second evidence validation.
                clock["now"] = RULE_NOW + 11
            return {
                "main_current": True, "head_current": True,
                "no_overlap": True, "checks_passed": True,
                "review_threads_clear": True, "owner_scope_approved": True,
                "owner_grant_signature_verified": True,
                "main_ruleset_verified": True,
                "privileged_bypass_actors_verified": True,
                "actual_main_sha": t["main_sha"],
                "actual_head_sha": t["head_sha"],
            }

        admission = {
            "current_83_rule_inventory_verified": True,
            "current_83_rule_gates_verified": True,
            "current_83_conflicts_resolved": True,
            "independent_proof_verified": True,
        }
        preflight = {
            "source_verified": True, "scope_verified": True,
            "resource_verified": True, "output_contract_verified": True,
        }
        with (tempfile.TemporaryDirectory() as location,
              patch("execution_guard.policy_issues", return_value=[]),
              patch("execution_guard.trusted_runtime_issues", return_value=[]),
              patch("test_execution_guard_audit.NOW", RULE_NOW),
              patch("check_execution_rule_evidence.time.time",
                    side_effect=lambda: clock["now"])):
            reserved = issued(t, "RESERVED")
            first = verify_audit_receipt(
                t, reserved, AUDIT_KEY, "RESERVED", now=RULE_NOW)
            failed = issued(t, "FAILED", first)
            def audit(_, phase):
                phases.append(phase)
                return {"RESERVED": reserved, "FAILED": failed}[phase]
            with self.assertRaisesRegex(
                    Blocked, "RULE_GATE: rule evidence expired before execution"):
                guarded_execute(
                    t, root=ROOT, secret=key, admission=lambda _: admission,
                    live_state=live, preflight=lambda _: preflight,
                    executor=lambda _: executed.append(True),
                    verify_result=lambda *_: True, audit=audit,
                    state_dir=location, rule_attester=lambda _: bundle,
                    rule_attestation_secret=RULE_KEY,
                    rule_evidence_resolver=lambda rid, _: store.get(rid),
                    audit_attestation_secret=AUDIT_KEY,
                )
        self.assertEqual(3, len(live_calls))
        self.assertEqual(["RESERVED", "FAILED"], phases)
        self.assertEqual([], executed)

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

    def test_corrupt_persisted_quota_ledger_denied_before_reservation(self):
        t = sample()
        with tempfile.TemporaryDirectory() as location:
            _reserve(location, t)
            ledger = Path(location) / "receipts.json"
            initial = json.loads(ledger.read_text("utf-8"))
            next_task = dict(t, nonce="next-unique-nonce")
            mutations = {
                "missing global inventory": lambda d: d.pop("_used_nonces"),
                "missing global nonce": lambda d: d.update(_used_nonces=[]),
                "unowned global nonce": lambda d: d["_used_nonces"].append("orphan"),
                "duplicate global nonce": lambda d: d["_used_nonces"].append(t["nonce"]),
                "invalid global nonce": lambda d: d.update(_used_nonces=[42]),
                "wrong global type": lambda d: d.update(_used_nonces={}),
                "missing task nonce": lambda d: d[t["task_id"]].update(nonces=[]),
                "duplicate task nonce": lambda d: d[t["task_id"]]["nonces"].append(t["nonce"]),
                "negative calls": lambda d: d[t["task_id"]].update(calls=-1),
                "negative units": lambda d: d[t["task_id"]].update(units=-1),
                "boolean calls": lambda d: d[t["task_id"]].update(calls=True),
                "boolean units": lambda d: d[t["task_id"]].update(units=True),
                "counter mismatch": lambda d: d[t["task_id"]].update(calls=2),
                "zero units used": lambda d: d[t["task_id"]].update(units=0),
                "invalid task binding": lambda d: d[t["task_id"]].update(binding="z" * 64),
                "unexpected task fields": lambda d: d[t["task_id"]].update(extra=True),
                "duplicate nonce in another task": lambda d: d.update(
                    another=copy.deepcopy(d[t["task_id"]])),
                "malformed extra task": lambda d: d.update(another={"nonces": []}),
            }
            for label, mutation in mutations.items():
                with self.subTest(corruption=label):
                    damaged = copy.deepcopy(initial)
                    mutation(damaged)
                    ledger.write_text(json.dumps(damaged), "utf-8")
                    with self.assertRaisesRegex(Blocked, "quota ledger invalid"):
                        _reserve(location, next_task)
                    self.assertEqual(damaged, json.loads(ledger.read_text("utf-8")))
            ledger.write_text(json.dumps(initial), "utf-8")
            _reserve(location, next_task)
            self.assertEqual(2, json.loads(ledger.read_text("utf-8"))[t["task_id"]]["calls"])

    def test_quota_files_owner_only_and_lock_state_not_symlinks(self):
        for fault in ("directory", "lock", "ledger", "hardlink_lock",
                      "hardlink_ledger", "symlink_lock", "symlink_ledger"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as location:
                t = sample()
                _reserve(location, t)
                directory = Path(location)
                lock = directory / "lock"
                ledger = directory / "receipts.json"
                self.assertEqual(0o600, stat.S_IMODE(lock.stat().st_mode))
                self.assertEqual(0o600, stat.S_IMODE(ledger.stat().st_mode))
                expected = ledger.read_bytes()
                if fault == "directory":
                    os.chmod(directory, 0o750)
                elif fault == "lock":
                    os.chmod(lock, 0o640)
                elif fault == "ledger":
                    os.chmod(ledger, 0o644)
                elif fault == "hardlink_lock":
                    os.link(lock, directory / "linked-lock")
                elif fault == "hardlink_ledger":
                    os.link(ledger, directory / "linked-ledger")
                elif fault == "symlink_lock":
                    lock.unlink()
                    os.symlink(ledger, lock)
                else:
                    saved = directory / "saved-receipts"
                    ledger.rename(saved)
                    os.symlink(saved, ledger)
                with self.assertRaises(Blocked):
                    _reserve(location, dict(t, nonce="other-private-nonce"))
                if fault == "directory":
                    os.chmod(directory, 0o700)
                if fault == "symlink_ledger":
                    self.assertEqual(expected, (directory / "saved-receipts").read_bytes())
                else:
                    self.assertEqual(expected, ledger.read_bytes())

    def test_private_quota_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as location:
            alias = Path(location) / "quota-link"
            private = Path(location) / "private"
            private.mkdir(mode=0o700)
            os.symlink(private, alias)
            with self.assertRaisesRegex(Blocked, "owner-only"):
                _reserve(alias, sample())

    def test_quota_ledger_tracks_independent_task_nonces(self):
        with tempfile.TemporaryDirectory() as location:
            t = sample()
            _reserve(location, t)
            _reserve(location, dict(t, task_id="other-task", nonce="other-task-nonce"))
            state = json.loads((Path(location) / "receipts.json").read_text("utf-8"))
            self.assertEqual({"single", "other-task-nonce"}, set(state["_used_nonces"]))
            self.assertEqual(1, state[t["task_id"]]["calls"])
            self.assertEqual(1, state["other-task"]["calls"])
            with self.assertRaisesRegex(Blocked, "reserved quota ledger identity"):
                _reserve(location, dict(t, task_id="_used_nonces", nonce="reserved"))

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
        ok = dict(current_24_rule_inventory_verified=True,
                  current_24_rule_gates_verified=True,
                  current_24_conflicts_resolved=True,
                  independent_proof_verified=True)
        state = dict(main_current=True, head_current=True, no_overlap=True,
                     checks_passed=True, review_threads_clear=True,
                     owner_scope_approved=True,
                     owner_grant_signature_verified=True, main_ruleset_verified=True,
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

    def test_legacy_candidates_archived_without_runtime_authority(self):
        history = load(ROOT, "canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json")
        self.assertEqual(78, sum(len(g["rule_pointers"]) for g in history["candidate_groups"]))
        self.assertTrue(all(g["owner_admitted"] is True for g in history["candidate_groups"]))
        self.assertFalse(history["decisions_complete"])
        for path in (LEDGER, "canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json",
                     "canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json",
                     "scripts/check_legacy_rule_blobs.py",
                     "scripts/check_execution_guard_history.py"):
            with self.subTest(path=path):
                self.assertNotIn(path, GUARD_SOURCE_BINDINGS)

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

    def test_all_guard_and_authoritative_manifests_bound_in_signed_contract(self):
        self.assertGreaterEqual(len(GUARD_SOURCE_BINDINGS), 12)
        for name in sorted(GUARD_SOURCE_BINDINGS):
            self.assertTrue((ROOT / name).is_file(), name)
            bad = sample()
            del bad["source_hashes"][name]
            with self.subTest(name=name, mutation="missing"), self.assertRaises(Blocked):
                check_task(ROOT, bad)
            bad = sample()
            bad["source_hashes"][name] = "0" * 64
            with self.subTest(name=name, mutation="modified"), self.assertRaises(Blocked):
                check_task(ROOT, bad)

    def test_all_canonical_policy_source_hashes_mandatory(self):
        for name in load(ROOT, CATALOG)["policy_files"]:
            bad = sample()
            del bad["source_hashes"][name]
            with self.subTest(name=name), self.assertRaises(Blocked):
                check_task(ROOT, bad)

    def test_owner_restoration_contract_drift_fails_closed(self):
        current=load(ROOT,CATALOG)
        for key,value in (("source_count",77),("mapped_existing",21),
                          ("admitted_new",55),("excluded_for_conflict",1),
                          ("active_count",79)):
            bad=copy.deepcopy(current)
            bad["owner_historical_reconciliation"][key]=value
            with patch("execution_guard.load",side_effect=lambda root,name:
                       bad if name==CATALOG else load(root,name)):
                with self.subTest(key=key):
                    self.assertTrue(policy_issues(ROOT))
        
    def test_structural_policy_does_not_require_random_runtime_events(self):
        self.assertEqual([], policy_issues(ROOT, require_prior_runtime_proofs=False))
        self.assertTrue(any("active per-rule" in issue for issue in policy_issues(ROOT)))
        self.assertTrue(any("independent gate" in issue for issue in policy_issues(ROOT)))

    def test_custom_root_policy_code_with_matching_surface_sha_is_rejected(self):
        """Policy source authority must follow the requested staged tree, not module ROOT."""
        from check_guard_policy_surface import git_blob_sha
        catalog=load(ROOT,CATALOG)
        paths=set(catalog["policy_files"]).union((
            GOV, CATALOG,
            "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json",
            "canonical/registries/CFA3-EXECUTION-GUARD-OWNER-RULE-SPEC-001.json",
            "docs/governance/exports/CFA3-EXECUTION-GUARD-RULES-AND-CANDIDATES-20261011.json"))
        with tempfile.TemporaryDirectory() as tmp:
            staging=Path(tmp)
            for relative in paths:
                destination=staging/relative
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,destination)
            self.assertEqual([],policy_issues(staging,require_prior_runtime_proofs=False))
            relative="canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json"
            target=staging/relative
            source=json.loads(target.read_text("utf-8"))
            source["rule"]["code"]="TAMPERED_STAGED_RULE_CODE"
            target.write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            surface_path=staging/"canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json"
            surface=json.loads(surface_path.read_text("utf-8"))
            for entry in surface["sources"]:
                if entry["path"]==relative:
                    entry["git_blob_sha1"]=git_blob_sha(target.read_bytes())
                    break
            else:
                self.fail("staged policy missing from source surface")
            surface_path.write_text(json.dumps(surface,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            findings=policy_issues(staging,require_prior_runtime_proofs=False)
            self.assertTrue(any("new owner rule does not match its canonical policy" in x for x in findings),findings)

    def test_unverified_independent_services_block_before_rule_evaluation(self):
        catalog = load(ROOT, CATALOG)
        self.assertEqual(83, len(catalog["rules"]))
        missing = trusted_runtime_issues(catalog)
        for part in ("rule attester", "rule evaluator", "evidence resolver",
                     "content store", "mutation audit", "owner signing service"):
            with self.subTest(part=part):
                self.assertTrue(any(part in issue for issue in missing))
        called = []
        with patch("execution_guard.policy_issues", return_value=[]):
            with self.assertRaisesRegex(Blocked, "RUNTIME_AUTHORITY_UNAVAILABLE"):
                guarded_execute(sample(), root=ROOT, secret=b"x" * 32,
                                rule_attester=lambda _: called.append("rule"),
                                executor=lambda _: called.append("executor"))
        self.assertEqual([], called)

    def test_current_rule_code_drift_and_pending_proof_still_block(self):
        gov = load(ROOT, GOV)
        cat = load(ROOT, CATALOG)
        self.assertEqual(83, len(cat["rules"]))
        self.assertEqual([], validate_current_rule_map(gov, cat))
        self.assertTrue(any("active per-rule" in x for x in policy_issues(ROOT)))
        self.assertTrue(any("independent gate" in x for x in policy_issues(ROOT)))

if __name__ == "__main__":
    unittest.main()
