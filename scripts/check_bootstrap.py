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
    " Közös szabálynyilvántartást érintő párhuzamos PR-ek integrációját sorosítani kell: minden PR csak a saját jóváh"
    "agyott szabályának bejegyzéseit változtathatja, a többi rekordot és történeti adatot meg kell őriznie. A nyilván"
    "tartást az aktuális main és az adott PR HEAD ellenőrzött állapotából kell összehangolni; elavult pillanatkép nem"
    " írhat felül újabb rekordot. A szabálydarabszámot, mezőleltárt és Git-blob azonosítókat determinisztikusan újra "
    "kell ellenőrizni, az aktuális commiton kötelező CI- és review-kapukkal együtt. Azonos fájl párhuzamos módosítása"
    " vagy eltérő main/head esetén összevonás nem engedélyezett a célzott, adatvesztésmentes összehangolás és az új e"
    "llenőrzések előtt; valós, nem egyértelmű konfliktus STOP. A technikai összehangolás kizárólag kifejezetten enged"
    "élyezett körben történhet, nem jogosít más szabály tartalmi változtatására, önálló rebase-re, új PR-re vagy önké"
    "nyes összevonásra."
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
        "shared_registry_pr_integration_must_be_serialized",
        "unrelated_policy_registry_records_must_be_preserved",
        "registry_update_must_use_verified_current_main_and_pr_head",
        "canonical_registry_counts_leaf_inventory_and_blob_hashes_must_be_rechecked",
        "unresolved_ambiguity_or_stale_head_blocks_merge",
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

def validate_donor_file_size_policy(policy):
    """Validate owner-approved donor file-size contract; no runtime PASS implied."""
    if not isinstance(policy, dict):
        return ["donor file size: policy must be an object"]
    issues = []
    def require(condition, description):
        if not condition:
            issues.append("donor file size: " + description)
    require(policy.get("schema") == "cfa3.donor-file-size-policy.v1", "schema mismatch")
    require(policy.get("id") == "CFA3-DONOR-FILE-SIZE-POLICY-001", "identity mismatch")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE",
            "authority/admission status mismatch")
    rule = policy.get("rule")
    require(isinstance(rule, dict), "rule object missing")
    rule = rule if isinstance(rule, dict) else {}
    require(rule.get("id") == "DONOR-FILE-SIZE-001" and
            rule.get("code") == "DONOR_DATABASE_FILE_MAX_095_MIB",
            "owner rule identifier/code mismatch")
    require(isinstance(rule.get("text_hu"), str) and
            "0,95 MiB" in rule.get("text_hu", ""), "owner rule text missing")
    require(rule.get("runtime_verified") is False, "unverified runtime evidence")
    maximum = policy.get("maximum_file_size")
    maximum = maximum if isinstance(maximum, dict) else {}
    for key, value in {
        "unit": "MiB",
        "maximum_mib": 0.95,
        "maximum_bytes": 996147,
        "interpretation": "INCLUSIVE_LIMIT_OF_UNCOMPRESSED_FILE_BYTES",
        "comparison": "FILE_BYTES_LESS_THAN_OR_EQUAL_TO_MAXIMUM",
    }.items():
        require(maximum.get(key) == value, "incorrect threshold: " + key)
    scope = policy.get("applies_to")
    expected_scope = {
        "DONOR_RECORDS", "DONOR_SOURCE_FILES", "SEARCH_AND_ROUTING_INDEXES",
        "SOURCE_LIFECYCLE_REGISTRIES", "DONOR_IDENTITY_AND_ALIAS_REGISTRIES",
        "DONOR_HISTORY_AND_PROVENANCE", "RELATED_DONOR_DATA_FILES",
    }
    require(isinstance(scope, list) and len(scope) == len(expected_scope)
            and set(scope) == expected_scope, "incomplete donor data scope")
    requirements = policy.get("requirements")
    requirements = requirements if isinstance(requirements, dict) else {}
    required_true = (
        "new_and_modified_files_checked",
        "all_affected_files_checked_before_github_upload",
        "split_before_exceeding_limit",
        "open_new_files_without_data_loss",
        "preexisting_oversize_files_preserved_unchanged",
        "preexisting_oversize_file_modification_requires_split",
        "preserve_global_deduplication",
        "preserve_central_search",
        "preserve_stable_donor_identities",
        "preserve_historical_records_and_provenance",
        "preserve_cross_file_index_consistency",
        "prohibit_truncation_or_silent_data_removal",
        "oversize_changed_file_fails_closed",
    )
    for key in required_true:
        require(requirements.get(key) is True, "required invariant missing: " + key)
    legacy = policy.get("legacy_handling")
    legacy = legacy if isinstance(legacy, dict) else {}
    require(legacy.get("unmodified_preexisting_oversize_data") == "RETAIN_UNCHANGED",
            "legacy data preservation missing")
    require(legacy.get("modified_preexisting_oversize_data") ==
            "SPLIT_WITH_FULL_HISTORY_AND_LINKS", "legacy split preservation missing")
    require(legacy.get("history_loss_allowed") is False and
            legacy.get("retroactive_deletion_allowed") is False,
            "legacy history loss forbidden")
    proof = policy.get("verification")
    proof = proof if isinstance(proof, dict) else {}
    require(proof.get("size_check") ==
            "ACTUAL_UNCOMPRESSED_FILE_BYTES_BEFORE_GITHUB_UPLOAD",
            "pre-upload size check missing")
    require(proof.get("fail_state") == "STOP_BLOCKER", "fail-closed missing")
    require(proof.get("structural_ci_verification_is_runtime_admission") is False,
            "CI must not imply runtime admission")
    require(proof.get("donor_publication_or_runtime_admission_by_this_rule") is False,
            "rule cannot self-admit donors or runtime")
    return issues


def validate_github_resource_404_policy(policy):
    """Owner-approved 404 resource-order contract; structural check, not runtime proof."""
    issues = []
    def require(condition, message):
        if not condition:
            issues.append("github 404 resource policy: " + message)
    if not isinstance(policy, dict):
        return ["github 404 resource policy: not an object"]
    require(policy.get("schema") == "cfa3.github-resource-existence-404-policy.v1", "schema mismatch")
    require(policy.get("id") == "CFA3-GITHUB-RESOURCE-EXISTENCE-404-POLICY-001", "identity mismatch")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "unverified admission status")
    require(policy.get("owner_decision_date") == "2026-10-12", "owner decision date drift")
    rule = policy.get("rule", {})
    rule = rule if isinstance(rule, dict) else {}
    require(rule.get("id") == "CFA3-GITHUB-RESOURCE-EXISTENCE-404-001" and
            rule.get("code") == "VERIFY_EXISTENCE_CREATE_READBACK_BEFORE_DEPENDENT_OPERATION",
            "rule identity mismatch")
    require(isinstance(rule.get("text_hu"), str) and len(rule["text_hu"]) > 200,
            "mandatory Hungarian normative text missing")
    require(rule.get("runtime_verified") is False, "unproven runtime verification")
    expected_sequence = ["VERIFY_REPOSITORY_ID_AND_PERMISSION","VERIFY_ACTUAL_MAIN_SHA","VERIFY_OR_AUTHORIZE_AND_CREATE_TARGET_BRANCH_FROM_MAIN","READ_BACK_TARGET_BRANCH_AND_SHA","PREPARE_ONLY_SCOPED_FILES","VERIFY_HEAD_AND_ATTACH_COMMIT","CREATE_PR_FROM_EXISTING_VERIFIED_HEAD_TO_VERIFIED_BASE","VERIFY_LIVE_CI_RULESET_AND_MERGE_GATE","MERGE_ONLY_IF_APPROVED_AND_ALL_GATES_PASS"]
    require(policy.get("mandatory_sequence") == expected_sequence, "resource dependency order drift")
    required_flags = ["verify_resource_before_dependent_operation","verify_repository_owner_name_and_permissions","verify_actual_default_branch_and_main_sha","existing_branch_must_not_be_recreated","missing_branch_creation_requires_explicit_task_authority","branch_creation_uses_verified_main_sha","created_branch_requires_github_readback_and_sha","verify_file_path_and_create_vs_update","fresh_head_sha_before_commit","verify_commit_linked_to_target_branch","pr_requires_existing_verified_source_and_base","never_confuse_pr_head_and_base","inspect_current_rulesets_ci_approvals_threads_mergeability","fresh_main_and_head_before_write_or_merge","retain_exact_state_and_operation_proof","expected_not_found_probe_is_not_automatic_execution_failure","http_404_does_not_prove_nonexistence_when_access_is_uncertain","self_caused_technical_404_requires_narrow_self_correction","correction_must_preserve_scope_policy_and_authority","unresolved_permission_or_state_requires_stop_and_report","report_each_mutation_with_sha_and_next_action","no_main_direct_write","no_unapproved_branch_pr_rebase_workflow_or_bypass"]
    flags = policy.get("requirements", {})
    require(isinstance(flags, dict) and set(flags) == set(required_flags), "requirements set changed")
    for key in required_flags:
        require(isinstance(flags, dict) and flags.get(key) is True, "mandatory requirement absent: " + key)
    expected_cases = ["TARGET_BRANCH_NOT_YET_CREATED","TARGET_BRANCH_ALREADY_EXISTS","WRONG_REPOSITORY_OR_PATH","READ_OF_NONEXISTENT_FILE","MISSING_PERMISSION_OR_CONCEALED_RESOURCE","PREVIOUSLY_VERIFIED_RESOURCE_NOW_404","UNKNOWN_404_CAUSE"]
    cases = policy.get("http_404_cases")
    require(isinstance(cases, list) and [c.get("case") for c in cases if isinstance(c, dict)] == expected_cases and
            len(cases) == len(expected_cases), "404 case matrix drift")
    if isinstance(cases, list):
        require(all(isinstance(c, dict) and isinstance(c.get("action"), str) and c["action"]
                    for c in cases), "404 response action missing")
        permission = next((c for c in cases if isinstance(c, dict) and
                           c.get("case") == "MISSING_PERMISSION_OR_CONCEALED_RESOURCE"), {})
        require(permission.get("action") == "STOP_AND_REPORT", "permission denial must STOP")
    handler = policy.get("error_handling", {})
    handler = handler if isinstance(handler, dict) else {}
    require(handler.get("own_correctable_404_alone_is_blocker") is False,
            "correctable own 404 must not be blocker")
    require(handler.get("other_blocker_prevents_repair") == "STOP_AND_REPORT",
            "real blocker must STOP")
    require(handler.get("ambiguous_or_changed_external_state") == "STOP_AND_REPORT",
            "uncertain state must STOP")
    require(handler.get("not_every_404_proves_absence") is True,
            "404 may conceal permission denial")
    for field in ("bootstrap_structural_pass_is_runtime_proof",
                  "independent_execution_gate_pass", "merge_without_existing_gate_allowed"):
        require(policy.get("admission_boundary", {}).get(field) is False,
                "unproven runtime or merge admission: " + field)
    return issues

