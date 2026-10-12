"""83 current owner-admitted rules: original 24 + 56 additions, all 78 accounted."""
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
    def test_exact_83_current_rules_and_all_78_admitted(self):
        self.assertEqual([],self.check())
        self.assertEqual(83,len(active_expected_codes(self.gov,self.spec)))
        self.assertEqual(83,len(self.spec["active_rules"]))
        self.assertEqual(78,len(self.spec["historical_candidates"]))
        self.assertEqual(0,self.spec["historical_reconciliation"]["excluded_for_conflict"])
        self.assertEqual(22,self.spec["historical_reconciliation"]["mapped_existing"])
        self.assertEqual(56,self.spec["historical_reconciliation"]["admitted_new"])
        self.assertTrue(all(not r["runtime_verified"] for r in self.spec["active_rules"]))
    def test_each_missing_owner_rule_denied(self):
        for index in range(83):
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
            altered_export["current_rules"][-3]["source_git_blob_sha1"]=forged_sha
            issues=validate(altered_spec,self.gov,self.coverage,altered_export,root=custom_root)
            self.assertTrue(any("owner-approved rule text changed" in x for x in issues),issues)

    def test_coordinated_requirement_or_decision_date_tampering_rejected(self):
        """Regenerated source inventory and export cannot authorize new owner semantics."""
        from check_guard_policy_surface import SURFACE, git_blob_sha, leaves
        policy_path="canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json"
        cases={
            "extra_requirement":("requirements","independent_owner_task_may_share_existing_pr",
                                 "unapproved or missing rule-admission requirement"),
            "altered_owner_date":(None,"owner_decision_date","owner-approved decision date changed"),
            "extra_root_field":(None,"owner_approval_may_be_skipped",
                                "unapproved or missing policy root field"),
            "extra_rule_field":("rule","skip_source_authorization",
                                "unapproved or missing rule field"),
            "extra_responsibility_field":("responsibility","blame_user_without_proof",
                                          "unapproved or missing responsibility field"),
            "extra_admission_boundary_field":("admission_boundary","owner_approval_may_be_skipped",
                                              "unapproved or missing admission boundary field"),
        }
        for case,(section,field,expected_message) in cases.items():
            policy=json.loads((ROOT/policy_path).read_text("utf-8"))
            target=policy if section is None else policy[section]
            target[field]="2026-10-12" if case=="altered_owner_date" else True
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

    def test_rule_admission_proof_mode_requires_approved_value(self):
        tampered=copy.deepcopy(self.spec)
        tampered["active_rules"][-3]["proof_mode"]="NO_PROOF_REQUIRED"
        self.assertIn("rule admission proof mode changed",self.check(spec=tampered))

    def test_export_post_historical_admission_count_cannot_drift(self):
        for count in (0,1,99):
            tampered=copy.deepcopy(self.export)
            tampered["owner_reconciliation"]["post_historical_rule_admissions"]=count
            with self.subTest(post_historical_rule_admissions=count):
                self.assertIn("governance export post-historical admission count inconsistent",
                              self.check(export=tampered))

    def test_export_all_current_id_and_code_pairs_required(self):
        first=copy.deepcopy(self.export)
        first["current_rules"][0]=copy.deepcopy(first["current_rules"][-1])
        self.assertIn("canonical export current rule ID/code set incomplete or duplicated",
                      self.check(export=first))
        second=copy.deepcopy(self.export)
        second["current_rules"][0]["code"]="TAMPERED_CODE"
        self.assertIn("canonical export current rule ID/code set incomplete or duplicated",
                      self.check(export=second))

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
        for index in (-3,-2,-1):
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
                del flags["current_83_global_status_not_sufficient_for_task_authority"]
            elif change=="false":
                flags["current_83_global_status_not_sufficient_for_task_authority"]=False
            else:
                flags["current_81_global_status_not_sufficient_for_task_authority"]=True
            with self.subTest(change=change):
                self.assertTrue(self.check(coverage=bad))

    def test_export_summary_covers_both_current_admissions(self):
        for bad_text in ("81 aktív szabály",
                         "83 aktív szabály RULE-ADMISSION-001",
                         "83 aktív szabály CFA3-SEQUENTIAL-COMMAND-001"):
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
