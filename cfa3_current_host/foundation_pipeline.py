"""Operational CPU bridge: Current Host proof plan -> Foundation authorities.

Only explicitly registered CFA3-owned test operations may run. A successful
reference test is not Physical Current Host PASS. GUI/physical host tests need
their actual environment and externally validated Evidence receipts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .core import CFA3_KINDS, Graph, Mode as PlanMode, Plan
from .foundation_runtime import (
    FoundationDenied, FoundationRuntime, Mode as WorkloadMode, Request,
)


class PipelineBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class BoundOperation:
    component_id: str
    test_case: str
    handoff_id: str | None
    source_revision: str
    source_digest: str
    runner: object

    def __post_init__(self):
        if (not self.component_id or not self.test_case or not self.source_revision
                or not isinstance(self.source_digest, str)
                or not self.source_digest.startswith("sha256:")
                or len(self.source_digest) != 71):
            raise ValueError("exact CFA3 component/revision/artifact binding required")
        if not callable(self.runner):
            raise PipelineBlocked("CFA3_TEST_RUNNER_REQUIRED")


class FoundationPipeline:
    """Bind a complete explicit plan; never discover or execute external code."""

    def __init__(self, graph: Graph, foundation: FoundationRuntime):
        self.graph = graph
        self.foundation = foundation
        self._runners: dict[tuple[str, str, str | None], BoundOperation] = {}

    def register(self, binding: BoundOperation):
        node = self.graph.nodes.get(binding.component_id)
        if node is None or node.ownership not in CFA3_KINDS:
            raise PipelineBlocked("EXTERNAL_COMPONENT_NOT_EXECUTABLE")
        if binding.source_revision != node.revision:
            raise PipelineBlocked("STALE_COMPONENT_REVISION")
        key = (binding.component_id, binding.test_case, binding.handoff_id)
        if key in self._runners:
            raise PipelineBlocked("DUPLICATE_TEST_BINDING")
        self._runners[key] = binding

    def execute(self, plan: Plan, *, actor: str, mode: WorkloadMode,
                model_id: str | None = None) -> dict:
        if not isinstance(plan, Plan):
            raise TypeError("Current Host structural plan required")
        if plan.mode == PlanMode.NONE:
            return {
                "status": "NO_CFA3_TEST_REQUIRED", "observations": (),
                "physical_current_host_pass": False,
            }
        # Preflight ALL selected capabilities to avoid starting partial tests
        # while a required GUI/handoff/rollback test has no implementation.
        pending = []
        for obligation in plan.obligations:
            key = (obligation.component_id, obligation.test.value, obligation.handoff_id)
            binding = self._runners.get(key)
            node = self.graph.nodes.get(obligation.component_id)
            if (binding is None or node is None or node.ownership not in CFA3_KINDS
                    or binding.source_revision != node.revision):
                pending.append(key)
        if pending:
            return {
                "status": "BLOCKED_MISSING_OR_STALE_CFA3_TESTS",
                "missing": tuple(pending), "observations": (),
                "physical_current_host_pass": False,
            }
        reports = []
        for obligation in plan.obligations:
            key = (obligation.component_id, obligation.test.value, obligation.handoff_id)
            binding = self._runners[key]
            request = Request(
                actor=actor, component=binding.component_id,
                operation="current-host." + binding.test_case.lower(),
                capability="cfa3.current-host",
                artifact_digest=binding.source_digest, cpu_threads=1,
                mode=mode, model_id=model_id,
            )
            try:
                lease = self.foundation.start(request)
                result = self.foundation.run_owned_callable(lease, binding.runner)
                # Local observations are not Evidence authority receipts.
                digest = hashlib.sha256(repr(result["value"]).encode("utf-8")).hexdigest()
                reports.append({
                    "component": obligation.component_id,
                    "case": obligation.test.value,
                    "handoff": obligation.handoff_id,
                    "reference_status": result["result"],
                    "local_output_digest": "sha256:" + digest,
                })
            except Exception as exc:
                return {
                    "status": "BLOCKED_OR_FAILED_CFA3_TEST",
                    "failed": key, "error_type": type(exc).__name__,
                    "observations": tuple(reports),
                    "physical_current_host_pass": False,
                }
        return {
            "status": "REFERENCE_TESTS_EXECUTED",
            "observations": tuple(reports),
            "physical_current_host_pass": False,
            "next_gate": "REAL_PHYSICAL_EVIDENCE_AUTHORITY",
        }