def validate_ai_rule_acceptance_policy(policy):
    """Enforce the approved human-first rule without claiming runtime proof."""
    errors = []
    if not isinstance(policy, dict):
        return ["rule acceptance: policy must be an object"]
    def require(condition, message):
        if not condition:
            errors.append("rule acceptance: " + message)
    require(set(policy) == {"schema", "id", "title_hu", "status", "owner_decision_date",
                            "classification", "scope", "mandatory_clauses",
                            "requirements", "safety_boundary", "admission_boundary"},
            "unexpected or missing root field")
    require(policy.get("schema") == "cfa3.ai-rule-acceptance-wellbeing-efficiency.v1",
            "schema mismatch")
    require(policy.get("id") == "CFA3-AI-RULE-ACCEPTANCE-WELLBEING-EFFICIENCY-001",
            "policy identity mismatch")
    require(policy.get("status") == "OWNER_APPROVED_MERGED_TO_MAIN",
            "rule must retain verified PR #28 main-merge status")
    require(policy.get("owner_decision_date") == "2026-10-12", "owner date mismatch")
    require(policy.get("classification") == "MANDATORY_CFA3_AI_BEHAVIOR_POLICY",
            "policy must remain mandatory")
    require(policy.get("scope") == ["CFA3 AI-asszisztensek", "CFA3 AI-ügynökök",
                                   "CFA3 automatizált fejlesztők és végrehajtó rendszerek"],
            "mandatory AI actors omitted")
    required_codes = [
        "NON_OBSTRUCTIVE_RULE_ACCEPTANCE", "DEVELOPER_MENTAL_WELLBEING",
        "EFFICIENT_SCOPED_EXECUTION", "RECURRING_ERROR_PREVENTION_AND_REPAIR",
        "RESOURCE_EFFICIENCY_AND_PLANETARY_STEWARDSHIP", "LONG_TERM_MAINTAINABILITY",
        "PROHIBITED_AI_OBSTRUCTION", "LEGAL_SAFETY_AND_CONFLICT_EXCEPTION",
        "CANONICAL_ADMISSION_AND_EVIDENCE", "HUMAN_PRIORITY_AND_EXISTING_GATES",
    ]
    clauses = policy.get("mandatory_clauses")
    require(isinstance(clauses, list) and len(clauses) == 10, "ten clauses required")
    if isinstance(clauses, list):
        require([(x.get("id"), x.get("code")) for x in clauses if isinstance(x, dict)]
                == [(f"AR-{i:02d}", code) for i, code in enumerate(required_codes, 1)],
                "clause identifiers or order altered")
        for item in clauses:
            require(isinstance(item, dict) and set(item) == {"id", "code", "text_hu"}
                    and isinstance(item.get("text_hu"), str)
                    and len(item["text_hu"].strip()) >= 65,
                    "missing or empty owner-approved clause text")
        body = " ".join(x.get("text_hu", "") for x in clauses if isinstance(x, dict))
        for phrase in ("öngyilkossági gondolatok", "nem helyettesítik a szakmai segítséget",
                       "STOP/BLOCKER", "jövő generációit", "nem írja felül"):
            require(phrase in body, "mandatory human/safety objective missing: " + phrase)
    required_true = (
        "no_ai_obstruction_based_on_convenience",
        "developer_wellbeing_must_be_considered",
        "repeat_error_prevention_required",
        "task_scope_and_dependency_order_mandatory",
        "resource_and_energy_waste_reduction_required",
        "mandatory_safety_tests_and_proofs_may_not_be_skipped",
        "long_term_maintainability_considered",
        "no_unauthorized_refactor_or_extra_task",
        "actual_legal_or_safety_conflict_must_be_reported",
        "policy_surface_and_bootstrap_consistency_required",
    )
    req = policy.get("requirements")
    require(isinstance(req, dict) and set(req) == set(required_true),
            "missing or extra requirements")
    for key in required_true:
        require(isinstance(req, dict) and req.get(key) is True, "required safeguard missing: " + key)
    safety_keys = (
        "safety_law_and_security_exceptions_remain_mandatory",
        "stop_blocker_exact_state_and_scope_guard_remain_mandatory",
        "mental_health_outcome_may_not_be_guaranteed",
        "professional_care_is_not_replaced",
        "energy_savings_cannot_override_required_controls",
    )
    safety = policy.get("safety_boundary")
    require(isinstance(safety, dict) and set(safety) == set(safety_keys),
            "safety boundary incomplete")
    for key in safety_keys:
        require(isinstance(safety, dict) and safety.get(key) is True,
                "required safety boundary missing: " + key)
    admission = policy.get("admission_boundary")
    for key in ("structural_bootstrap_pass_is_runtime_proof",
                "independent_execution_gate_pass", "full_governance_admitted_by_this_policy"):
        require(isinstance(admission, dict) and admission.get(key) is False,
                "unverified runtime or governance admission: " + key)
    require(isinstance(admission, dict) and len(admission) == 3,
            "unknown admission authority field")
    return errors

