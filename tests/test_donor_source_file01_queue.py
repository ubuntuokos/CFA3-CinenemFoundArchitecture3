"""Checks the indexed two-phase donor source-file 001 queue, without fake phase PASS."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_donor_source_file01_queue as queue

class SourceFile001TwoPhaseQueueTests(unittest.TestCase):
    def test_complete_source_file_index_replay(self):
        actual = queue.validated_queue()
        self.assertEqual(actual, queue.build())
        groups = actual["classification_groups"]
        positions = [p for name in queue.GROUPS for p in groups[name]]
        self.assertEqual(len(positions), 1919)
        self.assertEqual(sorted(positions), list(range(1919)))
        self.assertEqual(len(set(positions)), 1919)
        source = json.loads(queue.SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(len(source["records"]), 1919)
        for name in queue.GROUPS:
            self.assertEqual(groups[name],
                             [i for i, row in enumerate(source["records"])
                              if queue.classify(row) == name])

    def test_no_false_admission_or_phase_completion(self):
        record = queue.validated_queue()
        self.assertFalse(record["new_donor_approval"])
        self.assertFalse(record["runtime_or_license_admission"])
        self.assertFalse(record["type_prefilter_is_live_source_verification"])
        self.assertFalse(record["phase_1"]["completeness_pass"])
        self.assertFalse(record["phase_2"]["completeness_pass"])
        self.assertEqual(record["phase_2"]["crawled_collections"], 0)
        self.assertFalse(record["global_donor_database_complete"])
        self.assertFalse(record["arbitrary_depth_or_15_percent_expansion_quota"])

    def test_preserved_size_and_source_pin(self):
        self.assertLessEqual(len(queue.rendered()), 996147)
        self.assertLessEqual(queue.OUTPUT.stat().st_size, 996147)
        self.assertEqual(queue.validated_queue()["source_catalog_git_blob_sha1"],
                         queue.SOURCE_GIT_BLOB)

    def test_corrupted_queue_fails_closed(self):
        correct = queue.validated_queue()
        mutated = json.loads(json.dumps(correct))
        mutated["classification_groups"]["direct_candidates"].pop()
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "fake.json"
            fake.write_text(json.dumps(mutated), encoding="utf-8")
            with patch.object(queue, "OUTPUT", fake):
                with self.assertRaises(ValueError):
                    queue.validated_queue()

if __name__ == "__main__":
    unittest.main()
