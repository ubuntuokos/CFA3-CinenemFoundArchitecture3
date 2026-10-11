"""Regression coverage: old unmerged donor proposals stay searchable, not approved."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_unmerged_proposals as proposals
from donor_reference_lookup import lookup
from source_lifecycle import DEFAULT_INDEX, evaluate

class UnmergedProposalTests(unittest.TestCase):
    def test_every_archived_unmerged_proposal_is_searchable_and_nonadmitted(self):
        rows = proposals.proposal_records()
        candidates = [r for r in rows if r["donor_registration"] ==
                      "UNMERGED_PROPOSAL_NOT_OWNER_APPROVED"]
        aliases = [r for r in rows if r["donor_registration"] ==
                   "UNVERIFIED_REKEY_PROPOSAL_NOT_APPLIED"]
        self.assertEqual((len(candidates), len(aliases)), (17, 3))
        for record in rows:
            for key in ("runtime_admission", "code_copy_authorized",
                        "license_authorized", "model_provider_admission"):
                self.assertIs(record[key], False)
        for row in candidates:
            self.assertEqual(proposals.lookup_proposal(donor_id=row["donor_id"]), row)
            self.assertEqual(proposals.lookup_proposal(
                original_url=row["proposed_locator_not_original_submission"]), row)
        for row in aliases:
            self.assertIsNone(proposals.lookup_proposal(donor_id=row["donor_id"]))
            self.assertEqual(proposals.lookup_proposal(
                original_url=row["proposed_locator_not_verified_alias"]), row)
            self.assertEqual(row["previous_decision"], "HISTORICAL_SOURCE_KEY_RETAINED")

    def test_active_reference_endpoint_sees_pending_only_if_not_canonical(self):
        row = proposals.proposal_records()[0]
        answer = lookup(original_url=row["proposed_locator_not_original_submission"])
        self.assertEqual(answer["donor_registration"], "UNMERGED_PROPOSAL_NOT_OWNER_APPROVED")
        self.assertEqual(answer["donor_id"], row["donor_id"])
        canonical = lookup(donor_id="FA3-DONOR-OPENEXR-001")
        self.assertNotEqual(canonical["donor_registration"], "UNVERIFIED_REKEY_PROPOSAL_NOT_APPLIED")
        proposed = next(x for x in proposals.proposal_records()
                        if x["donor_id"] == "FA3-DONOR-OPENEXR-001")
        alias = lookup(original_url=proposed["proposed_locator_not_verified_alias"])
        self.assertEqual(alias["donor_registration"], "UNVERIFIED_REKEY_PROPOSAL_NOT_APPLIED")
        self.assertIs(alias["runtime_admission"], False)

    def test_lifecycle_gate_preserves_proposal_status_without_admission(self):
        index = json.loads(DEFAULT_INDEX.read_text(encoding="utf-8"))
        proposed = proposals.proposal_records()[0]["proposed_locator_not_original_submission"]
        decision = evaluate(proposed, index)
        self.assertEqual(decision["disposition"], "HISTORICAL_PROPOSAL_REVIEW_REQUIRED")
        self.assertFalse(decision["automatic_donor_registration"])
        self.assertEqual(decision["historical_proposal"]["donor_registration"],
                         "UNMERGED_PROPOSAL_NOT_OWNER_APPROVED")
        self.assertEqual(evaluate("https://example.invalid/never-seen", index)["disposition"],
                         "BLOCKED_INDEX_INCOMPLETE")

    def test_tampered_archival_proposal_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            modified = Path(tmp) / "old.json"
            original = proposals.ARCHIVE.read_text(encoding="utf-8")
            modified.write_text(original.replace('"release_ready": false',
                                                 '"release_ready": true'), encoding="utf-8")
            with patch.object(proposals, "ARCHIVE", modified):
                with self.assertRaises(ValueError):
                    proposals.proposal_records()

if __name__ == "__main__":
    unittest.main()