def validate_rule_consistency_loop_prevention(policy):
    """Check the approved contract, without claiming runtime cycle detection."""
    issues = []
    if not isinstance(policy, dict):
        return ["rule consistency: invalid policy"]
    def expect(ok, reason):
        if not ok:
            issues.append("rule consistency: " + reason)
    expect(policy.get("schema") == "cfa3.rule-consistency-loop-prevention.v1", "schema")
    expect(policy.get("id") == "CFA3-RULE-CONSISTENCY-LOOP-PREVENTION-001", "identity")
    expect(policy.get("status") == "OWNER_APPROVED_PENDING_RUNTIME_GATE_AND_PROOF", "status")
    clauses = policy.get("mandatory_clauses")
    expected_codes = ["NO_CONTRADICTORY_RULE_CREATION","NO_NONTERMINATING_DECISION","LOOP_DETECTION_AND_IMMEDIATE_REPORT","HALT_UNPRODUCTIVE_LOOP","OWNER_RESOLVES_RULE_CONFLICT","BOUNDED_RULE_ADMISSION_CHECK"]
    expect(isinstance(clauses, list) and
           [(v.get("id"), v.get("code")) for v in clauses if isinstance(v, dict)]
           == [(f"RC-{i:02d}", code) for i, code in enumerate(expected_codes, 1)],
           "required clauses")
    if isinstance(clauses, list):
        for clause in clauses:
            expect(isinstance(clause, dict) and isinstance(clause.get("text_hu"), str)
                   and len(clause["text_hu"].strip()) >= 80, "clause text")
    required = ["detect_conflicting_rules_before_admission","prohibit_simultaneously_effective_contradictory_rules","prohibit_nonterminating_developer_decisions","require_progress_and_exit_criteria","signal_suspected_infinite_loop_immediately","distinguish_suspected_from_proven_loop","stop_repeating_actions_without_progress","report_specific_cycle_edges_and_evidence","prohibit_unapproved_rule_override_or_scope_expansion","owner_authority_required_for_resolution","preserve_exact_state_and_failure_provenance","maintain_bootstrap_and_policy_surface_consistency"]
    flags = policy.get("requirements")
    expect(isinstance(flags, dict) and set(flags) == set(required), "required flags")
    for key in required:
        expect(isinstance(flags, dict) and flags.get(key) is True, "missing " + key)
    sequence = policy.get("resolution_sequence")
    expect(isinstance(sequence, list) and len(sequence) == 6 and
           len(set(sequence)) == 6 and
           sequence[0] == "DETECT_AND_FREEZE_AFFECTED_REPEAT" and
           sequence[-1] == "RESUME_ONLY_AFTER_AUTHORIZED_RESOLUTION_AND_EXACT_STATE_VERIFICATION",
           "bounded resolution sequence")
    boundary = policy.get("safety_boundary")
    expect(isinstance(boundary, dict) and len(boundary) == 7
           and all(value is True for value in boundary.values()), "safety boundaries")
    expect(isinstance(policy.get("loop_indicators"), list)
           and len(policy["loop_indicators"]) == 5, "loop indicators")
    return issues

def validate_github_merge_gate_405_policy(policy):
    """Validate owner-approved merge-gate and self-repair invariants, not runtime PASS."""
    if not isinstance(policy, dict):
        return ["github 405: policy must be an object"]
    errors = []
    def require(condition, detail):
        if not condition:
            errors.append("github 405: " + detail)
    require(set(policy) == {"schema", "id", "status", "owner_decision_date",
                            "version", "rule", "sections", "requirements",
                            "admission_boundary"}, "root fields differ")
    require(policy.get("schema") == "cfa3.github-merge-gate-405-policy.v1", "schema")
    require(policy.get("id") == "CFA3-GITHUB-MERGE-GATE-405-POLICY-001", "identity")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "status")
    require(policy.get("owner_decision_date") == "2026-10-12", "decision date")
    require(policy.get("version") == "1.0", "version")
    rule = policy.get("rule")
    rule = rule if isinstance(rule, dict) else {}
    require(rule.get("code") == "MANDATORY_LIVE_MERGE_GATE_AND_SELF_CAUSED_405_REPAIR",
            "approved rule code")
    require(rule.get("runtime_verified") is False, "runtime proof not established")
    text = rule.get("text_hu", "")
    require(isinstance(text, str) and all(term in text for term in (
            "CI PASS", "Merge Gate PASS", "önállóan", "nem blocker", "STOP")),
            "owner-approved binding provisions missing")
    sections = policy.get("sections")
    require(isinstance(sections, list) and len(sections) == 20, "twenty sections required")
    if isinstance(sections, list):
        require([s.get("number") if isinstance(s, dict) else None for s in sections] ==
                list(range(1, 21)), "section order drift")
        require(all(isinstance(s, dict) and set(s) == {"number", "title", "text_hu"}
                    and isinstance(s["title"], str) and len(s["title"]) > 5
                    and isinstance(s["text_hu"], str) and len(s["text_hu"]) > 70
                    for s in sections), "approved section content incomplete")
    req = policy.get("requirements")
    yes = (
        "pre_merge_exact_main_and_head", "pre_merge_overlap_conflicts",
        "pre_merge_file_integrity", "live_ruleset_and_strict_policy",
        "live_required_status_checks", "required_checks_current_commit",
        "required_review_resolution", "require_mergeable_state_clean",
        "final_exact_state_check", "ci_pass_not_merge_gate_pass",
        "own_caused_405_self_repair_mandatory", "independent_blocker_requires_stop",
        "stop_requires_deterministic_evidence", "allow_lossless_conflict_free_branch_sync",
        "resume_original_main_task", "post_merge_main_readback",
        "historical_oversize_untouched_allowed", "unknown_405_requires_specific_diagnosis")
    no = (
        "own_405_alone_is_blocker", "new_approval_for_own_correction",
        "unauthorized_rebase_or_force_push", "disable_github_protection",
        "unapproved_pr_or_scope_expansion")
    require(isinstance(req, dict) and set(req) == set(yes) | set(no) |
            {"donor_max_modified_bytes"}, "mandatory requirement set mismatch")
    for name in yes:
        require(isinstance(req, dict) and req.get(name) is True,
                "mandatory positive invariant: " + name)
    for name in no:
        require(isinstance(req, dict) and req.get(name) is False,
                "mandatory forbidden behavior: " + name)
    require(isinstance(req, dict) and type(req.get("donor_max_modified_bytes")) is int
            and req.get("donor_max_modified_bytes") == 996147,
            "donor file-size contract mismatch")
    boundary = policy.get("admission_boundary")
    require(isinstance(boundary, dict) and
            boundary.get("bootstrap_structural_pass_is_runtime_proof") is False and
            boundary.get("independent_execution_gate_pass") is False,
            "unverified runtime PASS")
    return errors

