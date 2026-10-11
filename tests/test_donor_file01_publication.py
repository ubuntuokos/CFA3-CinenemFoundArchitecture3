"""First historical donor file: full canonical source and lookup verification."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from donor_reference_lookup import lookup_published

SOURCE = ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-REFERENCE-REGISTRY-001.json"
PUBLISHED = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json"
CANON = ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json"
PIN = "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b"
STATES = {"ACCEPTED_REFERENCE": 825, "CANDIDATE": 963, "ANALYZED": 130, "SUPERSEDED": 1}


class FirstDonorFilePublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = SOURCE.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if blob != PIN:
            raise AssertionError("Historical source file blob changed")
        cls.source = json.loads(raw)
        cls.catalog = json.loads(PUBLISHED.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANON.read_text(encoding="utf-8"))

    def test_first_file_is_complete_and_statuses_unchanged(self):
        doc = self.catalog
        self.assertEqual(doc["schema"], "cfa3.donor-source-file-publication.v1")
        self.assertEqual(doc["source_file_sequence"], 1)
        self.assertEqual(doc["source_git_blob_sha"], PIN)
        self.assertEqual(doc["publication_state"], "CANONICAL_REFERENCE_SEARCHABLE_PARTIAL_L1")
        self.assertFalse(doc["global_l1_completed"])
        self.assertIsNone(doc["original_l1_B"])
        self.assertTrue(doc["historical_decisions_preserved"])
        self.assertTrue(doc["no_new_approval"])
        self.assertFalse(doc["runtime_admission"])
        self.assertEqual(doc["source_count"], 1919)
        self.assertEqual(doc["approved_reference_count"], 825)
        self.assertEqual(doc["status_counts"], STATES)
        self.assertEqual(len(doc["records"]), 1919)
        self.assertEqual(len(doc["lookup_by_id"]), 1919)
        self.assertEqual(len(doc["lookup_by_locator"]), 1997)
        self.assertEqual(doc["alias_index_size"], 1997)

        self.assertEqual(Counter(e["status"] for e in self.source["entries"]), Counter(STATES))
        for position, entry in enumerate(self.source["entries"]):
            row = doc["records"][position]
            sid = entry["donor_id"]
            with self.subTest(donor=sid):
                self.assertEqual(doc["lookup_by_id"][sid], position)
                self.assertEqual(row["donor_id"], sid)
                self.assertEqual(row["normalized_key"], entry["source"]["normalized_key"])
                self.assertEqual(row["original_url"], entry["source"]["locator"])
                self.assertEqual(row["historical_status"], entry["status"])
                self.assertEqual(row["source_kind"], entry["source"]["kind"])
                self.assertEqual(row["source_file_sequence"], 1)
                self.assertTrue(row["previous_owner_decision_preserved"])
                self.assertEqual(row["donor_registration"] == "CANONICAL_REFERENCE_REGISTERED",
                                 entry["status"] == "ACCEPTED_REFERENCE")
                for key in ("runtime_admission", "code_copy_authorized",
                            "license_authorized", "model_provider_admission"):
                    self.assertIs(row[key], False)
                aliases = [entry["source"]["locator"],
                           *entry["source"].get("previous_locators", []),
                           *entry.get("legacy_source_keys", []),
                           *entry.get("intake_provenance", {}).get("original_locators", [])]
                self.assertEqual(set(row["lookup_aliases"]), set(aliases))
                for alias in row["lookup_aliases"]:
                    self.assertEqual(doc["lookup_by_locator"][alias], sid)

    def test_existing_canonical_donors_are_preserved_and_first_file_is_linked(self):
        canonical = self.canonical
        self.assertEqual(canonical["donor_count"], 81)
        self.assertEqual(len(canonical["records"]), 81)
        self.assertEqual(len(canonical["sequential_file_publications"]), 1)
        first = canonical["sequential_file_publications"][0]
        self.assertEqual(first["source_sequence"], 1)
        self.assertEqual(first["source_records"], 1919)
        self.assertEqual(first["accepted_reference_records"], 825)
        self.assertFalse(first["full_L1_level_pass"])
        self.assertEqual(first["published_catalog"],
                         "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json")
        for row in canonical["records"]:
            published = self.catalog["records"][self.catalog["lookup_by_id"][row["donor_id"]]]
            self.assertEqual(published["original_url"], row["original_url"])
            self.assertEqual(published["normalized_key"], row["normalized_key"])
            self.assertEqual(published["donor_registration"], "CANONICAL_REFERENCE_REGISTERED")

    def test_published_lookup_readback_and_no_unprocessed_second_file(self):
        records = self.catalog["records"]
        for row in (records[0], records[1], records[50], records[900], records[-1]):
            self.assertEqual(lookup_published(donor_id=row["donor_id"]), row)
            self.assertEqual(lookup_published(original_url=row["original_url"]), row)
        self.assertIsNone(lookup_published(donor_id="DOES-NOT-EXIST"))
        self.assertIsNone(lookup_published(original_url="https://example.invalid/unregistered"))


if __name__ == "__main__":
    unittest.main()
