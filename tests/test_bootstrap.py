"""Negative-path tests for the new CFA3 bootstrap policy checker."""
import copy
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_bootstrap import check,load,validate_objects
from check_legacy_rule_blobs import validate_frozen_tree, FROZEN_COMMIT, EXPECTED_TRACKED_BLOBS

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
        bad["expansion_limit"]["comparison"]="RAW_OUTBOUND_LINK_OCCURRENCES_FROM_CURRENT_LEVEL_BEFORE_DEDUPLICATION_OR_CLASSIFICATION"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["per_level_not_cumulative"]=False
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["count_previously_known_discovered_urls"]=True
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["count_new_unique_sources_once_per_level"]=False
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["expansion_limit"]["index_incomplete_state"]="ASSUME_NEW"
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
        bad=copy.deepcopy(pol)
        bad["plan_finalization"]["migration_status"]="COMPLETE"
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        bad=copy.deepcopy(pol)
        bad["plan_finalization"]["published_levels"]=["L1"]
        self.assertTrue(validate_donor_classification_plan(bad,decision))
        changed_decision=copy.deepcopy(decision)
        changed_decision["plan_finalization"]["donor_import_complete"]=True
        self.assertTrue(validate_donor_classification_plan(pol,changed_decision))
        bad["boundaries"]["status_of_actual_migration"]="COMPLETED"
        self.assertTrue(validate_donor_classification_plan(bad,decision))

    def test_mandatory_execution_compliance_cannot_be_weakened(self):
        self.assertEqual([], validate_objects(self.gov, self.cpu, self.platform, self.ledger))
        for key in ("assumption_based_execution", "task_definition",
                    "approved_guidelines_rules_and_architecture",
                    "approved_cfa3_design_description", "approved_cfa3_branding_and_identity",
                    "unverified_or_missing_mandatory_requirement"):
            invalid = copy.deepcopy(self.gov)
            invalid["execution_integrity_policy"]["requirements"][key] = "OPTIONAL"
            self.assertTrue(validate_objects(invalid, self.cpu, self.platform, self.ledger), key)
        invalid = copy.deepcopy(self.gov)
        invalid["development_rules"] = [rule for rule in invalid["development_rules"] if rule["id"] != "DEV-12"]
        self.assertTrue(validate_objects(invalid, self.cpu, self.platform, self.ledger))
        invalid = copy.deepcopy(self.gov)
        invalid["ai_behavior_rules"] = [rule for rule in invalid["ai_behavior_rules"] if rule["id"] != "AI-12"]
        self.assertTrue(validate_objects(invalid, self.cpu, self.platform, self.ledger))
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

    def test_every_legacy_seed_sha_format(self):
        self.assertEqual(21, len(self.ledger["source_records"]))
        invalid=copy.deepcopy(self.ledger)
        invalid["source_records"][0]["blob_sha"]="abcd"
        self.assertTrue(validate_objects(self.gov,self.cpu,self.platform,invalid))
        invalid=copy.deepcopy(self.ledger)
        invalid["source_records"][0]["blob_sha"]="z"*40
        self.assertTrue(validate_objects(self.gov,self.cpu,self.platform,invalid))
        invalid=copy.deepcopy(self.ledger)
        invalid["source_records"][0]["blob_sha"]=None
        self.assertTrue(validate_objects(self.gov,self.cpu,self.platform,invalid))

    @staticmethod
    def _frozen_tree_fixture(ledger):
        entries = [{"type":"blob","path":r["path"],"sha":r["blob_sha"]}
                   for r in ledger["source_records"]]
        for i in range(EXPECTED_TRACKED_BLOBS-len(entries)):
            entries.append({"type":"blob",
                            "path":"unrelated/file-" + str(i).zfill(5),
                            "sha":"0"*40})
        return {"sha":FROZEN_COMMIT,"truncated":False,"tree":entries}

    def test_tree_comparison_rejects_missing_and_mutated_sources(self):
        frozen=self._frozen_tree_fixture(self.ledger)
        self.assertEqual([],validate_frozen_tree(self.ledger,frozen))
        altered=copy.deepcopy(self.ledger)
        altered["source_records"][0]["blob_sha"]="f"*40
        self.assertTrue(any("mismatches" in e for e in validate_frozen_tree(altered,frozen)))
        altered=copy.deepcopy(self.ledger)
        altered["source_records"][0]["blob_sha"]="a"*39
        self.assertTrue(any("invalid 40" in e for e in validate_frozen_tree(altered,frozen)))
        altered=copy.deepcopy(frozen)
        altered["tree"][0]["path"]="unrelated/replacement"
        self.assertTrue(any("absent" in e for e in validate_frozen_tree(self.ledger,altered)))

    def test_frozen_tree_identity_and_truncation_required(self):
        original=self._frozen_tree_fixture(self.ledger)
        for change in (
            {"sha":"a"*40},
            {"truncated":True},
            {"truncated":None},
            {"tree":[]},
        ):
            modified=copy.deepcopy(original)
            modified.update(change)
            self.assertTrue(validate_frozen_tree(self.ledger,modified))
        altered=copy.deepcopy(self.ledger)
        altered["source_main_commit"]="f"*40
        self.assertTrue(validate_frozen_tree(altered,original))

    def test_exhaustive_frozen_tree_manifest(self):
        from check_legacy_rule_blobs import validate_complete_inventory
        frozen = load("canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json")
        self.assertEqual(3159, frozen["blob_count"])
        self.assertEqual(3159, len(frozen["files"]))
        self.assertTrue(frozen["no_files_excluded_from_rule_review"])
        self.assertEqual("UNREVIEWED_RULE_APPLICABILITY", frozen["review_status_default"])
        paths = [row[0] for row in frozen["files"]]
        self.assertEqual(sorted(paths), paths)
        self.assertEqual(len(paths), len(set(paths)))
        sample = {
            "sha": frozen["commit"], "truncated": False,
            "tree": [{"path":r[0], "sha":r[1], "size":r[2], "type":"blob"}
                     for r in frozen["files"]]
        }
        # Real Git tree has 121 directory entries in addition to its 3159 blobs.
        sample["tree"].extend(
            {"path": "_synthetic_directory_%03d" % i, "type": "tree"}
            for i in range(frozen["tree_entry_count"] - len(sample["tree"]))
        )
        self.assertEqual([], validate_complete_inventory(frozen, sample))
        bad = copy.deepcopy(frozen)
        bad["files"][0][1] = "a" * 40 if bad["files"][0][1] != "a" * 40 else "b" * 40
        self.assertTrue(validate_complete_inventory(bad, sample))
        bad = copy.deepcopy(frozen)
        bad["files"] = bad["files"][1:]
        self.assertTrue(validate_complete_inventory(bad, sample))
        bad = copy.deepcopy(frozen)
        bad["no_files_excluded_from_rule_review"] = False
        self.assertTrue(validate_complete_inventory(bad, sample))
        bad = copy.deepcopy(sample)
        bad["truncated"] = True
        self.assertTrue(validate_complete_inventory(frozen, bad))

    def test_rule_admission_bootstrap_requirements(self):
        from check_bootstrap import validate_rule_admission
        policy = load("canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json")
        self.assertEqual([], validate_rule_admission(policy))
        broken = copy.deepcopy(policy)
        broken["requirements"]["independent_owner_task_may_share_existing_pr"] = True
        self.assertTrue(validate_rule_admission(broken))
        broken = copy.deepcopy(policy)
        broken["owner_decision_date"] = "2026-10-12"
        self.assertTrue(validate_rule_admission(broken))
        for section, extra in (
            (None, "owner_approval_may_be_skipped"),
            ("rule", "skip_source_authorization"),
            ("responsibility", "blame_user_without_proof"),
            ("admission_boundary", "owner_approval_may_be_skipped"),
        ):
            broken = copy.deepcopy(policy)
            target = broken if section is None else broken[section]
            target[extra] = True
            with self.subTest(extra_semantic_field=section or "root"):
                self.assertTrue(validate_rule_admission(broken))

        for key in policy["requirements"]:
            broken = copy.deepcopy(policy)
            broken["requirements"][key] = False
            with self.subTest(requirement=key):
                self.assertTrue(validate_rule_admission(broken))
        broken = copy.deepcopy(policy)
        broken["responsibility"]["ai_developer"] = ""
        self.assertTrue(validate_rule_admission(broken))
        for field in ("if_both_roles_are_same_actor", "attribution_basis"):
            broken = copy.deepcopy(policy)
            broken["responsibility"][field] = "UNVERIFIED_GUESS"
            with self.subTest(responsibility=field):
                self.assertTrue(validate_rule_admission(broken))
        for field in ("ai_assistant", "ai_developer"):
            broken = copy.deepcopy(policy)
            broken["responsibility"][field] = "UNVERIFIED_ROLE_SWAP"
            with self.subTest(exact_role=field):
                self.assertTrue(validate_rule_admission(broken))
        for replacement in (
            "Nem jóváhagyott szabályszöveg; " * 12,
            policy["rule"]["text_hu"] + " Tiltott, tulajdonos által nem engedélyezett szövegbővítés.",
        ):
            broken = copy.deepcopy(policy)
            broken["rule"]["text_hu"] = replacement
            with self.subTest(owner_text_tampering=replacement[:30]):
                self.assertTrue(validate_rule_admission(broken))
        broken = copy.deepcopy(policy)
        broken["rule"]["runtime_verified"] = True
        self.assertTrue(validate_rule_admission(broken))

    def test_one_command_one_response_policy_positive_and_negative(self):
        from check_bootstrap import validate_sequential_command_policy
        policy = load("canonical/policies/CFA3-SEQUENTIAL-COMMAND-POLICY-001.json")
        self.assertEqual([], validate_sequential_command_policy(policy))
        for key in policy["requirements"]:
            bad = copy.deepcopy(policy)
            bad["requirements"][key] = False
            with self.subTest(requirement=key):
                self.assertTrue(validate_sequential_command_policy(bad))
        bad = copy.deepcopy(policy)
        bad["sequence"].pop(1)
        self.assertTrue(validate_sequential_command_policy(bad))
        bad = copy.deepcopy(policy)
        bad["rule"]["runtime_verified"] = True
        self.assertTrue(validate_sequential_command_policy(bad))

    def test_donor_file_size_policy_positive_and_negative(self):
        from check_bootstrap import validate_donor_file_size_policy
        policy = load("canonical/policies/CFA3-DONOR-FILE-SIZE-POLICY-001.json")
        self.assertEqual([], validate_donor_file_size_policy(policy))
        for key in policy["requirements"]:
            broken = copy.deepcopy(policy)
            broken["requirements"][key] = False
            with self.subTest(invariant=key):
                self.assertTrue(validate_donor_file_size_policy(broken))
        for value in (996148, 0, 1000000):
            broken = copy.deepcopy(policy)
            broken["maximum_file_size"]["maximum_bytes"] = value
            self.assertTrue(validate_donor_file_size_policy(broken))
        broken = copy.deepcopy(policy)
        broken["applies_to"].pop()
        self.assertTrue(validate_donor_file_size_policy(broken))
        broken = copy.deepcopy(policy)
        broken["legacy_handling"]["retroactive_deletion_allowed"] = True
        self.assertTrue(validate_donor_file_size_policy(broken))
        broken = copy.deepcopy(policy)
        broken["rule"]["runtime_verified"] = True
        self.assertTrue(validate_donor_file_size_policy(broken))


    def test_github_resource_404_policy_positive_and_negative(self):
        from check_bootstrap import validate_github_resource_404_policy
        policy = load("canonical/policies/CFA3-GITHUB-RESOURCE-EXISTENCE-404-POLICY-001.json")
        self.assertEqual([], validate_github_resource_404_policy(policy))
        for field in policy["requirements"]:
            broken = copy.deepcopy(policy)
            broken["requirements"][field] = False
            with self.subTest(requirement=field):
                self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        broken["mandatory_sequence"][2], broken["mandatory_sequence"][3] = (
            broken["mandatory_sequence"][3], broken["mandatory_sequence"][2])
        self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        broken["http_404_cases"].pop()
        self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        for case in broken["http_404_cases"]:
            if case["case"] == "MISSING_PERMISSION_OR_CONCEALED_RESOURCE":
                case["action"] = "CONTINUE"
        self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        broken["error_handling"]["own_correctable_404_alone_is_blocker"] = True
        self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        broken["rule"]["runtime_verified"] = True
        self.assertTrue(validate_github_resource_404_policy(broken))
        broken = copy.deepcopy(policy)
        broken["admission_boundary"]["merge_without_existing_gate_allowed"] = True
        self.assertTrue(validate_github_resource_404_policy(broken))

    def test_ai_rule_acceptance_wellbeing_efficiency(self):
        from check_bootstrap import validate_ai_rule_acceptance_policy
        policy = load("canonical/policies/CFA3-AI-RULE-ACCEPTANCE-WELLBEING-EFFICIENCY-001.json")
        self.assertEqual([], validate_ai_rule_acceptance_policy(policy))
        for key in policy["requirements"]:
            bad = copy.deepcopy(policy)
            bad["requirements"][key] = False
            with self.subTest(requirement=key):
                self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        for key in policy["safety_boundary"]:
            bad = copy.deepcopy(policy)
            bad["safety_boundary"][key] = False
            with self.subTest(safety=key):
                self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        bad = copy.deepcopy(policy)
        bad["mandatory_clauses"].pop()
        self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        bad = copy.deepcopy(policy)
        bad["mandatory_clauses"][1]["text_hu"] = "Eltávolított mentálhigiénés védelem"
        self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        bad = copy.deepcopy(policy)
        bad["status"] = "MERGED_WITHOUT_EVIDENCE"
        self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        bad = copy.deepcopy(policy)
        bad["status"] = "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE"
        self.assertTrue(validate_ai_rule_acceptance_policy(bad))
        bad = copy.deepcopy(policy)
        bad["admission_boundary"]["independent_execution_gate_pass"] = True
        self.assertTrue(validate_ai_rule_acceptance_policy(bad))

    def test_rule_consistency_loop_prevention_positive_and_negative(self):
        from check_bootstrap import validate_rule_consistency_loop_prevention
        rule = load("canonical/policies/CFA3-RULE-CONSISTENCY-LOOP-PREVENTION-001.json")
        self.assertEqual([], validate_rule_consistency_loop_prevention(rule))
        for key in rule["requirements"]:
            invalid = copy.deepcopy(rule)
            invalid["requirements"][key] = False
            with self.subTest(requirement=key):
                self.assertTrue(validate_rule_consistency_loop_prevention(invalid))
        for key in rule["safety_boundary"]:
            invalid = copy.deepcopy(rule)
            invalid["safety_boundary"][key] = False
            with self.subTest(boundary=key):
                self.assertTrue(validate_rule_consistency_loop_prevention(invalid))
        for field, value in [
            ("status", "RUNTIME_PROVEN"),
            ("id", "UNRELATED_POLICY"),
            ("mandatory_clauses", []),
            ("resolution_sequence", []),
            ("loop_indicators", []),
        ]:
            invalid = copy.deepcopy(rule)
            invalid[field] = value
            with self.subTest(field=field):
                self.assertTrue(validate_rule_consistency_loop_prevention(invalid))

    def test_github_merge_gate_405_positive_and_negative(self):
        from check_bootstrap import validate_github_merge_gate_405_policy
        policy = load("canonical/policies/CFA3-GITHUB-MERGE-GATE-405-POLICY-001.json")
        self.assertEqual([], validate_github_merge_gate_405_policy(policy))
        for name, value in policy["requirements"].items():
            invalid = copy.deepcopy(policy)
            invalid["requirements"][name] = (996148 if name == "donor_max_modified_bytes"
                                             else not value)
            with self.subTest(requirement=name):
                self.assertTrue(validate_github_merge_gate_405_policy(invalid))
        for path, value in (
                (("rule", "runtime_verified"), True),
                (("rule", "text_hu"), "405 without required self-repair"),
                (("admission_boundary", "independent_execution_gate_pass"), True),
                (("requirements", "disable_github_protection"), True),
                (("requirements", "own_405_alone_is_blocker"), True),
                (("requirements", "independent_blocker_requires_stop"), False)):
            invalid = copy.deepcopy(policy)
            invalid[path[0]][path[1]] = value
            with self.subTest(guard=path):
                self.assertTrue(validate_github_merge_gate_405_policy(invalid))
        invalid = copy.deepcopy(policy)
        invalid["sections"].pop()
        self.assertTrue(validate_github_merge_gate_405_policy(invalid))

    def test_policy_long_term_validation_positive_and_negative(self):
        from check_bootstrap import validate_policy_long_term_validation
        policy = load("canonical/policies/CFA3-POLICY-LONG-TERM-VALIDATION-001.json")
        self.assertEqual([], validate_policy_long_term_validation(policy))
        for key in policy["requirements"]:
            bad = copy.deepcopy(policy)
            bad["requirements"][key] = False
            with self.subTest(requirement=key):
                self.assertTrue(validate_policy_long_term_validation(bad))
        for key in policy["admission_boundary"]:
            bad = copy.deepcopy(policy)
            bad["admission_boundary"][key] = True
            with self.subTest(boundary=key):
                self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        old = bad["mandatory_clauses"][1]["text_hu"]
        bad["mandatory_clauses"][1]["text_hu"] = "X" * len(old)
        self.assertEqual(len(old), len(bad["mandatory_clauses"][1]["text_hu"]))
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["mandatory_evidence_provisions"][0] = "Módosított előírás"
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_fields"].remove("rule_id")
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_fields"].remove("policy_revision_sha256")
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_binding"]["verified_stable_requires_matching_rule_id_and_policy_revision_sha256"] = False
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["verification_states"][3]["code"] = "PRELIMINARY_PASS"
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["status"] = "VERIFIED_STABLE"
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["scope"] = []
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["scope"][0] = "Más feladat"
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_fields"].remove("verification_state")
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_binding"]["verification_state_allowed_codes"] = ["VERIFIED_STABLE"]
        self.assertTrue(validate_policy_long_term_validation(bad))
        bad = copy.deepcopy(policy)
        bad["evidence_binding"]["verification_state_field"] = "ignored_state"
        self.assertTrue(validate_policy_long_term_validation(bad))


    def test_policy_exact_finalization_owner_text_positive_and_negative(self):
        from check_bootstrap import validate_policy_exact_finalization
        import tempfile
        from pathlib import Path
        p = load("canonical/policies/CFA3-POLICY-EXACT-FINALIZATION-001.json")
        self.assertEqual([], validate_policy_exact_finalization(p, ROOT))
        for field, bad_value in (
                ("status", "OWNER_APPROVED_MERGED_TO_MAIN"),
                ("approved_section_count", 12),
                ("approved_text_sha256", "0" * 64),
                ("finalization_gates", ["TEXT", "CI"]),
                ("lifecycle_evidence_source", "PR_ONLY")):
            bad = copy.deepcopy(p)
            bad[field] = bad_value
            with self.subTest(field=field):
                self.assertTrue(validate_policy_exact_finalization(bad, ROOT))
        for k in p["requirements"]:
            bad = copy.deepcopy(p)
            bad["requirements"][k] = False
            with self.subTest(requirement=k):
                self.assertTrue(validate_policy_exact_finalization(bad, ROOT))
        for k in p["admission_boundary"]:
            bad = copy.deepcopy(p)
            bad["admission_boundary"][k] = True
            with self.subTest(boundary=k):
                self.assertTrue(validate_policy_exact_finalization(bad, ROOT))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / p["approved_text_path"]
            target.parent.mkdir(parents=True)
            original = (ROOT / p["approved_text_path"]).read_bytes()
            target.write_bytes(original.replace(b"TEXT PASS:", b"TEXT OK:", 1))
            self.assertTrue(validate_policy_exact_finalization(p, tmp))
            target.write_bytes(original[:len(original)//2])
            self.assertTrue(validate_policy_exact_finalization(p, tmp))

    def test_policy_surface_all_current_canonical_fields(self):
        from check_guard_policy_surface import validate_snapshot
        surface = load("canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json")
        self.assertEqual([], validate_snapshot(surface, ROOT))
        self.assertEqual(15, surface["source_policy_count"])
        from check_guard_policy_surface import validate_catalog_policy_leaf_total
        coverage = load("canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json")
        self.assertEqual([],validate_catalog_policy_leaf_total(surface, coverage))
        bad_catalog = copy.deepcopy(coverage)
        bad_catalog["canonical_policy_leaf_fields_enumerated"] += 1
        self.assertTrue(validate_catalog_policy_leaf_total(surface, bad_catalog))
        bad_catalog["canonical_policy_leaf_fields_enumerated"] -= 2
        self.assertTrue(validate_catalog_policy_leaf_total(surface, bad_catalog))
        self.assertFalse(surface["semantic_rule_admission"])
        self.assertEqual(sum(len(s["leaves"]) for s in surface["sources"]),
                         sum(s["leaf_count"] for s in surface["sources"]))
        broken = copy.deepcopy(surface)
        broken["sources"][0]["leaves"] = broken["sources"][0]["leaves"][1:]
        self.assertTrue(validate_snapshot(broken, ROOT))
        broken = copy.deepcopy(surface)
        broken["sources"][0]["git_blob_sha1"] = "0" * 40
        self.assertTrue(validate_snapshot(broken, ROOT))
        broken = copy.deepcopy(surface)
        broken["sources"] = broken["sources"][1:]
        self.assertTrue(validate_snapshot(broken, ROOT))
        broken = copy.deepcopy(surface)
        broken["semantic_rule_admission"] = True
        self.assertTrue(validate_snapshot(broken, ROOT))

if __name__=="__main__":
    unittest.main()