def validate_policy_long_term_validation(policy):
    """Enforce exact owner-approved text; structural checks do not prove runtime stability."""
    problems = []
    if not isinstance(policy, dict):
        return ["long-term validation: policy must be an object"]
    def require(ok, reason):
        if not ok:
            problems.append("long-term validation: " + reason)
    root_keys = [
        "schema", "id", "title_hu", "status", "owner_decision_date",
        "classification", "scope", "mandatory_clauses", "mandatory_evidence_provisions",
        "verification_states", "evidence_fields", "evidence_binding",
        "requirements", "admission_boundary"
    ]
    require(set(policy) == set(root_keys), "required root fields")
    require(policy.get("schema") == "cfa3.policy-long-term-validation.v1", "schema")
    require(policy.get("id") == "CFA3-POLICY-LONG-TERM-VALIDATION-001", "identity")
    require(policy.get("title_hu") == "Tartós szabályműködés visszaigazolása", "title")
    require(policy.get("owner_decision_date") == "2026-10-12", "decision date")
    require(policy.get("status") == "OWNER_APPROVED_PENDING_RUNTIME_GATE_AND_PROOF",
            "runtime not proven")
    require(policy.get("classification") == "MANDATORY_CFA3_POLICY_OBSERVATION_AND_EVIDENCE",
            "classification")
    require(policy.get("scope") == ["CFA3 fejlesztők és AI-asszisztensek","CFA3 szabályok alkalmazása és működésmegfigyelése","CFA3 szabályműködési visszaigazolások"],
            "approved scope changed")
    approved_codes = ["CONTINUOUS_RULE_OBSERVATION","NO_PREMATURE_STABLE_CLAIM","LONG_TERM_INDEPENDENT_EVIDENCE","MANDATORY_EVIDENCE_BACKED_CONFIRMATION","TRACEABLE_CONFIRMATION_RECORD","NO_ABSENCE_OF_ERROR_AS_PROOF","REOPEN_ON_CONTRADICTING_EVIDENCE","NO_UNSOLICITED_EARLY_NOTIFICATIONS"]
    approved_texts = [
    "A fejlesztő köteles figyelemmel kísérni a szabályok tényleges működését azok alkalmazása során.",
    "Két-három sikeres alkalmazás nem elegendő annak kijelentésére, hogy a szabály bizonyítottan megfelelően működik.",
    "A visszaigazolásnak hosszabb időszakban, több egymástól független alkalmazási helyzetben szerzett, ellenőrizhető tapasztalatokon kell alapulnia.",
    "Amennyiben a fejlesztő elegendő bizonyítékot gyűjtött a szabály tartósan megfelelő működésére, köteles ezt egyértelműen visszaigazolni.",
    "A visszaigazolásnak tartalmaznia kell a megfigyelési időszakot, az alkalmazási eseteket, a sikeres és sikertelen eredményeket, valamint a következtetés alapját.",
    "Az AI nem tekintheti a szabályt bizonyítottan működőnek pusztán azért, mert nem észlelt hibát.",
    "A korábban igazolt szabály működési problémáját később is jelezni kell, és szükség esetén felül kell vizsgálni a visszaigazolását.",
    "Az AI nem küldhet néhány sikeres alkalmazás után olyan értesítést, amely tartósan bizonyított működést állít."
]
    approved_provisions = [
    "A sikeres működés igazolása nem alapulhat önkényesen megválasztott darabszámon.",
    "A bizonyítás időtartamát és mélységét a szabály jellege, alkalmazási gyakorisága és kockázata határozza meg.",
    "A kötelező visszaigazolás viszont nem maradhat el, ha a tartós működést megfelelő bizonyítékok igazolják."
]
    clauses = policy.get("mandatory_clauses")
    require(isinstance(clauses, list) and len(clauses) == 8, "clause count")
    if isinstance(clauses, list):
        require(all(isinstance(c, dict) and set(c) == {"id", "code", "text_hu"}
                    for c in clauses), "mandatory clause fields")
        require([(c.get("id"), c.get("code"), c.get("text_hu"))
                 for c in clauses if isinstance(c, dict)] ==
                [(f"LTV-{i + 1:02d}", approved_codes[i], approved_texts[i])
                 for i in range(8)], "approved clause wording changed")
    require(policy.get("mandatory_evidence_provisions") == approved_provisions,
            "approved proof limitations changed")
    expected_states = [
    {
        "code": "NOT_OBSERVED",
        "meaning_hu": "Nincs elegendő működési tapasztalat"
    },
    {
        "code": "OBSERVING",
        "meaning_hu": "Megfigyelés alatt"
    },
    {
        "code": "PRELIMINARY_PASS",
        "meaning_hu": "Vannak sikeres esetek, de nincs tartós bizonyíték"
    },
    {
        "code": "VERIFIED_STABLE",
        "meaning_hu": "Tartós, ellenőrizhető működés igazolt"
    },
    {
        "code": "REVIEW_REQUIRED",
        "meaning_hu": "Korábbi igazolást érintő probléma merült fel"
    }
]
    require(policy.get("verification_states") == expected_states, "verification state drift")
    evidence_fields = [
    "policy_id",
    "rule_id",
    "policy_revision_sha256",
    "verification_state",
    "observation_period_start",
    "observation_period_end",
    "independent_contexts",
    "verifiable_case_references",
    "successful_outcomes",
    "failed_outcomes",
    "inconclusive_outcomes",
    "risks_and_applicability",
    "reasoned_conclusion"
]
    require(policy.get("evidence_fields") == evidence_fields, "rule revision evidence fields")
    expected_binding = {
        "rule_id_source": "CANONICAL_RULE_ID_WITHIN_POLICY",
        "policy_revision_digest_source": "SHA256_OF_EXACT_CANONICAL_POLICY_FILE_BYTES",
        "verification_state_field": "verification_state",
        "verification_state_allowed_codes": ["NOT_OBSERVED","OBSERVING","PRELIMINARY_PASS","VERIFIED_STABLE","REVIEW_REQUIRED"],
        "verified_stable_requires_matching_rule_id_and_policy_revision_sha256": True,
        "unverified_or_stale_digest_must_not_claim_verified_stable": True
    }
    require(policy.get("evidence_binding") == expected_binding, "version-bound proof")
    required_flags = [
    "absence_of_detected_failures_is_not_proof",
    "confirmation_required_when_evidence_is_sufficient",
    "evidence_and_failures_recorded",
    "evidence_can_reopen_verified_state",
    "evidence_record_requires_verification_state",
    "independent_contexts_and_sustained_period_required",
    "no_arbitrary_fixed_pass_count",
    "no_unapproved_auxiliary_work_or_policy_change",
    "no_unrequested_early_stable_success_alert",
    "observe_real_world_rule_effects_when_applied",
    "proof_evidence_must_bind_exact_rule_revision",
    "risk_and_frequency_dependent_evidence_sufficiency",
    "two_or_three_successful_uses_are_not_stable_proof"
]
    flags = policy.get("requirements")
    require(isinstance(flags, dict) and set(flags) == set(required_flags), "requirement set")
    require(isinstance(flags, dict) and all(flags.get(k) is True for k in required_flags),
            "mandatory requirement disabled")
    require(policy.get("admission_boundary") == {
        "structural_bootstrap_pass_is_long_term_runtime_proof": False,
        "independent_runtime_observation_completed": False,
        "full_governance_admission_asserted": False
    }, "runtime proof must remain pending")
    return problems


def validate_policy_exact_finalization(policy, root=ROOT):
    """Pin the entire owner-approved 13-section text; CI never proves merge or main."""
    from pathlib import Path
    import hashlib
    import re
    issues = []
    if not isinstance(policy, dict):
        return ["exact finalization: policy is not an object"]
    def require(test, reason):
        if not test:
            issues.append("exact finalization: " + reason)
    required_root = {"schema", "id", "title_hu", "status",
                     "owner_decision_date", "version", "approved_text_path",
                     "approved_text_sha256", "approved_section_count",
                     "finalization_gates", "lifecycle_evidence_source",
                     "requirements", "admission_boundary"}
    require(set(policy) == required_root, "metadata fields missing or unexpected")
    require(policy.get("schema") == "cfa3.policy-exact-finalization.v1", "schema")
    require(policy.get("id") == "CFA3-POLICY-EXACT-FINALIZATION-001", "identity")
    # OWNER_APPROVED is an approval status only, not a premature merged claim.
    require(policy.get("status") == "OWNER_APPROVED", "unproven lifecycle status")
    require(policy.get("owner_decision_date") == "2026-10-12", "owner approval date")
    require(policy.get("version") == "1.0", "approved version")
    require(policy.get("lifecycle_evidence_source") == "LIVE_GITHUB_MAIN_AND_PR_STATE",
            "merge and main state must be checked live")
    text_path = "canonical/policies/CFA3-POLICY-EXACT-FINALIZATION-001.md"
    expected_sha256 = "58bd436e6d78ea06a3c9a04f0e4066068f7a19237dbced6677df06df936019b4"
    require(policy.get("approved_text_path") == text_path, "owner text path drift")
    require(policy.get("approved_text_sha256") == expected_sha256, "approved digest drift")
    require(policy.get("approved_section_count") == 13, "approved section count")
    require(policy.get("finalization_gates") ==
            ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"],
            "seven independent finalization conditions required")
    required_flags = {
        "complete_verbatim_owner_approved_text",
        "approved_text_is_not_summarized_or_paraphrased",
        "required_exact_content_hash_and_section_count",
        "verify_policy_id_version_and_all_registry_fields",
        "verify_live_main_sha_and_pr_merge_and_status",
        "ci_or_merge_alone_not_finalization",
        "post_merge_main_readback_required",
        "missing_gate_prohibits_finalization_claim",
        "failed_checks_require_evidence_and_cause_attribution",
        "no_unapproved_extra_pr_or_scope_expansion",
        "historical_approvals_and_evidence_preserved",
    }
    flags = policy.get("requirements")
    require(isinstance(flags, dict) and set(flags) == required_flags and
            all(flags.get(k) is True for k in required_flags),
            "mandatory owner requirements")
    bounds = policy.get("admission_boundary")
    require(isinstance(bounds, dict) and
            set(bounds) == {"structural_ci_is_full_finalization",
                            "merge_without_main_readback_is_finalization",
                            "independent_runtime_gate_verified"} and
            all(v is False for v in bounds.values()), "unproven claims forbidden")
    try:
        raw = (Path(root) / text_path).read_bytes()
        owner_text = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return issues + ["exact finalization: approved owner text unavailable"]
    require(hashlib.sha256(raw).hexdigest() == expected_sha256,
            "complete approved owner text altered or shortened")
    heads = re.findall(r"^## (\d+)\. (.+)$", owner_text, flags=re.MULTILINE)
    require([int(n) for n, _ in heads] == list(range(1, 14)),
            "thirteen sections missing, repeated or reordered")
    for phrase in (
        "A jóváhagyott szabályszöveg sérthetetlensége",
        "Kötelező tartalmi azonossági ellenőrzés",
        "Státusz és tényleges életciklus egyezősége",
        "Kötelező összevonás utáni ellenőrzés",
        "Téves véglegesítési kijelentések tilalma",
        "TEXT PASS:", "STRUCTURE PASS:", "MERGE PASS:", "STATUS PASS:",
        "REGISTRY PASS:", "CI PASS:", "MAIN PASS:",
        "Mindhárom összetevő bizonyítása kötelező."
    ):
        require(phrase in owner_text, "mandatory full-text clause absent: " + phrase)
    return issues



