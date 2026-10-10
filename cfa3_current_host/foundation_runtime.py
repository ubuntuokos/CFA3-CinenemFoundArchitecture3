"""CPU-only local CFA3 Foundation service and actual admission/lease enforcement.

Security grants, Model Router, HRB and Workload Mode are separate authorities
composed by this runtime. They do not import drivers, inspect vendor software,
or certify plugin implementations. The local implementation is a Foundation
bootstrap and not itself security-certified or physical Current Host PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import os
import threading
import time
import uuid


class FoundationDenied(RuntimeError):
    pass


class Mode(str, Enum):
    NONE = "NONE"
    AI = "AI"
    RENDER = "RENDER"
    INTERACTIVE = "INTERACTIVE"


@dataclass(frozen=True)
class Request:
    actor: str
    component: str
    operation: str
    capability: str
    artifact_digest: str
    cpu_threads: int
    mode: Mode
    model_id: str | None = None
    ttl_seconds: float = 60.0

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip()
               for x in (self.actor, self.component, self.operation,
                         self.capability, self.artifact_digest)):
            raise ValueError("actor, component, operation, capability and digest required")
        if not self.artifact_digest.startswith("sha256:") or len(self.artifact_digest) != 71:
            raise ValueError("SHA-256 artifact digest required")
        if any(c not in "0123456789abcdef" for c in self.artifact_digest[7:]):
            raise ValueError("lowercase SHA-256 digest required")
        if (type(self.cpu_threads) is not int or self.cpu_threads < 1
                or type(self.mode) is not Mode or self.mode is Mode.NONE
                or type(self.ttl_seconds) not in (float, int)
                or not math.isfinite(self.ttl_seconds)
                or not 0 < self.ttl_seconds <= 600):
            raise ValueError("bounded CPU request and explicit non-NONE mode required")
        if self.model_id is not None and (not isinstance(self.model_id, str)
                                           or not self.model_id.strip()):
            raise ValueError("model identifier cannot be empty")


class SecurityAuthority:
    """Explicit local policy: no grants are inferred from plugin manifests."""

    def __init__(self, grants=()):
        self._grants = frozenset(grants)

    def check(self, req: Request):
        if (req.actor, req.component, req.operation, req.capability) not in self._grants:
            raise FoundationDenied("SECURITY_GRANT_DENIED")


class RightsAuthority:
    """Requires externally reviewed exact SHA-256s; no license guesswork."""

    def __init__(self, approved_digests=()):
        self._approved = frozenset(approved_digests)

    def check(self, req: Request):
        if req.artifact_digest not in self._approved:
            raise FoundationDenied("ARTIFACT_RIGHTS_NOT_ADMITTED")


class ModelRouter:
    """One central exact CPU model-routing authority; no silent fallback."""

    def __init__(self, cpu_model_ids=()):
        self._cpu = frozenset(cpu_model_ids)

    def resolve(self, req: Request) -> str:
        if req.model_id is None:
            return "NO_MODEL_REQUIRED"
        if req.model_id not in self._cpu:
            raise FoundationDenied("MODEL_ROUTE_NOT_ADMITTED")
        return "CPU:" + req.model_id


class CpuResourceBroker:
    """One central bounded CPU lease broker for the local Foundation."""

    def __init__(self, total_threads: int):
        if type(total_threads) is not int or total_threads < 1:
            raise ValueError("at least one CPU thread required")
        self.total_threads = total_threads
        self._used = 0
        self._leases: dict[str, int] = {}
        self._lock = threading.RLock()

    def acquire(self, threads: int) -> str:
        with self._lock:
            if type(threads) is not int or threads < 1:
                raise ValueError("CPU lease must request positive integer threads")
            if threads > self.total_threads - self._used:
                raise FoundationDenied("HRB_CAPACITY_EXHAUSTED")
            lease = uuid.uuid4().hex
            self._leases[lease] = threads
            self._used += threads
            return lease

    def release(self, lease: str):
        with self._lock:
            slots = self._leases.pop(lease, None)
            if slots is None:
                raise FoundationDenied("UNKNOWN_HRB_LEASE")
            self._used -= slots

    @property
    def allocated(self) -> int:
        with self._lock:
            return self._used


class WorkloadModeBroker:
    """Mandatory global operating-mode indicator; incompatible modes block."""

    def __init__(self):
        self._active: dict[str, Mode] = {}
        self._lock = threading.RLock()

    @property
    def indicator(self) -> str:
        with self._lock:
            if not self._active:
                return Mode.NONE.value
            return next(iter(self._active.values())).value

    def acquire(self, mode: Mode) -> str:
        with self._lock:
            if type(mode) is not Mode or mode == Mode.NONE:
                raise FoundationDenied("INVALID_WORKLOAD_MODE")
            if self._active and any(m != mode for m in self._active.values()):
                raise FoundationDenied("WORKLOAD_MODE_CONFLICT")
            token = uuid.uuid4().hex
            self._active[token] = mode
            return token

    def release(self, token: str):
        with self._lock:
            if token not in self._active:
                raise FoundationDenied("UNKNOWN_MODE_TOKEN")
            del self._active[token]


@dataclass(frozen=True)
class Session:
    session_id: str
    request: Request
    route: str
    hrb_lease: str
    mode_lease: str
    deadline_monotonic: float


class FoundationRuntime:
    """Compose distinct authorities; no runtime- or physical-PASS issuance."""

    def __init__(self, *, security: SecurityAuthority, rights: RightsAuthority,
                 model_router: ModelRouter, hrb: CpuResourceBroker,
                 modes: WorkloadModeBroker):
        self.security = security
        self.rights = rights
        self.model_router = model_router
        self.hrb = hrb
        self.modes = modes
        self._live: dict[str, Session] = {}
        self._lock = threading.RLock()
        self._events: list[dict] = []

    @property
    def audit(self) -> tuple[dict, ...]:
        with self._lock:
            return tuple(dict(event) for event in self._events)

    def _record(self, event, session, detail):
        self._events.append({"event": event, "session_id": session,
                             "detail": detail, "monotonic": time.monotonic()})

    def start(self, request: Request) -> Session:
        with self._lock:
            self.security.check(request)
            self.rights.check(request)
            route = self.model_router.resolve(request)
            # Incompatible modes must not consume resource leases.
            mode_token = self.modes.acquire(request.mode)
            try:
                hrb_token = self.hrb.acquire(request.cpu_threads)
            except BaseException:
                self.modes.release(mode_token)
                raise
            session = Session(
                uuid.uuid4().hex, request, route, hrb_token, mode_token,
                time.monotonic() + request.ttl_seconds
            )
            self._live[session.session_id] = session
            self._record("ADMITTED_REFERENCE", session.session_id, route)
            return session

    def validate(self, session: Session):
        with self._lock:
            if (not isinstance(session, Session)
                    or self._live.get(session.session_id) != session):
                raise FoundationDenied("UNKNOWN_OR_CHANGED_SESSION")
            if time.monotonic() >= session.deadline_monotonic:
                raise FoundationDenied("EXPIRED_SESSION")

    def finish(self, session: Session):
        with self._lock:
            # Cleanup must work even after TTL expiry, without restoring authority.
            if (not isinstance(session, Session)
                    or self._live.get(session.session_id) != session):
                raise FoundationDenied("UNKNOWN_OR_CHANGED_SESSION")
            del self._live[session.session_id]
            self.hrb.release(session.hrb_lease)
            self.modes.release(session.mode_lease)
            self._record("RELEASED", session.session_id, "NONE")

    def run_owned_callable(self, session: Session, operation):
        """Execute an explicitly supplied CFA3-owned callable; never plugin code.

        This convenience path is for in-process CFA3 unit/reference operations
        only. It cannot preempt hung user code or make physical PASS.
        """
        self.validate(session)
        try:
            if not callable(operation):
                raise FoundationDenied("INVALID_CFA3_TEST_OPERATION")
            result = operation()
            return {"result": "REFERENCE_COMPLETED", "value": result,
                    "physical_current_host_pass": False}
        except BaseException:
            self._record("REFERENCE_FAILED", session.session_id, "operation-error")
            raise
        finally:
            self.finish(session)
