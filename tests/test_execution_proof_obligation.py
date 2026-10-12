"""Negative tests for owner-approved execution and proof obligation integrity."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_bootstrap import validate_execution_and_proof_obligation

IDENT = "CFA3-POLICY-EXECUTION-AND-PROOF-OBLIGATION-001"
SOURCE = f"canonical/policies/{IDENT}.md"
POLICY = f"canonical/policies/{IDENT}.json"


class ExecutionProofObligationTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / POLICY).read_text(encoding="utf-8"))

    def test_approved_source_passes(self):
        self.assertEqual([], validate_execution_and_proof_obligation(self.policy, ROOT))

    def test_changed_digest_fails(self):
        broken = copy.deepcopy(self.policy)
        broken["approved_text_sha256"] = "0" * 64
        self.assertTrue(validate_execution_and_proof_obligation(broken, ROOT))

    def test_requirement_turned_off_fails(self):
        broken = copy.deepcopy(self.policy)
        broken["requirements"]["sha256_verification"] = False
        self.assertTrue(validate_execution_and_proof_obligation(broken, ROOT))

    def test_changed_document_fails_even_with_rehashed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / SOURCE
            dest.parent.mkdir(parents=True)
            raw = (ROOT / SOURCE).read_bytes() + b"\nUnauthorized change\n"
            dest.write_bytes(raw)
            broken = copy.deepcopy(self.policy)
            broken["approved_text_sha256"] = hashlib.sha256(raw).hexdigest()
            self.assertTrue(validate_execution_and_proof_obligation(broken, root))

    def test_missing_document_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(validate_execution_and_proof_obligation(self.policy, Path(tmp)))


if __name__ == "__main__":
    unittest.main()
