"""Full frozen-repository transfer, independently checked against raw archive."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from donor_reference_lookup import lookup_snapshot, ValidatedSnapshot
from donor_delta_routes import archived_delta, archived_mentor_delta, archived_baseline_union, delta_aliases
from transfer_donors import OUTPUT, build, digest


class DonorTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(OUTPUT.read_text())
        cls.by_id = {r["source_id"]: r for r in cls.snapshot["records"]}
        cls.snapshot_handle = ValidatedSnapshot(cls.snapshot)

    def test_every_old_main_record_preserved_without_status_or_field_loss(self):
        archive = json.loads((ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
        self.assertEqual(len(archive["entries"]), 1919)
        for original in archive["entries"]:
            target = self.by_id[original["donor_id"]]
            self.assertEqual(target["historical_record"], original)
            self.assertEqual(target["historical_status"], original["status"])
            self.assertEqual(target["historical_record_sha256"], digest(original))
        self.assertEqual(self.snapshot["missing_legacy_main_ids"], [])
        self.assertEqual(self.snapshot["additional_recovered_records"], 62)

    def test_every_transferred_id_and_locator_resolves(self):
        self.assertEqual(len(self.by_id), 1981)
        # Reuse exactly one authenticated handle across all indexed lookups.
        with patch("donor_reference_lookup.validate_snapshot",
                   side_effect=AssertionError("full snapshot revalidation in batch")):
            for row in self.snapshot["records"]:
                self.assertEqual(lookup_snapshot(self.snapshot_handle, donor_id=row["source_id"]),
                                 row["reference_record"])
            for route in self.snapshot["locator_routes"]:
                self.assertEqual(lookup_snapshot(self.snapshot_handle, original_url=route["alias"]),
                                 self.by_id[route["preferred_source_id"]]["reference_record"])
                self.assertTrue(set(route["related_source_ids"]) <= self.by_id.keys())
        self.assertEqual(len(self.snapshot["locator_routes"]), 3946)

    def test_all_56_original_odbc_delta_urls_have_exact_donor_routes(self):
        evidence = archived_delta()
        self.assertEqual(evidence["source_count"], 56)
        aliases = delta_aliases(self.snapshot["records"])
        self.assertEqual(len(aliases), 574)
        self.assertEqual(aliases["https://github.com/lurcher/unixODBC"],
                         "FA3-DONOR-LURCHER-UNIXODBC-001")
        self.assertEqual(aliases["https://github.com/topics/mp4-files?l=go&o=asc&s=forks"],
                         "FA3-DONOR-MP4-FILES-CS-TOPIC-001")
        for url, sid in aliases.items():
            self.assertEqual(lookup_snapshot(self.snapshot_handle, original_url=url),
                             lookup_snapshot(self.snapshot_handle, donor_id=sid))

    def test_mentor_delta_original_source_and_evidence_links(self):
        delta = archived_mentor_delta()
        self.assertEqual(len(delta["records"]), 15)
        self.assertEqual(len(delta_aliases(self.snapshot["records"])), 574)
        for row in delta["records"]:
            for url in (row["source_url"], row["license_evidence_url"]):
                matched = lookup_snapshot(self.snapshot_handle, original_url=url)
                self.assertEqual(matched["donor_id"], row["donor_id"])

    def test_all_445_owner_baseline_identities_and_raw_urls_are_routed(self):
        union = archived_baseline_union()
        self.assertEqual(len(union["source_coverage"]), 445)
        aliases = delta_aliases(self.snapshot["records"])
        self.assertEqual(len(aliases), 574)
        for row in union["source_coverage"]:
            urls = [row["canonical_locator"], *row["original_locators"],
                    row["canonical_locator_in_registry"]]
            for url in urls:
                self.assertEqual(lookup_snapshot(self.snapshot_handle, original_url=url)["donor_id"],
                                 row["resolved_donor_id"])

    def test_existing_81_donor_views_are_unchanged(self):
        prior = json.loads((ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
        for record in prior["records"]:
            self.assertEqual(lookup_snapshot(self.snapshot_handle, donor_id=record["donor_id"]), record)

    def test_candidates_and_unapproved_proposals_never_become_approved(self):
        states = {"CANDIDATE": "CANDIDATE_PRESERVED", "ANALYZED": "ANALYZED_SOURCE_PRESERVED",
                  "BLOCKED": "UNAPPROVED_SOURCE_PRESERVED", "SUPERSEDED": "SUPERSEDED_REFERENCE_PRESERVED"}
        for row in self.snapshot["records"]:
            if row["pre_transfer_status"] in states:
                self.assertEqual(row["reference_state"], states[row["pre_transfer_status"]])
        self.assertEqual(len(self.snapshot["unadmitted_historical_proposals"]), 17)
        self.assertEqual(len(self.snapshot["unapplied_historical_rekeys"]), 3)
        self.assertFalse(self.snapshot["all_historical_submissions_complete"])
        self.assertFalse(self.snapshot["global_l1_completed"])

    def test_tampered_lookup_and_authority_fail_closed(self):
        bad = copy.deepcopy(self.snapshot)
        sid = next(iter(bad["lookup_by_id"]))
        bad["lookup_by_id"][sid] = -1
        self.assertRaises(ValueError, lookup_snapshot, bad, donor_id=sid)
        bad = dict(self.snapshot, runtime_admission=True)
        self.assertRaises(ValueError, lookup_snapshot, bad, donor_id=sid)
        bad = copy.deepcopy(self.snapshot)
        bad["records"][0]["reference_record"]["license_authorized"] = True
        self.assertRaises(ValueError, lookup_snapshot, bad, donor_id=bad["records"][0]["source_id"])
        bad = copy.deepcopy(self.snapshot)
        candidate = next(r for r in bad["records"] if r["pre_transfer_status"] == "CANDIDATE")
        candidate["reference_state"] = "CANONICAL_REFERENCE_REGISTERED"
        candidate["reference_record"]["donor_registration"] = "CANONICAL_REFERENCE_REGISTERED"
        self.assertRaises(ValueError, lookup_snapshot, bad, donor_id=candidate["source_id"])

    def test_all_56_pending_historical_links_have_current_owner_authorization(self):
        from transfer_donors import current_owner_confirmations
        confirmed = current_owner_confirmations()
        pending = {
            r["source_id"]: r for r in self.snapshot["records"]
            if r["pre_transfer_status"] == "OWNER_APPROVED_PENDING_PUBLICATION"
            and r["historical_record"].get("intake_provenance", {}).get(
                "canonical_approval_admitted") is False
        }
        self.assertEqual(len(pending), 56)
        self.assertEqual(set(confirmed), set(pending))
        for donor_id, row in pending.items():
            self.assertEqual(confirmed[donor_id], (
                row["historical_record"]["source"]["locator"],
                row["historical_record_sha256"]))
            self.assertEqual(lookup_snapshot(self.snapshot_handle, donor_id=donor_id),
                             row["reference_record"])
        altered = copy.deepcopy(self.snapshot)
        donor_id = next(iter(pending))
        altered["records"][altered["lookup_by_id"][donor_id]]["historical_record_sha256"] = "0" * 64
        self.assertRaises(ValueError, lookup_snapshot, altered, donor_id=donor_id)

    def test_snapshot_reproduces_from_preserved_inputs(self):
        self.assertEqual(build(), self.snapshot)
        self.assertEqual(digest(self.snapshot["records"]), self.snapshot["record_set_sha256"])

    def test_rejection_history_survives_without_reactivating_source(self):
        original = json.loads((ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-REJECTION-AUDIT-001.json").read_text())
        self.assertEqual(self.snapshot["rejection_audit"], original)
        for row in original["entries"]:
            sid = row["donor"]["donor_id"]
            self.assertNotIn(sid, self.by_id)
            result = lookup_snapshot(self.snapshot_handle, donor_id=sid)
            self.assertEqual(result["donor_registration"], "REJECTED_REFERENCE_NOT_ACTIVE")
            self.assertEqual(result["rejection_history"], row)
            self.assertEqual(lookup_snapshot(self.snapshot_handle, original_url=row["donor"]["source"]["locator"]), result)
            self.assertFalse(result["runtime_admission"])


if __name__ == "__main__":
    unittest.main()
