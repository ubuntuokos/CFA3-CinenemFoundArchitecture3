#!/usr/bin/env python3
"""CFA3 fail-closed execution gate foundation; NOT a full governance PASS."""
import fcntl
import hashlib
import hmac
import json
import math
import os
from pathlib import Path, PurePosixPath
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GOV = "canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
LEDGER = "canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json"
CATALOG = "canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json"
FROZEN_TREE = "canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json"
POLICY_SURFACE = "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json"
HISTORY_REGISTER = "canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json"
ACTIONS = {"GUI_RENDER", "REPOSITORY_WRITE", "WORKFLOW_START", "ARTIFACT_EXPORT"}
# Every task authorization must bind these exact source bytes, in addition to
# all dynamically discovered canonical/policies/*.json files.
GUARD_SOURCE_BINDINGS = frozenset({
    GOV, LEDGER, CATALOG, FROZEN_TREE, POLICY_SURFACE, "AGENTS.md",
    "docs/branding/CFA3-BRANDING.md",
    ".github/workflows/cfa3-bootstrap.yml",
    "scripts/check_bootstrap.py",
    "scripts/check_guard_policy_surface.py",
    "scripts/check_legacy_rule_blobs.py",
    "scripts/check_execution_guard_ruleset.py",
    "scripts/check_execution_rule_evidence.py",
    "scripts/check_execution_guard_history.py",
    "scripts/check_execution_guard_github_state.py",
    HISTORY_REGISTER,
    "scripts/execution_guard.py",
})

class Blocked(RuntimeError):
    pass

def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def local_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise Blocked("invalid path")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or str(p) != relative:
        raise Blocked("path traversal")
    root = Path(root).resolve()
    result = (root / str(p)).resolve()
    if not result.is_relative_to(root):
        raise Blocked("path outside canonical root")
    return result

