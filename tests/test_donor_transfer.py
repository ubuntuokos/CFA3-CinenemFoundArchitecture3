"""Full frozen-repository transfer, independently checked against raw archive."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from donor_reference_lookup import lookup_snapshot
from transfer_donors import OUTPUT, build, digest


class DonorTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(OUTPUT.read_text())
        cls.by_id = {r["source_id"]: r for r in cls.snapshot["records"]}

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
        for row in self.snapshot["records"]:
            self.assertEqual(lookup_snapshot(self.snapshot, donor_id=row["source_id"]), row["reference_record"])
        for route in self.snapshot["locator_routes"]:
            self.assertEqual(lookup_snapshot(self.snapshot, original_url=route["alias"]),
                             self.by_id[route["preferred_source_id"]]["reference_record"])
            self.assertTrue(set(route["related_source_ids"]) <= self.by_id.keys())
        self.assertEqual(len(self.snapshot["locator_routes"]), 3946)

    def test_existing_81_donor_views_are_unchanged(self):
        prior = json.loads((ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
        for record in prior["records"]:
            self.assertEqual(lookup_snapshot(self.snapshot, donor_id=record["donor_id"]), record)

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

    def test_snapshot_reproduces_from_preserved_inputs(self):
        self.assertEqual(build(), self.snapshot)
        self.assertEqual(digest(self.snapshot["records"]), self.snapshot["record_set_sha256"])


if __name__ == "__main__":
    unittest.main()
