#!/usr/bin/env python3
"""Structural bootstrap guard: never issues CFA3 runtime/admission PASS."""
import json
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(relative, root=ROOT):
    return json.loads((root / relative).read_text(encoding="utf-8"))

def validate_objects(gov, cpu, platform, ledger):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    require(gov.get("schema") == "cfa3.repository-governance.v1", "governance schema mismatch")
    require(gov.get("repository") == "ubuntuokos/CFA3-CinenemFoundArchitecture3", "target repository mismatch")
    require(gov.get("task_policy", {}).get("blocker_means_stop") is True, "BLOCKER=STOP is mandatory")
    require(gov.get("task_policy", {}).get("main_direct_write_allowed") is False, "main direct writes forbidden")
    require(gov.get("task_policy", {}).get("one_active_implementation_pr") is True, "single active implementation PR required")
    require(gov.get("task_policy", {}).get("new_pr_requires_explicit_approval") is True, "unapproved PR is forbidden")
    require(gov.get("task_policy", {}).get("exact_main_and_head_check_before_mutation") is True, "fresh state is mandatory")
    require(gov.get("legacy_policy_transfer", {}).get("unaltered_unchecked_transfer_forbidden") is True, "unchecked legacy transfer forbidden")
    require(gov.get("evidence_policy", {}).get("reference_ci_not_physical_pass") is True, "CI cannot prove physical PASS")
    require(gov.get("evidence_policy", {}).get("physical_current_host_evidence_only_from_physical_run") is True, "physical proof must be real")
    require(gov.get("readiness", {}).get("full_development_governance_admission") == "PENDING_RECONCILIATION", "cannot claim full governance admission")
    require(gov.get("readiness", {}).get("foundation_verified") is False, "cannot claim unbuilt Foundation PASS")
    development_rules = gov.get("development_rules", [])
    ai_behavior_rules = gov.get("ai_behavior_rules", [])
    require({x.get("id") for x in development_rules} == {f"DEV-{i:02d}" for i in range(1, 13)}
            and len(development_rules) == 12, "DEV-01..12 exact coverage missing or duplicated")
    require({x.get("id") for x in ai_behavior_rules} == {f"AI-{i:02d}" for i in range(1, 13)}
            and len(ai_behavior_rules) == 12, "AI-01..12 exact coverage missing or duplicated")
    require(any(x.get("id") == "DEV-12" and x.get("code") == "NO_ASSUMPTIONS_EXACT_SCOPE_AND_CANONICAL_DESIGN" for x in development_rules),
            "mandatory development execution rule DEV-12 missing")
    require(any(x.get("id") == "AI-12" and x.get("code") == "NO_ASSUMPTIONS_AND_MANDATORY_CFA3_COMPLIANCE" for x in ai_behavior_rules),
            "mandatory AI execution rule AI-12 missing")
    execution = gov.get("execution_integrity_policy", {})
    require(execution.get("id") == "CFA3-TASK-EXECUTION-COMPLIANCE-001", "execution compliance identity missing")
    require(execution.get("status") == "FINAL_MANDATORY", "execution compliance must be mandatory")
    require(execution.get("interpretation") == "PROHIBITION_NOT_PREFERENCE", "execution compliance cannot be optional")
    required_execution = {
        "assumption_based_execution": "FORBIDDEN",
        "task_definition": "EXACT_DESCRIPTION_GOAL_SCOPE_AND_CONSTRAINTS_MANDATORY",
        "unrequested_task_expansion": "FORBIDDEN",
        "approved_guidelines_rules_and_architecture": "MANDATORY_NO_DEVIATION",
        "approved_cfa3_design_description": "MANDATORY_NO_DEVIATION",
        "approved_cfa3_branding_and_identity": "MANDATORY_NO_DEVIATION",
        "self_invented_or_substitute_design": "FORBIDDEN",
        "current_authoritative_or_deterministic_source_verification": "REQUIRED_BEFORE_EACH_RELEVANT_OPERATION",
        "unverified_or_missing_mandatory_requirement": "STOP_AND_REPORT_BLOCKER",
        "autonomous_bypass_or_workaround": "FORBIDDEN",
    }
    for field, expected in required_execution.items():
        require(execution.get("requirements", {}).get(field) == expected, "mandatory execution compliance missing: " + field)
    require(execution.get("verified_branding_reference") == "docs/branding/CFA3-BRANDING.md",
            "official CFA3 branding reference missing")
    require(platform.get("capability_target_count") == 200, "new target baseline must be 200")
    require(platform.get("capability_registry_complete") is False, "200-capability ledger not yet verified")
    require(platform.get("foundation_verified") is False, "full Foundation not yet verified")
    require(platform.get("gui", {}).get("technology") == "Qt 6", "Qt 6 is mandatory")
    require(platform.get("gui", {}).get("mandatory_for_all_gui_apps") is True, "Qt 6 GUI coverage mandatory")
    require(platform.get("languages", {}).get("default_for_new_native_components") == "Rust", "Rust-first baseline mandatory")
    require(platform.get("hardware", {}).get("cpu_only_base") is True, "CPU-only baseline mandatory")
    require(platform.get("host_verification", {}).get("actual_edges_only") is True, "no synthetic app edges")
    require(cpu.get("cpu_native_baseline_required") is True, "CPU-native platform baseline mandatory")
    require(cpu.get("no_silent_cpu_or_cloud_fallback") is True, "silent fallback forbidden")
    require(cpu.get("environment", {}).get("development", {}).get("cpu_fallback") == "ALLOW_WITH_PROVENANCE", "development fallback must have provenance")
    require(cpu.get("environment", {}).get("development", {}).get("automatic_switch") == "PREAUTHORIZED_PROFILE_ONLY", "implicit unapproved fallback forbidden")
    require(cpu.get("environment", {}).get("development", {}).get("gpu_test_may_pass_on_cpu") is False, "GPU test cannot PASS on CPU")
    require(cpu.get("environment", {}).get("qualification", {}).get("physical_accelerator_pass_requires_accelerator") is True, "accelerator PASS requires accelerator")
    require(ledger.get("inventory_complete") is False, "legacy source ledger must not be misrepresented as complete")
    require(ledger.get("source_repository") == "ubuntuokos/Final-Architecture-v3.0", "legacy source mismatch")
    require(len(ledger.get("source_records", [])) > 0, "source ledger is empty")
    require(all(r.get("code_reuse_authorized") is False for r in ledger.get("source_records", [])), "unreviewed code reuse is forbidden")
    paths = [r.get("path") for r in ledger.get("source_records", [])]
    require(len(paths) == len(set(paths)), "duplicate source ledger paths")
    for record in ledger.get("source_records", []):
        sha = record.get("blob_sha")
        require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) is not None,
                "legacy source record has invalid Git blob SHA: " + str(record.get("path")))
    return errors

