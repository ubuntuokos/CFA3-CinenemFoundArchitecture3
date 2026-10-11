#!/usr/bin/env python3
"""Verify an independently signed, exactly scoped CFA3 owner authorization.

The signing key and evidence loader MUST be controlled by the owner authority,
outside the agent or repository. This is a validator, NOT a grant issuer and
NOT a globally deployed gateway.
"""
import hashlib
import hmac
import json
import math
import re
import time

from check_execution_rule_evidence import request_digest, RuleEvidenceBlocked

SCHEMA = "cfa3.execution-guard-owner-authorization.v1"
SIGNATURE = re.compile(r"^[0-9a-f]{64}$")
MAX_GRANT_AGE_SECONDS = 300
EXPECTED = frozenset({
    "schema", "approved", "task_sha256", "task_id", "nonce",
    "operation", "target", "scope_targets", "main_sha", "head_sha", "branch",
    "issued_at", "expires_at", "signature",
})
ALLOWED_OPERATIONS = frozenset({"REPOSITORY_WRITE", "WORKFLOW_START"})

class OwnerGrantBlocked(ValueError):
    pass

def serialized(data):
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise OwnerGrantBlocked("invalid owner grant encoding") from exc

def verify_owner_grant(task, grant, key, *, now=None):
    if type(key) is not bytes or len(key) < 32:
        raise OwnerGrantBlocked("separate owner-authority key unavailable")
    if not isinstance(task, dict) or not isinstance(grant, dict):
        raise OwnerGrantBlocked("signed owner authorization absent")
    if set(grant) != EXPECTED or grant["schema"] != SCHEMA or grant["approved"] is not True:
        raise OwnerGrantBlocked("owner grant schema, fields or approval invalid")
    if task.get("operation") not in ALLOWED_OPERATIONS:
        raise OwnerGrantBlocked("owner grant unsupported for this operation")
    try:
        bound_sha = request_digest(task)
    except RuleEvidenceBlocked as exc:
        raise OwnerGrantBlocked("invalid signed task binding") from exc
    checks = {
        "task_sha256": bound_sha,
        "task_id": task.get("task_id"),
        "nonce": task.get("nonce"),
        "operation": task.get("operation"),
        "target": task.get("target"),
        "scope_targets": task.get("scope_targets"),
        "main_sha": task.get("main_sha"),
        "head_sha": task.get("head_sha"),
        "branch": task.get("branch"),
    }
    for name, expected in checks.items():
        if grant.get(name) != expected or type(grant.get(name)) is not type(expected):
            raise OwnerGrantBlocked("authorization not bound to exact task: " + name)
    nonce = grant.get("nonce")
    if not isinstance(nonce, str) or len(nonce) < 8:
        raise OwnerGrantBlocked("owner authorization nonce missing")
    moment = time.time() if now is None else now
    issued, expires = grant.get("issued_at"), grant.get("expires_at")
    deadline = task.get("expires_at")
    if (type(moment) not in (int, float) or not math.isfinite(moment)
            or type(issued) not in (int, float) or not math.isfinite(issued)
            or type(expires) not in (int, float) or not math.isfinite(expires)
            or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or issued > moment or moment - issued > MAX_GRANT_AGE_SECONDS
            or expires <= moment or expires > deadline):
        raise OwnerGrantBlocked("owner approval stale, expired, future or exceeds task scope")
    sign = grant.get("signature")
    if not isinstance(sign, str) or SIGNATURE.fullmatch(sign) is None:
        raise OwnerGrantBlocked("owner authorization signature missing")
    payload = {k: v for k, v in grant.items() if k != "signature"}
    expected_sig = hmac.new(key, serialized(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sign, expected_sig):
        raise OwnerGrantBlocked("owner authorization signature invalid")
    return True
