#!/usr/bin/env python3
"""Verify signed acknowledgements from a separately controlled durable audit writer.

This module does not write evidence or mint signatures. A no-op callback, a
self-assertion by an agent, or mocked evidence can never certify physical
deployment or durable storage in production.
"""
import hashlib
import hmac
import json
import math
import re
import time

from check_execution_rule_evidence import request_digest, RuleEvidenceBlocked

SCHEMA = "cfa3.execution-guard-audit-receipt.v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FIELDS = frozenset((
    "schema", "task_sha256", "task_id", "nonce", "operation", "main_sha",
    "phase", "event_id", "store_id", "sequence", "previous_receipt_sha256",
    "durably_committed", "issued_at", "signature",
))
PHASES = frozenset(("RESERVED", "FAILED", "VERIFIED"))
MAX_AGE_SECONDS = 60

class AuditBlocked(ValueError):
    pass

def canonical_bytes(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError) as exc:
        raise AuditBlocked("cannot canonicalize audit evidence") from exc

def verify_audit_receipt(task, receipt, key, phase, *, previous=None, now=None):
    """Reject forged, stale, wrong-phase or unchained durable acknowledgements."""
    if type(key) is not bytes or len(key) < 32:
        raise AuditBlocked("trusted independent audit signing key unavailable")
    if not isinstance(task, dict) or not isinstance(receipt, dict):
        raise AuditBlocked("trusted independent audit receipt missing")
    if set(receipt) != FIELDS or receipt.get("schema") != SCHEMA:
        raise AuditBlocked("audit receipt schema or fields invalid")
    if phase not in PHASES or receipt.get("phase") != phase:
        raise AuditBlocked("audit phase mismatch")
    try:
        task_digest = request_digest(task)
    except RuleEvidenceBlocked as exc:
        raise AuditBlocked("cannot bind audit to exact task") from exc
    for k, v in (
        ("task_sha256", task_digest),
        ("task_id", task.get("task_id")),
        ("nonce", task.get("nonce")),
        ("operation", task.get("operation")),
        ("main_sha", task.get("main_sha")),
    ):
        if receipt.get(k) != v or type(receipt.get(k)) is not type(v):
            raise AuditBlocked("audit/task identity mismatch: " + k)
    if receipt.get("durably_committed") is not True:
        raise AuditBlocked("durable audit acknowledgement missing")
    event, store, seq = (receipt.get("event_id"), receipt.get("store_id"),
                         receipt.get("sequence"))
    if (not isinstance(event, str) or len(event) < 16 or
            not isinstance(store, str) or len(store) < 4 or
            type(seq) is not int or seq < 1):
        raise AuditBlocked("independent audit event, store or sequence invalid")
    if previous is None:
        if phase != "RESERVED" or receipt.get("previous_receipt_sha256") is not None:
            raise AuditBlocked("initial audit event must be standalone RESERVED")
    else:
        if (phase not in ("FAILED", "VERIFIED") or
                not isinstance(previous, dict) or previous.get("phase") != "RESERVED" or
                receipt.get("previous_receipt_sha256") != previous.get("sha256") or
                store != previous.get("store_id") or
                type(previous.get("sequence")) is not int or
                seq <= previous["sequence"] or
                event == previous.get("event_id")):
            raise AuditBlocked("audit chain/store continuity invalid")
    now = time.time() if now is None else now
    issued, expiry = receipt.get("issued_at"), task.get("expires_at")
    # DEV-01: after a RESERVED event, a signed FAILED acknowledgement may
    # report a late expiration. It never authorizes work or VERIFIED success,
    # and may only be issued and checked within 60s after task expiry.
    bounded_expired_failure = (
        phase == "FAILED" and previous is not None
        and type(now) in (int, float) and math.isfinite(now)
        and type(issued) in (int, float) and math.isfinite(issued)
        and type(expiry) in (int, float) and math.isfinite(expiry)
        and expiry <= issued <= now and 0 <= now - expiry <= MAX_AGE_SECONDS
    )
    if (type(now) not in (int, float) or not math.isfinite(now) or
            type(issued) not in (int, float) or not math.isfinite(issued) or
            type(expiry) not in (int, float) or not math.isfinite(expiry) or
            issued > now or now - issued > MAX_AGE_SECONDS or
            (now >= expiry and not bounded_expired_failure)):
        raise AuditBlocked("audit proof timestamp invalid, stale or task expired")
    signature = receipt.get("signature")
    if not isinstance(signature, str) or SHA256.fullmatch(signature) is None:
        raise AuditBlocked("audit proof signature missing")
    signed = {k: v for k, v in receipt.items() if k != "signature"}
    expected_sig = hmac.new(key, canonical_bytes(signed), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        raise AuditBlocked("audit proof signature mismatch")
    return {
        "phase": phase, "store_id": store, "sequence": seq, "event_id": event,
        "sha256": hashlib.sha256(canonical_bytes(receipt)).hexdigest(),
    }
