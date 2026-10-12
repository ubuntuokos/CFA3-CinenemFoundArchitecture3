"""Regression tests for the approved execution-completion policy admission."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_bootstrap import validate_execution_completion_and_verified_finalization

IDENT = "CFA3-POLICY-EXECUTION-COMPLETION-AND-VERIFIED-FINALIZATION-001"
RELATIVE = pathlib.Path("canonical/policies") / (IDENT + ".md")


class ExecutionCompletionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "canonical/policies" / (IDENT + ".json")).read_text("utf-8"))

    def test_approved_source_passes(self):
        self.assertEqual([], validate_execution_completion_and_verified_finalization(self.policy))

    def test_title_change_fails_even_when_present(self):
        altered = copy.deepcopy(self.policy)
        altered["title_hu"] += " (changed)"
        self.assertTrue(any("exact approved title" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_wrong_approved_digest_fails(self):
        altered = copy.deepcopy(self.policy)
        altered["approved_text_sha256"] = "0" * 64
        self.assertTrue(any("approved original digest" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_classification_change_fails(self):
        altered = copy.deepcopy(self.policy)
        altered["classification"] = "OTHER_CLASSIFICATION"
        self.assertTrue(any("exact approved classification" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_scope_change_fails(self):
        altered = copy.deepcopy(self.policy)
        altered["scope"] = ["unapproved domain"]
        self.assertTrue(any("exact approved scope" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_extra_root_field_fails(self):
        altered = copy.deepcopy(self.policy)
        altered["unapproved_field"] = "unapproved"
        self.assertTrue(any("exact approved root keys" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_missing_root_field_fails(self):
        altered = copy.deepcopy(self.policy)
        del altered["scope"]
        self.assertTrue(any("exact approved root keys" in x for x in
                            validate_execution_completion_and_verified_finalization(altered)))

    def test_modified_canonical_text_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            changed = pathlib.Path(directory) / RELATIVE
            changed.parent.mkdir(parents=True)
            changed.write_bytes((ROOT / RELATIVE).read_bytes() + b"\nnot-approved\n")
            errors = validate_execution_completion_and_verified_finalization(self.policy, directory)
            self.assertTrue(any("full text integrity" in x for x in errors))


if __name__ == "__main__":
    unittest.main()
