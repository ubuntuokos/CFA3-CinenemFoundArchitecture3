"""Positive and negative tests for the pre-upload donor file-size guard."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_donor_file_size import LIMIT_BYTES, is_donor_data, validate_changed_files

class DonorFileSizeTests(unittest.TestCase):
    def test_donor_file_identification(self):
        for name in (
            "canonical/registries/CFA3-DONOR-SOURCE-FILE-003.json",
            "canonical/registries/CFA3-DONOR-L1-URL-ROUTING-20261010.json",
            "canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json",
            "archive/donor/data.jsonl",
            "somewhere/donor-aliases.csv",
            "docs/governance/exports/CFA3-DONOR-DATA-SNAPSHOT.json",
        ):
            with self.subTest(name=name):
                self.assertTrue(is_donor_data(name))
        for name in (
            "scripts/check_donor_file_size.py",
            "canonical/policies/CFA3-DONOR-FILE-SIZE-POLICY-001.json",
            "docs/governance/DONOR-MIGRATION.md",
            "canonical/registries/NOT-DONOR-DATA.py",
        ):
            with self.subTest(name=name):
                self.assertFalse(is_donor_data(name))

    def test_exact_limit_allowed_excess_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = "canonical/registries/CFA3-DONOR-SOURCE-FILE-003.json"
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x" * LIMIT_BYTES)
            issues, checked = validate_changed_files([path], root)
            self.assertEqual([], issues)
            self.assertEqual([(path, LIMIT_BYTES)], checked)
            target.write_bytes(b"x" * (LIMIT_BYTES + 1))
            issues, checked = validate_changed_files([path], root)
            self.assertEqual(1, len(issues))
            self.assertIn("STOP/BLOCKER", issues[0])
            self.assertEqual(LIMIT_BYTES + 1, checked[0][1])

    def test_historical_unchanged_oversize_not_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json"
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"x" * (LIMIT_BYTES + 10))
            issues, checked = validate_changed_files([], root)
            self.assertEqual(([], []), (issues, checked))
            issues, checked = validate_changed_files(
                ["canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json"], root)
            self.assertEqual(1, len(issues))

    def test_missing_or_oversized_modified_data_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues, checked = validate_changed_files(
                ["canonical/registries/CFA3-DONOR-ABSENT.json"], root)
            self.assertEqual([], checked)
            self.assertEqual(1, len(issues))
            self.assertIn("cannot measure", issues[0])

if __name__ == "__main__":
    unittest.main()