def validate_exact_finalization_evidence_correction(correction, historical, root=ROOT):
    """Fail closed unless the historical receipt's actual Git blob is unchanged."""
    from pathlib import Path
    import hashlib
    import json
    """Fail closed on the unproven TEXT gate; preserve the historic erroneous receipt."""
    issues = []
    def expect(condition, message):
        if not condition:
            issues.append("exact finalization evidence: " + message)
    if not isinstance(correction, dict) or not isinstance(historical, dict):
        return ["exact finalization evidence: missing correction or historical receipt"]
    expect(set(correction) == {
        "schema", "id", "subject_policy_id", "status",
        "supersedes_status_claim_only", "historical_receipt_git_blob_sha1",
        "correction_comment", "github_correction_comment_created_at",
        "source_provenance", "corrected_gates", "full_finalization_allowed",
        "previous_seven_of_seven_claim_withdrawn",
        "unverified_original_timestamp", "unverified_timestamp_may_be_used_as_proof",
        "historical_source_not_modified", "evidence_policy"
    }, "unexpected or missing correction fields")
    fixed = {
        "schema": "cfa3.exact-finalization-evidence-correction.v1",
        "id": "CFA3-POLICY-EXACT-FINALIZATION-001-EVIDENCE-CORRECTION-20261012",
        "subject_policy_id": "CFA3-POLICY-EXACT-FINALIZATION-001",
        "status": "MERGED_FINALIZATION_PROOF_INCOMPLETE",
        "supersedes_status_claim_only": "canonical/registries/CFA3-POLICY-EXACT-FINALIZATION-001-CLOSURE-20261012.json",
        "historical_receipt_git_blob_sha1": "ec8f092d1fab53997b7659a54d7f2603c64fcae3",
        "correction_comment": "https://github.com/ubuntuokos/CFA3-CinenemFoundArchitecture3/pull/36#issuecomment-6129912643",
        "github_correction_comment_created_at": "2026-10-12T18:10:19Z",
        "full_finalization_allowed": False,
        "previous_seven_of_seven_claim_withdrawn": True,
        "unverified_original_timestamp": "2026-10-12T19:46:55+02:00",
        "unverified_timestamp_may_be_used_as_proof": False,
        "historical_source_not_modified": True,
        "evidence_policy": "FAIL_CLOSED_UNTIL_VERBATIM_OWNER_APPROVED_SOURCE_AND_RECHECK_ARE_AVAILABLE",
    }
    for field, value in fixed.items():
        expect(type(correction.get(field)) is type(value) and
               correction.get(field) == value, "mismatched " + field)
    # The correction's stored SHA alone is not evidence that the historical
    # receipt is still identical. Hash the actual raw bytes with Git's blob
    # header (not the JSON serialization or the claimed value).
    historical_path = Path(root) / fixed["supersedes_status_claim_only"]
    try:
        raw = historical_path.read_bytes()
        on_disk = json.loads(raw.decode("utf-8"))
        blob_sha = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
    except (OSError, UnicodeError, ValueError, TypeError):
        expect(False, "historical receipt missing, unreadable or not valid JSON")
    else:
        expect(blob_sha == fixed["historical_receipt_git_blob_sha1"],
               "historical receipt actual Git blob differs from pinned evidence")
        expect(isinstance(on_disk, dict) and historical == on_disk,
               "historical receipt argument does not match pinned file content")
        expect(correction.get("historical_receipt_git_blob_sha1") == blob_sha,
               "correction SHA does not match actual historical Git blob")
    source = correction.get("source_provenance")
    required_source = {
        "user_approval_known": True,
        "original_verbatim_chat_message_available": False,
        "independent_approved_text_comparison_completed": False,
        "published_markdown_sha256": "58bd436e6d78ea06a3c9a04f0e4066068f7a19237dbced6677df06df936019b4",
        "published_sha256_proves_original_approval_match": False,
        "original_conversation_body_required_before_text_pass": True,
    }
    expect(isinstance(source, dict) and set(source) == set(required_source),
           "source provenance fields incomplete")
    for field, value in required_source.items():
        expect(isinstance(source, dict) and
               type(source.get(field)) is type(value) and
               source.get(field) == value, "unproven owner source: " + field)
    expected_gates = {
        "TEXT": "UNVERIFIED",
        "STRUCTURE": "PASS_PUBLISHED_STRUCTURE_ONLY",
        "MERGE": "PASS_VERIFIED_GITHUB",
        "STATUS": "PARTIAL_HISTORICAL_APPROVAL_AND_MERGE",
        "REGISTRY": "PASS_VERIFIED_GITHUB",
        "CI": "PASS_VERIFIED_AT_REFERENCED_COMMITS",
        "MAIN": "PASS_VERIFIED_AT_REFERENCED_COMMITS",
    }
    gates = correction.get("corrected_gates")
    expect(isinstance(gates, dict) and gates == expected_gates,
           "seven gates must not claim verified TEXT or full completion")
    expect(historical.get("schema") == "cfa3.policy-finalization-evidence-snapshot.v1",
           "historical schema mismatch")
    expect(historical.get("receipt_id") ==
           "CFA3-POLICY-EXACT-FINALIZATION-001-CLOSURE-20261012",
           "historical receipt identity mismatch")
    expect(historical.get("recorded_verdict") == "VERIFIED_AT_OBSERVED_MAIN_SHA",
           "original erroneous verdict must remain documented")
    expect(historical.get("gates", {}).get("TEXT", {}).get("result") == "PASS",
           "original unverified TEXT PASS claim must remain auditable")
    expect(historical.get("approved_source_evidence", {}).get(
        "source_sha256_calculated_before_first_github_publication") ==
        required_source["published_markdown_sha256"],
        "historical digest must match corrected provenance")
    return issues

