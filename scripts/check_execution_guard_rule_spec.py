#!/usr/bin/env python3
"""Current 81 owner-authorized rules, preserving 24 original identities and 78 sources."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SPEC="canonical/registries/CFA3-EXECUTION-GUARD-OWNER-RULE-SPEC-001.json"
GOV="canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
COVERAGE="canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json"
EXPORT="docs/governance/exports/CFA3-EXECUTION-GUARD-RULES-AND-CANDIDATES-20261011.json"
RULE_ADMISSION_POLICY="canonical/policies/CFA3-RULE-ADMISSION-POLICY-001.json"
AMENDMENTS={"HU_ONLY_UNLESS_EXPLICIT_OTHER","SECOND_CONSECUTIVE_OWN_ERROR_APPROVAL","DONOR_SDK_PARALLEL_NONBLOCKING_WHEN_DISJOINT","SHORT_OWNER_COMMANDS_LIMITED_TO_MAIN_TASK","AI_GENERATION_COMMENT_DOCUMENT_ONLY"}
def active_expected_codes(gov,spec):
    if not isinstance(gov,dict) or not isinstance(spec,dict):
        raise ValueError("authoritative owner rules unavailable")
    original=[*gov.get("development_rules",[]),*gov.get("ai_behavior_rules",[])]
    if len(original)!=24 or any(not isinstance(x,dict) for x in original):
        raise ValueError("24 original DEV/AI rules unavailable")
    expected={}
    for prefix,rows in (("DEV",original[:12]),("AI",original[12:])):
        for i,x in enumerate(rows,1):
            if x.get("id")!=f"{prefix}-{i:02d}" or not isinstance(x.get("code"),str):
                raise ValueError("original rule identity changed")
            expected[x["id"]]=x["code"]
    rows=spec.get("active_rules")
    if not isinstance(rows,list) or len(rows)!=81 or spec.get("active_rule_count")!=81:
        raise ValueError("81 current rules required")
    found=set()
    for row in rows:
        if not isinstance(row,dict): raise ValueError("malformed active rule")
        ident,code=row.get("id"),row.get("code")
        if not isinstance(ident,str) or not isinstance(code,str) or not ident or not code or ident in found:
            raise ValueError("invalid/duplicate active ID or code")
        found.add(ident)
        if ident in expected and expected[ident]!=code:
            raise ValueError("original canonical ID/code changed")
        if ident not in expected:
            if ident=="RULE-ADMISSION-001":
                if row.get("provenance")!="OWNER_SUPPLIED_2026_10_11" or row.get("canonical_policy_path")!=RULE_ADMISSION_POLICY:
                    raise ValueError("new rule missing exact owner policy provenance")
            elif row.get("provenance")!="OWNER_RECONFIRMED_2026_10_11" or not isinstance(row.get("historical_source"),dict):
                raise ValueError("additional historical rule without owner source")
            expected[ident]=code
    if len(expected)!=81 or found!=set(expected):
        raise ValueError("current 81 active rules incomplete")
    return expected
def validate(spec,gov,coverage,reference):
    if not all(isinstance(x,dict) for x in (spec,gov,coverage,reference)):
        return ["rule source not an object"]
    try: expected=active_expected_codes(gov,spec)
    except (ValueError,KeyError,TypeError) as exc: return ["active rule set invalid: "+str(exc)]
    issues=[]
    rules=coverage.get("rules")
    if not isinstance(rules,dict) or set(rules)!=set(expected):
        issues.append("81 active rules absent from coverage")
    else:
        for ident,code in expected.items():
            row=rules[ident]
            if not isinstance(row,dict) or row.get("code")!=code or row.get("status") not in ("PENDING_RUNTIME_GATE_AND_PROOF","VERIFIED_GATE"):
                issues.append("current active code/status drift: "+ident)
    for row in spec["active_rules"]:
        if not isinstance(row.get("text_hu"),str) or len(row["text_hu"].strip())<20 or row.get("runtime_verified") is not False or not row.get("proof_mode"):
            issues.append("owner text or runtime status invalid")
    old={x["id"] for x in [*gov["development_rules"],*gov["ai_behavior_rules"]]}
    if {x["id"] for x in spec["active_rules"][:24]}!=old:
        issues.append("original 24 rule texts missing")
    hist=spec.get("historical_candidates");refs=reference.get("historical_rule_candidates")
    own=spec.get("historical_reconciliation");reg=coverage.get("owner_historical_reconciliation")
    if not isinstance(hist,list) or len(hist)!=78 or not isinstance(refs,list) or len(refs)!=78 or not isinstance(own,dict) or not isinstance(reg,dict):
        return issues+["78 owner sources not all present"]
    count={"HISTORICAL_CANDIDATE_DEV_AI":0,"HISTORICAL_CANDIDATE_QUALITY":0,"HISTORICAL_CANDIDATE_TASK_SCOPE":0}
    active={r["id"]:r for r in spec["active_rules"]}
    for row,ref in zip(hist,refs):
        if not isinstance(row,dict) or any(row.get(k)!=ref.get(k) for k in ("id","type","source_path","source_json_pointer")) or row.get("current_rule_admission") is not True or row.get("active_execution_check") is not True or row.get("mapped_to_rule_id")!=row.get("id") or ref.get("active_rule_receipt_scope") is not True or ref.get("excluded_from_execution_guard_active_rule_set") is not False or row.get("id") not in active:
            issues.append("owner source admission/provenance lost")
            continue
        count[row["type"]]+=1
        if row["type"]=="HISTORICAL_CANDIDATE_DEV_AI":
            if row["id"] not in old or row.get("admission_disposition")!="MAPPED_TO_EXISTING_24":
                issues.append("old identity lost")
        elif row["id"] in old or active[row["id"]]["text_hu"]!=row.get("text_hu") or active[row["id"]]["code"]!=ref.get("code") or row.get("admission_disposition")!="ADMITTED_ADDITIONAL_56":
            issues.append("new owner rule not identical to source")
    if count!={"HISTORICAL_CANDIDATE_DEV_AI":22,"HISTORICAL_CANDIDATE_QUALITY":29,"HISTORICAL_CANDIDATE_TASK_SCOPE":27}:
        issues.append("22+29+27 owner sources not accounted for")
    for data in (own,reg):
        if data.get("source_count")!=78 or data.get("mapped_existing")!=22 or data.get("admitted_new")!=56 or data.get("excluded_for_conflict")!=0 or data.get("active_count")!=81 or data.get("post_historical_rule_admissions")!=1 or data.get("all_source_rules_accounted_for") is not True:
            issues.append("owner reinstatement counts invalid")
    if (reference.get("owner_reconciliation",{}).get("total")!=81 or
            reference.get("counts",{}).get("current_canonical")!=81 or
            len(reference.get("current_rules",[]))!=81):
        issues.append("provenance export incorrectly excludes current rules")
    try:
        new_policy=json.loads((ROOT/RULE_ADMISSION_POLICY).read_text("utf-8"))
        new_owner_rule=active["RULE-ADMISSION-001"]
        if (new_owner_rule.get("code")!=new_policy["rule"]["code"] or
                new_owner_rule.get("text_hu")!=new_policy["rule"]["text_hu"] or
                new_policy["rule"]["id"]!="RULE-ADMISSION-001" or
                new_owner_rule.get("runtime_verified") is not False):
            issues.append("new owner rule does not match its canonical policy")
        if (reference["current_rules"][-1].get("id")!="RULE-ADMISSION-001" or
                reference["current_rules"][-1].get("source_git_blob_sha1")!=
                next(s["git_blob_sha1"] for s in
                     json.loads((ROOT/"canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json").read_text("utf-8"))["sources"]
                     if s["path"]==RULE_ADMISSION_POLICY)):
            issues.append("new owner rule source is not the policy-surface revision")
    except (OSError,ValueError,TypeError,KeyError,StopIteration):
        issues.append("new owner rule canonical source unavailable")
    amend=spec.get("owner_amendments")
    if not isinstance(amend,list) or {x.get("id") for x in amend if isinstance(x,dict)}!=AMENDMENTS or any(any(id not in expected for id in a.get("mapped_to",[])) for a in amend):
        issues.append("owner clarifications missing or outside rule set")
    return issues
def main():
    try:
        docs=[json.loads((ROOT/p).read_text("utf-8")) for p in (SPEC,GOV,COVERAGE,EXPORT)]
        issues=validate(*docs)
    except (OSError,ValueError,TypeError,KeyError) as exc: issues=["unreadable owner source: "+type(exc).__name__]
    for msg in issues:print("OWNER_RULE_SPEC_BLOCKED:",msg,file=sys.stderr)
    if issues:return 1
    print("OWNER_RULE_SPEC_STRUCTURAL_PASS: 81 current rules; 78 submitted all admitted (22 mapped, 56 additional); runtime proof remains independent")
    return 0
if __name__=="__main__":sys.exit(main())