def validate_source_lifecycle(policy, index):
    errors=[]
    gates=policy.get("invariants",{})
    for key in ("lookup_before_analysis","existing_approved_decision_is_immutable",
                "no_automatic_decision_overwrite","no_duplicate_canonical_sources",
                "repository_move_preserves_logical_identity",
                "no_unapproved_new_pr_or_implementation",
                "rights_verification_required_before_code_modification",
                "legacy_config_and_bad_decision_inheritance_forbidden"):
        if gates.get(key) is not True:
            errors.append("source lifecycle invariant missing: "+key)
    if gates.get("incomplete_source_index")!="BLOCK_UNKNOWN_CLASSIFICATION":
        errors.append("source lifecycle incomplete index must block unknown links")
    if policy.get("id")!="CFA3-SOURCE-LIFECYCLE-POLICY-001":
        errors.append("source lifecycle policy identity mismatch")
    if policy.get("authority_status")!="OWNER_APPROVED_PENDING_REVIEW_AND_MERGE":
        errors.append("source lifecycle policy admission misrepresented")
    if index.get("schema") not in ("cfa3.source-lifecycle-index.v1", "cfa3.source-lifecycle-index.v2"):
        errors.append("source lifecycle index schema mismatch")
    if index.get("complete") is not False:
        errors.append("cannot claim complete donor/source migration")
    from source_lifecycle import validate_index
    try:
        validate_index(index)
    except (ValueError, TypeError, AttributeError) as exc:
        errors.append("invalid source lifecycle index: " + str(exc))
    return errors

