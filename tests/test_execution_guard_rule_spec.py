"""82 current owner-admitted rules: original 24 + 56 additions, all 78 accounted."""
import copy
import json
import tempfile
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_execution_guard_rule_spec import SPEC,GOV,COVERAGE,EXPORT,validate,active_expected_codes
class OwnerRuleSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec,cls.gov,cls.coverage,cls.export=[
            json.loads((ROOT/name).read_text("utf-8")) for name in (SPEC,GOV,COVERAGE,EXPORT)]
    def check(self,spec=None,coverage=None,export=None):
        return validate(self.spec if spec is None else spec,self.gov,
                        self.coverage if coverage is None else coverage,
                        self.export if export is None else export)
    def test_exact_82_current_rules_and_all_78_admitted(self):
        self.assertEqual([],self.check())
        self.assertEqual(82,len(active_expected_codes(self.gov,self.spec)))
        self.assertEqual(82,len(self.spec["active_rules"]))
        self.assertEqual(78,len(self.spec["historical_candidates"]))
        self.assertEqual(0,self.spec["historical_reconciliation"]["excluded_for_conflict"])
        self.assertEqual(22,self.spec["historical_reconciliation"]["mapped_existing"])
        self.assertEqual(56,self.spec["historical_reconciliation"]["admitted_new"])
        self.assertTrue(all(not r["runtime_verified"] for r in self.spec["active_rules"]))
    def test_each_missing_owner_rule_denied(self):
        for index in range(82):
            bad=copy.deepcopy(self.spec);bad["active_rules"].pop(index)
            with self.subTest(index=index):
                self.assertTrue(self.check(bad))
    def test_every_source_admission_required(self):
        for index in range(78):
            bad=copy.deepcopy(self.spec);bad["historical_candidates"][index]["active_execution_check"]=False
            with self.subTest(index=index):
                self.assertTrue(self.check(bad))
    def test_no_silent_re_exclusion_or_source_change(self):
        bad=copy.deepcopy(self.spec);bad["historical_reconciliation"]["excluded_for_conflict"]=1
        self.assertTrue(self.check(bad))
        bad=copy.deepcopy(self.spec);bad["historical_candidates"][0]["source_json_pointer"]="/wrong"
        self.assertTrue(self.check(bad))
        bad=copy.deepcopy(self.export);bad["historical_rule_candidates"][0]["excluded_from_execution_guard_active_rule_set"]=True
        self.assertTrue(self.check(export=bad))
    def test_original_24_codes_immutable(self):
        bad=copy.deepcopy(self.spec);bad["active_rules"][0]["code"]="FAKE"
        self.assertTrue(self.check(bad))
        bad=copy.deepcopy(self.coverage);bad["rules"]["DEV-01"]["code"]="FAKE"
        self.assertTrue(self.check(coverage=bad))
    def test_new_rule_is_exactly_source_bound(self):
        bad = copy.deepcopy(self.spec)
        bad["active_rules"][-2]["text_hu"] = "This is an unauthorized change."
        self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.spec)
        bad["active_rules"][-2]["canonical_policy_path"] = "wrong.json"
        self.assertTrue(self.check(bad))
        broken_export = copy.deepcopy(self.export)
        broken_export["current_rules"].pop()
        self.assertTrue(self.check(export=broken_export))

    def test_coordinated_owner_text_surface_and_export_tampering_rejected(self):
        """Matching forged owner spec, policy and provenance must not bypass authority."""
        from check_guard_policy_surface import SURFACE, git_blob_sha
        source="canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json"
        policy=json.loads((ROOT/source).read_text("utf-8"))
        policy["rule"]["text_hu"]="Nem jóváhagyott, módosított szabályszöveg. " * 18
        altered_spec=copy.deepcopy(self.spec)
        altered_spec["active_rules"][-2]["text_hu"]=policy["rule"]["text_hu"]
        altered_export=copy.deepcopy(self.export)
        surface=json.loads((ROOT/SURFACE).read_text("utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            custom_root=Path(temp)
            target=custom_root/source
            target.parent.mkdir(parents=True,exist_ok=True)
            raw=(json.dumps(policy,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
            target.write_bytes(raw)
            forged_sha=git_blob_sha(raw)
            for rec in surface["sources"]:
                if rec["path"]==source:
                    rec["git_blob_sha1"]=forged_sha
                    break
            else:
                self.fail("approved rule policy not in surface")
            surface_target=custom_root/SURFACE
            surface_target.parent.mkdir(parents=True,exist_ok=True)
            surface_target.write_text(json.dumps(surface,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            altered_export["current_rules"][-2]["source_git_blob_sha1"]=forged_sha
            issues=validate(altered_spec,self.gov,self.coverage,altered_export,root=custom_root)
            self.assertTrue(any("owner-approved rule text changed" in x for x in issues),issues)

    def test_coordinated_requirement_or_decision_date_tampering_rejected(self):
        """Regenerated source inventory and export cannot authorize new owner semantics."""
        from check_guard_policy_surface import SURFACE, git_blob_sha, leaves
        policy_path="canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json"
        for case in ("extra_requirement", "altered_owner_date"):
            policy=json.loads((ROOT/policy_path).read_text("utf-8"))
            expected_message=("unapproved or missing rule-admission requirement"
                              if case=="extra_requirement" else "owner-approved decision date changed")
            if case=="extra_requirement":
                policy["requirements"]["independent_owner_task_may_share_existing_pr"]=True
            else:
                policy["owner_decision_date"]="2026-10-12"
            surface=json.loads((ROOT/SURFACE).read_text("utf-8"))
            altered_export=copy.deepcopy(self.export)
            altered_coverage=copy.deepcopy(self.coverage)
            with tempfile.TemporaryDirectory() as temp:
                staged=Path(temp)
                target=staged/policy_path
                target.parent.mkdir(parents=True,exist_ok=True)
                raw=(json.dumps(policy,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
                target.write_bytes(raw)
                sha=git_blob_sha(raw)
                for row in surface["sources"]:
                    if row["path"]==policy_path:
                        row["git_blob_sha1"]=sha
                        row["leaves"]=leaves(policy)
                        row["leaf_count"]=len(row["leaves"])
                        break
                else:
                    self.fail("policy missing from canonical surface")
                altered_coverage["canonical_policy_leaf_fields_enumerated"]=sum(
                    row["leaf_count"] for row in surface["sources"])
                altered_export["current_rules"][-2]["source_git_blob_sha1"]=sha
                snapshot=staged/SURFACE
                snapshot.parent.mkdir(parents=True,exist_ok=True)
                snapshot.write_text(json.dumps(surface,ensure_ascii=False,indent=2)+"\n",
                                    encoding="utf-8")
                issues=validate(self.spec,self.gov,altered_coverage,altered_export,
                                root=staged)
                with self.subTest(case=case):
                    self.assertTrue(any(expected_message in issue for issue in issues),issues)

    def test_coverages_policy_leaf_total_must_match_surface(self):
        for delta in (-1,1):
            tampered=copy.deepcopy(self.coverage)
            tampered["canonical_policy_leaf_fields_enumerated"]+=delta
            with self.subTest(delta=delta):
                self.assertTrue(self.check(coverage=tampered))

    def test_sequential_rule_source_bound_and_negative(self):
        bad = copy.deepcopy(self.spec)
        bad["active_rules"][-1]["text_hu"] = "Unauthorized replacement sentence."
        self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.spec)
        bad["active_rules"][-1]["canonical_policy_path"] = "wrong.json"
        self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.export)
        bad["current_rules"][-1]["source_git_blob_sha1"] = "0"*40
        self.assertTrue(self.check(export=bad))

    def test_every_repeated_active_rule_count_and_status_is_checked(self):
        cases=(
            ("rule_receipt_protocol","known_current_governance_rule_count",81),
            ("owner_rule_specification","active_texts",81),
            ("owner_rule_specification","status","OWNER_81_RULES_SOURCE_ACCOUNTED_NO_RUNTIME_PASS"),
            ("runtime_preflight_separation","required_task_receipts",
             "verify_rule_receipts FOR_OWNER_APPROVED_81"),
        )
        for section,field,value in cases:
            with self.subTest(section=section,field=field):
                bad=copy.deepcopy(self.coverage)
                bad[section][field]=value
                self.assertTrue(self.check(coverage=bad))

    def test_provenance_fields_fail_closed_for_each_new_rule(self):
        tamper={
            "type":"OTHER_SOURCE",
            "id":"FAKE-001",
            "code":"FAKE_CODE",
            "authority":"UNAPPROVED",
            "active_rule_receipt_scope":False,
            "excluded_by_request":True,
            "source_path":"wrong-policy.json",
            "source_json_pointer":"/wrong",
            "source_git_blob_sha1":"0"*40,
        }
        for index in (-2,-1):
            for field,value in tamper.items():
                with self.subTest(index=index,field=field):
                    bad=copy.deepcopy(self.export)
                    bad["current_rules"][index][field]=value
                    self.assertTrue(self.check(export=bad))

    def test_preflight_active_count_flag_is_current_and_required(self):
        for change in ("remove", "false", "stale"):
            bad=copy.deepcopy(self.coverage)
            flags=bad["runtime_preflight_separation"]
            if change=="remove":
                del flags["current_82_global_status_not_sufficient_for_task_authority"]
            elif change=="false":
                flags["current_82_global_status_not_sufficient_for_task_authority"]=False
            else:
                flags["current_81_global_status_not_sufficient_for_task_authority"]=True
            with self.subTest(change=change):
                self.assertTrue(self.check(coverage=bad))

    def test_export_summary_covers_both_current_admissions(self):
        for bad_text in ("81 aktív szabály",
                         "82 aktív szabály RULE-ADMISSION-001",
                         "82 aktív szabály CFA3-SEQUENTIAL-COMMAND-001"):
            bad=copy.deepcopy(self.export)
            bad["important"]=bad_text
            with self.subTest(summary=bad_text):
                self.assertTrue(self.check(export=bad))

    def test_no_fake_runtime_pass(self):
        bad=copy.deepcopy(self.spec);bad["active_rules"][79]["runtime_verified"]=True
        self.assertTrue(self.check(bad))
    def test_owner_amendments_complete(self):
        bad=copy.deepcopy(self.spec);bad["owner_amendments"].pop()
        self.assertTrue(self.check(bad))
if __name__=="__main__":unittest.main()