def load(root, name):
    try:
        return json.loads(local_path(root, name).read_text("utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise Blocked("authoritative source unavailable: " + name) from exc

def validate_current_rule_map(governance, catalog):
    """Exact current canonical rule-code and evidence-state mapping.

    A catalog that only contains the right IDs but swaps the meaning of one
    code is invalid. Mapping is NOT a verified runtime policy implementation.
    """
    issues = []
    if not isinstance(governance, dict) or not isinstance(catalog, dict):
        return ["canonical governance or rule catalog is not an object"]
    mapped = catalog.get("rules")
    if not isinstance(mapped, dict):
        return ["DEV/AI catalog rules missing"]
    expected = {}
    for section, prefix in (("development_rules", "DEV"), ("ai_behavior_rules", "AI")):
        records = governance.get(section)
        if not isinstance(records, list) or len(records) != 12:
            issues.append("current canonical rule section must have 12 entries: " + section)
            continue
        for n, item in enumerate(records, 1):
            if not isinstance(item, dict):
                issues.append("malformed canonical rule")
                continue
            ident, code = item.get("id"), item.get("code")
            if ident != "%s-%02d" % (prefix, n) or not isinstance(code, str) or not code:
                issues.append("canonical rule ID/code/sequence invalid: " + section)
                continue
            if ident in expected:
                issues.append("duplicate canonical rule ID")
            expected[ident] = code
    if len(expected) != 24 or set(mapped) != set(expected):
        issues.append("DEV/AI inventory differs from 24 canonical rule identities")
    for ident, code in expected.items():
        row = mapped.get(ident)
        if not isinstance(row, dict) or row.get("code") != code:
            issues.append("DEV/AI canonical code mismatch: " + ident)
        elif row.get("status") not in ("PENDING_RUNTIME_GATE_AND_PROOF", "VERIFIED_GATE"):
            issues.append("unknown gate state: " + ident)
    return issues

def policy_issues(root=ROOT):
    """Unknown legacy rules and incomplete runtime gates MUST prevent all effects."""
    try:
        gov, ledger, catalog = [load(root, n) for n in (GOV, LEDGER, CATALOG)]
    except Blocked as exc:
        return [str(exc)]
    issues = []
    if catalog.get("schema") != "cfa3.execution-guard-coverage.v1":
        issues.append("invalid coverage catalog")
    issues.extend(validate_current_rule_map(gov, catalog))
    rules = catalog.get("rules", {})
    if not isinstance(rules, dict) or any(
            not isinstance(record, dict) or record.get("status") != "VERIFIED_GATE"
            for record in rules.values()):
        issues.append("DEV/AI per-rule execution gates not verified")
    policy_files = {str(p.relative_to(root)) for p in
                    (Path(root) / "canonical/policies").glob("*.json")}
    if (set(catalog.get("policy_files", [])) != policy_files or
            len(catalog.get("policy_files", [])) != len(policy_files)):
        issues.append("canonical policy file coverage incomplete")
    try:
        frozen = load(root, FROZEN_TREE)
        frozen_rows = frozen.get("files", [])
        mapped = {record[0]: record[1] for record in frozen_rows
                  if isinstance(record, list) and len(record) == 3}
        if (frozen.get("schema") != "cfa3.legacy-frozen-tree.v1" or
                frozen.get("commit") != ledger.get("source_main_commit") or
                frozen.get("blob_count") != 3159 or
                len(frozen_rows) != 3159 or len(mapped) != len(frozen_rows) or
                frozen.get("no_files_excluded_from_rule_review") is not True or
                any(mapped.get(record.get("path")) != record.get("blob_sha")
                    for record in ledger.get("source_records", []))):
            issues.append("full frozen file inventory invalid or missing seed bindings")
    except (Blocked, ValueError, TypeError, KeyError, IndexError):
        issues.append("full frozen file inventory absent or malformed")
    try:
        from check_guard_policy_surface import validate_snapshot
        surface = load(root, POLICY_SURFACE)
        issues.extend(validate_snapshot(surface, root))
    except (Blocked, OSError, ValueError, TypeError, ImportError):
        issues.append("canonical policy field snapshot unavailable or inconsistent")
    try:
        from check_execution_guard_history import validate, pending
        reg = load(root, HISTORY_REGISTER)
        frozen = load(root, FROZEN_TREE)
        issues.extend(validate(reg, frozen, ledger))
        issues.extend(pending(reg, frozen))
    except (Blocked, ImportError, OSError, TypeError, ValueError):
        issues.append("historical per-file rule accountability missing")
    if ledger.get("inventory_complete") is not True:
        issues.append("historical rule inventory incomplete")
    if gov.get("legacy_policy_transfer", {}).get("rule_inventory_complete") is not True:
        issues.append("canonical rule inventory incomplete")
    if gov.get("readiness", {}).get("full_development_governance_admission") != "VERIFIED":
        issues.append("governance admission not verified")
    if catalog.get("coverage_complete") is not True or (
            catalog.get("missing_rules") != 0 or catalog.get("unresolved_conflicts") != 0):
        issues.append("MISSING=0 / UNRESOLVED_CONFLICT=0 unproven")
    if catalog.get("independent_evidence_verified") is not True:
        issues.append("independent gate execution evidence absent")
    return issues

def verify_signature(task, secret):
    """HMAC key must only exist in independent gateway service, NEVER AI context."""
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise Blocked("trusted signing key unavailable")
    signature = task.get("signature")
    if not isinstance(signature, str) or len(signature) != 64:
        raise Blocked("owner authorization unsigned")
    data = {k: v for k, v in task.items() if k != "signature"}
    actual = hmac.new(secret, canonical_bytes(data), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, signature):
        raise Blocked("authorization tampered")

def check_task(root, task, now=None):
    required = ("task_id", "nonce", "operation", "target", "scope_targets",
                "main_sha", "expires_at", "expected_outputs", "units",
                "max_calls", "max_units", "source_hashes")
    if not isinstance(task, dict) or any(k not in task for k in required):
        raise Blocked("incomplete task contract")
    if task["operation"] not in ACTIONS:
        raise Blocked("operation outside allowlist")
    if any(not isinstance(task[k], str) or not task[k] for k in
           ("task_id", "nonce", "target")):
        raise Blocked("task identity missing")
    sha = task["main_sha"]
    if not isinstance(sha, str) or len(sha) != 40 or any(
            c not in "0123456789abcdef" for c in sha):
        raise Blocked("invalid main/head revision")
    if (type(task["expires_at"]) not in (int, float) or
            not math.isfinite(task["expires_at"]) or
            (time.time() if now is None else now) >= task["expires_at"]):
        raise Blocked("expired task authorization")
    for key in ("expected_outputs", "units", "max_calls", "max_units"):
        if type(task[key]) is not int or task[key] < 1:
            raise Blocked("invalid result count or budget")
    if task["units"] > task["max_units"]:
        raise Blocked("quota exceeded")
    local_path(root, task["target"])
    scopes = task["scope_targets"]
    if not isinstance(scopes, list) or not scopes or task["target"] not in scopes:
        raise Blocked("target not included in signed exact scope")
    for item in scopes:
        local_path(root, item)
    if task["operation"] in ("REPOSITORY_WRITE", "WORKFLOW_START"):
        if task.get("branch") in (None, "", "main", "master"):
            raise Blocked("missing or protected branch")
        rev = task.get("head_sha")
        if not isinstance(rev, str) or len(rev) != 40 or any(
                c not in "0123456789abcdef" for c in rev):
            raise Blocked("exact head SHA required")
    if task["operation"] == "WORKFLOW_START" and task.get("explicit_workflow_approval") is not True:
        raise Blocked("explicit signed workflow authorization required")
    if task["target"].startswith(("legacy/", "archive/legacy/")):
        raise Blocked("legacy source is read-only")
    hashes = task["source_hashes"]
    if not isinstance(hashes, dict):
        raise Blocked("invalid source digest map")
    mandatory = set(GUARD_SOURCE_BINDINGS)
    declared = load(root, CATALOG).get("policy_files", [])
    if not isinstance(declared, list) or not all(isinstance(x, str) for x in declared):
        raise Blocked("invalid canonical policy-source declarations")
    mandatory.update(declared)
    if not mandatory.issubset(hashes):
        missing = sorted(mandatory.difference(hashes))
        raise Blocked("missing mandatory policy/guard source hashes: " + ", ".join(missing))
    for name, digest in hashes.items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise Blocked("bad source digest")
        try:
            observed = hashlib.sha256(local_path(root, name).read_bytes()).hexdigest()
        except OSError as exc:
            raise Blocked("source not available: " + name) from exc
        if not hmac.compare_digest(observed, digest):
            raise Blocked("canonical source changed: " + name)
    if task["operation"] == "GUI_RENDER":
        catalog = load(root, CATALOG)
        design, plan = task.get("design_source"), task.get("approved_plan_source")
        if not design or not plan or design not in hashes or plan not in hashes or (
                design not in catalog.get("approved_design_sources", [])):
            raise Blocked("accepted design specification and plan not verified")
    if task.get("claims_physical_pass"):
        raise Blocked("reference CI cannot certify physical Current Host PASS")
    return True

def _reserve(folder, task):
    """Durable task-envelope binding, global nonce replay and quota protection."""
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink() or (folder / "lock").is_symlink():
        raise Blocked("trusted private quota store unavailable")
    fields = ("task_id", "operation", "target", "scope_targets", "main_sha",
              "head_sha", "branch", "expires_at", "expected_outputs",
              "max_calls", "max_units", "source_hashes", "design_source",
              "approved_plan_source", "explicit_workflow_approval")
    binding = hashlib.sha256(canonical_bytes({k: task.get(k) for k in fields})).hexdigest()
    with (folder / "lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        ledger = folder / "receipts.json"
        if ledger.is_symlink():
            raise Blocked("symlinked quota state forbidden")
        try:
            data = json.loads(ledger.read_text("utf-8")) if ledger.exists() else {}
            if not isinstance(data, dict):
                raise ValueError("bad ledger type")
            used = data.get("_used_nonces", [])
            row = data.get(task["task_id"],
                           {"nonces": [], "units": 0, "calls": 0, "binding": binding})
            if not isinstance(used, list) or not isinstance(row, dict) or any(
                    k not in row for k in ("nonces", "units", "calls", "binding")):
                raise ValueError("invalid quota data")
        except (OSError, ValueError, TypeError) as exc:
            raise Blocked("quota ledger invalid") from exc
        if row["binding"] != binding:
            raise Blocked("immutable task scope or resource ceiling changed")
        if task["nonce"] in used or task["nonce"] in row["nonces"]:
            raise Blocked("single-use nonce replay")
        if row["calls"] + 1 > task["max_calls"] or (
                row["units"] + task["units"] > task["max_units"]):
            raise Blocked("task resource budget exhausted")
        used.append(task["nonce"])
        row["nonces"].append(task["nonce"])
        row["units"] += task["units"]
        row["calls"] += 1
        data["_used_nonces"], data[task["task_id"]] = used, row
        tmp = folder / ("receipts.%d.tmp" % os.getpid())
        try:
            with tmp.open("x", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, sort_keys=True)
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, ledger)
            descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as exc:
            raise Blocked("quota reservation could not be persisted") from exc
        finally:
            if tmp.exists():
                tmp.unlink()

def guarded_execute(task, *, root=ROOT, secret=None, admission=None,
                    live_state=None, preflight=None, executor=None,
                    verify_result=None, audit=None, state_dir=None,
                    rule_attester=None, rule_attestation_secret=None,
                    rule_evidence_resolver=None):
    """Requires a separately isolated trusted service with exclusive credentials.

    It cannot intercept native ChatGPT tools or other unguarded service routes.
    """
    issues = policy_issues(root)
    if issues:
        raise Blocked("POLICY_INCOMPLETE: " + "; ".join(issues))
    check_task(root, task)
    verify_signature(task, secret)
    if not all(callable(f) for f in (
            admission, live_state, preflight, executor, verify_result, audit,
            rule_attester, rule_evidence_resolver)) or state_dir is None:
        raise Blocked("trusted rule attester/execution/admission/audit adapter missing")
    if (not isinstance(rule_attestation_secret, bytes) or
            len(rule_attestation_secret) < 32 or
            hmac.compare_digest(secret, rule_attestation_secret)):
        raise Blocked("separate trusted rule proof key required")
    from check_execution_rule_evidence import verify_rule_receipts, RuleEvidenceBlocked
    try:
        verify_rule_receipts(task, rule_attester(task), load(root, GOV),
                             rule_attestation_secret,
                             evidence_resolver=rule_evidence_resolver)
    except RuleEvidenceBlocked as exc:
        raise Blocked("RULE_GATE: " + str(exc)) from exc
    evidence = admission(task)
    if not isinstance(evidence, dict) or any(evidence.get(x) is not True for x in (
            "complete_rule_inventory", "rule_gates_verified",
            "all_conflicts_resolved", "independent_proof_verified")):
        raise Blocked("independent full-rule admission not verified")
    proof = live_state(task)
    if not isinstance(proof, dict) or any(proof.get(x) is not True for x in (
            "main_current", "head_current", "no_overlap", "checks_passed",
            "review_threads_clear", "owner_scope_approved",
            "main_ruleset_verified", "privileged_bypass_actors_verified")):
        raise Blocked("fresh exact-state authorization failed")
    if proof.get("actual_main_sha") != task["main_sha"]:
        raise Blocked("main SHA drift")
    if task["operation"] in ("REPOSITORY_WRITE", "WORKFLOW_START"):
        if proof.get("actual_head_sha") != task["head_sha"]:
            raise Blocked("head SHA drift")
    checked = preflight(task)
    if not isinstance(checked, dict) or any(checked.get(x) is not True for x in (
            "source_verified", "scope_verified", "resource_verified",
            "output_contract_verified")):
        raise Blocked("trusted preflight failed")
    if task["operation"] == "GUI_RENDER" and checked.get("design_verified") is not True:
        raise Blocked("GUI design must be independently verified")
    _reserve(state_dir, task)
    audit(task, "RESERVED")  # if audit fails, execution does not start; quota is consumed
    try:
        outputs = executor(task)
        if not isinstance(outputs, (list, tuple)) or len(outputs) != task["expected_outputs"]:
            raise Blocked("RESULT_GATE: wrong output count")
        if verify_result(task, outputs) is not True:
            raise Blocked("RESULT_GATE: independent output validation failed")
    except Exception:
        audit(task, "FAILED")
        raise
    audit(task, "VERIFIED")
    return outputs

if __name__ == "__main__":
    if sys.argv[1:] != ["--status"]:
        print("BLOCKER: direct tool use forbidden", file=sys.stderr)
        sys.exit(2)
    for issue in policy_issues(ROOT):
        print("BLOCKER:", issue)
    sys.exit(1 if policy_issues(ROOT) else 0)
