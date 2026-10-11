#!/usr/bin/env python3
"""CFA3 fail-closed execution gate foundation; NOT a full governance PASS."""
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GOV = "canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
LEDGER = "canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json"
CATALOG = "canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json"
ACTIONS = {"GUI_RENDER", "REPOSITORY_WRITE", "WORKFLOW_START", "ARTIFACT_EXPORT"}

class Blocked(RuntimeError):
    pass

def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def local_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise Blocked("invalid path")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or "." in p.parts:
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

def policy_issues(root=ROOT):
    """Unknown legacy rules and incomplete runtime gates MUST prevent all effects."""
    try:
        gov, ledger, catalog = [load(root, n) for n in (GOV, LEDGER, CATALOG)]
    except Blocked as exc:
        return [str(exc)]
    issues = []
    if catalog.get("schema") != "cfa3.execution-guard-coverage.v1":
        issues.append("invalid coverage catalog")
    expected = {r["id"] for section in ("development_rules", "ai_behavior_rules")
                for r in gov.get(section, []) if isinstance(r, dict) and "id" in r}
    rules = catalog.get("rules")
    if len(expected) != 24 or not isinstance(rules, dict) or set(rules) != expected:
        issues.append("DEV/AI inventory does not match canonical policy")
    elif any(record.get("status") != "VERIFIED_GATE" for record in rules.values()):
        issues.append("DEV/AI per-rule execution gates not verified")
    policy_files = {str(p.relative_to(root)) for p in
                    (Path(root) / "canonical/policies").glob("*.json")}
    if set(catalog.get("policy_files", [])) != policy_files:
        issues.append("canonical policy file coverage incomplete")
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
    if type(task["expires_at"]) not in (int, float) or (
            time.time() if now is None else now) >= task["expires_at"]:
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
    if task["operation"] == "REPOSITORY_WRITE" and (
            task.get("branch") in (None, "", "main", "master")):
        raise Blocked("direct main write not authorized")
    if task["target"].startswith(("legacy/", "archive/legacy/")):
        raise Blocked("legacy source is read-only")
    hashes = task["source_hashes"]
    if not isinstance(hashes, dict) or not {GOV, LEDGER, CATALOG}.issubset(hashes):
        raise Blocked("mandatory source digests missing")
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
    if task.get("claims_physical_pass") is True:
        raise Blocked("reference CI cannot certify physical Current Host PASS")
    return True

def _reserve(folder, task):
    """Atomic task-quota/one-use nonce reservation BEFORE irreversible tool call."""
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink():
        raise Blocked("private trusted budget store missing")
    with (folder / "lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        ledger = folder / "receipts.json"
        try:
            data = json.loads(ledger.read_text("utf-8")) if ledger.exists() else {}
            if not isinstance(data, dict):
                raise ValueError("invalid budget ledger")
        except (OSError, ValueError) as exc:
            raise Blocked("budget ledger corrupt") from exc
        row = data.get(task["task_id"], {"nonces": [], "units": 0, "calls": 0})
        if task["nonce"] in row["nonces"]:
            raise Blocked("single-use authorization replay")
        if row["calls"] + 1 > task["max_calls"] or (
                row["units"] + task["units"] > task["max_units"]):
            raise Blocked("resource limit reached")
        row["nonces"].append(task["nonce"])
        row["units"] += task["units"]
        row["calls"] += 1
        data[task["task_id"]] = row
        temp = folder / ("receipts.%d.tmp" % os.getpid())
        try:
            with temp.open("x", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, ledger)
        except OSError as exc:
            raise Blocked("cannot persist resource reservation") from exc
        finally:
            if temp.exists():
                temp.unlink()

def guarded_execute(task, *, root=ROOT, secret=None, live_state=None,
                    executor=None, verify_result=None, state_dir=None):
    """Only a separate trusted service holding tool credentials may invoke this.

    Native ChatGPT tools and any external route outside this gateway are NOT
    intercepted. Current incomplete policy inventory causes denial.
    """
    issues = policy_issues(root)
    if issues:
        raise Blocked("POLICY_INCOMPLETE: " + "; ".join(issues))
    check_task(root, task)
    verify_signature(task, secret)
    if not all(callable(f) for f in (live_state, executor, verify_result)) or (
            state_dir is None):
        raise Blocked("trusted live-state / result / execution adapters absent")
    proof = live_state(task)
    fields = ("main_current", "head_current", "no_overlap", "checks_passed",
              "review_threads_clear", "owner_scope_approved")
    if not isinstance(proof, dict) or any(proof.get(k) is not True for k in fields):
        raise Blocked("fresh exact-state or owner authority not verified")
    if proof.get("actual_main_sha") != task["main_sha"]:
        raise Blocked("main drift")
    _reserve(state_dir, task)
    artifacts = executor(task)
    if not isinstance(artifacts, (list, tuple)) or (
            len(artifacts) != task["expected_outputs"]):
        raise Blocked("RESULT_GATE: requested result count not met")
    if verify_result(task, artifacts) is not True:
        raise Blocked("RESULT_GATE: independent verification failed")
    return artifacts

if __name__ == "__main__":
    if sys.argv[1:] != ["--status"]:
        print("BLOCKER: direct tool use forbidden", file=sys.stderr)
        sys.exit(2)
    for issue in policy_issues(ROOT):
        print("BLOCKER:", issue)
    sys.exit(1 if policy_issues(ROOT) else 0)
