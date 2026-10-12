"""CSA local development utility: structural and negative-path tests."""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import csa

class CSATests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name)
        self.archive = self.path / "archive"
        csa.init(self.archive)
        self.text = self.path / "suggestion.txt"
        self.text.write_text("Új képesség: offline keresés.\n", encoding="utf-8")
        self.args = type("Args", (), dict(project="CFA3", title="Offline keresés",
                       category=["AI"], suggestion_file=str(self.text),
                       source="chat:2026-10-12", conversation_id="conversation-local"))

    def seed(self):
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
        return csa.all_records(self.archive)[0]

    def test_add_verify_find_export(self):
        p, record = self.seed()
        self.assertEqual(record["id"], "CSA-000001")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            csa.find(self.archive, type("Q", (), dict(query="offline", project="CFA3")))
        self.assertIn("CSA-000001", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            csa.verify(self.archive)
        output = self.path / "export.zip"
        csa.export(self.archive, type("E", (), dict(id=None, project=None, output=str(output))))
        import zipfile
        with zipfile.ZipFile(output) as z:
            self.assertEqual(p.read_bytes(),
                             z.read("projects/CFA3/suggestions/CSA-000001.md"))
            self.assertIn("CSA-EXPORT-MANIFEST.csv", z.namelist())

    def test_duplicate_rejected(self):
        self.seed()
        with self.assertRaisesRegex(ValueError, "possible duplicate"):
            csa.add(self.archive, self.args)

    def test_approval_does_not_change_implementation(self):
        self.seed()
        args = type("State", (), dict(id="CSA-000001", kind="approval",
                                     state="APPROVED", evidence="owner-message"))
        csa.change(self.archive, args)
        record = csa.all_records(self.archive)[0][1]
        self.assertEqual(record["implementation"], "UNKNOWN")
        self.assertEqual(record["approval"], "APPROVED")

    def test_implementation_claim_requires_independent_proof(self):
        self.seed()
        args = type("State", (), dict(id="CSA-000001", kind="implementation",
                                     state="IMPLEMENTED", evidence="old AI claim"))
        with self.assertRaisesRegex(ValueError, "independent"):
            csa.change(self.archive, args)

    def test_markdown_not_split_by_json_limit(self):
        self.text.write_text("X" * (csa.JSON_LIMIT + 12), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
            csa.verify(self.archive)
        self.assertGreater(csa.all_records(self.archive)[0][0].stat().st_size,
                           csa.JSON_LIMIT)

    def test_json_size_limit(self):
        oversize = self.archive / "sources" / "huge.json"
        oversize.parent.mkdir(parents=True, exist_ok=True)
        oversize.write_text(json.dumps({"x": "A" * csa.JSON_LIMIT}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON size"):
            csa.verify(self.archive)

    def test_corrupt_suggestion_rejected(self):
        path, _ = self.seed()
        path.write_text(path.read_text("utf-8") + "tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "content drift"):
            csa.verify(self.archive)

    def test_data_root_cannot_be_application_checkout(self):
        code = self.path / "fake-checkout"
        (code / "canonical" / "policies").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "application repository"):
            csa.safe_root(code)

if __name__ == "__main__":
    unittest.main()
