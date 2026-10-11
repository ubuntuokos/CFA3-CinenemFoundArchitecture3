"""Unit gates for GitHub live-state integration (synthetic, no network)."""
import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_execution_guard_github_state import validate_snapshot, LiveStateBlocked, live_state_callback

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
                live_state_callback(token,13,lambda _:True)
        with self.assertRaises(LiveStateBlocked):
            live_state_callback("synthetic-no-network",13,None)

if __name__=="__main__":
    unittest.main()