def validate_donor_classification_plan(policy, decision):
    """Check approved design invariants only; never certify actual donor migration."""
    errors=[]
    def require(condition, message):
        if not condition:
            errors.append("donor classification plan: "+message)
    require(policy.get("schema")=="cfa3.donor-bounded-classification-policy.v1", "schema mismatch")
    require(policy.get("id")=="CFA3-DONOR-BOUNDED-CLASSIFICATION-001", "policy identifier missing")
    require(policy.get("repository_status")=="OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "repo admission status overstated")
    legacy=policy.get("legacy_scope",{})
    require(legacy.get("repair_legacy_repo_required") is False,"legacy repair must not be prerequisite")
    require(legacy.get("preserve_raw_records_and_original_links") is True,"lossless preservation required")
    require(legacy.get("all_owner_approved_submissions_must_be_accounted_for") is True,"owner donor coverage required")
    require(legacy.get("import_legacy_runtime_or_configuration") is False,"no legacy runtime/config import")
    require(legacy.get("import_old_classifier_unchanged") is False,"legacy classifier must be redesigned")
    classification=policy.get("classification",{})
    require(classification.get("levels")==["L1","L2","L3","L4","L5"],"L1–L5 only")
    require(classification.get("max_level")==5,"no sixth level")
    require(classification.get("sequence")=="STRICT_SEQUENTIAL","level concurrency forbidden")
    depth=classification.get("global_depth_contract",{})
    require(depth.get("accounting")=="ABSOLUTE_GLOBAL_LEVELS_L1_THROUGH_L5","depth contract: global levels")
    require(depth.get("original_roots")=="ONLY_FROZEN_L1_INPUT_IDENTITIES","only original frozen L1 roots")
    require(depth.get("root_level")==1,"global root is L1")
    require(depth.get("discovered_child_level_rule")=="CHILD_GLOBAL_LEVEL_EQUALS_PARENT_GLOBAL_LEVEL_PLUS_ONE","child must increment global depth by one")
    require(depth.get("levels_are_relative_to_new_donor") is False,"no relative donor depth")
    for key in ("newly_discovered_donor_may_restart_depth",
                "newly_classified_or_approved_donor_may_become_additional_L1_root"):
        require(depth.get(key) is False,key+" forbidden")
    expected_remaining={"L1":5,"L2":4,"L3":3,"L4":2,"L5":1}
    require(depth.get("remaining_levels_by_discovery_level")==expected_remaining,
            "remaining global depth mapping L1:5,L2:4,L3:3,L4:2,L5:1")
    require(depth.get("remaining_levels_include_discovery_level") is True,"include current level")
    require(depth.get("max_global_level")==5,"global depth must stop at L5")
    require(depth.get("enqueue_child_only_when_parent_level_below")==5,"cannot enqueue after L5")
    require(depth.get("last_level_further_expansion")=="FORBIDDEN","L5 cannot expand further")
    require(depth.get("prohibit_L6_and_later") is True,"L6 and deeper prohibited")
    for key in ("level_publication_does_not_reset_depth","reappearing_known_source_does_not_reset_depth",
                "discovery_approval_does_not_reset_depth","no_hidden_reparenting_or_root_promotion"):
        require(depth.get(key) is True,key+" required")
    require(depth.get("same_source_found_again")==
            "PRESERVE_PRIOR_DECISION_AND_ADD_PROVENANCE_ONLY_NO_NEW_ROOT",
            "known source re-encounter cannot create a new root")
    require(depth.get("existing_original_L1_root")==
            "RETAIN_ORIGINAL_L1_ROOT_ONLY_NO_SECONDARY_RESET",
            "old L1 root cannot become a second root")
    require(depth.get("multiple_parent_paths")==
            "RECORD_ALL_VERIFIED_EDGES_BUT_DO_NOT_RESTART_OR_EXTEND_DEPTH",
            "multiple parents do not extend depth")

    require(classification.get("single_canonical_source_identity") is True,"one canonical identity")
    require(classification.get("existing_source_previous_decision_overwrite") is False,"prior decision cannot be overwritten")
    require(classification.get("known_source_no_reanalysis") is True,"known source must not be redone")
    require(classification.get("discovery_is_admission") is False,"discovery cannot admit donor")
    lim=policy.get("expansion_limit",{})
    require((lim.get("limit_numerator"),lim.get("limit_denominator"),lim.get("limit_rounding"))==(115,100,"FLOOR"),"15% exact threshold required")
    require(lim.get("initial_count_field")=="frozen_l1_input_link_records_B","baseline must be frozen L1 count")
    require(lim.get("comparison")=="NET_NEW_UNIQUE_SOURCE_IDENTITIES_AFTER_COMPLETE_PRIOR_INDEX_LOOKUP_AND_DEDUPLICATION","net-new identities only")
    for key in ("count_new_unique_sources_once_per_level","preserve_raw_links_and_every_parent_relation",
                "known_aliases_and_superseded_identities_reused","per_level_not_cumulative","denominator_frozen_for_entire_run",
                "stop_on_first_count_exceed","no_auto_truncation_to_limit",
                "no_new_level_on_stop","no_auto_resume","retained_completed_levels_remain_published"):
        require(lim.get(key) is True,key+" must be true")
    require(lim.get("count_repeated_discovered_urls") is False,"duplicates do not consume net-new quota")
    require(lim.get("count_previously_known_discovered_urls") is False,"known URLs do not consume net-new quota")
    require(lim.get("known_source_reanalysis") is False,"known sources cannot be reanalyzed")
    require(lim.get("index_incomplete_state")=="BLOCKED_INDEX_INCOMPLETE","incomplete index blocks new identities")
    require(lim.get("known_only_branch")=="EARLY_EXHAUSTION_CANDIDATE_PENDING_LEVEL_PUBLICATION","exhaustion requires publication")
    require(lim.get("do_not_use")=="ACTIVE_DONOR_DATABASE_SIZE_OR_RAW_OUTBOUND_OCCURRENCE_COUNT_AS_NUMERATOR","invalid limit numerator")
    require(lim.get("over_limit_state")=="STOPPED_EXPANSION_LIMIT","limit violation must stop")
    sample=lim.get("example",{})
    require((sample.get("l1_input"),sample.get("limit"))==(445,511),"sample limit incorrect")
    require([(c.get("raw_links"),c.get("known_links"),c.get("net_new_unique")) for c in sample.get("cases",[])]==[(650,445,205),(512,512,0),(800,151,649)],"approved example cases changed")
    require(policy.get("owner_rule_override",{}).get("owner_explicit_approval") is True,"missing owner approval")
    require(decision.get("expansion_rule_override",{}).get("approved") is True,"missing owner decision")
    require("NET_NEW_UNIQUE_SOURCE_LIMIT_FIXED_AT_115_PERCENT_OF_FROZEN_L1" in decision.get("nonnegotiable",[]),"decision still uses raw-quota rule")
    pub=policy.get("level_publish_gate",{})
    require(pub.get("policy_id")=="CFA3-DONOR-LEVEL-PUBLISH-GATE-001","mandatory gate identity")
    require(pub.get("next_level_requires_prior_level")=="PUBLISHED_AND_VERIFIED_PASS","no next level without publication PASS")
    for key in ("mandatory_after_every_completed_level","read_back_by_canonical_id",
                "read_back_by_source_locator","searchable_index_required",
                "parent_child_provenance_required","atomic_or_versioned_publish_required",
                "previous_published_snapshot_preserved_on_failure",
                "fail_closed_if_missing_required_evidence"):
        require(pub.get(key) is True,key+" required")
    final=policy.get("final_acceptance",{})
    for key in ("approved_source_coverage_missing","unresolved_identity_conflicts",
                "unjustified_duplicates","unclassified_relevant_sources",
                "broken_source_relations","unpublished_approved_donors",
                "inherited_bad_legacy_configurations"):
        require(type(final.get(key)) is int and final.get(key)==0,key+" target must be zero")
    require(final.get("stopped_expansion_limit_is_not_final_success") is True,"limit STOP cannot become FULL PASS")
    bounds=policy.get("boundaries",{})
    require(bounds.get("status_of_actual_migration")=="PENDING","migration not performed")
    require(bounds.get("data_migration_performed_by_this_change") is False,"no fabricated donor import")
    require(bounds.get("live_network_crawl_performed_by_this_change") is False,"no fabricated crawl")
    require(bounds.get("current_host_pass_claim") is False,"no physical PASS fabricated")
    fin=policy.get("plan_finalization",{})
    require(fin.get("state")=="FINAL_OWNER_APPROVED_TECHNICAL_PLAN","final plan missing")
    require(fin.get("scope")=="DESIGN_DOCUMENTATION_AND_STRUCTURAL_GUARD_ONLY","final plan scope changed")
    require(fin.get("implementation_status")=="PENDING" and fin.get("migration_status")=="PENDING",
            "final plan status must not fake data migration")
    require(fin.get("source_index_complete") is False,"no fake source index")
    require(fin.get("published_levels")==[],"no invented level PASS")
    df=decision.get("plan_finalization",{})
    require(df.get("state")==fin.get("state"),"decision/final plan mismatch")
    require(df.get("donor_import_complete") is False,"no invented donor import")
    require(df.get("published_levels")==[],"no invented published levels")
    require(decision.get("approved_policy_id")==policy.get("id"),"decision/policy mismatch")
    require(decision.get("status")=="OWNER_APPROVED_PLAN_PENDING_REPOSITORY_MERGE","decision merge status overstated")
    require(decision.get("owner_approved") is True,"owner approval missing")
    clarification=decision.get("depth_clarification",{})
    require(clarification.get("global_depth_not_per_donor") is True,"owner global depth clarification")
    require(clarification.get("frozen_original_roots_only") is True,"no newly created donor roots")
    require(clarification.get("newly_discovered_donors_no_root_reset") is True,"no donor-based depth restart")
    require(clarification.get("remaining_levels_including_current")==expected_remaining,
            "owner-confirmed remaining depth mapping")
    require(clarification.get("absolute_max_level")==5,"owner-confirmed max depth")
    for key in ("GLOBAL_DISCOVERY_DEPTH_L1_TO_L5_NEVER_RESETS",
                "DISCOVERED_DONORS_NOT_NEW_FIVE_LEVEL_ROOTS",
                "REMAINING_DEPTH_AT_L2_4_L3_3_L4_2_L5_1",
                "NO_L6"):
        require(key in decision.get("nonnegotiable",[]),"nonnegotiable missing: "+key)

    require(decision.get("effects",{}).get("runtime_admission") is False,"runtime cannot be admitted")
    return errors


APPROVED_RULE_ADMISSION_TEXT_HU = (
    "Szabály felvételekor az AI kizárólag a kijelölt főfeladattal foglalkozhat; minden új szabályt fel kell venni a CFA3-CURRENT-POLICY-SURFACE-001.json "
    "nyilvántartásba; ellenőrizni kell a Bootstrap követelményeit; az új szabályhoz igazítani kell a fixen beírt tesztértékeket; a PR-t valamennyi közvetlenül "
    "szükséges, egymással konzisztens fájllal kell előkészíteni; sikertelen ellenőrzésnél bizonyíték alapján egyértelműen meg kell jelölni, hogy a hiányosságért "
    "az AI asszisztens vagy az AI fejlesztő felelős. Külön tulajdonosi feladat vagy önállóan jóváhagyott új szabály csak a saját feladatához kötött ágon és "
    "PR-ben vezethető be; másik, már megnyitott feladat PR-jébe automatikusan nem helyezhető át. A közös nyilvántartás szükséges konzisztens módosítása nem "
    "teszi közössé a két feladat hatáskörét."
)

def validate_rule_admission(policy):
    """Check the owner's new rule-admission contract without claiming runtime PASS."""
    errors = []
    if not isinstance(policy, dict):
        return ["rule admission: owner-approved policy must be an object"]
    def require(condition, message):
        if not condition:
            errors.append("rule admission: " + message)
    require(set(policy) == {"schema", "id", "status", "owner_decision_date",
                            "rule", "requirements", "responsibility", "admission_boundary"},
            "unapproved or missing policy root field")
    require(policy.get("schema") == "cfa3.rule-admission-policy.v1", "schema mismatch")
    require(policy.get("id") == "CFA3-RULE-ADMISSION-POLICY-001", "identity mismatch")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "unverified merge status")
    require(policy.get("owner_decision_date") == "2026-10-11",
            "owner-approved decision date changed")
    rule = policy.get("rule")
    require(isinstance(rule, dict) and set(rule) ==
            {"id", "code", "text_hu", "scope", "runtime_verified"},
            "unapproved or missing rule field")
    if not isinstance(rule, dict):
        rule = {}
    require(rule.get("id") == "RULE-ADMISSION-001" and
            rule.get("code") == "EXACT_SCOPE_POLICY_SURFACE_BOOTSTRAP_TEST_PR_AND_FAILURE_ATTRIBUTION",
            "rule identity/code missing")
    require(rule.get("text_hu") == APPROVED_RULE_ADMISSION_TEXT_HU,
            "owner-approved rule text changed")
    require(rule.get("scope") == "ONLY_THE_OWNER_DESIGNATED_MAIN_TASK", "rule scope widened")
    require(rule.get("runtime_verified") is False, "unverified runtime PASS is forbidden")
    required = (
        "rule_admission_may_not_expand_the_main_task",
        "new_rule_must_be_registered_in_canonical_policy_surface",
        "bootstrap_requirements_checked_before_pr",
        "fixed_test_expectations_updated_when_new_rule_is_added",
        "pr_must_include_all_directly_affected_consistent_files",
        "independent_owner_task_must_have_dedicated_branch_and_pr",
        "positive_and_negative_bootstrap_checks_required",
        "failed_check_requires_responsible_ai_role",
        "failed_check_must_report_root_cause_and_evidence",
        "no_unjustified_attribution_or_fabricated_pass",
        "failed_gate_requires_stop_and_report",
    )
    requirements = policy.get("requirements")
    require(isinstance(requirements, dict) and set(requirements) == set(required),
            "unapproved or missing rule-admission requirement")
    for name in required:
        require(isinstance(requirements, dict) and requirements.get(name) is True,
                "mandatory requirement absent: " + name)
    responsibility = policy.get("responsibility")
    require(isinstance(responsibility, dict) and set(responsibility) ==
            {"ai_assistant", "ai_developer", "unverifiable_cause",
             "if_both_roles_are_same_actor", "attribution_basis"},
            "unapproved or missing responsibility field")
    if not isinstance(responsibility, dict):
        responsibility = {}
    require(responsibility.get("ai_assistant") == "Feladatvezérlési, hatásköri, ellenőrzés-előkészítési és jelentési hiányosság.", "ai_assistant exact accountability drift")
    require(responsibility.get("ai_developer") == "Implementációs, teszt-, konfigurációs, adat- és PR-fájlkonzisztencia miatti hiányosság.", "ai_developer exact accountability drift")
    require(responsibility.get("unverifiable_cause") ==
            "STOP_AND_REPORT_UNVERIFIED_CAUSE_NO_FALSE_ATTRIBUTION",
            "uncertain cause must not be invented")
    require(responsibility.get("if_both_roles_are_same_actor") ==
            "REPORT_BOTH_ROLES_WITH_SPECIFIC_CAUSE",
            "same actor must report both roles and concrete cause")
    require(responsibility.get("attribution_basis") ==
            "DETERMINISTIC_CHECK_LOGS_AND_EXACT_CHANGED_FILES",
            "responsibility requires deterministic evidence and exact changed files")
    admission_boundary = policy.get("admission_boundary")
    require(isinstance(admission_boundary, dict) and set(admission_boundary) ==
            {"bootstrap_structural_pass_is_runtime_proof", "independent_execution_gate_pass"},
            "unapproved or missing admission boundary field")
    if not isinstance(admission_boundary, dict):
        admission_boundary = {}
    require(admission_boundary.get("bootstrap_structural_pass_is_runtime_proof") is False,
            "bootstrap may not fake runtime gate proof")
    require(admission_boundary.get("independent_execution_gate_pass") is False,
            "independent gate PASS may not be fabricated")
    return errors