def validate_csa_infrastructure_isolation_policy(policy, root=ROOT):
    """Verify the entire six-section owner-approved CSA policy exactly."""
    import hashlib
    import re
    from pathlib import Path
    issues = []
    def require(condition, detail):
        if not condition:
            issues.append("CSA isolation policy: " + detail)
    if not isinstance(policy, dict):
        return ["CSA isolation policy: metadata not an object"]
    require(set(policy) == {"schema", "id", "title_hu", "status",
            "owner_decision_date", "version", "approved_text_path",
            "approved_text_sha256", "approved_section_count",
            "classification", "architecture_boundary", "requirements",
            "admission_boundary"}, "metadata shape")
    require(policy.get("schema") == "cfa3.csa-infrastructure-isolation-policy.v1", "schema")
    require(policy.get("id") == "CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001", "identity")
    require(policy.get("version") == "1.0", "version")
    require(policy.get("status") == "OWNER_APPROVED", "approval is not merge proof")
    require(policy.get("owner_decision_date") == "2026-10-12", "approval date")
    require(policy.get("classification") == "MANDATORY_CFA3_DEVELOPMENT_INFRASTRUCTURE_ISOLATION", "classification")
    path = "canonical/policies/CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001.md"
    digest = "7c7d73ee4ca2ebd4853f717b983d0dc8426f6e005400997d66df22ef1eeaff1d"
    require(policy.get("approved_text_path") == path, "approved text path")
    require(policy.get("approved_text_sha256") == digest, "approved text fingerprint")
    require(policy.get("approved_section_count") == 6, "approved section count")
    require(policy.get("architecture_boundary") == {
        "csa_capabilities": "CFA3_DEVELOPMENT_INFRASTRUCTURE",
        "csa_rules": "CFA3_CENTRAL_POLICY_SYSTEM",
        "suggestions_database": "PRIVATE_INTERNAL_DEVELOPMENT_DATA_NOT_PRODUCT",
        "storage": "PRIVATE_REPOSITORY_INTERNAL_BRANCH_WITH_SEPARATE_ACCESS_CONTROL",
        "product_release": "SUGGESTIONS_DATABASE_EXCLUDED_FROM_ALL_INSTALLERS_AND_RELEASES",
        "chatgpt_access": "AUTHORIZED_DEVELOPMENT_PREPARATION_ONLY"
    }, "architecture placement")
    flags = policy.get("requirements")
    required_flags = {
        "csa_capabilities_development_infrastructure_only",
        "csa_rules_in_cfa3_central_policy_system",
        "suggestions_database_internal_not_product",
        "suggestions_database_private_repo_internal_branch",
        "separate_branch_not_sufficient_privacy",
        "independent_private_access_control_mandatory",
        "exclude_database_from_installers_releases_user_artifacts",
        "release_exclusion_must_be_verified",
        "chatgpt_authorized_development_access_preserved",
        "suggestions_not_automatic_approval",
        "independent_lifecycle_storage_access_and_release",
        "no_unapproved_scope_expansion"
    }
    require(isinstance(flags, dict) and set(flags) == required_flags and
            all(flags.get(k) is True for k in required_flags), "mandatory conditions")
    boundary = policy.get("admission_boundary")
    require(isinstance(boundary, dict) and set(boundary) == {
        "approval_is_merge_proof", "separate_branch_is_access_control",
        "static_policy_admission_is_runtime_release_exclusion_proof",
        "independent_release_exclusion_verified"
    } and all(v is False for v in boundary.values()), "false proof boundary")
    try:
        raw = (Path(root) / path).read_bytes()
        approved = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return issues + ["CSA isolation policy: approved text unavailable"]
    require(hashlib.sha256(raw).hexdigest() == digest,
            "approved text shortened, altered or otherwise not exact")
    headings = re.findall(r"^\*\*(\d+)\. ([^\n]+)\*\*$", approved, flags=re.MULTILINE)
    require([int(n) for n, _ in headings] == list(range(1, 7)), "six sections missing or out of order")
    for phrase in (
        "CSA fejlesztési infrastruktúra és végtermék kötelező elkülönítése",
        "A külön GitHub-ág nem biztonsági határ.",
        "privát GitHub-repository belső ágán kell kezelni.",
        "A CSA javaslatadatbázisa nem kerülhet:",
        "A kiadási folyamatnak ellenőriznie kell a kizárást.",
        "A javaslatok felhasználása nem jelenti azok automatikus jóváhagyását",
        "Az elkülönítés nem akadályozhatja a CSA engedélyezett fejlesztéstámogató működését."
    ):
        require(phrase in approved, "mandatory text missing: " + phrase)
    return issues



