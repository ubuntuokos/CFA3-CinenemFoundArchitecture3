"""Negative-path tests for the new CFA3 bootstrap policy checker."""
import copy
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_bootstrap import check,load,validate_objects

class BootstrapPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gov=load("canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json")
        cls.cpu=load("canonical/policies/CFA3-CPU-EXECUTION-POLICY-001.json")
        cls.platform=load("canonical/policies/CFA3-PLATFORM-CONSTRAINTS-001.json")
        cls.ledger=load("canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json")

    def test_structural_seed(self):
        self.assertEqual([],check())

    def test_disabling_blocker_stop_is_rejected(self):
        gov=copy.deepcopy(self.gov)
        gov["task_policy"]["blocker_means_stop"]=False
        self.assertTrue(validate_objects(gov,self.cpu,self.platform,self.ledger))

    def test_unprotected_direct_main_is_rejected(self):
        gov=copy.deepcopy(self.gov)
        gov["task_policy"]["main_direct_write_allowed"]=True
        self.assertTrue(validate_objects(gov,self.cpu,self.platform,self.ledger))

    def test_silent_fallback_rejected(self):
        cpu=copy.deepcopy(self.cpu)
        cpu["no_silent_cpu_or_cloud_fallback"]=False
        self.assertTrue(validate_objects(self.gov,cpu,self.platform,self.ledger))

    def test_gpu_pass_cannot_be_faked_with_cpu(self):
        cpu=copy.deepcopy(self.cpu)
        cpu["environment"]["development"]["gpu_test_may_pass_on_cpu"]=True
        self.assertTrue(validate_objects(self.gov,cpu,self.platform,self.ledger))

    def test_legacy_175_is_not_new_baseline(self):
        platform=copy.deepcopy(self.platform)
        platform["capability_target_count"]=175
        self.assertTrue(validate_objects(self.gov,self.cpu,platform,self.ledger))

    def test_cannot_claim_unreviewed_source_inventory_complete(self):
        ledger=copy.deepcopy(self.ledger)
        ledger["inventory_complete"]=True
        self.assertTrue(validate_objects(self.gov,self.cpu,self.platform,ledger))

    def test_qt6_cannot_be_silently_removed(self):
        platform=copy.deepcopy(self.platform)
        platform["gui"]["technology"]="Web-only"
        self.assertTrue(validate_objects(self.gov,self.cpu,platform,self.ledger))

if __name__=="__main__":
    unittest.main()
