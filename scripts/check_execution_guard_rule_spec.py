#!/usr/bin/env python3
"""Verify exact owner-supplied rule descriptions without inventing runtime PASS.

Only the 24 already-admitted canonical rule IDs are active. The 78 earlier
explicitly excluded historical candidates remain descriptive reference data.
"""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SPEC="canonical/registries/CFA3-EXECUTION-GUARD-OWNER-RULE-SPEC-001.json"
GOV="canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
COVERAGE="canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json"
EXPORT="docs/governance/exports/CFA3-EXECUTION-GUARD-RULES-AND-CANDIDATES-20261011.json"
AMENDMENTS={"HU_ONLY_UNLESS_EXPLICIT_OTHER","SECOND_CONSECUTIVE_OWN_ERROR_APPROVAL",
            "DONOR_SDK_PARALLEL_NONBLOCKING_WHEN_DISJOINT",
            "SHORT_OWNER_COMMANDS_LIMITED_TO_MAIN_TASK",
            "AI_GENERATION_COMMENT_DOCUMENT_ONLY"}
ALLOWED_MODES={"DETERMINISTIC_AND_AUDITED","SIGNED_SCOPE_AND_AUDIT",
               "SIGNED_SCOPE","LIVE_GITHUB","LIVE_GITHUB_AND_OWNER_OVERRIDE",
               "LIVE_GITHUB_AND_OWNER_GRANT","INDEPENDENT_AUDIT",
               "SIGNED_OWNER_DECISION","SIGNED_OWNER_DECISION_AND_AUDIT",
               "SIGNED_SCOPE_AND_CANONICAL_SOURCES","LIVE_STATE",
               "LIVE_STATE_AND_OWNER_OVERRIDE","SIGNED_OPERATION_PERMISSION",
               "LIVE_STATE_AND_OWNER_GRANT","FAIL_CLOSED_ADMISSION"}

def validate(spec,governance,coverage,reference):
    errors=[]
    if not all(isinstance(x,dict) for x in (spec,governance,coverage,reference)):
        return ["rule sources missing or malformed"]
    canonical=[*governance.get("development_rules",[]),*governance.get("ai_behavior_rules",[])]
    if len(canonical)!=24 or not all(isinstance(r,dict) for r in canonical):
        return ["24 canonical DEV/AI records unavailable"]
    expected={(r["id"],r["code"]) for r in canonical}
    current=spec.get("active_rules")
    if not isinstance(current,list) or len(current)!=24 or spec.get("active_rule_count")!=24:
        return ["24 active owner rule descriptions missing"]
    seen=set()
    for row in current:
        if not isinstance(row,dict):
            errors.append("malformed active owner rule")
            continue
        key=(row.get("id"),row.get("code"))
        if key in seen or key not in expected:
            errors.append("rule ID/code not identical to canonical governance")
        seen.add(key)
        if (not isinstance(row.get("text_hu"),str)
                or len(row["text_hu"].strip())<40
                or row.get("proof_mode") not in ALLOWED_MODES
                or row.get("runtime_verified") is not False):
            errors.append("non-final text, evidence-class or fake runtime PASS")
    if seen!=expected:
        errors.append("owner 24-rule scope is not complete and unique")
    if spec.get("schema")!="cfa3.execution-guard-owner-rule-spec.v1":
        errors.append("unexpected owner source contract")
    e=spec.get("historical_exclusion")
    reg=coverage.get("historical_execution_exclusion")
    if (not isinstance(e,dict) or not isinstance(reg,dict) or
            e.get("explicit_owner_exclusion_retained") is not True or
            e.get("excluded_count")!=78 or e.get("eligible_for_runtime_admission") is not False or
            reg.get("excluded_historical_candidate_count")!=78 or
            reg.get("candidates_admitted_to_current_rule_set") is not False or
            reg.get("current_required_rule_count")!=24):
        errors.append("owner's 78 historical candidate exclusion weakened")
    historical=spec.get("excluded_historical_candidates")
    refs=reference.get("historical_rule_candidates")
    if not isinstance(historical,list) or len(historical)!=78 or not isinstance(refs,list) or len(refs)!=78:
        return errors+["78 historical reference texts incomplete"]
    for row,ref in zip(historical,refs):
        if not isinstance(row,dict) or any(row.get(k)!=ref.get(k) for k in
                ("type","id","source_path","source_json_pointer")):
            errors.append("historical source provenance or order changed")
        elif (not isinstance(row.get("text_hu"),str)
              or len(row["text_hu"].strip())<20
              or row.get("current_rule_admission") is not False
              or row.get("active_execution_check") is not False):
            errors.append("historical rule text missing or silently activated")
    addons=spec.get("owner_amendments")
    if not isinstance(addons,list) or {x.get("id") for x in addons if isinstance(x,dict)}!=AMENDMENTS:
        errors.append("owner-specific amendments not all preserved")
    else:
        for x in addons:
            if not isinstance(x.get("text_hu"),str) or not x["text_hu"].strip():
                errors.append("missing owner amendment text")
            if any(y not in {r["id"] for r in canonical} for y in x.get("mapped_to",[])):
                errors.append("owner amendment maps outside the current 24 rules")
    return errors

def main():
    try:
        docs=[json.loads((ROOT/path).read_text("utf-8"))
              for path in (SPEC,GOV,COVERAGE,EXPORT)]
        errors=validate(*docs)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        errors=["owner rule source unreadable: "+type(exc).__name__]
    for error in errors:
        print("OWNER_RULE_SPEC_BLOCKED:",error,file=sys.stderr)
    if errors:return 1
    print("OWNER_RULE_SPEC_STRUCTURAL_PASS: 24 owner-text current rules and 78 excluded "
          "historical texts; NOT independent runtime PASS")
    return 0

if __name__=="__main__":sys.exit(main())
