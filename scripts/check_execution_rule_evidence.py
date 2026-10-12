#!/usr/bin/env python3
"""Validate independently attested evidence for each currently known DEV/AI rule.

A receipt is NOT a check implemented by this module. Only the isolated trusted
rule attester may issue its own HMAC receipts after actually evaluating the
identified rule. All rules must be accounted for; missing receipt => STOP.
The historical inventory and runtime admission remain separately fail-closed.
"""
import hashlib
import hmac
import json
import math
import re
import time
from pathlib import Path

SCHEMA = "cfa3.execution-guard-rule-receipt.v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GOV = "canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
MAX_AGE_SECONDS = 60
MAX_EVIDENCE_BYTES = 131072
EVIDENCE_SCHEMA = "cfa3.execution-guard-rule-evidence.v1"

class RuleEvidenceBlocked(ValueError):
    pass

def bytes_canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def request_digest(task):
    if not isinstance(task, dict):
        raise RuleEvidenceBlocked("invalid task contract")
    data = {k: v for k, v in task.items() if k != "signature"}
    try:
        return hashlib.sha256(bytes_canonical(data)).hexdigest()
    except (TypeError, ValueError) as exc:
        raise RuleEvidenceBlocked("cannot canonicalize task contract") from exc

def expected_rules(governance):
    from check_execution_guard_rule_spec import SPEC, active_expected_codes
    try:
        root=Path(__file__).resolve().parents[1]
        owner=json.loads((root/SPEC).read_text("utf-8"))
        return active_expected_codes(governance,owner)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise RuleEvidenceBlocked("owner-authorized 83 rule identities missing") from exc

def original_expected_rules(governance):
    if not isinstance(governance, dict):
        raise RuleEvidenceBlocked("missing canonical governance")
    expected = {}
    for section, prefix in (("development_rules", "DEV"), ("ai_behavior_rules", "AI")):
        entries = governance.get(section)
        if not isinstance(entries, list) or len(entries) != 12:
            raise RuleEvidenceBlocked("canonical rule section size mismatch: " + section)
        for index, entry in enumerate(entries, 1):
            if not isinstance(entry, dict):
                raise RuleEvidenceBlocked("invalid canonical rule entry")
            ident, code = entry.get("id"), entry.get("code")
            if ident != "%s-%02d" % (prefix, index) or not isinstance(code, str) or not code:
                raise RuleEvidenceBlocked("unknown canonical DEV/AI rule")
            if ident in expected:
                raise RuleEvidenceBlocked("duplicate canonical rule")
            expected[ident] = code
    if len(expected) != 24:
        raise RuleEvidenceBlocked("canonical rule count mismatch")
    return expected

def verify_evidence_bytes(receipt, evidence_resolver):
    """Content-addressed independent evidence, not a hash-only assertion.

    The resolver must fetch from a protected evidence store, not from the
    requesting agent. Matching JSON metadata is necessary, never sufficient
    to prove a gate actually ran; the real producer remains separately trusted.
    """
    if not callable(evidence_resolver):
        raise RuleEvidenceBlocked("trusted evidence content resolver missing")
    ident = receipt["rule_id"]
    digest = receipt["evidence_sha256"]
    try:
        raw = evidence_resolver(ident, digest)
    except Exception as exc:
        raise RuleEvidenceBlocked("independent rule evidence unreadable: " + ident) from exc
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_EVIDENCE_BYTES:
        raise RuleEvidenceBlocked("rule evidence missing or oversized: " + ident)
    observed = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(observed, digest):
        raise RuleEvidenceBlocked("rule evidence body SHA-256 mismatch: " + ident)
    try:
        body = json.loads(raw.decode("utf-8"))
        if (type(body) is not dict or bytes_canonical(body) != raw):
            raise ValueError("evidence encoding not canonical")
    except (UnicodeError, ValueError, TypeError) as exc:
        raise RuleEvidenceBlocked("rule evidence not canonical JSON: " + ident) from exc
    expected_fields = ("rule_id", "code", "task_sha256", "governance_sha256",
                       "main_sha", "gate_id", "verdict", "checked_at")
    for field in expected_fields:
        if body.get(field) != receipt.get(field) or type(body.get(field)) is not type(receipt.get(field)):
            raise RuleEvidenceBlocked("rule evidence content disagrees with signed receipt: " + ident + ":" + field)
    if body.get("schema") != EVIDENCE_SCHEMA:
        raise RuleEvidenceBlocked("unrecognized rule evidence schema: " + ident)
    implementation = body.get("evaluator_sha256")
    if not isinstance(implementation, str) or SHA256.fullmatch(implementation) is None:
        raise RuleEvidenceBlocked("rule evaluator implementation fingerprint absent: " + ident)
    return True

