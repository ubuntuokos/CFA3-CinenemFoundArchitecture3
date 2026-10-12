"""Verify append-only evidence for 10 more historical phase-1 GitHub sources."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "canonical/registries"
CAT = BASE / "CFA3-DONOR-SOURCE-FILE-001.json"
QUEUE = BASE / "CFA3-DONOR-SOURCE-FILE-001-TWO-PHASE-QUEUE-001.json"
FIRST = BASE / "CFA3-DONOR-SOURCE-FILE-001-PHASE1-UPSTREAM-OBSERVATIONS-001.json"
SECOND = BASE / "CFA3-DONOR-SOURCE-FILE-001-PHASE1-UPSTREAM-OBSERVATIONS-002.json"

def validate(doc, source, queue, previous):
    rows = doc["records"]
    positions = [r["source_file_position"] for r in rows]
    if positions != [28,30,31,32,33,34,36,38,39,40]:
        raise ValueError("Unexpected source positions")
    if {r["source_file_position"] for r in previous["records"]} & set(positions):
        raise ValueError("Historical observation duplicated")
    if doc["observed_repo_metadata_found"] != sum(r["github_repository_metadata"] == "RETURNED" for r in rows):
        raise ValueError("Found count differs")
    if doc["observed_repo_metadata_not_found"] != sum(r["github_repository_metadata"] == "NOT_FOUND_AT_CHECK" for r in rows):
        raise ValueError("Missing count differs")
    for r in rows:
        old = source["records"][r["source_file_position"]]
        if (r["source_file_position"] not in queue["classification_groups"]["direct_candidates"]
                or old["donor_id"] != r["donor_id"]
                or old["original_url"] != r["original_url"]
                or old["historical_status"] != r["prior_historical_decision"]
                or not r["known_source_not_new_discovery"]
                or r["rights_review_complete"]):
            raise ValueError("Historical donor identity or approval changed")

class Phase1ObservedBatch002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CAT.read_text(encoding="utf-8"))
        cls.queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        cls.previous = json.loads(FIRST.read_text(encoding="utf-8"))
        cls.doc = json.loads(SECOND.read_text(encoding="utf-8"))

    def test_history_and_checks(self):
        self.assertEqual(self.doc["queue_git_blob_sha1"], "5ccd43c3ae8ba8a62e3674e08d14c14bae3579ec")
        self.assertEqual(self.doc["previous_evidence_git_blob_sha1"], "cc4ac8ed4ab583d8f75af0af0cfe3ed61bc92c8a")
        validate(self.doc, self.catalog, self.queue, self.previous)

    def test_no_false_admission(self):
        self.assertFalse(self.doc["phase_1_complete"])
        self.assertFalse(self.doc["phase_2_started"])
        self.assertEqual(self.doc["new_sources_admitted"], 0)
        self.assertEqual(self.doc["runtime_or_license_admissions"], 0)

    def test_tamper_fails(self):
        changed = json.loads(json.dumps(self.doc))
        changed["records"][0]["donor_id"] = "INVALID"
        with self.assertRaises(ValueError):
            validate(changed, self.catalog, self.queue, self.previous)

    def test_size_limit(self):
        self.assertLessEqual(SECOND.stat().st_size, 996147)

if __name__ == "__main__":
    unittest.main()