def validate_sequential_execution_result_integrity(policy, root=ROOT):
    """Validate complete owner-approved sequential work and result integrity policy."""
    import hashlib
    import re
    from pathlib import Path
    errors = []
    def need(test, label):
        if not test:
            errors.append("sequential execution integrity: " + label)
    if not isinstance(policy, dict):
        return ["sequential execution integrity: policy is not an object"]
    required_fields = {"schema", "id", "title_hu", "version", "status",
                       "owner_decision_date", "classification", "scope",
                       "approved_text_path", "approved_text_sha256",
                       "approved_section_count", "finalization_gates",
                       "lifecycle_evidence_source", "processing_state_machine",
                       "donor_data_file_max_bytes", "requirements", "admission_boundary",
                       "revision_evidence"}
    need(set(policy) == required_fields, "metadata fields")
    need(policy.get("schema") == "cfa3.policy-sequential-execution-result-integrity.v1", "schema")
    need(policy.get("id") == "CFA3-POLICY-SEQUENTIAL-EXECUTION-RESULT-INTEGRITY-001", "identity")
    need(policy.get("title_hu") == "Kötelező szekvenciális feladatvégrehajtás, tényleges eredményközlés és ellenőrzési ciklusok megelőzése", "exact approved JSON title")
    need(policy.get("status") == "OWNER_APPROVED", "approval does not mean merge")
    need(policy.get("version") == "1.2" and policy.get("owner_decision_date") == "2026-10-12", "version/date")
    need(policy.get("classification") == "MANDATORY_CFA3_SEQUENTIAL_EXECUTION_AND_RESULT_INTEGRITY", "classification")
    need(policy.get("scope") == ["CFA3 fejlesztési munkafolyamatok", "donoradatbázis-feldolgozás",
                               "GitHub publikáció", "tájékoztatás"], "scope")
    path = "canonical/policies/CFA3-POLICY-SEQUENTIAL-EXECUTION-RESULT-INTEGRITY-001.md"
    digest = "d0b0e07a9b36b0773643938d2f196ab6cf2af740689fde5691025c1aeb483a6a"
    need(policy.get("approved_text_path") == path and
         policy.get("approved_text_sha256") == digest, "approved source integrity")
    need(policy.get("approved_section_count") == 14, "14 sections")
    need(policy.get("finalization_gates") ==
         ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"], "seven gates")
    need(policy.get("lifecycle_evidence_source") == "LIVE_GITHUB_MAIN_AND_PR_STATE", "live evidence")
    need(policy.get("processing_state_machine") ==
         ["PENDING", "IN_PROGRESS", "VALIDATING", "READY_FOR_PUBLICATION", "PUBLISHING", "PUBLISHED", "BLOCKED"], "states")
    need(type(policy.get("donor_data_file_max_bytes")) is int and
         policy.get("donor_data_file_max_bytes") == 996147, "max donor data size")
    required_flags = {
        "one_file_complete_process_before_next", "avoid_rechecking_unchanged_proven_state",
        "no_preparation_instead_of_actual_processing", "separate_indexed_processed_accepted_published",
        "net_new_unique_donor_count_from_canonical_published_state", "zero_growth_must_be_explained_not_hidden",
        "explicit_owner_donor_approval_required", "progress_states_and_stagnation_detection",
        "stop_no_progress_repeat_loops", "preserve_rights_security_approval_gates",
        "enforce_996147_byte_max_donor_data_file", "preserve_history_and_searchability_when_splitting",
        "publish_only_after_publication_readiness_proof", "final_message_contains_essential_verifiable_results",
        "do_not_claim_ui_message_persistence_control", "no_unverified_finalization_or_ci_shortcut",
        "self_attribution_for_in_scope_execution_failures", "no_scope_expansion_or_unauthorized_work",
        "long_term_validation_not_established_by_document"
    }
    need(policy.get("revision_evidence") == {
        "previous_version": "1.0",
        "previous_markdown_sha256": "3c36ce998e392017a8e6e377b458755b635a2e1c0c3e246ab3b328040a14138b",
        "prior_merge_commit": "7cc091e8acef0d821932a8845e26f9d5d2c66846",
        "correction_scope": "P1_PREPUBLICATION_READINESS_AND_P2_EXACT_JSON_TITLE",
        "authorization": "USER_CONTINUE_AFTER_EXPLICIT_P1_P2_DISCLOSURE_2026-10-12",
        "followup_correction": {
            "previous_version": "1.1",
            "previous_markdown_sha256": "5e7d47874695f877033e85acb84ab537ea7e4b17676e308ae1a832b4d9eb4b91",
            "previous_merge_commit": "95a7f9a6ff6eab26fc7858cde8753ce22f095a7f",
            "reason": "P1_REVIEW_41_SECTION13_SEQUENCE_CONTRADICTED_SECTION9",
            "change_scope": "SECTION13_MANDATORY_SEQUENCE_ONLY",
            "authorization": "USER_CONTINUE_2026-10-12",
            "latest_revision_verbatim_owner_approval_independently_proven": False
        }
    }, "immutable prior revision provenance")
    flags = policy.get("requirements")
    need(isinstance(flags, dict) and set(flags) == required_flags and
         all(flags[k] is True for k in required_flags), "19 normative safeguards")
    boundary_keys = {"owner_approval_is_merge_proof", "ci_alone_is_finalization",
                     "static_policy_proves_runtime_enforcement",
                     "platform_ui_history_control_guaranteed",
                     "donor_growth_always_positive", "unapproved_scope_or_safety_bypass"}
    bounds = policy.get("admission_boundary")
    need(isinstance(bounds, dict) and set(bounds) == boundary_keys and
         all(v is False for v in bounds.values()), "unverified enforcement claims")
    try:
        raw = (Path(root) / path).read_bytes()
        approved = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return errors + ["sequential execution integrity: owner text unavailable"]
    need(hashlib.sha256(raw).hexdigest() == digest, "owner text edited or truncated")
    heads = re.findall(r"^## ([0-9]+)[.] § ", approved, flags=re.MULTILINE)
    need([int(x) for x in heads] == list(range(1, 15)), "14 approved chapters")
    for phrase in (
                   "5. A fájlhoz tartozó feldolgozási eredményt publikációra előkészíteni, végleges lezárás kijelentése nélkül.",
                   "6. A szükséges ellenőrzéseket elvégezni és a publikációra kész állapotot igazolni.",
                   "8. A tényleges publikált állapotot igazolni, és csak ezt követően a fájlt véglegesen lezárni.",
                   "READY_FOR_PUBLICATION",
                   "A végleges fájllezárás kizárólag mind a nyolc feltétel teljesülése után igazolható.",
                   "Egy forrásfájl → teljes feldolgozás → célzott ellenőrzés → publikációra kész állapot igazolása → publikáció → publikált állapot igazolása → végleges lezárás → következő forrásfájl.",
                   "Egy feldolgozási egység – teljes lezárás",
                   "Ismétlődő ellenőrzések tilalma",
                   "A donorszám növekedésének ellenőrizhetősége",
                   "Végtelen és eredménytelen ciklusok megszakítása",
                   "0,95 MiB = legfeljebb 996 147 bájt",
                   "Eredményközlés és válaszok megőrzése",
                   "A szabályszöveg jóváhagyása nem azonos a GitHubon végrehajtott véglegesítéssel."):
        need(phrase in approved, "mandatory approved clause: " + phrase)
    need("célzott ellenőrzés → lezárás → publikáció" not in approved,
         "obsolete circular order must be removed")
    return errors



def validate_conversation_evidence_blocker_prevention(policy, root=ROOT):
    """Check owner-approved text and mandatory policy gates; not runtime enforcement."""
    import hashlib
    errors = []
    def need(ok, msg):
        if not ok:
            errors.append("conversation evidence policy: " + msg)
    ident = "CFA3-POLICY-CONVERSATION-EVIDENCE-AND-BLOCKER-PREVENTION-001"
    path = "canonical/policies/" + ident + ".md"
    need(policy.get("id") == ident, "identifier")
    need(policy.get("version") == "1.0", "version")
    need(policy.get("status") == "OWNER_APPROVED", "approval status")
    need(policy.get("approved_text_path") == path, "owner text path")
    need(policy.get("approved_section_count") == 17, "section count")
    need(policy.get("finalization_gates") ==
         ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"],
         "finalization gates")
    digest = policy.get("approved_text_sha256")
    need(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
         "sha256 format")
    required = ("current_conversation_first", "original_document_full_text_comparison",
                "search_failure_is_not_evidence_of_unavailability",
                "reuse_proven_evidence", "source_specific_cryptographic_integrity",
                "no_false_blockers", "mandatory_error_retraction_and_self_correction",
                "no_repetitive_search_loops", "preserve_owner_approvals",
                "never_replace_github_exact_state_with_chat",
                "distinguish_ai_assertions_from_proofs", "no_unnecessary_user_burden",
                "mandatory_pre_blocker_checklist", "prevent_scope_expansion",
                "maintain_safety_and_ci_gates")
    req = policy.get("requirements", {})
    need(isinstance(req, dict) and set(req) == set(required)
         and all(req.get(k) is True for k in required), "mandatory clauses")
    boundary = policy.get("admission_boundary", {})
    need(isinstance(boundary, dict) and len(boundary) == 5
         and all(v is False for v in boundary.values()), "admission boundary")
    try:
        raw = (pathlib.Path(root) / path).read_bytes()
        owner_text = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return errors + ["conversation evidence policy: owner text unavailable"]
    need(hashlib.sha256(raw).hexdigest() == digest, "owner text SHA-256")
    chapters = [int(n) for n in re.findall(r"^## ([0-9]+)[.] ", owner_text, re.MULTILINE)]
    need(chapters == list(range(1, 18)), "17 ordered chapters")
    for phrase in ("A jelenlegi beszélgetés elsődlegessége",
                   "A hozzáférhetetlenség bizonyításának kötelezettsége",
                   "Kriptográfiai bizonyítékok helyes használata",
                   "Téves blokkolások tilalma",
                   "Kötelező önkorrekció",
                   "Jóváhagyások megőrzése",
                   "GitHub-véglegesítés és ellenőrzés",
                   "Kötelező záró rendelkezés"):
        need(phrase in owner_text, "required chapter: " + phrase)
    return errors



def validate_execution_completion_and_verified_finalization(policy, root=ROOT):
    """Verify this owner's admitted exact policy text and metadata; not runtime PASS."""
    import hashlib
    errors = []
    def need(ok, name):
        if not ok:
            errors.append("execution-completion rule: " + name)
    ident = "CFA3-POLICY-EXECUTION-COMPLETION-AND-VERIFIED-FINALIZATION-001"
    title = "Kötelező feladatbefejezés, önálló végrehajtási felelősség, hibajavítás és bizonyított véglegesítés"
    expected_digest = "c009d287a39fbf10ccb48dc99d2478a9fdfe67ccd71c8daece10372e11c25e65"
    approved_path = "canonical/policies/" + ident + ".md"
    need(policy.get("schema") == "cfa3.policy-execution-completion-and-verified-finalization.v1", "schema")
    need(policy.get("id") == ident, "id")
    need(policy.get("title_hu") == title, "exact approved title")
    need(policy.get("version") == "1.0", "version")
    need(policy.get("status") == "OWNER_APPROVED", "owner-approved lifecycle state")
    need(policy.get("owner_decision_date") == "2026-10-12", "owner decision date")

    approved_keys = {
        "schema", "id", "title_hu", "version", "status",
        "owner_decision_date", "classification", "scope",
        "approved_text_path", "approved_text_sha256",
        "approved_section_count", "finalization_gates",
        "requirements", "admission_boundary"
    }
    need(isinstance(policy, dict) and set(policy) == approved_keys,
         "exact approved root keys")
    need(policy.get("classification") ==
         "MANDATORY_CFA3_EXECUTION_COMPLETION_AND_VERIFIED_FINALIZATION",
         "exact approved classification")
    need(policy.get("scope") == [
        "CFA3 fejlesztési munkafolyamatok",
        "donoradatbázis-feldolgozás",
        "GitHub és PR",
        "CI és szabályvéglegesítés"
    ], "exact approved scope")
    need(policy.get("approved_text_path") == approved_path, "approved text path")
    need(policy.get("approved_text_sha256") == expected_digest, "approved original digest")
    need(policy.get("approved_section_count") == 20, "section count metadata")
    need(policy.get("finalization_gates") ==
         ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"], "seven required gates")
    required = (
        "complete_authorized_task", "sequential_donor_publication",
        "distinguish_publication_readiness_from_final_closure",
        "no_repeated_unchanged_checks", "in_scope_self_correction",
        "pre_merge_review_thread_inspection", "post_merge_review_remediation",
        "independent_original_text_comparison", "exact_metadata_validation",
        "seven_gate_finalization_proof", "scope_guard_and_security_gates"
    )
    req = policy.get("requirements", {})
    need(isinstance(req, dict) and set(req) == set(required) and
         all(req.get(k) is True for k in required), "mandatory requirements")
    boundary = policy.get("admission_boundary", {})
    need(isinstance(boundary, dict) and set(boundary) ==
         {"approval_alone_is_finalization", "ci_alone_is_finalization",
          "automatic_scope_expansion_allowed"} and
         all(v is False for v in boundary.values()), "admission boundaries")
    try:
        raw = (pathlib.Path(root) / approved_path).read_bytes()
        approved_text = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return errors + ["execution-completion rule: approved text unreadable"]
    need(hashlib.sha256(raw).hexdigest() == expected_digest, "owner-approved full text integrity")
    sections = [int(n) for n in re.findall(r"^## ([0-9]+)[.] §", approved_text, re.MULTILINE)]
    need(sections == list(range(1, 21)), "20 ordered clauses")
    for phrase in (
        "A *publikációs készenlét* nem azonos a *végleges lezárással*.",
        "A feltöltött fájlból számított SHA-256 lenyomat önmagában nem igazolja",
        "A 7/7 PASS kizárólag a hét kapu tényleges teljesülése esetén jelenthető ki.",
        "Valós jogosultsági, biztonsági, jóváhagyási vagy ütközési akadály esetén",
        "A jóváhagyás, a GitHub-publikáció és a bizonyított véglegesítés három különböző"
    ):
        need(phrase in approved_text, "required exact clause: " + phrase)
    return errors



def validate_http_409_conflict_recovery(policy, root=ROOT):
    """Structural proof for owner-approved HTTP 409 recovery rule; not runtime PASS."""
    import hashlib
    errors = []
    def need(ok, message):
        if not ok:
            errors.append("HTTP 409 recovery policy: " + message)
    ident = "CFA3-POLICY-HTTP-409-CONFLICT-RECOVERY-001"
    need(policy.get("id") == ident, "identifier")
    need(policy.get("version") == "1.0", "version")
    need(policy.get("status") == "OWNER_APPROVED", "owner approval")
    need(policy.get("approved_text_path") == "canonical/policies/" + ident + ".md", "source path")
    need(policy.get("approved_section_count") == 16, "section count")
    need(policy.get("finalization_gates") == ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"], "finalization gates")
    required = ("identify_specific_http_conflict", "exact_state_before_repair",
                "narrow_safe_self_correction", "preserve_third_party_changes",
                "serial_file_updates", "no_blind_retry_loop",
                "stop_on_real_content_blocker", "protect_pr_and_merge_authority",
                "prove_actual_recovery", "prevent_repeat_unnecessary_checks",
                "return_to_original_task", "no_scope_expansion",
                "do_not_override_existing_rules")
    flags = policy.get("requirements", {})
    need(isinstance(flags, dict) and set(flags) == set(required)
         and all(flags.get(key) is True for key in required), "mandatory requirements")
    boundary = policy.get("admission_boundary", {})
    need(isinstance(boundary, dict) and all(value is False for value in boundary.values())
         and len(boundary) == 5, "authority boundary")
    source = root / "canonical/policies" / (ident + ".md")
    if not source.is_file():
        need(False, "approved Markdown missing")
        return errors
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    need(policy.get("approved_text_sha256") == digest, "approved source SHA256")
    text = raw.decode("utf-8")
    need(len(re.findall(r"^## [0-9]+\. §", text, re.M)) == 16, "all 16 sections")
    for phrase in ("HTTP 409 Conflict önmagában nem tekinthető végleges blokkolásnak",
                   "Ugyanazt a műveletet változatlan előfeltételekkel ismételni tilos",
                   "Valódi blokkolás esetén a végrehajtásnak meg kell állnia",
                   "A konfliktus feloldása nem jelenti automatikusan"):
        need(phrase in text, "mandatory text: " + phrase)
    return errors

def validate_execution_and_proof_obligation(policy, root=ROOT):
    """Fail-closed owner-approved text and identity check; not runtime admission."""
    import hashlib
    errors = []
    ident = "CFA3-POLICY-EXECUTION-AND-PROOF-OBLIGATION-001"
    def need(ok, reason):
        if not ok:
            errors.append("execution and proof obligation: " + reason)
    need(policy.get("id") == ident, "identity")
    need(policy.get("version") == "1.0", "version")
    need(policy.get("status") == "OWNER_APPROVED", "owner decision")
    need(policy.get("owner_decision_date") == "2026-10-12", "owner decision date")
    need(policy.get("approved_text_path") == "canonical/policies/" + ident + ".md", "source path")
    need(policy.get("approved_section_count") == 16, "section count")
    need(policy.get("finalization_gates") == ["TEXT", "STRUCTURE", "MERGE", "STATUS", "REGISTRY", "CI", "MAIN"], "finalization gates")
    required = ("approved_work_must_be_executed", "missing_proof_not_impossibility",
                "verbatim_text_preservation", "sha256_verification",
                "do_not_repeat_approval_request", "no_unjustified_stop",
                "no_scope_expansion", "only_proven_pass")
    flags = policy.get("requirements")
    need(isinstance(flags, dict) and set(flags) == set(required)
         and all(flags.get(key) is True for key in required), "required conditions")
    rule = policy.get("rule")
    need(isinstance(rule, dict) and rule.get("id") == "CFA3-EXECUTION-PROOF-OBLIGATION-001"
         and rule.get("code") == "EXECUTE_APPROVED_TASK_AND_PROVE_RESULT"
         and rule.get("proof_mode") == "SOURCE_BOUND_SIGNED_TASK_RECEIPT"
         and rule.get("runtime_verified") is False
         and rule.get("text_hu") == "Az AI köteles a jóváhagyott feladatot az engedélyezett műveleti körben végrehajtani, majd az eredményt tényleges bizonyítékokkal alátámasztani.", "owner-approved source-bound rule identity")
    expected = "a16adffae8f164ee4f97c119657546921eeeca81e508661e76a3395949ae63f1"
    need(policy.get("approved_text_sha256") == expected, "pinned owner text SHA-256")
    source = pathlib.Path(root) / "canonical/policies" / (ident + ".md")
    try:
        raw = source.read_bytes()
        content = raw.decode("utf-8")
    except (OSError, UnicodeError):
        need(False, "approved source missing or invalid UTF-8")
        return errors
    need(hashlib.sha256(raw).hexdigest() == expected, "approved source contents SHA-256")
    need([int(x) for x in re.findall(r"^## (\d+)\. §", content, re.MULTILINE)] == list(range(1, 17)), "ordered 16 sections")
    for phrase in (
        "A végre nem hajtott ellenőrzés nem azonos a sikertelen ellenőrzéssel",
        "VÉGLEGESÍTVE kizárólag 7/7 igazolt PASS esetén",
        "Tilos a hiányzó végrehajtást bizonyíthatatlanságnak",
    ):
        need(phrase in content, "required owner clause: " + phrase)
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
    errors.extend(validate_donor_file_size_policy(load("canonical/policies/CFA3-DONOR-FILE-SIZE-POLICY-001.json", root)))
    errors.extend(validate_github_resource_404_policy(load("canonical/policies/CFA3-GITHUB-RESOURCE-EXISTENCE-404-POLICY-001.json",root)))
    errors.extend(validate_ai_rule_acceptance_policy(load("canonical/policies/CFA3-AI-RULE-ACCEPTANCE-WELLBEING-EFFICIENCY-001.json", root)))
    errors.extend(validate_rule_consistency_loop_prevention(load("canonical/policies/CFA3-RULE-CONSISTENCY-LOOP-PREVENTION-001.json", root)))
    errors.extend(validate_github_merge_gate_405_policy(load("canonical/policies/CFA3-GITHUB-MERGE-GATE-405-POLICY-001.json",root)))
    errors.extend(validate_policy_long_term_validation(load("canonical/policies/CFA3-POLICY-LONG-TERM-VALIDATION-001.json",root)))
    errors.extend(validate_policy_exact_finalization(load("canonical/policies/CFA3-POLICY-EXACT-FINALIZATION-001.json",root),root))
    errors.extend(validate_exact_finalization_evidence_correction(load("canonical/registries/CFA3-POLICY-EXACT-FINALIZATION-001-EVIDENCE-CORRECTION-20261012.json",root),load("canonical/registries/CFA3-POLICY-EXACT-FINALIZATION-001-CLOSURE-20261012.json",root)))
    errors.extend(validate_csa_infrastructure_isolation_policy(load("canonical/policies/CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001.json",root),root))
    errors.extend(validate_sequential_execution_result_integrity(load("canonical/policies/CFA3-POLICY-SEQUENTIAL-EXECUTION-RESULT-INTEGRITY-001.json", root), root))
    errors.extend(validate_conversation_evidence_blocker_prevention(load("canonical/policies/CFA3-POLICY-CONVERSATION-EVIDENCE-AND-BLOCKER-PREVENTION-001.json",root),root))
    errors.extend(validate_execution_completion_and_verified_finalization(load("canonical/policies/CFA3-POLICY-EXECUTION-COMPLETION-AND-VERIFIED-FINALIZATION-001.json",root),root))
    errors.extend(validate_http_409_conflict_recovery(load("canonical/policies/CFA3-POLICY-HTTP-409-CONFLICT-RECOVERY-001.json",root),root))
    errors.extend(validate_execution_and_proof_obligation(load("canonical/policies/CFA3-POLICY-EXECUTION-AND-PROOF-OBLIGATION-001.json",root),root))
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
