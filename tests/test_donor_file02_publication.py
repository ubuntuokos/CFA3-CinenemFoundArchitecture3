"""Second historical source file: immutable full coverage and real searchable read-back."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_source_file_02_lookup as index02

ARCH = ROOT / "archive/donor-source-migration/2026-10-09/CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json"
CAT = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-002.json"
CANON = ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json"


class DonorSource02Tests(unittest.TestCase):
    def test_full_source_content_published_and_indexed(self):
        source = json.loads(ARCH.read_text(encoding="utf-8"))
        pub = index02.verified_catalog()
        self.assertEqual(pub["records"], source["source_coverage"])
        self.assertEqual(len(pub["records"]), 445)
        self.assertEqual(len(pub["lookup_by_locator"]), 499)
        self.assertEqual(len(pub["lookup_by_id"]), 444)
        self.assertEqual(pub["status_counts"], {"ACCEPTED_REFERENCE": 444, "SUPERSEDED": 1})
        self.assertFalse(pub["global_l1_completed"])
        self.assertIsNone(pub["original_l1_B"])
        self.assertFalse(pub["runtime_admission"])
        for row in pub["records"]:
            self.assertIn(row["canonical_locator"], pub["lookup_by_locator"])
            for url in row["original_locators"]:
                self.assertEqual(pub["records"][pub["lookup_by_locator"][url]]["donor_id"], row["donor_id"])

    def test_public_api_readback_by_id_url_and_supersession(self):
        pub = index02.verified_catalog()
        for i in [0, 1, 50, 170, 172, 250, 444]:
            row = pub["records"][i]
            self.assertEqual(index02.lookup_source_file_02(original_url=row["canonical_locator"]), row)
            self.assertIn(row, index02.lookup_source_file_02(donor_id=row["donor_id"]))
        repeated = index02.lookup_source_file_02(donor_id="FA3-DONOR-AOMEDIACODEC-ORG-001")
        self.assertEqual(len(repeated), 2)
        superseded = [r for r in pub["records"] if r["status"] == "SUPERSEDED"]
        self.assertEqual(len(superseded), 1)
        self.assertEqual(index02.lookup_source_file_02(original_url=superseded[0]["canonical_locator"]), superseded[0])
        self.assertIsNone(index02.lookup_source_file_02(original_url="https://example.invalid/not-here"))

    def test_cli_second_file_original_url(self):
        url = index02.verified_catalog()["records"][0]["canonical_locator"]
        run = subprocess.run([sys.executable, str(ROOT / "scripts/donor_source_file_02_lookup.py"), "--url", url],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["canonical_locator"], url)

    def test_tampered_publication_is_rejected(self):
        pub = index02.verified_catalog()
        pub["records"][0]["donor_id"] = "FA3-DONOR-UNAUTHORIZED-TEST-001"
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "altered.json"
            altered.write_text(json.dumps(pub), encoding="utf-8")
            with patch.object(index02, "PUBLISHED", altered):
                with self.assertRaises(ValueError):
                    index02.lookup_source_file_02(original_url="https://example.invalid/none")

    def test_manifest_file_sequence_preserves_global_l1_boundary(self):
        doc = json.loads(CANON.read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "canonical/registries/CFA3-DONOR-L1-SOURCE-ARCHIVE-MANIFEST-001.json").read_text(encoding="utf-8"))
        seq = doc["sequential_file_publications"]
        self.assertEqual([x["source_sequence"] for x in seq], [1])
        receipts = manifest["per_file_completion_receipts"]
        self.assertEqual([x["published_catalog"] for x in receipts[:2]], [
            "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json",
            "canonical/registries/CFA3-DONOR-SOURCE-FILE-002.json"])
        self.assertEqual(receipts[1]["source_coverage_rows"], 445)
        self.assertTrue(receipts[1]["canonical_l1_published"])
        self.assertFalse(doc["global_l1_completed"])
        self.assertEqual(doc["donor_count"], 81)

    def test_all_canonical_registry_locator_aliases_are_indexed(self):
        pub = index02.verified_catalog()
        for row in pub["records"]:
            url = row["canonical_locator_in_registry"]
            self.assertIn(url, pub["lookup_by_locator"])
            self.assertEqual(pub["records"][pub["lookup_by_locator"][url]]["donor_id"], row["donor_id"])
            self.assertEqual(index02.lookup_source_file_02(original_url=url)["donor_id"], row["donor_id"])


if __name__ == "__main__":
    unittest.main()
