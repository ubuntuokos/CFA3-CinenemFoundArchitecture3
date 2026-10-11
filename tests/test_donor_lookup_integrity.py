"""Public lookup regressions for the five post-merge donor review findings."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_transfer_integrity as integrity
import transfer_donors
from donor_reference_lookup import lookup_snapshot, ValidatedSnapshot
from source_lifecycle import evaluate, note_revisions


class DonorLookupIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(transfer_donors.OUTPUT.read_text())
        cls.index = json.loads((integrity.REG / "CFA3-SOURCE-LIFECYCLE-INDEX-001.json").read_text())
        cls.rows = {row["source_id"]: row for row in cls.snapshot["records"]}

    def test_notes_only_upstream_revision_reuses_but_pr_revision_does_not(self):
        cases = {
            "FA3-DONOR-AGENTSCOPE-AI-AGENTSCOPE-001": "72f3f6fa0b2fc38b8517f408ab616f0f2bd229e6",
            "FA3-DONOR-ASCEND-PYTORCH-001": "9cd8d1f1483f8268944d80392d4aa91fd455339f",
        }
        for sid, revision in cases.items():
            url = self.rows[sid]["historical_record"]["source"]["locator"]
            observation = {"verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
                           "evidence_ref": "unit-test-observation-not-current-upstream-proof",
                           "checked_at": "2026-10-11", "support_status": "SUPPORTED",
                           "observed_revision": revision}
            answer = evaluate(url, self.index, observation)
            self.assertEqual(answer["disposition"], "REUSE_PRIOR_DECISION")
            self.assertEqual(answer["prior_decision"]["historical_upstream_evidence"]["notes"],
                             self.rows[sid]["historical_record"]["notes"])
            observation["observed_revision"] = "aab23277cf7d38d7b55b73bf0cae12491cb49dde"
            self.assertEqual(evaluate(url, self.index, observation)["disposition"], "CHANGE_REVIEW_REQUIRED")

    def test_note_parser_keeps_uncertainty_and_rejects_non_revision_hashes(self):
        self.assertEqual(note_revisions(["Materialized from donor-intake PR #704 exact head " + "a" * 40]), set())
        self.assertEqual(note_revisions(["Observed upstream revision at intake: abc123."]), set())
        self.assertEqual(note_revisions(["Upstream sha256 " + "a" * 64]), set())
        self.assertEqual(note_revisions(["Upstream " + "a" * 40, "Upstream " + "b" * 40]),
                         {"a" * 40, "b" * 40})

    def test_all_preserved_previous_locators_and_legacy_keys_are_searchable(self):
        aliases = {}
        for row in self.snapshot["records"]:
            history = row["historical_record"]
            for url in [*history.get("source", {}).get("previous_locators", []),
                        *history.get("legacy_source_keys", [])]:
                aliases[url] = row["source_id"]
        self.assertTrue(aliases)
        self.assertEqual(aliases["project:OpenCut"], "FA3-DONOR-OPENCUT-001")
        self.assertEqual(aliases["project:opencut"], "FA3-DONOR-OPENCUT-001")
        for url, sid in aliases.items():
            with self.subTest(url=url):
                self.assertEqual(evaluate(url, self.index)["source_id"], sid)
                self.assertEqual(lookup_snapshot(self.snapshot, original_url=url)["donor_id"], sid)

    def test_dangling_route_is_integrity_error_but_unknown_id_is_not_found(self):
        data = copy.deepcopy(self.snapshot)
        route = data["locator_routes"][0]
        route["preferred_source_id"] = "absent-id"
        route["related_source_ids"] = ["absent-id"]
        with self.assertRaisesRegex(ValueError, "missing donor"):
            lookup_snapshot(data, original_url=route["alias"])
        self.assertIsNone(lookup_snapshot(self.snapshot, donor_id="absent-id"))

    def test_all_56_current_confirmations_are_visible_and_bound(self):
        confirmations = json.loads(transfer_donors.OWNER_CONFIRMATION.read_text())
        self.assertEqual(len(confirmations["confirmed_records"]), 56)
        for row in confirmations["confirmed_records"]:
            answer = evaluate(row["original_locator"], self.index)
            self.assertEqual(answer["disposition"], "CHANGE_CHECK_REQUIRED")
            self.assertEqual(answer["prior_decision"]["owner_approval"]["record"], row)
        bad = copy.deepcopy(self.index)
        sid = confirmations["confirmed_records"][0]["source_id"]
        next(row for row in bad["source_records"] if row["source_id"] == sid)["prior_decision"]["owner_approval"] = None
        self.assertEqual(evaluate(confirmations["confirmed_records"][0]["original_locator"], bad)["disposition"],
                         "BLOCKED_INDEX_CONFLICT")

    def test_changed_files_after_cache_warmup_fail_closed(self):
        url = "https://github.com/ExistentialAudio/BlackHole"
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp)
            transfer = reg / integrity.TRANSFER_NAME
            confirmation = reg / integrity.CONFIRMATION_NAME
            for name in integrity.PROJECTION_INPUTS:
                shutil.copyfile(integrity.REG / name, reg / name)
            original_confirmation = confirmation.read_bytes()
            with patch.object(integrity, "REG", reg), \
                 patch.object(integrity, "OWNER_CONFIRMATION", confirmation), \
                 patch.object(transfer_donors, "OWNER_CONFIRMATION", confirmation):
                self.assertEqual(evaluate(url, self.index)["disposition"], "CHANGE_CHECK_REQUIRED")
                altered = copy.deepcopy(self.snapshot)
                altered["records"][0]["historical_record"]["notes"] = ["tampered"]
                altered["record_set_sha256"] = transfer_donors.digest(altered["records"])
                raw = (json.dumps(altered) + "\n").encode()
                transfer.write_bytes(raw)
                bad_index = copy.deepcopy(self.index)
                bad_index["input_sha256"][integrity.TRANSFER_NAME] = hashlib.sha256(raw).hexdigest()
                self.assertEqual(evaluate(url, bad_index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                shutil.copyfile(transfer_donors.OUTPUT, transfer)
                transfer.write_bytes(transfer.read_bytes() + b" ")
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                shutil.copyfile(transfer_donors.OUTPUT, transfer)
                doc = json.loads(original_confirmation)
                doc["confirmed_records"][0]["original_locator"] = "https://invalid.example"
                confirmation.write_text(json.dumps(doc))
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                confirmation.write_bytes(original_confirmation + b" ")
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                confirmation.unlink()
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")

    def test_lookup_rejects_corruption_outside_selected_record_and_indexes(self):
        sid = self.snapshot["records"][0]["source_id"]
        corruptions = [
            lambda d: d.__setitem__("record_count", 1),
            lambda d: d.__setitem__("record_set_sha256", "0" * 64),
            lambda d: d["records"][-1]["historical_record"].__setitem__("notes", ["altered"]),
            lambda d: d["lookup_by_id"].pop(d["records"][-1]["source_id"]),
            lambda d: d["lookup_by_locator"].pop(d["locator_routes"][-1]["alias"]),
        ]
        self.assertEqual(lookup_snapshot(self.snapshot, donor_id=sid)["donor_id"], sid)
        for corrupt in corruptions:
            bad = copy.deepcopy(self.snapshot)
            corrupt(bad)
            with self.assertRaises(ValueError):
                lookup_snapshot(bad, donor_id=sid)

    def test_existing_identity_cannot_replace_preserved_lifecycle_route(self):
        bad = copy.deepcopy(self.index)
        route = next(r for r in bad["locator_routes"] if r["alias"] == "project:OpenCut")
        route["preferred_source_id"] = "FA3-DONOR-AGENTSCOPE-AI-AGENTSCOPE-001"
        route["related_source_ids"] = [route["preferred_source_id"]]
        self.assertEqual(evaluate("project:OpenCut", bad)["disposition"], "BLOCKED_INDEX_CONFLICT")

    def test_every_projected_decision_and_provenance_field_is_bound(self):
        fields = {
            "decision_id": "forged-decision", "revision": "0" * 64,
            "outcome": "ACCEPTED_REFERENCE", "historical_outcome": "ACCEPTED_REFERENCE",
            "submission_review": {"approved": True}, "intake_provenance": {"approved": True},
            "owner_approval": {"approved": True}, "canonical_reference_registration": {},
        }
        for field, altered in fields.items():
            with self.subTest(field=field):
                bad = copy.deepcopy(self.index)
                row = next(r for r in bad["source_records"] if r["reference_state"] == "CANDIDATE_PRESERVED")
                row["prior_decision"][field] = altered
                self.assertEqual(evaluate(row["canonical_url"], bad)["disposition"], "BLOCKED_INDEX_CONFLICT")
        bad = copy.deepcopy(self.index)
        bad["source_records"][0]["observed_revision"] = "0" * 40
        self.assertEqual(evaluate(bad["source_records"][0]["canonical_url"], bad)["disposition"], "BLOCKED_INDEX_CONFLICT")

    def test_confirmation_document_cannot_target_another_snapshot(self):
        original = json.loads(transfer_donors.OWNER_CONFIRMATION.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / integrity.CONFIRMATION_NAME
            with patch.object(transfer_donors, "OWNER_CONFIRMATION", path), \
                 patch.object(integrity, "OWNER_CONFIRMATION", path):
                for field in ("id", "source_commit", "transfer_snapshot_id"):
                    with self.subTest(field=field):
                        bad = copy.deepcopy(original)
                        bad[field] = "unrelated-snapshot"
                        path.write_text(json.dumps(bad))
                        with self.assertRaises(ValueError):
                            integrity.confirmation_evidence()

    def test_returned_evidence_cannot_mutate_later_lookup(self):
        url = "https://github.com/agentscope-ai/agentscope"
        answer = evaluate(url, self.index)
        answer["prior_decision"]["historical_upstream_evidence"]["notes"].append("forged")
        again = evaluate(url, self.index)
        self.assertNotIn("forged", again["prior_decision"]["historical_upstream_evidence"]["notes"])

    def test_retaining_lookup_result_does_not_invalidate_identical_value_cache(self):
        integrity._validate_snapshot_payload.cache_clear()
        sid = self.snapshot["records"][0]["source_id"]
        held = lookup_snapshot(self.snapshot, donor_id=sid)
        before = integrity._validate_snapshot_payload.cache_info()
        again = lookup_snapshot(self.snapshot, donor_id=sid)
        after = integrity._validate_snapshot_payload.cache_info()
        self.assertEqual(held, again)
        self.assertEqual(after.misses, before.misses)
        self.assertEqual(after.hits, before.hits + 1)


    def test_all_rejections_are_bound_to_pinned_archive(self):
        sid = self.snapshot["records"][0]["source_id"]
        original = self.snapshot["rejection_audit"]["entries"][0]
        changes = [
            lambda d: d["rejection_audit"]["entries"].clear(),
            lambda d: d["rejection_audit"]["entries"][0]["donor"].__setitem__("status", "VERIFIED_SAFE"),
            lambda d: d["rejection_audit"]["entries"].append(copy.deepcopy(original)),
            lambda d: d["rejection_audit"].__setitem__("authority", True),
            lambda d: d["rejection_audit"]["entries"][0]["donor"]["source"].__setitem__(
                "locator", "project:forged"),
        ]
        for change in changes:
            bad = copy.deepcopy(self.snapshot)
            change(bad)
            with self.assertRaisesRegex(ValueError, "rejection audit"):
                lookup_snapshot(bad, donor_id=sid)
            with self.assertRaisesRegex(ValueError, "rejection audit"):
                ValidatedSnapshot(bad)

    def test_archive_tampering_cannot_use_warm_validation_cache(self):
        sid = self.snapshot["records"][0]["source_id"]
        lookup_snapshot(self.snapshot, donor_id=sid)  # warm whole-snapshot cache
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / integrity.REJECTION_ARCHIVE.name
            archive.write_bytes(integrity.REJECTION_ARCHIVE.read_bytes())
            with patch.object(integrity, "REJECTION_ARCHIVE", archive):
                self.assertEqual(lookup_snapshot(self.snapshot, donor_id=sid)["donor_id"], sid)
                archive.write_bytes(archive.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "rejection audit Git blob"):
                    lookup_snapshot(self.snapshot, donor_id=sid)

    def test_immutable_handle_preserves_full_batch_identity_and_isolation(self):
        handle = ValidatedSnapshot(self.snapshot)
        first_id = self.snapshot["records"][0]["source_id"]
        record = lookup_snapshot(handle, donor_id=first_id)
        record["donor_registration"] = "FORGED"
        self.assertNotEqual(lookup_snapshot(handle, donor_id=first_id)["donor_registration"], "FORGED")
        with self.assertRaises(TypeError):
            handle._data["records"][0]["reference_record"]["donor_registration"] = "FORGED"
        with self.assertRaises(AttributeError):
            handle._data = self.snapshot
        with self.assertRaises(AttributeError):
            handle._previous = {"unverified-alias": first_id}
        with self.assertRaises(TypeError):
            handle[0] = self.snapshot
        # Both public lookup indexes must be usable without whole-snapshot hashing.
        with patch("donor_reference_lookup.validate_snapshot",
                   side_effect=AssertionError("revalidation in immutable batch")):
            for row in self.snapshot["records"]:
                result = lookup_snapshot(handle, donor_id=row["source_id"])
                self.assertEqual(result["donor_id"], row["source_id"])
            for route in self.snapshot["locator_routes"]:
                result = lookup_snapshot(handle, original_url=route["alias"])
                self.assertEqual(result["donor_id"], route["preferred_source_id"])
        self.assertIsNone(lookup_snapshot(handle, donor_id="unknown-source-id"))
        rejected = lookup_snapshot(handle, original_url="project:donutbrowser")
        self.assertEqual(rejected["donor_registration"], "REJECTED_REFERENCE_NOT_ACTIVE")
        rejected["rejection_history"]["donor"]["status"] = "FORGED"
        self.assertEqual(lookup_snapshot(handle, original_url="project:donutbrowser")
                         ["rejection_history"]["donor"]["status"], "REJECTED")

    def test_mutating_original_after_handle_creation_cannot_poison_batch(self):
        original = copy.deepcopy(self.snapshot)
        handle = ValidatedSnapshot(original)
        sid = original["records"][0]["source_id"]
        original["records"][0]["historical_record"]["notes"] = ["POISON"]
        self.assertEqual(lookup_snapshot(handle, donor_id=sid)["donor_id"], sid)
        with self.assertRaises(ValueError):
            lookup_snapshot(original, donor_id=sid)


    def test_verified_snapshot_cache_is_not_mutable_by_lookup_callers(self):
        original = self.snapshot["records"][0]["pre_transfer_status"]
        dirty, sha = integrity.verified_snapshot()
        dirty["records"][0]["pre_transfer_status"] = "FORGED_STATUS"
        dirty["rejection_audit"]["entries"][0]["donor"]["source"]["locator"] = "project:forged"
        fresh, fresh_sha = integrity.verified_snapshot()
        self.assertEqual(sha, fresh_sha)
        self.assertEqual(fresh["records"][0]["pre_transfer_status"], original)
        self.assertEqual(fresh["rejection_audit"]["entries"][0]["donor"]["source"]["locator"],
                         "project:donutbrowser")
        self.assertNotEqual(evaluate("project:forged", self.index)["disposition"],
                            "BLOCKED_REJECTED_SOURCE")
        self.assertEqual(evaluate("project:donutbrowser", self.index)["disposition"],
                         "BLOCKED_REJECTED_SOURCE")

    def test_lifecycle_expected_projection_cache_cannot_be_poisoned(self):
        expected = integrity.expected_lifecycle_projection()
        route_preferred = self.index["locator_routes"][0]["preferred_source_id"]
        sid = next(row["source_id"] for row in self.index["source_records"]
                   if row["source_id"] != route_preferred)
        expected["source_records"][0]["prior_decision"]["outcome"] = "FORGED_DECISION"
        expected["locator_routes"][0]["preferred_source_id"] = sid
        fresh = integrity.expected_lifecycle_projection()
        self.assertNotEqual(fresh["source_records"][0]["prior_decision"]["outcome"], "FORGED_DECISION")
        self.assertEqual(fresh["locator_routes"], self.index["locator_routes"])
        bad = copy.deepcopy(self.index)
        bad["source_records"][0]["prior_decision"]["outcome"] = "FORGED_DECISION"
        self.assertEqual(evaluate(bad["source_records"][0]["canonical_url"], bad)["disposition"],
                         "BLOCKED_INDEX_CONFLICT")
        bad_route = copy.deepcopy(self.index)
        bad_route["locator_routes"][0]["preferred_source_id"] = sid
        self.assertEqual(evaluate(bad_route["source_records"][0]["canonical_url"], bad_route)["disposition"],
                         "BLOCKED_INDEX_CONFLICT")


    def test_completion_and_transfer_identity_claims_fail_closed(self):
        sid = self.snapshot["records"][0]["source_id"]
        forged = {
            "global_l1_completed": True,
            "all_historical_submissions_complete": True,
            "snapshot_transfer_complete": False,
            "id": "forged-transfer-id",
            "source_commit": "0" * 40,
            "rejection_audit_blob": "0" * 40,
            "legacy_main_records": 1981,
            "missing_legacy_main_ids": ["missing"],
        }
        for field, value in forged.items():
            with self.subTest(field=field):
                bad = copy.deepcopy(self.snapshot)
                bad[field] = value
                with self.assertRaisesRegex(ValueError, "snapshot identity"):
                    lookup_snapshot(bad, donor_id=sid)
                with self.assertRaisesRegex(ValueError, "snapshot identity"):
                    ValidatedSnapshot(bad)

    def test_internal_verified_snapshot_is_deeply_immutable(self):
        trusted, sha = integrity._trusted_snapshot()
        self.assertEqual(sha, hashlib.sha256(transfer_donors.OUTPUT.read_bytes()).hexdigest())
        with self.assertRaises(TypeError):
            trusted["global_l1_completed"] = True
        with self.assertRaises(TypeError):
            trusted["rejection_audit"]["entries"][0]["donor"]["source"]["locator"] = "project:forged"
        with self.assertRaises(AttributeError):
            trusted["records"].append({"source_id": "forged"})
        self.assertEqual(evaluate("project:donutbrowser", self.index)["disposition"],
                         "BLOCKED_REJECTED_SOURCE")

    def test_lifecycle_batch_does_not_deepcopy_full_transfer_or_projection(self):
        url = "https://github.com/ExistentialAudio/BlackHole"
        self.assertEqual(evaluate(url, self.index)["disposition"], "CHANGE_CHECK_REQUIRED")
        # Internal consumers must avoid public defensive-copy accessors on every hit.
        with patch("source_lifecycle.verified_snapshot",
                   side_effect=AssertionError("full snapshot copy on lifecycle hit")), \
             patch.object(integrity, "expected_lifecycle_projection",
                          side_effect=AssertionError("full projection copy on lifecycle hit")), \
             patch.object(integrity, "deepcopy",
                          side_effect=AssertionError("full evidence copy on lifecycle hit")):
            for _ in range(12):
                self.assertEqual(evaluate(url, self.index)["disposition"], "CHANGE_CHECK_REQUIRED")

    def test_constructor_bypass_cannot_become_validated_snapshot(self):
        sid = self.snapshot["records"][0]["source_id"]
        forged = copy.deepcopy(self.snapshot)
        forged["records"][0]["reference_record"]["historical_status"] = "FORGED"
        # The original tuple.__new__ exploit must fail at construction.
        with self.assertRaises(TypeError):
            tuple.__new__(ValidatedSnapshot, (forged, {}, {}))
        # An object allocated without the validating constructor has no
        # authenticated internal state, even if callers control its identity.
        untrusted = object.__new__(ValidatedSnapshot)
        with self.assertRaisesRegex(ValueError, "Unvalidated donor snapshot handle"):
            lookup_snapshot(untrusted, donor_id=sid)
        with self.assertRaisesRegex(ValueError, "Unvalidated donor snapshot handle"):
            _ = untrusted._data
        trusted = ValidatedSnapshot(self.snapshot)
        with self.assertRaises(AttributeError):
            object.__setattr__(trusted, "_data", forged)
        self.assertEqual(lookup_snapshot(trusted, donor_id=sid)["donor_id"], sid)
        self.assertIsNone(lookup_snapshot(trusted, donor_id="unknown-source-id"))

    def test_pinned_transfer_rejects_self_consistent_forged_history(self):
        altered = copy.deepcopy(self.snapshot)
        row = altered["records"][0]
        row["reference_record"]["historical_status"] = "FORGED_STATUS"
        altered["record_set_sha256"] = transfer_donors.digest(altered["records"])
        self.assertEqual(altered["record_count"], len(altered["records"]))
        with self.assertRaisesRegex(ValueError, "preserved transfer evidence"):
            lookup_snapshot(altered, donor_id=row["source_id"])
        with self.assertRaisesRegex(ValueError, "preserved transfer evidence"):
            ValidatedSnapshot(altered)

    def test_owner_approval_ledger_forgery_fails_even_with_matching_index_digest(self):
        sid = "FA3-DONOR-TAHOMA2D-001"
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp)
            for name in integrity.PROJECTION_INPUTS:
                shutil.copyfile(integrity.REG / name, reg / name)
            approval = reg / integrity.OWNER_APPROVAL_NAME
            doc = json.loads(approval.read_text())
            row = next(rec for rec in doc["records"] if rec["id"] == sid)
            row["owner_donor_approval"] = "FORGED_OWNER_APPROVAL"
            approval.write_text(json.dumps(doc))
            forged = copy.deepcopy(self.index)
            forged["input_sha256"][integrity.OWNER_APPROVAL_NAME] = hashlib.sha256(
                approval.read_bytes()).hexdigest()
            next(rec for rec in forged["source_records"]
                 if rec["source_id"] == sid)["prior_decision"]["owner_approval"] = row
            with patch.object(integrity, "REG", reg):
                self.assertEqual(evaluate("https://github.com/tahoma2d/tahoma2d", forged)
                                 ["disposition"], "BLOCKED_INDEX_CONFLICT")
                with self.assertRaisesRegex(ValueError, "owner approval ledger Git blob"):
                    integrity.expected_lifecycle_projection()

    def test_support_ended_never_silently_reuses_prior_decision(self):
        observation = {
            "verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
            "evidence_ref": "regression-verified-support-end-conflict",
            "checked_at": "2026-10-11",
            "event": "SUPPORT_ENDED",
            "support_status": "SUPPORTED",
            "observed_revision": "72f3f6fa0b2fc38b8517f408ab616f0f2bd229e6",
        }
        url = "https://github.com/agentscope-ai/agentscope"
        self.assertEqual(evaluate(url, self.index, observation)["disposition"],
                         "BLOCKED_UNVERIFIED_OBSERVATION")
        observation["support_status"] = "UNKNOWN"
        self.assertEqual(evaluate(url, self.index, observation)["disposition"],
                         "BLOCKED_UNVERIFIED_OBSERVATION")
        observation["support_status"] = "UNMAINTAINED"
        self.assertEqual(evaluate(url, self.index, observation)["disposition"],
                         "REPLACEMENT_PLAN_REQUIRED")

    def test_index_selector_and_authority_fields_cannot_disable_historical_routes(self):
        url = "https://github.com/lurcher/unixODBC"
        for field, value in {
            "active_reference_snapshot": "FORGED",
            "id": "FORGED",
            "source_status": "FORGED",
            "migration_authority": "FORGED",
            "repository_snapshot_transfer_complete": False,
        }.items():
            with self.subTest(field=field):
                forged = copy.deepcopy(self.index)
                forged[field] = value
                self.assertEqual(evaluate(url, forged)["disposition"],
                                 "BLOCKED_INDEX_CONFLICT")
        self.assertEqual(evaluate(url, self.index)["disposition"],
                         "CHANGE_CHECK_REQUIRED")

if __name__ == "__main__":
    unittest.main()
