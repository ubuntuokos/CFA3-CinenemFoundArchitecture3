"""Bounded legacy-delta readback: preserved approved records do not need re-analysis."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"canonical/registries/CFA3-DONOR-L1-LEGACY-DELTA-RECONCILIATION-20261009.json"
spec=importlib.util.spec_from_file_location("donor_l1",ROOT/"scripts/donor_l1.py")
donor_l1=importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)

class LegacyDeltaAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.archive={entry["source"]["normalized_key"]:entry
                     for entry, origin, _ in donor_l1.frozen_sources()
                     if origin=="OLD_MAIN_ARCHIVE"}

    def test_every_bounded_delta_has_same_archived_identity(self):
        a=self.audit
        self.assertEqual(a["state"],"BOUNDED_75_VERIFIED_NOT_GLOBAL_COMPLETENESS")
        self.assertEqual(len(a["groups"]),7)
        self.assertEqual(len(a["records"]),75)
        self.assertEqual(len({row["source_key"] for row in a["records"]}),75)
        self.assertEqual(sum(group["input_source_count"] for group in a["groups"]),75)
        self.assertEqual(a["checks"]["missing_from_archive"],0)
        for row in a["records"]:
            with self.subTest(key=row["source_key"]):
                original=self.archive[row["source_key"]]
                self.assertEqual(original["donor_id"],row["donor_id"])
                self.assertEqual(original["status"],row["archived_status"])

    def test_only_bounded_subsets_are_claimed(self):
        a=self.audit
        for claim in ("all_prior_chats","L1_publication","L2_to_L5","full_new_CFA3_admission"):
            self.assertTrue(a["not_verified"][claim])
        self.assertFalse(a["runtime_authorization"])
        self.assertEqual(set(g["legacy_pr"] for g in a["groups"]),{731,735,737,738,739,740})

    def test_archive_originals_not_reclassified(self):
        self.assertEqual(len(self.archive),1919)
        for row in self.audit["records"]:
            self.assertTrue(row["donor_id"])
            self.assertIn(row["archived_status"],
                          {"ACCEPTED_REFERENCE","ANALYZED","CANDIDATE","SUPERSEDED"})

if __name__=="__main__":
    unittest.main()
