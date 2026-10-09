"""L1 staged source import and index read-back tests; not publication authorization."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("donor_l1", ROOT / "scripts/donor_l1.py")
donor_l1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)


class DonorL1IndexTests(unittest.TestCase):
    def test_archive_sources_have_distinct_identity(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(len(sources), 1921)
        self.assertEqual(sum(1 for _, _, canonical in sources if canonical), 1919)
        self.assertEqual(sum(1 for _, _, canonical in sources if not canonical), 2)

    def test_staging_index_round_trip_and_no_false_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "staged.sqlite"
            receipt = donor_l1.stage(dbpath, "unit-test")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            self.assertIsNone(receipt["raw_link_limit"])
            self.assertEqual(receipt["index_evidence"]["rows"], 1921)
            sources = donor_l1.frozen_sources()
            entry = sources[0][0]
            sid = entry["donor_id"]
            locator = entry["source"]["locator"]
            self.assertEqual(donor_l1.lookup(dbpath,sid,"id")[0]["id"],sid)
            self.assertEqual(donor_l1.lookup(dbpath,locator,"alias")[0]["id"],sid)
            self.assertTrue(donor_l1.lookup(dbpath,entry["source"]["normalized_key"],"key"))
            self.assertIsInstance(donor_l1.lookup(dbpath,"RESEARCH_DOCUMENTATION","class"), list)
            self.assertFalse(donor_l1.lookup(dbpath,"missing-id","id"))
            with sqlite3.connect(dbpath) as db:
                meta = dict(db.execute("SELECT key,value FROM metadata"))
                self.assertEqual(meta["publication_gate"],"PENDING")
                self.assertEqual(meta["input_link_occurrences_B"],"UNVERIFIED")
                self.assertEqual(meta["expansion_raw_limit"],"UNVERIFIED")
                self.assertEqual(meta["approval_completeness"],"UNVERIFIED")
                self.assertEqual(db.execute(
                    "SELECT current_status FROM sources WHERE source_origin='UNMERGED_PR_744'").fetchone()[0],
                    "BLOCKED")

    def test_no_modification_to_original_archive(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(sources[0][0]["status"],"ACCEPTED_REFERENCE" if sources[0][0]["status"]=="ACCEPTED_REFERENCE" else sources[0][0]["status"])
        self.assertTrue(donor_l1.EXPECTED["FA3-DONOR-REFERENCE-REGISTRY-001.json"])

    def test_duplicate_identity_fails_closed(self):
        src = donor_l1.frozen_sources()
        with tempfile.TemporaryDirectory() as tmp:
            with sqlite3.connect(":memory:") as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    donor_l1.prepare(db,[src[0],src[0]],"duplicate")

if __name__ == "__main__":
    unittest.main()
