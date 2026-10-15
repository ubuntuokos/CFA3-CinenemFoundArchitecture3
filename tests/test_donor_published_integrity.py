"""All published lookup paths must authenticate the preserved donor decisions."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_reference_lookup as lookup


class PublishedIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(lookup.PUBLISHED_FIRST.read_bytes())
        cls.candidate = next(r for r in cls.catalog["records"]
                             if r["historical_status"] == "CANDIDATE")

    def assert_rejected(self, doc, query):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            with patch.object(lookup, "PUBLISHED_FIRST", path):
                with self.assertRaisesRegex(ValueError, "catalog digest mismatch"):
                    lookup.lookup_published(**query)

    def test_candidate_promotion_rejected_by_id_and_direct_url(self):
        doc = copy.deepcopy(self.catalog)
        row = doc["records"][doc["lookup_by_id"][self.candidate["donor_id"]]]
        row["historical_status"] = "ACCEPTED_REFERENCE"
        row["donor_registration"] = "CANONICAL_REFERENCE_REGISTERED"
        for query in ({"donor_id": row["donor_id"]},
                      {"original_url": row["original_url"]}):
            with self.subTest(query=query):
                self.assert_rejected(doc, query)

    def test_deleted_id_cannot_be_reported_as_missing(self):
        doc = copy.deepcopy(self.catalog)
        position = doc["lookup_by_id"].pop(self.candidate["donor_id"])
        doc["lookup_by_id"]["UNAPPROVED-REPLACEMENT"] = position
        self.assert_rejected(doc, {"donor_id": self.candidate["donor_id"]})

    def test_unrelated_corruption_blocks_hits_and_misses(self):
        edits = (
            ("original_url", "https://example.invalid/replaced"),
            ("previous_owner_decision_preserved", False),
            ("runtime_admission", True),
        )
        for field, value in edits:
            doc = copy.deepcopy(self.catalog)
            doc["records"][-1][field] = value
            for query in ({"donor_id": self.candidate["donor_id"]},
                          {"donor_id": "UNKNOWN"},
                          {"original_url": "https://example.invalid/unknown"}):
                with self.subTest(field=field, query=query):
                    self.assert_rejected(doc, query)

    def test_authentic_lookup_preserves_candidate_and_detaches_result(self):
        expected = copy.deepcopy(self.candidate)
        row = lookup.lookup_published(donor_id=expected["donor_id"])
        self.assertEqual(row, expected)
        row["historical_status"] = "ACCEPTED_REFERENCE"
        row["lookup_aliases"].clear()
        self.assertEqual(lookup.lookup_published(original_url=expected["original_url"]), expected)
        self.assertIsNone(lookup.lookup_published(donor_id="UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
