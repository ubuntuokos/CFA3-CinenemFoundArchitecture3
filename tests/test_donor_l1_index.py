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
        self.assertEqual(len(sources), 1944)
        self.assertEqual(sum(1 for _, _, canonical in sources if canonical), 1919)
        self.assertEqual(sum(1 for _, _, canonical in sources if not canonical), 25)

    def test_staging_index_round_trip_and_no_false_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "staged.sqlite"
            receipt = donor_l1.stage(dbpath, "unit-test")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            self.assertIsNone(receipt["raw_link_limit"])
            self.assertEqual(receipt["index_evidence"]["rows"], 1944)
            self.assertEqual(receipt["index_evidence"]["supplemental_unreconciled_owner_sources"], 23)
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
                self.assertEqual(meta["supplemental_owner_source_candidates"],"23")
                self.assertEqual(meta["all_owner_submissions_verified"],"FALSE")
                self.assertEqual(meta["bounded_union_link_records"],"445")
                self.assertEqual(meta["bounded_union_distinct_donor_ids"],"443")
                self.assertEqual(meta["bounded_union_original_url_records"],"445")
                self.assertEqual(db.execute(
                    "SELECT current_status FROM sources WHERE source_origin='UNMERGED_PR_744'").fetchone()[0],
                    "BLOCKED")

    def test_additional_explicit_approved_links_are_preserved_but_not_auto_admitted(self):
        supplement = donor_l1.json_read(donor_l1.SUPPLEMENT)
        self.assertEqual(supplement["verification_bounds"]["additional_exact_owner_marker_context_sources"], 8)
        expected = {
            "https://github.com/anthropics",
            "https://krater.ai/",
            "https://github.com/topics/ontology-development",
            "https://github.com/microsoft/Ontology-Playground",
            "https://github.com/ozekik/awesome-ontology",
            "https://infranodus.com/skills/ontology-creator",
            "https://github.com/nicovlr/smart-ontology-generator",
            "https://github.com/arunsr1ni/databricks-ontology-generator",
        }
        entries = [e for e in supplement["entries"] if e["submission_review"].get("original_chat_evidence_location") == "PRIOR_CFA3_CONVERSATION_CONTEXT"]
        self.assertEqual({e["source"]["locator"] for e in entries}, expected)
        for entry in entries:
            self.assertFalse(entry["intake_provenance"]["canonical_approval_admitted"])
            self.assertFalse(entry["submission_review"]["exact_submitted_URL_and_approval_pair_independently_verified"])
        self.assertFalse(supplement["verification_bounds"]["all_past_chats_exhaustively_audited"])

    def test_no_modification_to_original_archive(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(donor_l1.sha_blob(donor_l1.REGISTRY.read_bytes()),
                         donor_l1.EXPECTED["FA3-DONOR-REFERENCE-REGISTRY-001.json"])
        self.assertEqual(len(sources),1944)

    def test_historical_missing_sources_recoverable_without_false_admission(self):
        supplement = donor_l1.json_read(donor_l1.SUPPLEMENT)
        self.assertEqual(len(supplement["entries"]), 23)
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

    def test_owner_approval_evidence_is_bounded_and_nonadmitting(self):
        supplementary = donor_l1.json_read(donor_l1.SUPPLEMENT)
        evidence = supplementary["approval_evidence_reconciliation"]
        self.assertFalse(evidence["promotion_permitted"])
        self.assertFalse(evidence["source_index_complete"])
        self.assertEqual(evidence["conversation_wide_approval_report"]["affected_entries"], 10)
        self.assertFalse(evidence["conversation_wide_approval_report"]
                         ["exact_user_message_and_links_machine_auditable_in_repo"])
        self.assertEqual(len(evidence["remaining_unverified_suggested_references"]),4)
        self.assertEqual(evidence["explicit_covert_approval_historical_evidence"]["legacy_pr"],720)
        self.assertFalse(evidence["explicit_covert_approval_historical_evidence"]
                         ["new_repository_canonical_admission"])
        four = {"MakeHuman2","CharMorph","SMPL-X","DECA"}
        blocked = 0
        for entry in supplementary["entries"]:
            self.assertFalse(entry["intake_provenance"]["canonical_approval_admitted"])
            self.assertFalse(entry["submission_review"]
                             ["exact_submitted_URL_and_approval_pair_independently_verified"])
            if entry["name"] in four:
                blocked += 1
                self.assertEqual(entry["submission_review"]["evidence_gap"],
                                 "DIRECT_OWNER_DONORNAK_MARKER_NOT_VERIFIED_REFERENCE_ONLY")
        self.assertEqual(blocked,4)

    def test_duplicate_identity_fails_closed(self):
        src = donor_l1.frozen_sources()
        with tempfile.TemporaryDirectory() as tmp:
            with sqlite3.connect(":memory:") as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    donor_l1.prepare(db,[src[0],src[0]],"duplicate")

if __name__ == "__main__":
    unittest.main()
