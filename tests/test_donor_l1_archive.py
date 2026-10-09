"""Verify archived CFA3 donor source evidence only; never issue L1 publication PASS."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "archive/donor-source-migration/2026-10-09"
MANIFEST = ROOT / "canonical/registries/CFA3-DONOR-L1-SOURCE-ARCHIVE-MANIFEST-001.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class DonorL1ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(MANIFEST)
        cls.registry = read(ARCH / "FA3-DONOR-REFERENCE-REGISTRY-001.json")
        cls.union = read(ARCH / "CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json")
        cls.delta = read(ARCH / "CFA3-DONOR-MISSING-BASELINE-SOURCES-2026-10-07.json")
        cls.extra744 = read(ARCH / "PR-744-ADDITIONAL-REFERENCE.json")
        cls.extra745 = read(ARCH / "PR-745-ADDITIONAL-REFERENCE.json")

    def test_git_blob_exact_source_integrity(self):
        files = {
            "FA3-DONOR-REFERENCE-REGISTRY-001.json": "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b",
            "CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json": "d22dce8bfe3d9697a1121033ff7b387d051a638a",
            "FA3-APPLICATION-DONOR-LINKS-001.json": "803b9d62062e6aaaeb9fc69301a6202e20279a93",
        }
        for path, sha in files.items():
            with self.subTest(path=path):
                self.assertEqual(git_blob_sha((ARCH/path).read_bytes()), sha)

    def test_source_and_donor_ids_unique(self):
        entries = self.registry["entries"]
        self.assertEqual(len(entries), 1919)
        self.assertEqual(len({r["donor_id"] for r in entries}), 1919)
        self.assertEqual(len({r["source"]["normalized_key"] for r in entries}), 1919)
        statuses = {}
        for r in entries:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        self.assertEqual(statuses, {"ACCEPTED_REFERENCE":825,"CANDIDATE":963,"ANALYZED":130,"SUPERSEDED":1})

    def test_union_445_sources_have_historical_canonical_identity(self):
        keys = {r["source"]["normalized_key"] for r in self.registry["entries"]}
        ids = {r["donor_id"] for r in self.registry["entries"]}
        self.assertEqual(len(self.union["source_coverage"]), 445)
        for item in self.union["source_coverage"]:
            self.assertIn(item["normalized_key"], keys)
            self.assertIn(item["resolved_donor_id"], ids)
        self.assertEqual(self.union["post_materialization"]["union_missing"], 0)

    def test_previously_missing_twenty_in_main_not_duplicated(self):
        keys = {r["source"]["normalized_key"] for r in self.registry["entries"]}
        self.assertEqual(self.delta["submitted_url_count"], 20)
        self.assertEqual(len(self.delta["canonical_identities"]), 20)
        for item in self.delta["canonical_identities"]:
            self.assertIn(item["normalized_key"], keys)

    def test_unmerged_extra_sources_preserved_but_not_published(self):
        keys = {r["source"]["normalized_key"] for r in self.registry["entries"]}
        extra = [self.extra744,self.extra745]
        new_keys = [x["entry"]["source"]["normalized_key"] for x in extra]
        self.assertEqual(len(set(new_keys)), 2)
        self.assertTrue(all(x not in keys for x in new_keys))
        self.assertEqual({x["pr"] for x in extra}, {744,745})
        for item in extra:
            self.assertEqual(item["state"],"UNMERGED_HISTORICAL_PR_PRESERVED_NOT_CFA3_CANONICAL_ADMITTED")

    def test_manifest_fail_closed_no_l1_publication(self):
        self.assertEqual(self.manifest["status"], "SOURCE_ARCHIVE_STAGED_L1_NOT_PUBLISHED")
        self.assertEqual(self.manifest["source_registry"]["entries"], 1919)
        self.assertEqual(self.manifest["observed_distinct_historical_source_keys"], 1921)
        self.assertTrue(self.manifest["not_proof_of_all_user_submissions"])
        self.assertTrue(self.manifest["coverage_unknown_for_all_prior_conversations"])
        self.assertEqual(self.manifest["classified_new_cfa3_l1_count"],0)
        self.assertEqual(self.manifest["published_new_cfa3_donor_count"],0)
        self.assertEqual(self.manifest["level_pass_receipts"],[])
        self.assertFalse(self.manifest["source_lifecycle_index_complete"])
        self.assertTrue(self.manifest["no_new_l2_crawl"])
        index = read(ROOT / "canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json")
        self.assertFalse(index["complete"])
        self.assertEqual(index["source_records"],[])


if __name__ == "__main__":
    unittest.main()
