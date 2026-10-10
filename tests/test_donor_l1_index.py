"""L1 staged source import and index read-back tests; not publication authorization."""
import copy
import json
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
import unittest.mock
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("donor_l1", ROOT / "scripts/donor_l1.py")
donor_l1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)


class DonorL1IndexTests(unittest.TestCase):
    def test_direct_l1_access_catalog_has_full_stage_readback_and_never_claims_publication(self):
        catalog_path = ROOT / "canonical/registries/CFA3-DONOR-L1-STAGED-DIRECT-ACCESS-20261010.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["state"], "STAGED_NOT_PUBLISHED")
        self.assertFalse(catalog["canonical_level_published"])
        self.assertIsNone(catalog["global_baseline_B"])
        self.assertFalse(catalog["all_owner_submissions_exhaustively_verified"])
        self.assertFalse(catalog["runtime_admission"])
        self.assertEqual(catalog["source_count"], 1981)
        self.assertEqual(catalog["distinct_identity_count"], 1981)
        self.assertEqual(catalog["approval_summary"]["legacy_owner_approved_pending_publication"], 59)
        self.assertEqual(catalog["approval_summary"]["historical_pr_owner_approved_transfer_sources"], 2)
        self.assertEqual(catalog["approval_summary"]["historical_accepted_reference"], 825)
        self.assertEqual(catalog["approval_summary"]["legacy_candidate"], 963)
        self.assertEqual(catalog["approval_summary"]["legacy_analyzed"], 130)
        items = catalog["sources"]
        self.assertEqual(len(items), 1981)
        self.assertEqual(len({item["id"] for item in items}), 1981)
        self.assertEqual(len({item["key"] for item in items}), 1981)
        canonical = {item["id"]: item for item in items}
        for entry, origin, from_main in donor_l1.frozen_sources():
            item = canonical[entry["donor_id"]]
            self.assertEqual(item["key"], entry["source"]["normalized_key"])
            self.assertEqual(item["url"], entry["source"]["locator"])
            self.assertEqual(item["level"], 1)
            self.assertEqual(item.get("discovery_urls", []), entry["source"].get("discovery_urls", []))
            approved_origin = origin in {
                "HISTORICAL_OWNER_MESSAGE_APPROVED_TRANSFER",
                "HISTORICAL_OWNER_APPROVED_TRANSFER",
                "ADDITIONAL_OWNER_APPROVED_TRANSFER",
                "HISTORICAL_TRIPO_OWNER_APPROVED_TRANSFER",
                "HISTORICAL_PR_744_OWNER_APPROVED_TRANSFER",
                "HISTORICAL_PR_745_OWNER_APPROVED_TRANSFER",
            }
            expected_status = ("OWNER_APPROVED_PENDING_PUBLICATION" if entry["donor_id"] == "FA3-DONOR-OPENCUT-001" else
                entry["status"] if from_main else
                "OWNER_APPROVED_PENDING_PUBLICATION" if approved_origin else "BLOCKED")
            self.assertEqual(item["status"], expected_status)
        recovery = donor_l1.json_read(donor_l1.TRIPO_RECOVERY)
        for occurrence in recovery["url_provenance"]:
            item = canonical[occurrence["source_id"]]
            self.assertIn(occurrence["original_url"],
                          [item["url"]] + item.get("discovery_urls", []))

    def test_old_pr_744_745_explicit_donor_approvals_transfer_not_new_donors(self):
        approved = donor_l1.historical_pr_owner_approvals()
        self.assertEqual({r["old_pr"] for r in approved}, {744,745})
        self.assertEqual(len({r["id"] for r in approved}),2)
        self.assertTrue(all(r["historical_owner_marker"]=="donornak" for r in approved))
        self.assertTrue(all(r["new_staging_status"]=="OWNER_APPROVED_PENDING_PUBLICATION"
                            for r in approved))
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/"historical-pr-donors.sqlite"
            receipt=donor_l1.stage(dbpath,"historic-pr-approval")
            self.assertEqual(receipt["state"],"STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            self.assertEqual(receipt["index_evidence"]["rows"],1981)
            self.assertEqual(receipt["index_evidence"]["historical_pr_owner_approved_transfer_sources"],2)
            for entry in approved:
                matched=donor_l1.lookup(dbpath,entry["id"],"id")
                self.assertEqual(len(matched),1)
                self.assertEqual(matched[0]["status"],"OWNER_APPROVED_PENDING_PUBLICATION")
                for url in [entry["url"],*entry.get("additional_exact_search_aliases",[])]:
                    self.assertEqual(donor_l1.lookup(dbpath,url,"url")[0]["id"],entry["id"])
                self.assertEqual(entry["new_staging_status"],matched[0]["status"])
            with sqlite3.connect(dbpath) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM sources").fetchone()[0],1981)
                self.assertEqual(db.execute("SELECT count(*) FROM url_resolution").fetchone()[0],3943)
                self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='publication_gate'").fetchone()[0],"PENDING")

    def test_five_owner_url_resolutions_preserve_all_original_identities(self):
        owner_pairs = {
            "https://alternativeto.net/software/octane-render/?p=2": "FA3-DONOR-ALTERNATIVETO-NET-SOFTWARE-OCTANE-RENDER-P-2-DFF81B7B-001",
            "https://alternativeto.net/software/octane-render/?p=3": "FA3-DONOR-ALTERNATIVETO-NET-SOFTWARE-OCTANE-RENDER-P-3-DEF819E8-001",
            "https://alternativeto.net/software/octane-render/?p=4": "FA3-DONOR-ALTERNATIVETO-NET-SOFTWARE-OCTANE-RENDER-P-4-E5F824ED-001",
            "https://github.com/Ascend/triton-ascend": "FA3-DONOR-TRITON-LANG-TRITON-ASCEND-001",
            "https://clover.moe/mm3d": "FA3-DONOR-CLOVER-MOE-MM3D-A17787FE-001",
        }
        alternate_pairs = {
            "https://alternativeto.net/software/octane-render/?p=2": "FA3-DONOR-ALTERNATIVETO-OCTANE-ALTERNATIVES-001",
            "https://alternativeto.net/software/octane-render/?p=3": "FA3-DONOR-ALTERNATIVETO-OCTANE-ALTERNATIVES-001",
            "https://alternativeto.net/software/octane-render/?p=4": "FA3-DONOR-ALTERNATIVETO-OCTANE-ALTERNATIVES-001",
            "https://github.com/Ascend/triton-ascend": "FA3-DONOR-ASCEND-TRITON-ASCEND-LEGACY-001",
            "https://clover.moe/mm3d": "FA3-DONOR-CLOVER-MOE-MM3D-001",
        }
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/"url-resolution.sqlite"
            receipt=donor_l1.stage(dbpath,"owner-resolution-test")
            self.assertEqual(receipt["state"],"STAGED_NOT_PUBLISHED")
            self.assertEqual(receipt["index_evidence"]["ambiguous_urls_with_preserved_relations"],5)
            for url, expected_id in owner_pairs.items():
                self.assertEqual([x["id"] for x in donor_l1.lookup(dbpath,url,"url")], [expected_id])
                alias_ids={x["id"] for x in donor_l1.lookup(dbpath,url,"alias")}
                self.assertEqual(alias_ids, {expected_id,alternate_pairs[url]})
                with sqlite3.connect(dbpath) as db:
                    row=db.execute("SELECT preferred_source_id,authority,related_source_ids_json "
                                   "FROM url_resolution WHERE alias=?",(url,)).fetchone()
                    self.assertEqual(row[0], expected_id)
                    self.assertEqual(row[1], "HISTORICAL_OWNER_BASELINE")
                    self.assertEqual(set(json.loads(row[2])), alias_ids)
            self.assertEqual(donor_l1.lookup(dbpath,"https://github.com/Ascend/triton-ascend","id"),[])
            self.assertEqual(donor_l1.lookup(dbpath,"FA3-DONOR-ASCEND-TRITON-ASCEND-LEGACY-001","id")[0]["status"],"SUPERSEDED")
            self.assertEqual(donor_l1.lookup(dbpath,"FA3-DONOR-CLOVER-MOE-MM3D-001","id")[0]["status"],"ACCEPTED_REFERENCE")

    def test_historical_shgaf_original_submitted_url_views_are_not_lost(self):
        delta_path = ROOT / "archive/donor-source-migration/2026-10-09/CFA3-DONOR-SHGAF-HALLUCINATION-ASSURANCE-2026-10-06.json"
        delta = json.loads(delta_path.read_text(encoding="utf-8"))
        self.assertEqual(len(delta["submitted_urls"]), 20)
        bindings = {}
        for entry in delta["canonical_identities"]:
            for url in [entry["source"], *entry.get("submitted_views", [])]:
                self.assertNotIn(url, bindings)
                bindings[url] = entry["donor_id"]
        self.assertEqual(set(bindings), set(delta["submitted_urls"]))
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "shgaf-original-url-readback.sqlite"
            donor_l1.stage(dbpath, "shgaf-original-url-readback")
            with sqlite3.connect(dbpath) as db:
                for url, donor_id in bindings.items():
                    actual = db.execute("SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                                        (url,)).fetchone()
                    self.assertEqual(actual, (donor_id,))
                    provenance = db.execute(
                        "SELECT 1 FROM source_provenance WHERE source_id=? AND original_url=? "
                        "AND source_set='HISTORICAL_SHGAF_20261006'",
                        (donor_id, url)).fetchone()
                    self.assertIsNotNone(provenance)
                self.assertEqual(db.execute(
                    "SELECT count(*) FROM url_resolution").fetchone()[0], 3943)

    def test_direct_url_routing_exactly_matches_sqlite_and_preserves_all_relations(self):
        routing_path=ROOT/"canonical/registries/CFA3-DONOR-L1-URL-ROUTING-20261010.json"
        routing=json.loads(routing_path.read_text(encoding="utf-8"))
        self.assertEqual(routing["state"],"STAGED_NOT_PUBLISHED")
        self.assertFalse(routing["canonical_level_published"])
        self.assertIsNone(routing["original_L1_B"])
        self.assertEqual(routing["source_count"],1981)
        self.assertEqual(routing["alias_count"],3943)
        self.assertEqual(routing["multiple_related_identity_url_count"],5)
        self.assertEqual(routing["owner_baseline_original_urls"],445)
        self.assertEqual(routing["tripo_original_url_occurrences"],48)
        self.assertEqual(len(routing["entries"]),3943)
        self.assertEqual(len({x["alias"] for x in routing["entries"]}),3943)
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/"url-routing-readback.sqlite"
            donor_l1.stage(dbpath,"url-routing-readback")
            with sqlite3.connect(dbpath) as db:
                database_rows={a:(id_,authority,json.loads(ids)) for a,id_,authority,ids in db.execute(
                    "SELECT alias,preferred_source_id,authority,related_source_ids_json "
                    "FROM url_resolution ORDER BY alias")}
            self.assertEqual(len(database_rows),3943)
            for row in routing["entries"]:
                self.assertEqual(database_rows[row["alias"]],
                                 (row["preferred_source_id"],row["authority"],row["related_source_ids"]))
                self.assertIn(row["preferred_source_id"],row["related_source_ids"])
            self.assertEqual(sum(len(row["related_source_ids"]) > 1 for row in routing["entries"]),5)

    def test_historical_20261007_owner_links_imported_without_duplicate_or_runtime_admission(self):
        recovery = donor_l1.owner_message_recovery()
        self.assertEqual(len(recovery["entries"]), 3)
        self.assertEqual(len(recovery["existing_source_approval_overrides"]), 1)
        original = [entry["source"]["locator"] for entry in recovery["entries"]]
        self.assertEqual(set(original), {
            "https://github.com/ExistentialAudio/BlackHole",
            "https://github.com/ExistentialAudio",
            "https://github.com/upstash",
        })
        self.assertFalse(recovery["canonical_level_published"])
        self.assertFalse(recovery["runtime_admission"])
        with tempfile.TemporaryDirectory() as temp:
            dbpath = Path(temp) / "history-rescue.sqlite"
            receipt = donor_l1.stage(dbpath, "history-rescue")
            self.assertEqual(receipt["index_evidence"]["rows"], 1981)
            self.assertEqual(receipt["index_evidence"]["additional_20261007_owner_approved_source_records"], 3)
            self.assertEqual(receipt["index_evidence"]["historical_opencut_approval_overrides"], 1)
            all_links = [(e["source"]["locator"],e["donor_id"]) for e in recovery["entries"]]
            all_links.append(("https://github.com/opencut-app/opencut", "FA3-DONOR-OPENCUT-001"))
            for url, source_id in all_links:
                self.assertEqual([row["id"] for row in donor_l1.lookup(dbpath,url,"url")],[source_id])
                self.assertEqual(donor_l1.lookup(dbpath,source_id,"id")[0]["status"],
                                 "OWNER_APPROVED_PENDING_PUBLICATION")
            with sqlite3.connect(dbpath) as db:
                self.assertEqual(db.execute(
                    "SELECT historical_status FROM sources WHERE source_id='FA3-DONOR-OPENCUT-001'").fetchone()[0],
                    "CANDIDATE")
                self.assertEqual(db.execute(
                    "SELECT count(*) FROM source_provenance WHERE source_set='HISTORICAL_OWNER_MESSAGES_20261007'").fetchone()[0],4)
                self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='publication_gate'").fetchone()[0],"PENDING")

    def test_archive_sources_have_distinct_identity(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(len(sources), 1981)
        self.assertEqual(sum(1 for _, _, canonical in sources if canonical), 1919)
        self.assertEqual(sum(1 for _, _, canonical in sources if not canonical), 62)

    def test_staging_index_round_trip_and_no_false_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "staged.sqlite"
            receipt = donor_l1.stage(dbpath, "unit-test")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            self.assertIsNone(receipt["raw_link_limit"])
            self.assertEqual(receipt["index_evidence"]["rows"], 1981)
            self.assertEqual(receipt["index_evidence"]["observed_http_source_locators"], 1831)
            self.assertEqual(receipt["index_evidence"]["observed_non_http_source_locators"], 150)
            self.assertFalse(receipt["index_evidence"]["original_L1_link_record_count_B_verified"])
            self.assertEqual(
                receipt["index_evidence"]["observed_http_source_locators"]
                + receipt["index_evidence"]["observed_non_http_source_locators"],
                receipt["index_evidence"]["rows"])
            self.assertEqual(receipt["index_evidence"]["supplemental_unreconciled_owner_sources"], 23)
            self.assertEqual(receipt["index_evidence"]["additional_unreconciled_owner_sources"], 4)
            self.assertEqual(receipt["index_evidence"]["historical_url_provenance"], "BOUNDED_445_PASS")
            self.assertEqual(receipt["index_evidence"]["historical_tripo_provenance"], "BOUNDED_48_PASS")
            self.assertEqual(receipt["index_evidence"]["historical_tripo_pending_sources"], 0)
            self.assertEqual(receipt["index_evidence"]["historical_tripo_owner_approved_transfer_sources"], 30)
            self.assertEqual(receipt["index_evidence"]["historical_tripo_url_occurrences"], 48)
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
                self.assertEqual(meta["additional_owner_source_leads"],"4")
                self.assertEqual(meta["total_pending_owner_source_candidates"],"4")
                self.assertEqual(meta["legacy_owner_approved_pending_publication"],"59")
                self.assertEqual(meta["historical_pr_744_745_owner_approved_transfer_sources"],"2")
                self.assertEqual(meta["additional_20261007_owner_approved_source_records"],"3")
                self.assertEqual(meta["historical_opencut_approval_overrides"],"1")
                self.assertEqual(meta["historical_supplement_owner_approved_transfer_sources"],"19")
                self.assertEqual(meta["additional_owner_approved_transfer_sources"],"4")
                self.assertEqual(meta["historical_tripo_new_pending_sources"],"0")
                self.assertEqual(meta["historical_tripo_owner_approved_transfer_sources"],"30")
                self.assertEqual(meta["historical_tripo_original_occurrences"],"48")
                self.assertEqual(meta["historical_tripo_distinct_urls"],"46")
                self.assertEqual(meta["all_owner_submissions_verified"],"FALSE")
                self.assertEqual(meta["bounded_union_link_records"],"445")
                self.assertEqual(meta["bounded_union_distinct_donor_ids"],"443")
                self.assertEqual(meta["bounded_union_original_url_records"],"445")
                for n in (744, 745):
                    self.assertEqual(db.execute(
                        "SELECT current_status FROM sources WHERE source_origin=?",
                        (f"HISTORICAL_PR_{n}_OWNER_APPROVED_TRANSFER",)).fetchone()[0],
                        "OWNER_APPROVED_PENDING_PUBLICATION")

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

    def test_additional_owner_approval_leads_staged_without_promotion(self):
        leads = donor_l1.json_read(donor_l1.ADDITIONAL_LEADS)
        self.assertEqual(leads["status"], "CANDIDATE_STAGED_NOT_CANONICAL_PUBLISHED")
        self.assertFalse(leads["all_user_approvals_exhaustively_verified"])
        self.assertIsNone(leads["original_L1_B"])
        self.assertFalse(leads["runtime_admission"])
        self.assertEqual(len(leads["entries"]), 4)
        originals = {
            "https://github.com/getsentry/sentry",
            "https://github.com/scrapegraphai/scrapegraph-ai",
            "https://github.com/reconurge/flowsint",
            "https://github.com/fabio-rovai/open-ontologies",
        }
        self.assertEqual({e["source"]["locator"] for e in leads["entries"]}, originals)
        archive_keys = {e["source"]["normalized_key"] for e, origin, _ in donor_l1.frozen_sources()
                        if origin == "OLD_MAIN_ARCHIVE"}
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "leads.sqlite"
            receipt = donor_l1.stage(dbpath, "owner-leads-test")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            for lead in leads["entries"]:
                sid = lead["donor_id"]
                self.assertNotIn(lead["source"]["normalized_key"], archive_keys)
                self.assertFalse(lead["intake_provenance"]["canonical_approval_admitted"])
                self.assertFalse(lead["submission_review"]["exact_submitted_URL_and_approval_pair_independently_verified"])
                self.assertEqual(donor_l1.lookup(dbpath, sid, "id")[0]["status"], "OWNER_APPROVED_PENDING_PUBLICATION")
                self.assertEqual(donor_l1.lookup(dbpath, lead["source"]["locator"], "url")[0]["id"], sid)

    def test_tripo_recovery_exact_occurrences_with_owner_approved_transfer_unpublished(self):
        recovery = donor_l1.json_read(donor_l1.TRIPO_RECOVERY)
        self.assertEqual(recovery["original_submitted_url_occurrences"], 48)
        self.assertEqual(recovery["unique_submitted_urls"], 46)
        self.assertEqual(recovery["historical_url_order_sha256"], donor_l1.TRIPO_URL_ORDER_SHA256)
        self.assertEqual(recovery["historical_original_identity_set_sha256"], donor_l1.TRIPO_ORIGINAL_IDS_SHA256)
        self.assertEqual(donor_l1.historical_digest(
            [row["original_url"] for row in recovery["url_provenance"]]),
            donor_l1.TRIPO_URL_ORDER_SHA256)
        original_ids = ([entry["donor_id"] for entry in recovery["entries"]] +
                        [entry["legacy_proposed_donor_id"] for entry in recovery["existing_identity_matches"]] +
                        [recovery["historical_aggregate_reconciliation"]["historical_proposed_donor_id"]])
        self.assertEqual(len(original_ids), 36)
        self.assertEqual(donor_l1.historical_digest(sorted(original_ids)), donor_l1.TRIPO_ORIGINAL_IDS_SHA256)
        self.assertEqual(len(recovery["entries"]), 30)
        self.assertIsNone(recovery["original_L1_B"])
        self.assertFalse(recovery["all_owner_approvals_exhaustively_verified"])
        self.assertEqual(recovery["publication_gate"], "BLOCKED")
        self.assertEqual(recovery["legacy_owner_approval_transfer"]["historical_owner_marker"], "donornak")
        self.assertEqual(recovery["legacy_owner_approval_transfer"]["current_stage_approval_state"], "OWNER_APPROVED_PENDING_PUBLICATION")
        proposed_id = recovery["historical_aggregate_reconciliation"]["historical_proposed_donor_id"]
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "tripo-readback.sqlite"
            receipt = donor_l1.stage(dbpath, "tripo-no-admission")
            self.assertEqual(receipt["state"], "STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            with sqlite3.connect(dbpath) as db:
                rows = list(db.execute(
                    "SELECT occurrence_index,source_id,original_url,parent_id,global_level "
                    "FROM historical_link_occurrences ORDER BY occurrence_index"))
                self.assertEqual(len(rows), 48)
                self.assertEqual(len({row[2] for row in rows}), 46)
                self.assertEqual([row[0] for row in rows], list(range(1, 49)))
                self.assertTrue(all(row[3] is None and row[4] == 1 for row in rows))
                self.assertEqual(db.execute(
                    "SELECT count(*) FROM relations").fetchone()[0], 0)
                self.assertFalse(db.execute("SELECT 1 FROM sources WHERE source_id=?",
                                            (proposed_id,)).fetchone())
                self.assertEqual(db.execute(
                    "SELECT count(*) FROM sources WHERE source_origin=?",
                    ("HISTORICAL_TRIPO_OWNER_APPROVED_TRANSFER",)).fetchone()[0], 30)
            for preserved in recovery["historical_aggregate_reconciliation"]["preserved_archive_identities"]:
                expected = preserved["archived_donor_id"]
                self.assertIn(expected,
                              [row["id"] for row in donor_l1.lookup(
                                  dbpath, preserved["original_url"], "url")])
            for candidate in recovery["entries"]:
                self.assertEqual(
                    donor_l1.lookup(dbpath, candidate["donor_id"], "id")[0]["status"],
                    "OWNER_APPROVED_PENDING_PUBLICATION")
                self.assertFalse(candidate["intake_provenance"]["canonical_approval_admitted"])

    def test_historical_tripo_transfer_approval_fails_closed_if_owner_marker_missing(self):
        original_read = donor_l1.json_read
        source = original_read(donor_l1.TRIPO_RECOVERY)
        tampered = copy.deepcopy(source)
        tampered["entries"][0]["submission_review"]["reported_owner_marker"] = "not-an-owner-approval"
        def mocked(path):
            if path == donor_l1.TRIPO_RECOVERY:
                return tampered
            return original_read(path)
        with unittest.mock.patch.object(donor_l1, "json_read", side_effect=mocked):
            with self.assertRaisesRegex(ValueError, "Historical Tripo"):
                donor_l1.frozen_sources()

    def test_tripo_immutable_historical_source_digest_fails_closed_on_tampering(self):
        original_read = donor_l1.json_read
        manifest = original_read(donor_l1.TRIPO_RECOVERY)

        def read_with_manifest(replacement):
            def reader(path):
                if path == donor_l1.TRIPO_RECOVERY:
                    return copy.deepcopy(replacement)
                return original_read(path)
            return reader

        # Reordering complete records retains the count and URL multiset,
        # but must fail the original 48-occurrence *ordered* evidence gate.
        changed_urls = copy.deepcopy(manifest)
        changed_urls["url_provenance"][0], changed_urls["url_provenance"][1] = (
            changed_urls["url_provenance"][1], changed_urls["url_provenance"][0])
        with mock.patch.object(donor_l1, "json_read", side_effect=read_with_manifest(changed_urls)):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError, "immutable historical URL sequence mismatch"):
                    donor_l1.stage(Path(tmp) / "refuse.sqlite", "tripo-integrity-negative")

        # Replacing even one proposed legacy identity must fail prior to staging.
        changed_ids = copy.deepcopy(manifest)
        changed_ids["entries"][0]["donor_id"] += "-UNAPPROVED-REPLACEMENT"
        with mock.patch.object(donor_l1, "json_read", side_effect=read_with_manifest(changed_ids)):
            with self.assertRaisesRegex(ValueError, "immutable historical donor identity set mismatch"):
                donor_l1.frozen_sources()

    def test_no_modification_to_original_archive(self):
        sources = donor_l1.frozen_sources()
        self.assertEqual(donor_l1.sha_blob(donor_l1.REGISTRY.read_bytes()),
                         donor_l1.EXPECTED["FA3-DONOR-REFERENCE-REGISTRY-001.json"])
        self.assertEqual(len(sources),1981)

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
                expected_state = ("OWNER_APPROVED_PENDING_PUBLICATION" if donor_l1.explicit_legacy_donor_marker(entry)
                                  else "BLOCKED")
                self.assertEqual(donor_l1.lookup(dbpath,sid,"id")[0]["status"], expected_state)
                self.assertEqual(donor_l1.lookup(dbpath,entry["source"]["locator"],"url")[0]["id"],sid)
                self.assertFalse(entry["submission_review"]["exact_submitted_URL_and_approval_pair_independently_verified"])

    def test_historical_owner_command_is_transfer_approval_not_runtime_admission(self):
        assert donor_l1.explicit_legacy_donor_marker({"submission_review":{"reported_owner_marker":"donornak"}})
        assert donor_l1.explicit_legacy_donor_marker({"submission_review":{"reported_owner_marker":"vedd fel donornak"}})
        assert donor_l1.explicit_legacy_donor_marker({"submission_review":{"reported_owner_marker":"add a donorlistához"}})
        self.assertFalse(donor_l1.explicit_legacy_donor_marker({"submission_review":{"reported_owner_marker":"accepted donor/reference sources"}}))
        sources = donor_l1.frozen_sources()
        self.assertEqual(sum(1 for _, origin, _ in sources if origin == "HISTORICAL_OWNER_APPROVED_TRANSFER"),19)
        self.assertEqual(sum(1 for _, origin, _ in sources if origin == "ADDITIONAL_OWNER_APPROVED_TRANSFER"),4)
        self.assertEqual(sum(1 for _, origin, _ in sources if origin == "HISTORICAL_TRIPO_OWNER_APPROVED_TRANSFER"),30)
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/"legacy-owner-markers.sqlite"
            receipt=donor_l1.stage(dbpath,"legacy-marker-test")
            self.assertEqual(receipt["state"],"STAGED_NOT_PUBLISHED")
            self.assertIsNone(receipt["B"])
            with sqlite3.connect(dbpath) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM sources WHERE current_status='OWNER_APPROVED_PENDING_PUBLICATION'").fetchone()[0],59)
                self.assertEqual(db.execute("SELECT count(*) FROM sources WHERE source_origin='HISTORICAL_OWNER_APPROVAL_RECONCILIATION_PENDING'").fetchone()[0],4)
                self.assertEqual(dict(db.execute("SELECT key,value FROM metadata"))["publication_gate"],"PENDING")

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
