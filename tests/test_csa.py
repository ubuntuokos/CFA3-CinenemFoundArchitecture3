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
        self.roster = self.path / "baseline.json"
        self.roster.write_text(json.dumps({
            "schema": "cfa3.capability-name-roster.v1", "target_count": 200,
            "carried_legacy_names": 175, "numbered_unassigned_slots": 25,
            "names": [{"id": f"CAP-{i:03d}",
                        "name": f"Known {i}" if i <= 175 else f"CAP-{i:03d}",
                        "state": "LEGACY_NAME_CARRIED_FORWARD" if i <= 175
                        else "RESERVED_NUMBER_ONLY"} for i in range(1, 201)]
        }), encoding="utf-8")
        self.args = type("Args", (), dict(
            baseline_roster=str(self.roster), baseline_id="CAP-001",
            purpose="CFA3 offline search design", kind="RECOMMENDATION",
            applies_to=[], excludes=[], relation=[], donor_id=[],
            donor_registry=None, project="CFA3", title="Offline keresés",
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
            csa.verify(self.archive, self.roster)
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
                                     state="APPROVED", evidence="owner-message",
                                     baseline_roster=str(self.roster), donor_registry=None))
        csa.change(self.archive, args)
        record = csa.all_records(self.archive)[0][1]
        self.assertEqual(record["implementation"], "UNKNOWN")
        self.assertEqual(record["approval"], "APPROVED")

    def test_implementation_claim_requires_independent_proof(self):
        self.seed()
        args = type("State", (), dict(id="CSA-000001", kind="implementation",
                                     state="IMPLEMENTED", evidence="old AI claim",
                                     baseline_roster=str(self.roster), donor_registry=None))
        with self.assertRaisesRegex(ValueError, "independent"):
            csa.change(self.archive, args)

    def test_markdown_not_split_by_json_limit(self):
        self.text.write_text("X" * (csa.JSON_LIMIT + 12), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
            csa.verify(self.archive, self.roster)
        self.assertGreater(csa.all_records(self.archive)[0][0].stat().st_size,
                           csa.JSON_LIMIT)

    def test_json_size_limit(self):
        oversize = self.archive / "sources" / "huge.json"
        oversize.parent.mkdir(parents=True, exist_ok=True)
        oversize.write_text(json.dumps({"x": "A" * csa.JSON_LIMIT}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON size"):
            csa.verify(self.archive, self.roster)

    def test_corrupt_suggestion_rejected(self):
        path, _ = self.seed()
        path.write_text(path.read_text("utf-8") + "tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "content drift"):
            csa.verify(self.archive, self.roster)

    def test_data_root_cannot_be_application_checkout(self):
        code = self.path / "fake-checkout"
        (code / "canonical" / "policies").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "application repository"):
            csa.safe_root(code)

    def test_index_tampering_is_detected(self):
        self.seed()
        index = self.archive / "indexes" / "CSA-INDEX.md"
        index.write_text(index.read_text("utf-8") + "tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "index or manifest drift"):
            csa.verify(self.archive, self.roster)

    def test_allocated_reserved_slot_requires_order(self):
        import copy
        doc = json.loads(self.roster.read_text("utf-8"))
        doc["names"][175] = {"id": "CAP-176", "name": "New approved capability",
                              "state": "OWNER_APPROVED"}
        doc["numbered_unassigned_slots"] = 24
        self.roster.write_text(json.dumps(doc), encoding="utf-8")
        self.args.baseline_id = "CAP-176"
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
        doc["names"][176] = {"id": "CAP-177", "name": "Second approved",
                              "state": "OWNER_APPROVED"}
        doc["names"][175] = {"id": "CAP-176", "name": "CAP-176",
                              "state": "RESERVED_NUMBER_ONLY"}
        with self.assertRaisesRegex(ValueError, "lowest reserved"):
            csa.canonical_roster(self._write_roster(doc))

    def _write_roster(self, data):
        self.roster.write_text(json.dumps(data), encoding="utf-8")
        return self.roster

    def test_reserved_baseline_is_not_usable(self):
        self.args.baseline_id = "CAP-176"
        with self.assertRaisesRegex(ValueError, "reserved"):
            csa.add(self.archive, self.args)

    def test_missing_roster_blocks_verification(self):
        self.seed()
        with self.assertRaisesRegex(ValueError, "baseline roster required"):
            csa.verify(self.archive)

    def test_record_type_and_reverse_relation_index(self):
        first, _ = self.seed()
        self.text.write_text("Előzetes verzió a keresési tervhez.\n", "utf-8")
        self.args.kind = "PRELIMINARY_PLAN"
        self.args.relation = ["CSA-000001"]
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
        record = csa.all_records(self.archive)[1][1]
        self.assertEqual(record["approval"], "PENDING")
        self.assertEqual(record["record_kind"], "PRELIMINARY_PLAN")
        inverse = (self.archive / "indexes" / "CSA-RELATIONS.md").read_text("utf-8")
        self.assertIn("CSA-000001 |  | CSA-000002", inverse)
        csa.verify(self.archive, self.roster)

    def test_nonexistent_related_record_is_blocked(self):
        self.args.relation = ["CSA-999999"]
        with self.assertRaisesRegex(ValueError, "unknown or self-referencing"):
            csa.add(self.archive, self.args)

    def test_add_requires_traceable_source(self):
        self.args.source = ""
        with self.assertRaisesRegex(ValueError, "source/provenance"):
            csa.add(self.archive, self.args)

    def test_context_separates_preliminary_plan_and_inbound_links(self):
        self.seed()
        self.text.write_text("Nem véglegesített előzetes terv.\n", encoding="utf-8")
        self.args.kind = "PRELIMINARY_PLAN"
        self.args.relation = ["CSA-000001"]
        with contextlib.redirect_stdout(io.StringIO()):
            csa.add(self.archive, self.args)
        query = type("Query", (), dict(record_id=None, baseline_id="CAP-001",
                                       baseline_roster=str(self.roster), donor_registry=None))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            csa.context(self.archive, query)
        result = json.loads(out.getvalue())
        self.assertEqual(result["schema"], "csa.planning-context.v1")
        self.assertEqual(len(result["records"]), 2)
        first, second = result["records"]
        self.assertEqual(first["inbound_record_ids"], ["CSA-000002"])
        self.assertTrue(second["is_nonfinal_proposal"])
        self.assertEqual(second["record"]["record_kind"], "PRELIMINARY_PLAN")
        self.assertEqual(second["record"]["approval"], "PENDING")
        self.assertEqual(second["record"]["implementation"], "UNKNOWN")

    def test_context_does_not_accept_reserved_target(self):
        query = type("Query", (), dict(record_id=None, baseline_id="CAP-176",
                                       baseline_roster=str(self.roster), donor_registry=None))
        with self.assertRaisesRegex(ValueError, "reserved"):
            csa.context(self.archive, query)

    def test_context_refuses_broken_index(self):
        self.seed()
        path = self.archive / "indexes" / "CSA-RELATIONS.md"
        path.write_text("corrupted", encoding="utf-8")
        query = type("Query", (), dict(record_id="CSA-000001", baseline_id=None,
                                       baseline_roster=str(self.roster), donor_registry=None))
        with self.assertRaisesRegex(ValueError, "index or manifest drift"):
            csa.context(self.archive, query)

    def test_context_requires_precise_scope(self):
        query = type("Query", (), dict(record_id=None, baseline_id=None,
                                       baseline_roster=str(self.roster), donor_registry=None))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            csa.context(self.archive, query)

    def test_failed_multi_file_write_rolls_back_every_path(self):
        original = csa.atomic_text
        before = {p: p.read_bytes() for p in self.archive.rglob("*") if p.is_file()}
        count = [0]
        def fail_second_file(path, content):
            count[0] += 1
            if count[0] == 2:
                raise OSError("injected index write failure")
            return original(path, content)
        with patch.object(csa, "atomic_text", side_effect=fail_second_file):
            with self.assertRaisesRegex(OSError, "injected index"):
                csa.add(self.archive, self.args)
        after = {p: p.read_bytes() for p in self.archive.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.archive / csa.WRITE_MARKER).exists())
        csa.verify(self.archive)

    def test_unfinished_write_blocks_every_reader_and_writer(self):
        marker = self.archive / csa.WRITE_MARKER
        marker.write_text("manually inspect this interrupted update", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "incomplete CSA write"):
            csa.all_records(self.archive)
        with self.assertRaisesRegex(ValueError, "incomplete or concurrent CSA write"):
            csa.commit_changes(self.archive, {self.archive / "CSA-MANIFEST.md": "bad"})
        with self.assertRaisesRegex(ValueError, "incomplete CSA write"):
            csa.verify(self.archive)

    def test_status_update_rejects_unverified_roster_before_writing(self):
        self.seed()
        record_path, _ = csa.all_records(self.archive)[0]
        unchanged = record_path.read_bytes()
        status = type("State", (), dict(id="CSA-000001", kind="approval",
                                       state="APPROVED", evidence="owner-message",
                                       baseline_roster=None, donor_registry=None))
        with self.assertRaisesRegex(ValueError, "baseline roster required"):
            csa.change(self.archive, status)
        self.assertEqual(unchanged, record_path.read_bytes())

    def test_data_root_cannot_be_a_child_of_application_checkout(self):
        nested = ROOT / "planning-registry-data"
        with self.assertRaisesRegex(ValueError, "application repository"):
            csa.safe_root(nested)

if __name__ == "__main__":
    unittest.main()
