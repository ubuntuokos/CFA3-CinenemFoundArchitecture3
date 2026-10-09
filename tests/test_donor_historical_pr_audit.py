"""Bounded historical PR -> immutable archived donor identity audit.

This is NOT proof of all owner submissions, original B, or canonical L1 publication.
"""
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "canonical/registries"
MANIFESTS = [
    ("CFA3-DONOR-L1-HISTORICAL-PR-RECONCILIATION-A-20261010.json", 8, 23),
    ("CFA3-DONOR-L1-HISTORICAL-PR-RECONCILIATION-B-20261010.json", 10, 86),
]
spec = importlib.util.spec_from_file_location("donor_l1_pr_audit", ROOT / "scripts/donor_l1.py")
donor_l1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)


class HistoricalDonorPrAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = {
            x["donor_id"]: x
            for x, origin, _ in donor_l1.frozen_sources()
            if origin == "OLD_MAIN_ARCHIVE"
        }
        cls.reports = [json.loads((REGISTRY / f).read_text(encoding="utf-8"))
                       for f, _, _ in MANIFESTS]

    def test_exact_archived_identity_and_original_urls(self):
        self.assertEqual(len(self.archive), 1919)
        self.assertEqual(len(self.reports), 2)
        observed_prs = set()
        total_rows = 0
        for report, (_, expected_groups, expected_rows) in zip(self.reports, MANIFESTS):
            self.assertEqual(report["archived_registry_blob_sha"],
                             donor_l1.EXPECTED["FA3-DONOR-REFERENCE-REGISTRY-001.json"])
            self.assertEqual(report["legacy_main_sha"],
                             "a9c724da62bf49f3353c694990fc51443e634b4a")
            self.assertEqual(report["status"],
                             "VERIFIED_BOUNDED_LEGACY_PR_IDENTITIES_NOT_L1_PUBLISHED")
            self.assertEqual(len(report["groups"]), expected_groups)
            self.assertEqual(report["total_groups"], expected_groups)
            self.assertEqual(report["total_matched_rows"], expected_rows)
            self.assertIsNone(report["frozen_l1_B"])
            self.assertIs(report["global_approved_submissions_complete"], False)
            self.assertIs(report["canonical_level_published"], False)
            self.assertIs(report["runtime_admission"], False)
            for group in report["groups"]:
                number = group["historical_pr"]
                self.assertNotIn(number, observed_prs)
                observed_prs.add(number)
                self.assertRegex(group["pr_head_sha"], r"^[0-9a-f]{40}$")
                self.assertRegex(group["delta_blob_sha"], r"^[0-9a-f]{40}$")
                self.assertTrue(group["delta_path"].startswith("canonical/deltas/"))
                rows = group["archive_identities"]
                self.assertEqual(group["archive_match_count"], len(rows))
                self.assertGreater(len(rows), 0)
                urls = group["observed_original_submitted_urls"]
                self.assertGreater(len(urls), 0)
                for url in urls:
                    p = urlsplit(url)
                    self.assertIn(p.scheme, ("http", "https"))
                    self.assertTrue(p.hostname)
                if group["observed_submitted_url_count"] is not None:
                    self.assertEqual(group["observed_submitted_url_count"], len(urls))
                for row in rows:
                    donor_id = row.get("archived_donor_id")
                    if not donor_id:
                        donor_id = row["proposed_donor_id"]
                    archived = self.archive[donor_id]
                    key = row.get("archived_normalized_key", row.get("normalized_key"))
                    self.assertEqual(archived["source"]["normalized_key"], key)
                    if row.get("legacy_donor_id_alias_only") is True:
                        self.assertNotEqual(row["original_proposed_donor_id"], donor_id)
                    else:
                        self.assertEqual(
                            row.get("original_proposed_donor_id", row.get("proposed_donor_id")),
                            donor_id)
                total_rows += len(rows)
        self.assertEqual(total_rows, 109)
        self.assertEqual(len(observed_prs), 18)

    def test_one_explicit_legacy_alias_not_new_donor(self):
        rows = [r for g in self.reports[1]["groups"] for r in g["archive_identities"]
                if r.get("legacy_donor_id_alias_only")]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["original_proposed_donor_id"],
                         "FA3-DONOR-MICROSOFT-ONNXRUNTIME-001")
        self.assertEqual(row["archived_donor_id"],
                         "FA3-DONOR-MICROSOFT-ONNX-RUNTIME-001")
        self.assertEqual(row["normalized_key"], "github:microsoft/onnxruntime")
        self.assertEqual(self.reports[1]["legacy_donor_id_alias_rows"], 1)


if __name__ == "__main__":
    unittest.main()