def verify_rule_receipts(task, receipts, governance, attestation_secret, now=None,
                         evidence_resolver=None):
    """All 83 signed, scoped, fresh receipts required. No untrusted model PASS."""
    if (not isinstance(attestation_secret, bytes) or len(attestation_secret) < 32):
        raise RuleEvidenceBlocked("trusted independent attestation key missing")
    if not callable(evidence_resolver):
        raise RuleEvidenceBlocked("trusted independent evidence resolver missing")
    if not isinstance(receipts, list):
        raise RuleEvidenceBlocked("signed rule evidence must be a list")
    expected = expected_rules(governance)
    if len(receipts) != len(expected):
        raise RuleEvidenceBlocked("83 independent rule verdicts required")
    if not isinstance(task, dict) or not isinstance(task.get("source_hashes"), dict):
        raise RuleEvidenceBlocked("missing task source bindings")
    src = task["source_hashes"].get(GOV)
    if not isinstance(src, str) or SHA256.fullmatch(src) is None:
        raise RuleEvidenceBlocked("canonical governance digest missing")
    when = time.time() if now is None else now
    if type(when) not in (float, int) or not math.isfinite(when):
        raise RuleEvidenceBlocked("trusted time unavailable")
    digest = request_digest(task)
    found = set()
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise RuleEvidenceBlocked("malformed rule receipt")
        ident, code = receipt.get("rule_id"), receipt.get("code")
        if ident not in expected or ident in found:
            raise RuleEvidenceBlocked("unknown or duplicate rule receipt")
        found.add(ident)
        if code != expected[ident] or receipt.get("schema") != SCHEMA:
            raise RuleEvidenceBlocked("rule identity/code/schema mismatch: " + ident)
        if receipt.get("task_sha256") != digest or receipt.get("governance_sha256") != src:
            raise RuleEvidenceBlocked("rule attestation not bound to exact task/policy")
        if receipt.get("main_sha") != task.get("main_sha"):
            raise RuleEvidenceBlocked("rule attestation main SHA drift")
        if receipt.get("verdict") != "PASS":
            raise RuleEvidenceBlocked("rule not independently passed: " + ident)
        if receipt.get("gate_id") != "CFA3-RULE-GATE-" + ident:
            raise RuleEvidenceBlocked("unregistered rule gate identity: " + ident)
        evidence = receipt.get("evidence_sha256")
        if not isinstance(evidence, str) or SHA256.fullmatch(evidence) is None:
            raise RuleEvidenceBlocked("individual rule proof digest unavailable")
        at, until = receipt.get("checked_at"), receipt.get("expires_at")
        if (type(at) not in (float, int) or type(until) not in (float, int)
                or not math.isfinite(at) or not math.isfinite(until)
                or at > when or when - at > MAX_AGE_SECONDS
                or until <= when or until > task.get("expires_at", 0)):
            raise RuleEvidenceBlocked("expired, future-dated or non-fresh rule proof: " + ident)
        sig = receipt.get("signature")
        if not isinstance(sig, str) or SHA256.fullmatch(sig) is None:
            raise RuleEvidenceBlocked("independent rule signature missing: " + ident)
        signed = {k: v for k, v in receipt.items() if k != "signature"}
        actual = hmac.new(attestation_secret, bytes_canonical(signed),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, actual):
            raise RuleEvidenceBlocked("tampered or unauthenticated rule proof: " + ident)
        verify_evidence_bytes(receipt, evidence_resolver)
    if found != set(expected):
        raise RuleEvidenceBlocked("missing canonical rule proofs")
    return True

def bootstrap_rule_report(governance, catalog):
    """Validate 83 owner-admitted IDs/codes/status integrity, not unpredictable incidents.

    Bootstrap must neither cause an incident nor demand that a spontaneous
    violation has occurred. Runtime enforcers remain separately fail-closed.
    """
    from execution_guard import validate_current_rule_map
    issues = validate_current_rule_map(governance, catalog)
    try:
        expected = expected_rules(governance)
    except RuleEvidenceBlocked as exc:
        return [], issues + [str(exc)]
    if not isinstance(catalog, dict):
        return [], issues + ["rule catalog unavailable"]
    rules = catalog.get("rules")
    rules = rules if isinstance(rules, dict) else {}
    owner=catalog.get("owner_historical_reconciliation",{})
    if (not isinstance(owner,dict) or owner.get("source_count")!=78
            or owner.get("mapped_existing")!=22 or owner.get("admitted_new")!=56
            or owner.get("excluded_for_conflict")!=0 or owner.get("active_count")!=82
            or owner.get("all_source_rules_accounted_for") is not True):
        issues.append("owner-admitted 78 rule restoration incomplete")
    matrix = [(ident, code, rules.get(ident, {}).get("status", "MISSING")
               if isinstance(rules.get(ident), dict) else "MISSING")
              for ident, code in sorted(expected.items())]
    verified = all(state == "VERIFIED_GATE" for _, _, state in matrix)
    independently_attested = catalog.get("independent_evidence_verified") is True
    if verified != independently_attested:
        issues.append("runtime gate status and independent evidence claims disagree")
    if catalog.get("coverage_complete") is True and not (verified and independently_attested):
        issues.append("full coverage declared without independent gate evidence")
    return matrix, issues


def bootstrap_main():
    """This always remains a source/contract check, never a runtime event replay."""
    import sys
    from pathlib import Path
    from execution_guard import load, GOV, CATALOG
    if sys.argv[1:] != ["--bootstrap-report"]:
        print("usage: check_execution_rule_evidence.py --bootstrap-report", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    try:
        matrix, issues = bootstrap_rule_report(load(root, GOV), load(root, CATALOG))
    except (OSError, ValueError, TypeError) as exc:
        print("CFA3_RULE_MATRIX_BLOCKED:", type(exc).__name__, file=sys.stderr)
        return 1
    for ident, code, status in matrix:
        print("CFA3_RULE:", ident, code, status, "(structural inventory only)")
    if issues:
        for issue in issues:
            print("CFA3_RULE_MATRIX_FAIL:", issue, file=sys.stderr)
        return 1
    pending = sum(state != "VERIFIED_GATE" for _, _, state in matrix)
    print("CFA3_RULE_MATRIX_STRUCTURAL_PASS: 82 current owner-admitted rule identities;"
          " conditional runtime events are NOT required by bootstrap;"
          " pending rule statuses:", pending, "(informational); NOT execution authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(bootstrap_main())