def validate_sequential_command_policy(policy):
    """Validate one-command/one-response owner requirements; not runtime proof."""
    errors = []
    def require(condition, message):
        if not condition:
            errors.append("sequential command: " + message)
    require(policy.get("schema") == "cfa3.sequential-command-policy.v1", "schema mismatch")
    require(policy.get("id") == "CFA3-SEQUENTIAL-COMMAND-POLICY-001", "identity mismatch")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "unverified merge status")
    rule = policy.get("rule", {})
    require(rule.get("id") == "CFA3-SEQUENTIAL-COMMAND-001" and
            rule.get("code") == "ONE_COMMAND_ONE_RESPONSE", "rule identity/code mismatch")
    require(isinstance(rule.get("text_hu"), str) and len(rule["text_hu"]) > 100,
            "mandatory owner text missing")
    require(rule.get("scope") == "USER_EXECUTED_MULTI_STEP_COMMANDS_AND_TESTS",
            "rule scope drift")
    require(rule.get("runtime_verified") is False, "unverified runtime PASS")
    for key in ("one_executable_command_or_test_per_ai_response",
                "explicitly_state_expected_result",
                "user_executes_and_returns_complete_result",
                "ai_analyzes_actual_result_before_next_command",
                "next_command_only_after_response_analysis",
                "failed_result_requires_minimal_diagnostic_or_repair_next_step",
                "prohibit_preissued_command_batches",
                "prohibit_skipping_user_response",
                "prohibit_assumed_execution_or_fabricated_pass",
                "require_stepwise_error_isolation"):
        require(policy.get("requirements", {}).get(key) is True,
                "mandatory step requirement missing: " + key)
    require(policy.get("sequence") == [
        "AI_ISSUES_ONE_COMMAND_AND_EXPECTED_RESULT",
        "USER_EXECUTES_AND_RETURNS_COMPLETE_RESULT",
        "AI_ANALYZES_ACTUAL_RESULT",
        "AI_ISSUES_ONLY_NEXT_NECESSARY_COMMAND_OR_REPORTS_BLOCKER"
    ], "sequential handshake drift")
    for field in ("structural_bootstrap_pass_is_runtime_proof",
                  "independent_execution_gate_pass"):
        require(policy.get("admission_boundary", {}).get(field) is False,
                "unverified runtime admission: " + field)
    return errors

