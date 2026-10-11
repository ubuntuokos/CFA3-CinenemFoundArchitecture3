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

SCHEMA = "cfa3.execution-guard-rule-receipt.v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GOV = "canonical/policies/CFA3-REPOSITORY-GOVERNANCE-001.json"
MAX_AGE_SECONDS = 60

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

def verify_rule_receipts(task, receipts, governance, attestation_secret, now=None):
    """All 24 signed, scoped, fresh receipts required. No untrusted model PASS."""
    if (not isinstance(attestation_secret, bytes) or len(attestation_secret) < 32):
        raise RuleEvidenceBlocked("trusted independent attestation key missing")
    if not isinstance(receipts, list):
        raise RuleEvidenceBlocked("signed rule evidence must be a list")
    expected = expected_rules(governance)
    if len(receipts) != len(expected):
        raise RuleEvidenceBlocked("24 independent rule verdicts required")
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
    if found != set(expected):
        raise RuleEvidenceBlocked("missing canonical rule proofs")
    return True
