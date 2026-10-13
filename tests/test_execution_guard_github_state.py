"""Unit gates for GitHub live-state integration (synthetic, no network)."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_execution_guard_github_state import (validate_snapshot, LiveStateBlocked,
    live_state_callback, TrustedGithubReader, _verified_changed_paths)

def task():
    return {"operation":"REPOSITORY_WRITE", "main_sha":"a"*40, "head_sha":"b"*40,
            "branch":"guard/feature", "target":"scripts/execution_guard.py",
            "scope_targets":["scripts/execution_guard.py"]}

def snapshot():
    return {"main":"a"*40,
        "target_pr":{"number":13,"head_sha":"b"*40,"head_ref":"guard/feature",
                     "base_ref":"main","base_sha":"a"*40,"state":"open"},
        "target_branch_commit":"b"*40,
        "review_threads":[True,True],
        "head_checks":[{"name":n,"head_sha":"b"*40,"status":"completed",
                        "conclusion":"success","app_id":15368} for n in ("bootstrap","qt68-linux")],
        "open_prs":[{"number":13,"head_sha":"b"*40,
                     "changed_files":["scripts/execution_guard.py"]},
                    {"number":11,"head_sha":"c"*40,"changed_files":["scripts/donor_transfer.py"]}],
        "ruleset":{"id":24804719,"name":"CFA3-MAIN-PROTECTION",
                   "enforcement":"active","bypass_actors":[],
                   "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
                   "rules":[{"type":"deletion"},{"type":"non_fast_forward"},
                            {"type":"pull_request","parameters":{
                                "required_review_thread_resolution":True,
                                "require_extra_approval_for_unattributed_changes":True}},
                            {"type":"required_status_checks","parameters":{
                                "strict_required_status_checks_policy":True,
                                "required_status_checks":[
                                    {"context":"bootstrap","integration_id":15368},
                                    {"context":"qt68-linux","integration_id":15368}]}}]}}

class LiveGithubStateTests(unittest.TestCase):
    def check(self,data=None,contract=None):
        return validate_snapshot(task() if contract is None else contract,
                                 snapshot() if data is None else data)
    def test_current_facts_verified_but_never_owner_authority(self):
        p=self.check()
        self.assertTrue(p["no_overlap"])
        self.assertTrue(p["privileged_bypass_actors_verified"])
        self.assertFalse(p["owner_scope_approved"])

    def test_main_and_target_head_drift_block(self):
        for path,value in (("main","f"*40),("target_branch_commit","f"*40)):
            d=snapshot();d[path]=value
            with self.subTest(path=path),self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["target_pr"]["head_sha"]="f"*40
        with self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["target_pr"]["base_sha"]="f"*40
        with self.assertRaises(LiveStateBlocked):self.check(d)

    def test_donor_parallel_allowed_only_without_overlap(self):
        d=snapshot()
        self.assertTrue(self.check(d)["no_overlap"])
        d["open_prs"][1]["changed_files"].append("scripts/execution_guard.py")
        with self.assertRaises(LiveStateBlocked):self.check(d)

    def test_signed_scope_must_match_entire_live_pr_diff(self):
        data=snapshot()
        data["open_prs"][0]["changed_files"].append("docs/unauthorized.txt")
        with self.assertRaisesRegex(LiveStateBlocked, "signed exact scope"):
            self.check(data)
        expanded=task()
        expanded["scope_targets"].append("docs/not-in-pr.txt")
        with self.assertRaisesRegex(LiveStateBlocked, "signed exact scope"):
            self.check(contract=expanded)

    def test_renamed_old_and_new_paths_both_required(self):
        names = _verified_changed_paths(
            [{"filename": "scripts/new.py", "previous_filename": "scripts/old.py",
              "status": "renamed"}], 1)
        self.assertEqual(["scripts/new.py", "scripts/old.py"], names)
        data = snapshot()
        data["open_prs"][0]["changed_files"] = names
        signed = task()
        signed["target"] = "scripts/new.py"
        signed["scope_targets"] = names
        self.assertTrue(self.check(data, signed)["no_overlap"])
        signed["scope_targets"] = ["scripts/new.py"]
        with self.assertRaisesRegex(LiveStateBlocked, "signed exact scope"):
            self.check(data, signed)
        signed["scope_targets"] = names
        data["open_prs"][1]["changed_files"] = ["scripts/old.py"]
        with self.assertRaisesRegex(LiveStateBlocked, "concurrent PR"):
            self.check(data, signed)

    def test_incomplete_or_capped_file_inventory_denied(self):
        row = [{"filename": "scripts/new.py", "status": "modified"}]
        for count in (None, 0, True, 3000, 3001, 2):
            with self.subTest(count=count), self.assertRaises(LiveStateBlocked):
                _verified_changed_paths(row, count)
        with self.assertRaisesRegex(LiveStateBlocked, "source path"):
            _verified_changed_paths([{"filename": "scripts/new.py", "status": "renamed"}], 1)
        with self.assertRaisesRegex(LiveStateBlocked, "previous PR filename"):
            _verified_changed_paths([{"filename": "scripts/new.py",
                                     "previous_filename": "", "status": "renamed"}], 1)

    def test_trusted_reader_checks_complete_count_and_rename(self):
        reader = TrustedGithubReader("synthetic-read-only")
        rows = [{"filename": "scripts/new.py", "previous_filename": "scripts/old.py",
                 "status": "renamed"}]
        count = [1]
        other_count = [1]
        other_sha = ["c" * 40]
        def request(path, graphql=None):
            if path == "/git/ref/heads/main":
                return {"object": {"sha": "a" * 40}}
            if path == "/pulls/13":
                return {"number": 13,
                        "head": {"ref": "guard/feature", "sha": "b" * 40},
                        "base": {"ref": "main", "sha": "a" * 40},
                        "state": "open", "changed_files": count[0]}
            if path == "/pulls/11":
                return {"number": 11, "head": {"sha": other_sha[0]},
                        "state": "open", "changed_files": other_count[0]}
            if path == "/git/ref/heads/guard/feature":
                return {"object": {"sha": "b" * 40}}
            if path == "/rulesets/24804719":
                return snapshot()["ruleset"]
            raise AssertionError(path)
        def pages(path, key=None):
            if path == "/pulls?state=open":
                # Actual list endpoint omits changed_files. Every count
                # must be fetched from the corresponding detailed PR.
                return [{"number": 13, "head": {"sha": "b" * 40}},
                        {"number": 11, "head": {"sha": "c" * 40}}]
            if path == "/pulls/13/files":
                return rows
            if path == "/pulls/11/files":
                return [{"filename": "docs/other.txt", "status": "modified"}]
            if path == "/commits/" + "b" * 40 + "/check-runs":
                return []
            raise AssertionError(path)
        with (patch.object(reader, "request", side_effect=request),
              patch.object(reader, "pages", side_effect=pages),
              patch.object(reader, "review_threads", return_value=[])):
            proof = reader.snapshot(task(), 13)
            self.assertEqual(["scripts/new.py", "scripts/old.py"],
                             proof["open_prs"][0]["changed_files"])
            count[0] = 2
            with self.assertRaisesRegex(LiveStateBlocked, "inventory incomplete"):
                reader.snapshot(task(), 13)
            count[0] = 3000
            with self.assertRaisesRegex(LiveStateBlocked, "API cap"):
                reader.snapshot(task(), 13)
            count[0] = 1
            other_count[0] = 2
            with self.assertRaisesRegex(LiveStateBlocked, "inventory incomplete"):
                reader.snapshot(task(), 13)
            other_count[0] = 1
            other_sha[0] = "d" * 40
            with self.assertRaisesRegex(LiveStateBlocked, "detail changed"):
                reader.snapshot(task(), 13)

    def test_trusted_reader_rejects_drift_during_snapshot(self):
        for drift in (None, "main", "branch", "target", "open_prs"):
            with self.subTest(drift=drift):
                reader = TrustedGithubReader("synthetic-read-only")
                calls = {"main": 0, "branch": 0, "target": 0, "open_prs": 0}

                def request(path, graphql=None):
                    if path == "/git/ref/heads/main":
                        calls["main"] += 1
                        sha = "d" * 40 if drift == "main" and calls["main"] > 1 else "a" * 40
                        return {"object": {"sha": sha}}
                    if path == "/git/ref/heads/guard/feature":
                        calls["branch"] += 1
                        sha = "d" * 40 if drift == "branch" and calls["branch"] > 1 else "b" * 40
                        return {"object": {"sha": sha}}
                    if path == "/pulls/13":
                        calls["target"] += 1
                        count = 2 if drift == "target" and calls["target"] > 1 else 1
                        return {"number": 13, "state": "open", "changed_files": count,
                                "head": {"sha": "b" * 40, "ref": "guard/feature"},
                                "base": {"sha": "a" * 40, "ref": "main"}}
                    if path == "/pulls/11":
                        return {"number": 11, "state": "open", "changed_files": 1,
                                "head": {"sha": "c" * 40}}
                    if path == "/rulesets/24804719":
                        return snapshot()["ruleset"]
                    raise AssertionError(path)

                def pages(path, key=None):
                    if path == "/pulls?state=open":
                        calls["open_prs"] += 1
                        other = "d" * 40 if (drift == "open_prs"
                            and calls["open_prs"] > 1) else "c" * 40
                        return [{"number": 13, "head": {"sha": "b" * 40}},
                                {"number": 11, "head": {"sha": other}}]
                    if path == "/pulls/13/files":
                        return [{"filename": "scripts/execution_guard.py", "status": "modified"}]
                    if path == "/pulls/11/files":
                        return [{"filename": "docs/other.txt", "status": "modified"}]
                    if path == "/commits/" + "b" * 40 + "/check-runs":
                        return []
                    raise AssertionError(path)

                with (patch.object(reader, "request", side_effect=request),
                      patch.object(reader, "pages", side_effect=pages),
                      patch.object(reader, "review_threads", return_value=[])):
                    if drift is None:
                        result = reader.snapshot(task(), 13)
                        self.assertEqual("a" * 40, result["main"])
                        self.assertEqual(2, len(result["open_prs"]))
                    else:
                        with self.assertRaisesRegex(LiveStateBlocked, "changed during live snapshot"):
                            reader.snapshot(task(), 13)

    def test_missing_pr_page_and_duplicate_pr_block(self):
        for change in ("missing","duplicate"):
            d=snapshot()
            if change=="missing":d["open_prs"]=d["open_prs"][1:]
            else:d["open_prs"].append(copy.deepcopy(d["open_prs"][1]))
            with self.subTest(change=change),self.assertRaises(LiveStateBlocked):self.check(d)

    def test_all_required_checks_bound_to_exact_head_and_app(self):
        for key,value in (("head_sha","e"*40),("conclusion","failure"),
                          ("app_id",999),("status","queued")):
            d=snapshot();d["head_checks"][0][key]=value
            with self.subTest(key=key),self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["head_checks"].pop()
        with self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["head_checks"].append(copy.deepcopy(d["head_checks"][0]))
        with self.assertRaises(LiveStateBlocked):self.check(d)

    def test_missing_ruleset_bypass_denied(self):
        d=snapshot();del d["ruleset"]["bypass_actors"]
        with self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["ruleset"]["bypass_actors"]=[{"actor_id":4}]
        with self.assertRaises(LiveStateBlocked):self.check(d)

    def test_unresolved_or_unavailable_review_threads_block(self):
        d=snapshot();d["review_threads"]=[True,False]
        with self.assertRaises(LiveStateBlocked):self.check(d)
        d=snapshot();d["review_threads"]=None
        with self.assertRaises(LiveStateBlocked):self.check(d)

    def test_unknown_task_type_and_target_scope_block(self):
        for mode in ("ARTIFACT_EXPORT","GUI_RENDER","MERGE"):
            t=task();t["operation"]=mode
            with self.subTest(operation=mode),self.assertRaises(LiveStateBlocked):self.check(contract=t)
        t=task();t["target"]="not-a-PR-file"
        with self.assertRaises(LiveStateBlocked):self.check(contract=t)

    def test_missing_token_or_owner_verifier_blocks(self):
        for token in (None,""):
            with self.subTest(token=token),self.assertRaises(LiveStateBlocked):
                live_state_callback(token,13,lambda _:True,b"x"*32)
        with self.assertRaises(LiveStateBlocked):
            live_state_callback("synthetic-no-network",13,None,b"x"*32)

if __name__=="__main__":
    unittest.main()