def check(root=ROOT):
    gov=load("canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json",root)
    cpu=load("canonical/policies/CFA3-CPU-EXECUTION-POLICY-001.json",root)
    platform=load("canonical/policies/CFA3-PLATFORM-CONSTRAINTS-001.json",root)
    ledger=load("canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json",root)
    errors=validate_objects(gov,cpu,platform,ledger)
    policy=load("canonical/policies/CFA3-SOURCE-LIFECYCLE-POLICY-001.json",root)
    index=load("canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json",root)
    errors.extend(validate_source_lifecycle(policy,index))
    donor_policy=load("canonical/policies/CFA3-DONOR-BOUNDED-CLASSIFICATION-001.json",root)
    donor_decision=load("canonical/decisions/CFA3-DEC-DONOR-MIGRATION-AND-CLASSIFICATION-V2-20261009.json",root)
    errors.extend(validate_donor_classification_plan(donor_policy,donor_decision))
    rule_admission=load("canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json",root)
    errors.extend(validate_rule_admission(rule_admission))
    sequential=load("canonical/policies/CFA3-SEQUENTIAL-COMMAND-POLICY-001.json",root)
    errors.extend(validate_sequential_command_policy(sequential))
    from check_guard_policy_surface import SURFACE, validate_snapshot
    errors.extend(validate_snapshot(load(SURFACE,root),root))
    for name in ("README.md","AGENTS.md","docs/BOOTSTRAP.md","docs/governance/RECONCILIATION.md",".github/workflows/cfa3-bootstrap.yml"):
        if not (root/name).is_file():
            errors.append(f"missing bootstrap file: {name}")
    return errors

if __name__=="__main__":
    violations=check()
    if violations:
        for v in violations:
            print("BOOTSTRAP_GUARD_FAIL:",v,file=sys.stderr)
        sys.exit(1)
    print("BOOTSTRAP_STRUCTURAL_PASS (reference consistency only; NOT governance, Foundation, GPU or physical Current Host PASS)")
