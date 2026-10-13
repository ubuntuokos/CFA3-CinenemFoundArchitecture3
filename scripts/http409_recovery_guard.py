"""Fail-closed HTTP 409 recovery policy gate (v1.1).

The caller must route every recovery mutation through authorize_recovery and
provide fresh, independently obtained resource state. This module never
performs writes or claims that external, unmediated callers are protected.
"""
from dataclasses import dataclass
from enum import Enum

POLICY_ID = "CFA3-POLICY-HTTP-409-CONFLICT-RECOVERY-001"
VERSION = "1.1"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    STOP = "STOP"
    RECHECK = "RECHECK"


@dataclass(frozen=True)
class RecoveryResult:
    decision: Decision
    reason: str
    policy: str = POLICY_ID
    version: str = VERSION


def authorize_recovery(event, *, observed, scope, authority, evidence):
    """Authorize one targeted correction; all mandatory inputs are fail-closed.

    Required mappings are supplied by independent, authenticated adapters.
    No unverified assertion in event can grant permissions or prove freshness.
    """
    for item in (event, observed, scope, authority, evidence):
        if not isinstance(item, dict):
            return RecoveryResult(Decision.STOP, "INVALID_CONTRACT")
    if event.get("http_status") != 409:
        return RecoveryResult(Decision.STOP, "NOT_HTTP_409")
    if not all(isinstance(event.get(k), str) and event[k] for k in
               ("method", "endpoint", "resource", "operation_id", "cause")):
        return RecoveryResult(Decision.STOP, "UNIDENTIFIED_CONFLICT")
    if event.get("operation_id") != scope.get("operation_id"):
        return RecoveryResult(Decision.STOP, "SCOPE_MISMATCH")
    if scope.get("approved") is not True or scope.get("directly_necessary") is not True:
        return RecoveryResult(Decision.STOP, "OUT_OF_SCOPE")
    if event.get("action") not in ("refresh_precondition", "sequential_update",
                                   "correct_create_update", "correct_order"):
        return RecoveryResult(Decision.STOP, "ACTION_NOT_ALLOWED")
    if event.get("resource") != observed.get("resource") or not observed.get("version"):
        return RecoveryResult(Decision.STOP, "RESOURCE_NOT_VERIFIED")
    if observed.get("verified_independently") is not True:
        return RecoveryResult(Decision.STOP, "UNTRUSTED_EXACT_STATE")
    if observed.get("fresh") is not True:
        return RecoveryResult(Decision.RECHECK, "STALE_EXACT_STATE")
    if observed.get("precondition_matches") is not True:
        return RecoveryResult(Decision.RECHECK, "PRECONDITION_CHANGED")
    if authority.get("action_permitted") is not True:
        return RecoveryResult(Decision.STOP, "NO_AUTHORITY")
    if any(event.get(k) is True for k in ("force_push", "merge", "rebase",
                                          "new_pr", "cross_branch_change")):
        return RecoveryResult(Decision.STOP, "SENSITIVE_ACTION")
    if authority.get("content_decision_required") is True:
        return RecoveryResult(Decision.STOP, "OWNER_DECISION_REQUIRED")
    if evidence.get("third_party_changes_preserved") is not True:
        return RecoveryResult(Decision.STOP, "PRESERVATION_UNPROVEN")
    if evidence.get("security_gates_pass") is not True:
        return RecoveryResult(Decision.STOP, "SECURITY_GATE_UNPROVEN")
    if evidence.get("serialized_write") is not True:
        return RecoveryResult(Decision.STOP, "PARALLEL_WRITE")
    if event.get("attempt", 0) != 0 or evidence.get("same_failure_repeated") is True:
        return RecoveryResult(Decision.STOP, "RETRY_CYCLE_BLOCKED")
    if evidence.get("failure_recorded") is not True:
        return RecoveryResult(Decision.STOP, "AUDIT_MISSING")
    return RecoveryResult(Decision.ALLOW, "ONE_CONDITIONAL_ATTEMPT")


def verify_recovery(*, before, after, receipt):
    """A successful API response alone is insufficient for closure."""
    if not all(isinstance(x, dict) for x in (before, after, receipt)):
        return RecoveryResult(Decision.STOP, "INVALID_PROOF")
    if (before.get("resource") != after.get("resource") or
            after.get("readback_verified") is not True or
            after.get("version") is None or
            before.get("version") == after.get("version") or
            receipt.get("original_task_resumed") is not True or
            receipt.get("unauthorized_changes") is not False or
            receipt.get("original_conflict_resolved") is not True):
        return RecoveryResult(Decision.STOP, "RECOVERY_NOT_PROVEN")
    return RecoveryResult(Decision.ALLOW, "RECOVERY_VERIFIED_NOT_LONG_TERM_RUNTIME_PASS")
