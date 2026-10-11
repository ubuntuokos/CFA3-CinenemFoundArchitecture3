"""81 current owner-admitted rules: original 24 + 56 additions, all 78 accounted."""
import copy
import json
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
    def test_exact_81_current_rules_and_all_78_admitted(self):
        self.assertEqual([],self.check())
        self.assertEqual(81,len(active_expected_codes(self.gov,self.spec)))
        self.assertEqual(81,len(self.spec["active_rules"]))
        self.assertEqual(78,len(self.spec["historical_candidates"]))
        self.assertEqual(0,self.spec["historical_reconciliation"]["excluded_for_conflict"])
        self.assertEqual(22,self.spec["historical_reconciliation"]["mapped_existing"])
        self.assertEqual(56,self.spec["historical_reconciliation"]["admitted_new"])
        self.assertTrue(all(not r["runtime_verified"] for r in self.spec["active_rules"]))
    def test_each_missing_owner_rule_denied(self):
        for index in range(81):
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
        bad["active_rules"][-1]["text_hu"] = "This is an unauthorized change."
        self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.spec)
        bad["active_rules"][-1]["canonical_policy_path"] = "wrong.json"
        self.assertTrue(self.check(bad))
        broken_export = copy.deepcopy(self.export)
        broken_export["current_rules"].pop()
        self.assertTrue(self.check(export=broken_export))

    def test_every_repeated_active_rule_count_and_status_is_checked(self):
        cases=(
            ("rule_receipt_protocol","known_current_governance_rule_count",82),
            ("owner_rule_specification","active_texts",82),
            ("owner_rule_specification","status","OWNER_82_RULES_SOURCE_ACCOUNTED_NO_RUNTIME_PASS"),
            ("runtime_preflight_separation","required_task_receipts",
             "verify_rule_receipts FOR_OWNER_APPROVED_82"),
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
        for index in (-1,):
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
                del flags["current_81_global_status_not_sufficient_for_task_authority"]
            elif change=="false":
                flags["current_81_global_status_not_sufficient_for_task_authority"]=False
            else:
                flags["current_82_global_status_not_sufficient_for_task_authority"]=True
            with self.subTest(change=change):
                self.assertTrue(self.check(coverage=bad))

    def test_export_summary_covers_only_the_admitted_rule(self):
        for bad_text in ("80 aktív szabály",
                         "81 aktív szabály CFA3-SEQUENTIAL-COMMAND-001",
                         "81 aktív szabály RULE-ADMISSION-001 CFA3-SEQUENTIAL-COMMAND-001"):
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
