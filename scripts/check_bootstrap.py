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

def check(root=ROOT):
    gov=load("canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json",root)
    cpu=load("canonical/policies/CFA3-CPU-EXECUTION-POLICY-001.json",root)
    platform=load("canonical/policies/CFA3-PLATFORM-CONSTRAINTS-001.json",root)
    ledger=load("canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json",root)
    errors=validate_objects(gov,cpu,platform,ledger)
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
