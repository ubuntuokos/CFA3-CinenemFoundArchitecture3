"""Verify phase-1 GitHub source observations without changing prior donor status."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json"
QUEUE = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001-TWO-PHASE-QUEUE-001.json"
EVIDENCE = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001-PHASE1-UPSTREAM-OBSERVATIONS-001.json"

class DonorSource001Phase1EvidenceTests(unittest.TestCase):
    def test_prior_id_status_and_links_are_preserved(self):
        source = json.loads(CAT.read_text(encoding="utf-8"))
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(doc["catalog_git_blob_sha1"], queue["source_catalog_git_blob_sha1"])
        self.assertEqual(doc["queue_git_blob_sha1"], "5ccd43c3ae8ba8a62e3674e08d14c14bae3579ec")
        self.assertEqual(doc["verification_scope"], "INITIAL_15_KNOWN_DIRECT_REPOSITORY_REFERENCES_ONLY")
        self.assertEqual(len(doc["records"]), 15)
        self.assertEqual(doc["observed_repo_metadata_found"], 14)
        self.assertEqual(doc["observed_repo_metadata_not_found"], 1)
        self.assertEqual([row["source_file_position"] for row in doc["records"]],
                         [2, 3, 9, 10, 11, 12, 13, 14, 17, 22, 23, 24, 25, 26, 27])
        for row in doc["records"]:
            idx = row["source_file_position"]
            old = source["records"][idx]
            self.assertIn(idx, queue["classification_groups"]["direct_candidates"])
            self.assertEqual(old["donor_id"], row["donor_id"])
            self.assertEqual(old["original_url"], row["original_url"])
            self.assertEqual(old["historical_status"], row["prior_historical_decision"])
            self.assertTrue(row["known_source_not_new_discovery"])
            self.assertFalse(row["rights_review_complete"])

    def test_missing_and_outdated_historical_sources_not_deleted(self):
        doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        missing = [r for r in doc["records"] if r["github_repository_metadata"] == "NOT_FOUND_AT_CHECK"]
        old = [r for r in doc["records"] if r.get("last_push_before_three_year_cutoff")]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["original_url"], "https://github.com/6174/recut")
        self.assertEqual(len(old), 1)
        self.assertEqual(old[0]["original_url"], "https://github.com/adobe/c2pa-js")
        self.assertTrue(old[0]["existing_historical_record_retained"])
        self.assertFalse(doc["phase_1_complete"])
        self.assertFalse(doc["phase_2_started"])
        self.assertEqual(doc["new_sources_admitted"], 0)
        self.assertEqual(doc["runtime_or_license_admissions"], 0)

    def test_new_evidence_file_within_file_size_limit(self):
        self.assertLessEqual(EVIDENCE.stat().st_size, 996147)

if __name__ == "__main__":
    unittest.main()
