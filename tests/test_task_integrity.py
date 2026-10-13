"""Negative and positive contract tests for the CFA3 PR task integrity CI guard."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_task_integrity as guard


def contract(paths, kind="POLICY_ENFORCEMENT"):
    data = {
        "schema": guard.SCHEMA,
        "task_id": "CFA3-POLICY-TASK-INTEGRITY-AND-ENFORCED-COMPLETION-001",
        "task_kind": kind,
        "allowed_paths": paths,
        "approval_reference": "OWNER_CHAT_2026-10-13_TECHNICAL_ENFORCEMENT_REQUEST",
    }
    return "```cfa3-task\n" + json.dumps(data) + "\n```"


class TaskIntegrityTests(unittest.TestCase):
    def test_manifest_requires_exact_schema_and_single_block(self):
        parsed = guard.task_manifest(contract(["scripts/check_task_integrity.py"]))
        self.assertEqual("POLICY_ENFORCEMENT", parsed["task_kind"])
        for bad in ("", contract(["scripts/check_task_integrity.py"]) * 2,
                    "```cfa3-task\n{}\n```"):
            with self.assertRaises(guard.IntegrityError):
                guard.task_manifest(bad)

    def test_manifest_cannot_escape_repository_or_repeat_paths(self):
        for value in ("../secret", "/absolute", "canonical/../donor", "x\\y", "x//y"):
            with self.assertRaises(guard.IntegrityError):
                guard.task_manifest(contract([value]))
        with self.assertRaises(guard.IntegrityError):
            guard.task_manifest(contract(["x.py", "x.py"]))

    def test_scope_exactness_and_out_of_scope_pr(self):
        task = guard.task_manifest(contract(["scripts/check_task_integrity.py"]))
        guard.validate_scope(task, {"scripts/check_task_integrity.py"})
        with self.assertRaises(guard.IntegrityError):
            guard.validate_scope(task, {"README.md"})
        with self.assertRaises(guard.IntegrityError):
            guard.validate_scope(task, {"scripts/check_task_integrity.py", "README.md"})

    def test_donor_records_never_modified_by_policy_task(self):
        name = "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json"
        task = guard.task_manifest(contract([name], "POLICY"))
        with self.assertRaisesRegex(guard.IntegrityError, "donor records"):
            guard.validate_scope(task, {name})

    def test_enforcement_kind_only_allows_guard_files(self):
        task = guard.task_manifest(contract(["scripts/check_bootstrap.py"]))
        with self.assertRaisesRegex(guard.IntegrityError, "technical file boundary"):
            guard.validate_scope(task, {"scripts/check_bootstrap.py"})

    def make_policy(self, root, status, header, sections=2, published_hash=None):
        folder = Path(root) / "canonical/policies"
        folder.mkdir(parents=True)
        stem = "CFA3-SYNTHETIC-POLICY-001"
        text = "# " + stem + "\n\n**Státusz:** " + header + "  \n\n" + (
            "## 1. § Intro\n\n## 2. § Check\n")
        obj = {"id": stem, "status": status, "approved_section_count": sections}
        if published_hash is not None:
            obj["published_text_sha256"] = published_hash
        (folder / (stem + ".json")).write_text(json.dumps(obj), encoding="utf-8")
        (folder / (stem + ".md")).write_text(text, encoding="utf-8")
        return "canonical/policies/" + stem + ".json", text

    def test_approved_policy_requires_approved_visible_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, _ = self.make_policy(tmp, "OWNER_APPROVED", "JÓVÁHAGYÁSRA VÁR")
            with self.assertRaisesRegex(guard.IntegrityError, "non-approved"):
                guard.validate_policy_lifecycle({p}, Path(tmp))

    def test_pending_cannot_pretend_to_be_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, _ = self.make_policy(tmp, "PENDING_APPROVAL", "JÓVÁHAGYVA")
            with self.assertRaisesRegex(guard.IntegrityError, "falsely"):
                guard.validate_policy_lifecycle({p}, Path(tmp))

    def test_approved_policy_digest_and_section_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, body = self.make_policy(tmp, "OWNER_APPROVED", "JÓVÁHAGYVA")
            md = Path(tmp) / p.replace(".json", ".md")
            digest = hashlib.sha256(md.read_bytes()).hexdigest()
            self.make_policy(tmp, "OWNER_APPROVED", "JÓVÁHAGYVA", published_hash=digest)
            guard.validate_policy_lifecycle({p}, Path(tmp))
            self.make_policy(tmp, "OWNER_APPROVED", "JÓVÁHAGYVA", sections=3)
            with self.assertRaisesRegex(guard.IntegrityError, "paragraph"):
                guard.validate_policy_lifecycle({p}, Path(tmp))
            self.make_policy(tmp, "OWNER_APPROVED", "JÓVÁHAGYVA", published_hash="0" * 64)
            with self.assertRaisesRegex(guard.IntegrityError, "digest"):
                guard.validate_policy_lifecycle({p}, Path(tmp))

    def test_finalized_needs_post_merge_evidence_not_a_pr_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, _ = self.make_policy(tmp, "FINALIZED", "JÓVÁHAGYVA")
            with self.assertRaisesRegex(guard.IntegrityError, "cannot be independently"):
                guard.validate_policy_lifecycle({p}, Path(tmp))

    def test_registry_preserves_unrelated_entries(self):
        base = {"sources": [{"path": "canonical/policies/A.json", "x": 1},
                            {"path": "canonical/policies/B.json", "x": 2}]}
        altered = {"sources": [{"path": "canonical/policies/A.json", "x": 1},
                               {"path": "canonical/policies/B.json", "x": 9}]}
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / guard.SURFACE
            dest.parent.mkdir(parents=True)
            dest.write_text(json.dumps(altered), encoding="utf-8")
            with patch.object(guard, "git", return_value=json.dumps(base).encode("utf-8")):
                with self.assertRaisesRegex(guard.IntegrityError, "unrelated"):
                    guard.validate_registry_preservation({guard.SURFACE, "canonical/policies/A.json"},
                                                         "a" * 40, Path(tmp))

    def test_real_collision_requires_file_intersection(self):
        event = {"pull_request": {
            "number": 99, "head": {"sha": "b" * 40},
            "base": {"ref": "main", "sha": "a" * 40}}}
        live = {"number": 99, "state": "open", "body": "CFA3-POLICY-TASK-INTEGRITY-AND-ENFORCED-COMPLETION-001",
                "head": {"sha": "b" * 40}, "base": {"ref": "main", "sha": "a" * 40}}
        task = guard.task_manifest(contract(["scripts/check_task_integrity.py"]))
        with patch.object(guard, "api_get", return_value=live), patch.object(
            guard, "api_pages", return_value=[{"number": 99}, {"number": 8}]
        ), patch.object(guard, "github_changed_files", side_effect=lambda n, t: (
            {"scripts/check_task_integrity.py"} if n == 99 else {"README.md"}
        )):
            guard.validate_live_pr(event, task, {"scripts/check_task_integrity.py"}, "token")
        with patch.object(guard, "api_get", return_value=live), patch.object(
            guard, "api_pages", return_value=[{"number": 99}, {"number": 8}]
        ), patch.object(guard, "github_changed_files", return_value={"scripts/check_task_integrity.py"}):
            with self.assertRaisesRegex(guard.IntegrityError, "cross-PR"):
                guard.validate_live_pr(event, task, {"scripts/check_task_integrity.py"}, "token")

    def test_old_unrelated_pr_not_turned_into_new_blocker(self):
        event = {"repository": {"full_name": guard.REPO},
                 "pull_request": {"created_at": "2026-10-10T00:00:00Z"}}
        with patch.object(guard, "validate_live_pr", side_effect=AssertionError("should not call")):
            self.assertEqual("LEGACY_UNRELATED_PR_NOT_RETROACTIVELY_GATED",
                             guard.check_event(event, {"README.md"}, token=None))

    def test_new_pr_without_task_contract_is_denied(self):
        event = {"repository": {"full_name": guard.REPO},
                 "pull_request": {"created_at": "2026-10-13T07:00:00Z", "body": ""}}
        with self.assertRaisesRegex(guard.IntegrityError, "cfa3-task"):
            guard.check_event(event, {"README.md"}, token=None)


if __name__ == "__main__":
    unittest.main()
