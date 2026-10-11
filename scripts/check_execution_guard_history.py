#!/usr/bin/env python3
"""Validate per-file historic rule obligations; never transfer old authority."""
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
REGISTER="canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json"
FROZEN="canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json"
LEDGER="canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json"
SHA1=re.compile(r"^[0-9a-f]{40}$")
SHA256=re.compile(r"^[0-9a-f]{64}$")

def validate(reg, tree, ledger):
    if not all(isinstance(x,dict) for x in (reg,tree,ledger)):
        return ["source registry inputs must be objects"]
    errors=[]
    rows=tree.get("files",[])
    if not isinstance(rows,list) or len(rows)!=3159:
        return ["3159 original source files not available"]
    sources={r[0]:r[1] for r in rows if isinstance(r,list) and len(r)==3}
    if (len(sources)!=3159 or reg.get("schema")!="cfa3.legacy-rule-reconciliation.v1"
        or reg.get("source_repo")!=tree.get("repository")
        or reg.get("source_commit")!=tree.get("commit")
        or reg.get("source_commit")!=ledger.get("source_main_commit")
        or reg.get("source_count")!=3159):
        errors.append("historical source identity or cardinality mismatch")
    if (reg.get("default_disposition")!="UNREVIEWED"
        or reg.get("decisions_complete") is not False
        or reg.get("missing_rules") is not None
        or reg.get("unresolved_conflicts") is not None):
        errors.append("unverified rule admission or altered pending state")
    seeds=ledger.get("source_records",[])
    if (not isinstance(seeds,list) or reg.get("source_seed_count")!=len(seeds)
        or any(sources.get(x.get("path"))!=x.get("blob_sha") for x in seeds)):
        errors.append("initial seed provenance mismatch")
    groups=reg.get("candidate_groups",[])
    if not isinstance(groups,list) or len(groups)!=3:
        errors.append("known candidate groups incomplete")
    else:
        seen=set()
        for g in groups:
            path=g.get("source_path")
            if (path in seen or sources.get(path)!=g.get("source_git_sha")
                or g.get("owner_admitted") is not False or g.get("status")!="UNRECONCILED"):
                errors.append("candidate source drift or unauthorized admission")
            seen.add(path)
            pairs=g.get("rule_pointers")
            if (not isinstance(pairs,list) or not pairs or
                any(not isinstance(v,list) or len(v)!=2 or not all(isinstance(s,str) and s for s in v) for v in pairs)
                or len(set(p[0] for p in pairs))!=len(pairs)):
                errors.append("candidate rule pointer coverage invalid")
        if sum(len(g.get("rule_pointers",[])) for g in groups)!=78:
            errors.append("78 current known historic candidates not accounted for")
    decisions=reg.get("reviewed_dispositions")
    if not isinstance(decisions,list):return errors+["dispositions unavailable"]
    decided=set()
    for d in decisions:
        if not isinstance(d,dict):return errors+["malformed decision record"]
        path=d.get("source_path");digest=d.get("owner_evidence_sha256")
        if path in decided or sources.get(path)!=d.get("source_git_sha"):
            errors.append("invalid/repeated file decision provenance")
        decided.add(path)
        if (d.get("decision") not in ("NO_CURRENT_RULE","MAPPED_TO_NEW_CANONICAL","CONFLICT_REQUIRES_OWNER")
            or not isinstance(digest,str) or SHA256.fullmatch(digest) is None):
            errors.append("unsupported or owner-unauthenticated file disposition")
    return errors

def pending(reg, tree):
    all_files={r[0] for r in tree.get("files",[]) if isinstance(r,list) and len(r)==3}
    decided={d.get("source_path") for d in reg.get("reviewed_dispositions",[])
             if isinstance(d,dict) and d.get("decision") in ("NO_CURRENT_RULE","MAPPED_TO_NEW_CANONICAL")}
    missing=len(all_files-decided)
    return [f"{missing} original historical source dispositions unresolved"] if missing or len(all_files)!=3159 else []

def main():
    try:
        reg=json.loads((ROOT/REGISTER).read_text("utf-8"))
        tree=json.loads((ROOT/FROZEN).read_text("utf-8"))
        ledger=json.loads((ROOT/LEDGER).read_text("utf-8"))
        errors=validate(reg,tree,ledger)
    except (OSError,ValueError,TypeError) as e:
        errors=["unreadable source register: "+type(e).__name__]
    for x in errors:print("HISTORY_REGISTER_FAIL:",x,file=sys.stderr)
    if errors:return 1
    print("HISTORY_REGISTER_STRUCTURAL_PASS: all source obligations retained; runtime admission remains denied")
    return 0

if __name__=="__main__":sys.exit(main())
