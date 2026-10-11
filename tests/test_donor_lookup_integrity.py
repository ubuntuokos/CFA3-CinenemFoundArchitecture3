"""Public lookup regressions for the five post-merge donor review findings."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_transfer_integrity as integrity
import transfer_donors
from donor_reference_lookup import lookup_snapshot
from source_lifecycle import evaluate, note_revisions


class DonorLookupIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(transfer_donors.OUTPUT.read_text())
        cls.index = json.loads((integrity.REG / "CFA3-SOURCE-LIFECYCLE-INDEX-001.json").read_text())
        cls.rows = {row["source_id"]: row for row in cls.snapshot["records"]}

    def test_notes_only_upstream_revision_reuses_but_pr_revision_does_not(self):
        cases = {
            "FA3-DONOR-AGENTSCOPE-AI-AGENTSCOPE-001": "72f3f6fa0b2fc38b8517f408ab616f0f2bd229e6",
            "FA3-DONOR-ASCEND-PYTORCH-001": "9cd8d1f1483f8268944d80392d4aa91fd455339f",
        }
        for sid, revision in cases.items():
            url = self.rows[sid]["historical_record"]["source"]["locator"]
            observation = {"verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
                           "evidence_ref": "unit-test-observation-not-current-upstream-proof",
                           "checked_at": "2026-10-11", "support_status": "SUPPORTED",
                           "observed_revision": revision}
            answer = evaluate(url, self.index, observation)
            self.assertEqual(answer["disposition"], "REUSE_PRIOR_DECISION")
            self.assertEqual(answer["prior_decision"]["historical_upstream_evidence"]["notes"],
                             self.rows[sid]["historical_record"]["notes"])
            observation["observed_revision"] = "aab23277cf7d38d7b55b73bf0cae12491cb49dde"
            self.assertEqual(evaluate(url, self.index, observation)["disposition"], "CHANGE_REVIEW_REQUIRED")

    def test_note_parser_keeps_uncertainty_and_rejects_non_revision_hashes(self):
        self.assertEqual(note_revisions(["Materialized from donor-intake PR #704 exact head " + "a" * 40]), set())
        self.assertEqual(note_revisions(["Observed upstream revision at intake: abc123."]), set())
        self.assertEqual(note_revisions(["Upstream sha256 " + "a" * 64]), set())
        self.assertEqual(note_revisions(["Upstream " + "a" * 40, "Upstream " + "b" * 40]),
                         {"a" * 40, "b" * 40})

    def test_all_preserved_previous_locators_and_legacy_keys_are_searchable(self):
        aliases = {}
        for row in self.snapshot["records"]:
            history = row["historical_record"]
            for url in [*history.get("source", {}).get("previous_locators", []),
                        *history.get("legacy_source_keys", [])]:
                aliases[url] = row["source_id"]
        self.assertTrue(aliases)
        self.assertEqual(aliases["project:OpenCut"], "FA3-DONOR-OPENCUT-001")
        self.assertEqual(aliases["project:opencut"], "FA3-DONOR-OPENCUT-001")
        for url, sid in aliases.items():
            with self.subTest(url=url):
                self.assertEqual(evaluate(url, self.index)["source_id"], sid)
                self.assertEqual(lookup_snapshot(self.snapshot, original_url=url)["donor_id"], sid)

    def test_dangling_route_is_integrity_error_but_unknown_id_is_not_found(self):
        data = copy.deepcopy(self.snapshot)
        route = data["locator_routes"][0]
        route["preferred_source_id"] = "absent-id"
        route["related_source_ids"] = ["absent-id"]
        with self.assertRaisesRegex(ValueError, "missing donor"):
            lookup_snapshot(data, original_url=route["alias"])
        self.assertIsNone(lookup_snapshot(data, donor_id="absent-id"))

    def test_all_56_current_confirmations_are_visible_and_bound(self):
        confirmations = json.loads(transfer_donors.OWNER_CONFIRMATION.read_text())
        self.assertEqual(len(confirmations["confirmed_records"]), 56)
        for row in confirmations["confirmed_records"]:
            answer = evaluate(row["original_locator"], self.index)
            self.assertEqual(answer["disposition"], "CHANGE_CHECK_REQUIRED")
            self.assertEqual(answer["prior_decision"]["owner_approval"]["record"], row)
        bad = copy.deepcopy(self.index)
        sid = confirmations["confirmed_records"][0]["source_id"]
        next(row for row in bad["source_records"] if row["source_id"] == sid)["prior_decision"]["owner_approval"] = None
        self.assertEqual(evaluate(confirmations["confirmed_records"][0]["original_locator"], bad)["disposition"],
                         "BLOCKED_INDEX_CONFLICT")

    def test_changed_files_after_cache_warmup_fail_closed(self):
        url = "https://github.com/ExistentialAudio/BlackHole"
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp)
            transfer = reg / integrity.TRANSFER_NAME
            confirmation = reg / integrity.CONFIRMATION_NAME
            shutil.copyfile(transfer_donors.OUTPUT, transfer)
            shutil.copyfile(transfer_donors.OWNER_CONFIRMATION, confirmation)
            original_confirmation = confirmation.read_bytes()
            with patch.object(integrity, "REG", reg), \
                 patch.object(integrity, "OWNER_CONFIRMATION", confirmation), \
                 patch.object(transfer_donors, "OWNER_CONFIRMATION", confirmation):
                self.assertEqual(evaluate(url, self.index)["disposition"], "CHANGE_CHECK_REQUIRED")
                altered = copy.deepcopy(self.snapshot)
                altered["records"][0]["historical_record"]["notes"] = ["tampered"]
                altered["record_set_sha256"] = transfer_donors.digest(altered["records"])
                raw = (json.dumps(altered) + "\n").encode()
                transfer.write_bytes(raw)
                bad_index = copy.deepcopy(self.index)
                bad_index["input_sha256"][integrity.TRANSFER_NAME] = hashlib.sha256(raw).hexdigest()
                self.assertEqual(evaluate(url, bad_index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                shutil.copyfile(transfer_donors.OUTPUT, transfer)
                transfer.write_bytes(transfer.read_bytes() + b" ")
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                shutil.copyfile(transfer_donors.OUTPUT, transfer)
                doc = json.loads(original_confirmation)
                doc["confirmed_records"][0]["original_locator"] = "https://invalid.example"
                confirmation.write_text(json.dumps(doc))
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                confirmation.write_bytes(original_confirmation + b" ")
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")
                confirmation.unlink()
                self.assertEqual(evaluate(url, self.index)["disposition"], "BLOCKED_INDEX_CONFLICT")


if __name__ == "__main__":
    unittest.main()
