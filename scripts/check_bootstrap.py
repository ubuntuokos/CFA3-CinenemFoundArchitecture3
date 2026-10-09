#!/usr/bin/env python3
"""Structural bootstrap guard: never issues CFA3 runtime/admission PASS."""
import json
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
    require({x.get("id") for x in gov.get("development_rules", [])} == {f"DEV-{i:02d}" for i in range(1, 12)}, "DEV-01..11 coverage missing")
    require({x.get("id") for x in gov.get("ai_behavior_rules", [])} == {f"AI-{i:02d}" for i in range(1, 12)}, "AI-01..11 coverage missing")
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
    if index.get("schema")!="cfa3.source-lifecycle-index.v1":
        errors.append("source lifecycle index schema mismatch")
    if index.get("complete") is not False:
        errors.append("cannot claim complete donor/source migration")
    if index.get("source_records")!=[]:
        errors.append("bootstrap source index must remain empty pending migration")
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
    require(classification.get("single_canonical_source_identity") is True,"one canonical identity")
    require(classification.get("existing_source_previous_decision_overwrite") is False,"prior decision cannot be overwritten")
    require(classification.get("known_source_no_reanalysis") is True,"known source must not be redone")
    require(classification.get("discovery_is_admission") is False,"discovery cannot admit donor")
    lim=policy.get("expansion_limit",{})
    require((lim.get("limit_numerator"),lim.get("limit_denominator"),lim.get("limit_rounding"))==(115,100,"FLOOR"),"15% exact threshold required")
    require(lim.get("initial_count_field")=="l1_input_link_occurrences","baseline must be frozen L1 count")
    require(lim.get("comparison")=="RAW_OUTBOUND_LINK_OCCURRENCES_FROM_CURRENT_LEVEL_BEFORE_DEDUPLICATION_OR_CLASSIFICATION","count raw links before dedup")
    for key in ("count_repeated_discovered_urls","count_previously_known_discovered_urls",
                "per_level_not_cumulative","denominator_frozen_for_entire_run",
                "stop_on_first_count_exceed","no_auto_truncation_to_limit",
                "no_new_level_on_stop","no_auto_resume","retained_completed_levels_remain_published"):
        require(lim.get(key) is True,key+" must be true")
    require(lim.get("do_not_use")=="ACTIVE_DONOR_DATABASE_SIZE","donor DB size is not comparison base")
    require(lim.get("over_limit_state")=="STOPPED_EXPANSION_LIMIT","limit violation must stop")
    sample=lim.get("example",{})
    require((sample.get("l1_input"),sample.get("allowed_raw_outbound"),sample.get("stop_on"))==(1000,1150,1151),"boundary example incorrect")
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
    require(decision.get("approved_policy_id")==policy.get("id"),"decision/policy mismatch")
    require(decision.get("status")=="OWNER_APPROVED_PLAN_PENDING_REPOSITORY_MERGE","decision merge status overstated")
    require(decision.get("owner_approved") is True,"owner approval missing")
    require(decision.get("effects",{}).get("runtime_admission") is False,"runtime cannot be admitted")
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
