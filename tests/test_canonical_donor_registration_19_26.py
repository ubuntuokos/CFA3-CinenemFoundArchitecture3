"""Exact donor-ID and original-URL readback of canonical records from historical files 19–26."""
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json"
LEDGER = ROOT / "canonical/registries/CFA3-DONOR-OWNER-APPROVAL-19-26-20261010.json"


class CanonicalDonorRegistration1926Tests(unittest.TestCase):
    def test_complete_eight_source_files_and_original_url_lookup(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(registry["schema"], "cfa3.canonical-donor-reference-registry.v1")
        self.assertEqual(registry["id"], "CFA3-DONOR-REFERENCE-REGISTRY-001")
        self.assertEqual(registry["registration_state"], "PARTIAL_CANONICAL_REFERENCES_REGISTERED")
        self.assertEqual(registry["source_files_completed"], list(range(19, 27)))
        self.assertEqual(registry["donor_count"], 81)
        self.assertEqual(registry["original_url_occurrences"], 83)
        self.assertFalse(registry["global_l1_completed"])
        self.assertFalse(registry["all_historical_sources_exhaustively_reconciled"])
        self.assertFalse(registry["runtime_admission"])
        self.assertFalse(registry["code_or_license_admission"])

        records = registry["records"]
        self.assertEqual(len(records), 81)
        self.assertEqual(len(registry["lookup_by_id"]), 81)
        self.assertEqual(len(registry["lookup_by_original_url"]), 83)
        self.assertEqual(len({r["donor_id"] for r in records}), 81)
        self.assertEqual(len({r["normalized_key"] for r in records}), 81)

        # The separately recovered Vanessik record is NOT source file 19–26.
        expected = {
            e["id"]: e for e in ledger["records"]
            if any(e["originating_historical_file"] == g["source_path"]
                   for g in ledger["source_groups"])
        }
        self.assertEqual(len(expected), 81)
        observed_groups = Counter()
        actual_pairs = []
        for i, row in enumerate(records):
            sid = row["donor_id"]
            with self.subTest(donor=sid):
                self.assertIn(sid, expected)
                source = expected[sid]
                self.assertEqual(registry["lookup_by_id"][sid], i)
                self.assertEqual(row["normalized_key"], source["normalized_source_key"])
                self.assertEqual(row["original_url"], source["canonical_locator"])
                self.assertEqual(row["historical_status"], source["legacy_status"])
                self.assertEqual(row["historical_status"], "ACCEPTED_REFERENCE")
                self.assertEqual(row["donor_registration"], "CANONICAL_REFERENCE_REGISTERED")
                self.assertFalse(row["runtime_admission"])
                self.assertFalse(row["code_copy_authorized"])
                self.assertFalse(row["license_authorized"])
                self.assertFalse(row["model_provider_admission"])
                self.assertEqual(
                    row["original_submitted_urls"],
                    [v["url"] for v in source["original_submitted_urls"]])
                group = next(g for g in ledger["source_groups"]
                             if g["source_path"] == row["originating_historical_file"])
                self.assertEqual(row["source_sequence"], group["source_sequence"])
                observed_groups[row["source_sequence"]] += 1
                for url in row["original_submitted_urls"]:
                    self.assertEqual(registry["lookup_by_original_url"][url], sid)
                    actual_pairs.append((sid, url))
        self.assertEqual(
            dict(observed_groups),
            {g["source_sequence"]: g["unique_ids"] for g in ledger["source_groups"]})
        self.assertEqual(len(actual_pairs), 83)
        self.assertEqual(len({url for _, url in actual_pairs}), 83)
        expected_pairs = [
            (e["id"], url["url"]) for e in expected.values()
            for url in e["original_submitted_urls"]
        ]
        self.assertCountEqual(actual_pairs, expected_pairs)

    def test_filtered_topic_views_and_archived_comfy_original_are_preserved(self):
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        by_id = {r["donor_id"]: r for r in reg["records"]}
        memory = by_id["FA3-DONOR-GITHUB-TOPIC-AI-MEMORY-001"]
        self.assertEqual(
            memory["original_submitted_urls"],
            ["https://github.com/topics/ai-memory?o=desc&s=updated",
             "https://github.com/topics/ai-memory?o=asc&s=forks"])
        for url in memory["original_submitted_urls"]:
            self.assertEqual(reg["lookup_by_original_url"][url], memory["donor_id"])
        comfy = by_id["FA3-DONOR-COMFY-ORG-DESKTOP-ARCHIVED-001"]
        self.assertEqual(comfy["original_url"], "https://github.com/Comfy-Org/desktop")
        self.assertEqual(
            reg["lookup_by_original_url"]["https://github.com/Comfy-Org/desktop"],
            comfy["donor_id"])
        self.assertFalse(comfy["runtime_admission"])


if __name__ == "__main__":
    unittest.main()
