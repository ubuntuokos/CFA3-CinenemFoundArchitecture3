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
        self.assertEqual(len(sources), 1936)
        self.assertEqual(sum(1 for _, _, canonical in sources if canonical), 1919)
        self.assertEqual(sum(1 for _, _, canonical in sources if not canonical), 17)

    def test_staging_index_round_trip_and_no_false_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "staged.sqlite"
            receipt = donor_l1.stage(dbpath, "unit-test")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            self.assertIsNone(receipt["raw_link_limit"])
            self.assertEqual(receipt["index_evidence"]["rows"], 1936)
            self.assertEqual(receipt["index_evidence"]["supplemental_unreconciled_owner_sources"], 15)
            self.assertEqual(receipt["index_evidence"]["historical_url_provenance"], "BOUNDED_445_PASS")
            self.assertEqual(receipt["index_evidence"]["historical_unique_source_ids"], 443)
            sources = donor_l1.frozen_sources()
            entry = sources[0][0]
            sid = entry["donor_id"]
            locator = entry["source"]["locator"]
            self.assertEqual(donor_l1.lookup(dbpath,sid,"id")[0]["id"],sid)
            self.assertEqual(donor_l1.lookup(dbpath,locator,"alias")[0]["id"],sid)
            self.assertTrue(donor_l1.lookup(dbpath,entry["source"]["normalized_key"],"key"))
            self.assertIsInstance(donor_l1.lookup(dbpath,"RESEARCH_DOCUMENTATION","class"), list)
            self.assertFalse(donor_l1.lookup(dbpath,"missing-id","id"))
            union = donor_l1.json_read(donor_l1.UNION)
            self.assertEqual(len(union["source_coverage"]), 445)
            for original in union["source_coverage"]:
                for url in original["original_locators"]:
                    self.assertIn(original["resolved_donor_id"],
                                  [item["id"] for item in donor_l1.lookup(dbpath,url,"url")])
            supersession = union["superseded_resolution"]
            old_url = "https://github.com/Ascend/triton-ascend"
            self.assertIn(supersession["replacement_donor_id"],
                          [item["id"] for item in donor_l1.lookup(dbpath,old_url,"url")])
            with sqlite3.connect(dbpath) as db:
                meta = dict(db.execute("SELECT key,value FROM metadata"))
                self.assertEqual(meta["publication_gate"],"PENDING")
                self.assertEqual(meta["input_link_occurrences_B"],"UNVERIFIED")
                self.assertEqual(meta["expansion_raw_limit"],"UNVERIFIED")
                self.assertEqual(meta["approval_completeness"],"UNVERIFIED")
                self.assertEqual(meta["supplemental_owner_source_candidates"],"15")
                self.assertEqual(meta["all_owner_submissions_verified"],"FALSE")
                self.assertEqual(meta["bounded_union_link_records"],"445")
                self.assertEqual(meta["bounded_union_distinct_donor_ids"],"443")
                self.assertEqual(meta["bounded_union_original_url_records"],"445")
                self.assertEqual(db.execute(
                    "SELECT current_status FROM sources WHERE source_origin='UNMERGED_PR_744'").fetchone()[0],
                    "BLOCKED")

    def test_no_modification_to_original_archive(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(donor_l1.sha_blob(donor_l1.REGISTRY.read_bytes()),
                         donor_l1.EXPECTED["FA3-DONOR-REFERENCE-REGISTRY-001.json"])
        self.assertEqual(len(sources),1936)

    def test_historical_missing_sources_recoverable_without_false_admission(self):
        supplement = donor_l1.json_read(donor_l1.SUPPLEMENT)
        self.assertEqual(len(supplement["entries"]), 15)
        existing = {(e["source"]["normalized_key"]) for e,origin,_ in donor_l1.frozen_sources()
                    if origin=="OLD_MAIN_ARCHIVE"}
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp)/"staged.sqlite"
            donor_l1.stage(dbpath,"supplement-test")
            for entry in supplement["entries"]:
                self.assertNotIn(entry["source"]["normalized_key"], existing)
                sid = entry["donor_id"]
                self.assertEqual(donor_l1.lookup(dbpath,sid,"id")[0]["status"],"BLOCKED")
                self.assertEqual(donor_l1.lookup(dbpath,entry["source"]["locator"],"url")[0]["id"],sid)
                self.assertFalse(entry["submission_review"]["exact_submitted_URL_and_approval_pair_independently_verified"])

    def test_duplicate_identity_fails_closed(self):
        src = donor_l1.frozen_sources()
        with tempfile.TemporaryDirectory() as tmp:
            with sqlite3.connect(":memory:") as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    donor_l1.prepare(db,[src[0],src[0]],"duplicate")

if __name__ == "__main__":
    unittest.main()
