"""Signed-source rule text coverage, no historical automatic admission."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_execution_guard_rule_spec import SPEC,GOV,COVERAGE,EXPORT,validate

class OwnerRuleSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec,cls.gov,cls.coverage,cls.export=[
            json.loads((ROOT/path).read_text("utf-8"))
            for path in (SPEC,GOV,COVERAGE,EXPORT)]
    def check(self,spec=None):
        return validate(self.spec if spec is None else spec,
                        self.gov,self.coverage,self.export)
    def test_24_current_rule_texts_and_78_reference_texts_preserved(self):
        self.assertEqual([],self.check())
        self.assertEqual(24,len(self.spec["active_rules"]))
        self.assertEqual(78,len(self.spec["excluded_historical_candidates"]))
        self.assertTrue(all(not x["runtime_verified"] for x in self.spec["active_rules"]))
    def test_24_rule_texts_non_optional(self):
        for index in range(24):
            other=copy.deepcopy(self.spec)
            other["active_rules"][index]["text_hu"]=""
            with self.subTest(index=index),self.assertTrue(self.check(other))
    def test_no_forged_current_rule_authority(self):
        other=copy.deepcopy(self.spec);other["active_rules"][0]["code"]="INVENTED_CODE"
        self.assertTrue(self.check(other))
        other=copy.deepcopy(self.spec);other["active_rules"][0]["runtime_verified"]=True
        self.assertTrue(self.check(other))
    def test_78_excluded_refs_never_automatically_activated(self):
        for typ in ("HISTORICAL_CANDIDATE_DEV_AI",
                    "HISTORICAL_CANDIDATE_QUALITY",
                    "HISTORICAL_CANDIDATE_TASK_SCOPE"):
            other=copy.deepcopy(self.spec)
            chosen=next(x for x in other["excluded_historical_candidates"] if x["type"]==typ)
            chosen["active_execution_check"]=True
            with self.subTest(typ=typ),self.assertTrue(self.check(other))
    def test_missing_78_reference_or_wrong_provenance_blocks(self):
        other=copy.deepcopy(self.spec)
        other["excluded_historical_candidates"].pop()
        self.assertTrue(self.check(other))
        other=copy.deepcopy(self.spec)
        other["excluded_historical_candidates"][0]["source_json_pointer"]="/wrong"
        self.assertTrue(self.check(other))
    def test_second_consecutive_error_rule_and_command_semantics_preserved(self):
        amend={x["id"]:x for x in self.spec["owner_amendments"]}
        self.assertIn("SECOND_CONSECUTIVE_OWN_ERROR_APPROVAL",amend)
        self.assertIn("DONOR_SDK_PARALLEL_NONBLOCKING_WHEN_DISJOINT",amend)
        self.assertIn("SHORT_OWNER_COMMANDS_LIMITED_TO_MAIN_TASK",amend)
        other=copy.deepcopy(self.spec);other["owner_amendments"].pop()
        self.assertTrue(self.check(other))

if __name__=="__main__":unittest.main()
