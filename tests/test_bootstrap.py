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

    def test_lifecycle_policy_structural_guard(self):
        from check_bootstrap import validate_source_lifecycle
        policy=load("canonical/policies/CFA3-SOURCE-LIFECYCLE-POLICY-001.json")
        index=load("canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json")
        self.assertEqual([],validate_source_lifecycle(policy,index))
        broken=copy.deepcopy(policy)
        broken["invariants"]["lookup_before_analysis"]=False
        self.assertTrue(validate_source_lifecycle(broken,index))
        false_ready=copy.deepcopy(index)
        false_ready["complete"]=True
        self.assertTrue(validate_source_lifecycle(policy,false_ready))

    def test_donor_bounded_classification_policy(self):
        from check_bootstrap import validate_donor_classification_plan
        pol=load("canonical/policies/CFA3-DONOR-BOUNDED-CLASSIFICATION-001.json")
        decision=load("canonical/decisions/CFA3-DEC-DONOR-MIGRATION-AND-CLASSIFICATION-V2-20261009.json")
        self.assertEqual([], validate_donor_classification_plan(pol,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["comparison"]="NET_NEW_DONORS_AFTER_DEDUPLICATION"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["per_level_not_cumulative"]=False
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["count_previously_known_discovered_urls"]=False
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["level_publish_gate"]["next_level_requires_prior_level"]="CLASSIFICATION_FINISHED"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["max_level"]=6
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["newly_discovered_donor_may_restart_depth"]=True
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["remaining_levels_by_discovery_level"]["L2"]=5
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["remaining_levels_by_discovery_level"]["L3"]=5
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["remaining_levels_by_discovery_level"]["L4"]=5
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["remaining_levels_by_discovery_level"]["L5"]=5
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["newly_classified_or_approved_donor_may_become_additional_L1_root"]=True
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["last_level_further_expansion"]="ALLOWED"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["classification"]["global_depth_contract"]["multiple_parent_paths"]="CREATE_NEW_ROOT"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        broken_decision=copy.deepcopy(decision)
        broken_decision["depth_clarification"]["newly_discovered_donors_no_root_reset"]=False
        self.assertTrue(validate_donor_classification_plan(pol,broken_decision))
        bad["boundaries"]["status_of_actual_migration"]="COMPLETED"
        self.assertTrue(validate_donor_classification_plan(bad,decision))

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
