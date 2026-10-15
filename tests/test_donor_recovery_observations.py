"""Missing historical observation evidence must never produce a successful audit."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_donor_source_file01_recovery as recovery


class RecoveryObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name in recovery.OBSERVATION_BATCHES:
            shutil.copyfile(recovery.REG / name, self.directory / name)

    def read_batches(self):
        return recovery.observation_batches(
            lambda path, raw: json.loads(raw), self.directory)

    def test_original_two_batches_preserve_all_25_observations(self):
        self.assertEqual([len(doc["records"]) for doc in self.read_batches()], [15, 10])

    def test_either_missing_batch_is_rejected(self):
        for name in recovery.OBSERVATION_BATCHES:
            with self.subTest(batch=name):
                path = self.directory / name
                raw = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                    self.read_batches()
                path.write_bytes(raw)

    def test_renamed_batch_is_rejected_inside_and_outside_glob(self):
        original = self.directory / next(iter(recovery.OBSERVATION_BATCHES))
        for name in ("renamed.json", original.name.replace("001.json", "003.json")):
            with self.subTest(name=name):
                moved = original.rename(self.directory / name)
                with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                    self.read_batches()
                moved.rename(original)

    def test_truncated_or_absent_record_list_is_rejected(self):
        for name in recovery.OBSERVATION_BATCHES:
            path = self.directory / name
            raw = path.read_bytes()
            for records in (json.loads(raw)["records"][:-1], [], None):
                with self.subTest(batch=name, records=type(records).__name__):
                    doc = json.loads(raw)
                    doc["records"] = records
                    path.write_text(json.dumps(doc), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "record count mismatch"):
                        self.read_batches()
            path.write_bytes(raw)

    def test_extra_batch_cannot_silently_expand_audited_scope(self):
        path = self.directory / next(iter(recovery.OBSERVATION_BATCHES))
        shutil.copyfile(path, path.with_name(path.name.replace("001.json", "003.json")))
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            self.read_batches()

    def test_changed_metadata_with_original_identity_and_count_is_rejected(self):
        for name in recovery.OBSERVATION_BATCHES:
            path = self.directory / name
            raw = path.read_bytes()
            for field, value in (("github_repository_metadata", "NOT_FOUND_AT_CHECK"),
                                 ("reported_pushed_at", "2099-01-01T00:00:00Z"),
                                 ("rights_review_complete", True)):
                with self.subTest(batch=name, field=field):
                    doc = json.loads(raw)
                    doc["records"][0][field] = value
                    path.write_text(json.dumps(doc), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "observation digest mismatch"):
                        self.read_batches()
            path.write_bytes(raw)


if __name__ == "__main__":
    unittest.main()
