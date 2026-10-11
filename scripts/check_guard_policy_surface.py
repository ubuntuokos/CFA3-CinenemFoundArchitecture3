#!/usr/bin/env python3
"""CFA3 local canonical JSON policy field inventory: source-locked, fail-closed.

Complete path coverage of canonical/policies does NOT certify that all
requirements, authority decisions or runtime gates have been implemented.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SURFACE = "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json"

def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()

def leaves(node, pointer=""):
    if isinstance(node, dict):
        if not node:
            return [[pointer, "object_empty"]]
        out = []
        for k in sorted(node):
            segment = k.replace("~", "~0").replace("/", "~1")
            out.extend(leaves(node[k], pointer + "/" + segment))
        return out
    if isinstance(node, list):
        if not node:
            return [[pointer, "array_empty"]]
        out = []
        for index, child in enumerate(node):
            out.extend(leaves(child, pointer + "/" + str(index)))
        return out
    typ = ("null" if node is None else
           "boolean" if type(node) is bool else
           "integer" if type(node) is int else
           "number" if type(node) is float else
           "string" if type(node) is str else "unknown")
    return [[pointer, typ]]

def validate_snapshot(snapshot, root=ROOT):
    issues = []
    root = Path(root)
    if not isinstance(snapshot, dict) or snapshot.get("schema") != "cfa3.canonical-policy-surface.v1":
        return ["invalid policy surface schema"]
    if (snapshot.get("source_repository") !=
            "ubuntuokos/CFA3-CinenemFoundArchitecture3"):
        issues.append("wrong canonical policy repository")
    if snapshot.get("semantic_rule_admission") is not False or (
            snapshot.get("all_fields_disposition") !=
            "PENDING_RULE_APPLICABILITY_AND_GATE_PROOF"):
        issues.append("unreviewed field coverage must not become runtime admission")
    listed = snapshot.get("sources")
    if not isinstance(listed, list):
        return issues + ["canonical policy source list missing"]
    expected = sorted("canonical/policies/" + p.name
                      for p in (root / "canonical/policies").glob("*.json"))
    paths = [rec.get("path") for rec in listed if isinstance(rec, dict)]
    if (len(paths) != len(listed) or sorted(paths) != expected or
            len(set(paths)) != len(paths) or
            snapshot.get("source_policy_count") != len(paths)):
        issues.append("canonical policy files omitted, duplicated or unexpected")
        return issues
    for rec in listed:
        path = rec["path"]
        if not path.startswith("canonical/policies/"):
            issues.append("policy path escapes canonical policy scope")
            continue
        try:
            raw = (root / path).read_bytes()
            obj = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError, TypeError, UnicodeError):
            issues.append("missing/invalid policy JSON: " + path)
            continue
        if rec.get("git_blob_sha1") != git_blob_sha(raw):
            issues.append("canonical policy blob revision changed: " + path)
        status = obj.get("status", obj.get("authority_status",
                                         obj.get("repository_status", "UNSPECIFIED")))
        if rec.get("canonical_id") != obj.get("id") or rec.get("source_status") != status:
            issues.append("canonical policy ID/authority status drift: " + path)
        complete = leaves(obj)
        if rec.get("leaf_count") != len(complete) or rec.get("leaves") != complete:
            issues.append("canonical policy JSON field omitted or altered: " + path)
    return issues

def main():
    try:
        snapshot = json.loads((ROOT / SURFACE).read_text("utf-8"))
        issues = validate_snapshot(snapshot)
    except (OSError, ValueError, TypeError) as exc:
        issues = ["canonical policy field inventory unreadable: " + type(exc).__name__]
    if issues:
        for issue in issues:
            print("POLICY_SURFACE_FAIL:", issue, file=sys.stderr)
        return 1
    print("POLICY_SURFACE_STRUCTURAL_PASS: all canonical policy JSON fields and "
          "file revisions accounted for; NOT runtime or full-governance admission")
    return 0

if __name__ == "__main__":
    sys.exit(main())
