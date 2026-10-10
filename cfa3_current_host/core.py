"""CFA3 Current Host: scoped test selection and evidence boundary.

This is the CPU-only reference implementation of the Foundation/Layer/Global
planning contract. Only CFA3-owned code, hosts and connectors are in the
qualification scope. It never certifies hardware drivers, vendor software or
third-party plugins. No simulated or reference test can claim physical PASS.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ContractError(ValueError):
    pass


class Ownership(str, Enum):
    CFA3_COMPONENT = "CFA3_COMPONENT"
    CFA3_CONNECTOR = "CFA3_CONNECTOR"
    CFA3_PLUGIN_HOST = "CFA3_PLUGIN_HOST"
    VENDOR_DRIVER = "VENDOR_DRIVER"
    COMMERCIAL_SOFTWARE = "COMMERCIAL_SOFTWARE"
    COMMUNITY_PLUGIN = "COMMUNITY_PLUGIN"


class Mode(str, Enum):
    NONE = "NONE"
    SCOPED = "SCOPED"
    FULL = "FULL"


class Level(str, Enum):
    FOUNDATION = "FOUNDATION"
    LAYER = "LAYER"
    GLOBAL = "GLOBAL"


class TestKind(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    ROLLBACK = "ROLLBACK"
    STANDALONE_GUI = "STANDALONE_GUI"
    PARENT_GUI = "PARENT_INTEGRATION_GUI"
    HANDOFF = "HANDOFF"


CFA3_KINDS = frozenset({
    Ownership.CFA3_COMPONENT,
    Ownership.CFA3_CONNECTOR,
    Ownership.CFA3_PLUGIN_HOST,
})
FULL_TRIGGERS = frozenset({
    "GLOBAL_SECURITY_POLICY",
    "EVIDENCE_AUTHORITY",
    "GLOBAL_WORKLOAD_MODE_CONTRACT",
    "FOUNDATION_ABI",
})


@dataclass(frozen=True)
class Component:
    component_id: str
    layer: str
    revision: str
    ownership: Ownership
    capability_ids: tuple[str, ...] = ()
    gui: bool = False
    parent_id: str | None = None

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip() for x in
               (self.component_id, self.layer, self.revision)):
            raise ContractError("component ID, layer and revision required")
        if not isinstance(self.ownership, Ownership):
            raise ContractError("ownership must be an explicit enum")
        if len(set(self.capability_ids)) != len(self.capability_ids):
            raise ContractError("duplicate capability identifiers")
        if any(not isinstance(x, str) or not x for x in self.capability_ids):
            raise ContractError("invalid capability identifier")
        if self.parent_id == self.component_id:
            raise ContractError("component cannot parent itself")


@dataclass(frozen=True)
class Handoff:
    handoff_id: str
    producer_id: str
    consumer_id: str
    artifact_kind: str
    source_revision: str
    processing_owner: str
    acceptance_ref: str
    rollback_ref: str

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip() for x in (
            self.handoff_id, self.producer_id, self.consumer_id,
            self.artifact_kind, self.source_revision, self.processing_owner,
            self.acceptance_ref, self.rollback_ref
        )):
            raise ContractError("handoff needs exact origin, owner, acceptance and rollback")
        if self.producer_id == self.consumer_id:
            raise ContractError("self-handoff has no intercomponent boundary")


@dataclass(frozen=True)
class Obligation:
    level: Level
    component_id: str
    test: TestKind
    handoff_id: str | None = None


@dataclass(frozen=True)
class Plan:
    mode: Mode
    changed: tuple[str, ...]
    affected: tuple[str, ...]
    obligations: tuple[Obligation, ...]
    reason: str

    def __post_init__(self):
        if self.mode == Mode.NONE and (self.affected or self.obligations):
            raise ContractError("NONE may not carry hidden testing obligations")
        if self.mode != Mode.NONE and not self.obligations:
            raise ContractError("nonempty plan requires real obligations")


class Graph:
    def __init__(self):
        self.nodes: dict[str, Component] = {}
        self.edges: dict[str, Handoff] = {}

    def register_component(self, component: Component):
        if component.component_id in self.nodes:
            raise ContractError("duplicate component ID")
        self.nodes[component.component_id] = component

    def register_handoff(self, edge: Handoff):
        if edge.handoff_id in self.edges:
            raise ContractError("duplicate handoff ID")
        if edge.producer_id not in self.nodes or edge.consumer_id not in self.nodes:
            raise ContractError("handoff references unregistered component")
        producer = self.nodes[edge.producer_id]
        if producer.revision != edge.source_revision:
            raise ContractError("stale producer revision")
        if self.nodes[edge.consumer_id].ownership not in CFA3_KINDS:
            raise ContractError("CFA3 does not qualify external recipient products")
        self.edges[edge.handoff_id] = edge

    def _closure(self, changed: set[str]) -> set[str]:
        affected = set(changed)
        downstream: dict[str, list[str]] = {}
        for edge in self.edges.values():
            downstream.setdefault(edge.producer_id, []).append(edge.consumer_id)
        pending = deque(sorted(changed))
        while pending:
            cur = pending.popleft()
            for dst in downstream.get(cur, ()):
                if dst not in affected:
                    affected.add(dst)
                    pending.append(dst)
        return {name for name in affected if self.nodes[name].ownership in CFA3_KINDS}

    def plan(self, changed_ids, *, trigger: str = "CODE") -> Plan:
        ids = tuple(sorted(set(changed_ids)))
        if any(name not in self.nodes for name in ids):
            raise ContractError("unknown component in change scope")
        if not isinstance(trigger, str) or not trigger:
            raise ContractError("change trigger required")
        ours = {name for name in ids if self.nodes[name].ownership in CFA3_KINDS}
        # A vendor/third-party software update does not create a CFA3 test
        # obligation by itself. The CFA3 bridge is explicitly modeled as ours.
        if not ours:
            return Plan(Mode.NONE, ids, (), (), "EXTERNAL_PRODUCT_OUTSIDE_CFA3_SCOPE")
        if trigger in FULL_TRIGGERS:
            affected = {name for name, item in self.nodes.items() if item.ownership in CFA3_KINDS}
            mode = Mode.FULL
        else:
            affected = self._closure(ours)
            mode = Mode.SCOPED
        ordered: list[Obligation] = []
        for name in sorted(affected):
            node = self.nodes[name]
            level = Level.FOUNDATION if node.layer == "FOUNDATION" else Level.LAYER
            for kind in (TestKind.POSITIVE, TestKind.NEGATIVE, TestKind.ROLLBACK):
                ordered.append(Obligation(level, name, kind))
            if node.gui:
                ordered.append(Obligation(level, name, TestKind.STANDALONE_GUI))
                if node.parent_id is not None:
                    if node.parent_id not in self.nodes:
                        raise ContractError("real GUI parent not registered")
                    ordered.append(Obligation(level, name, TestKind.PARENT_GUI))
        # Only explicitly registered, genuinely affected handoffs are tested.
        for edge in sorted(self.edges.values(), key=lambda x: x.handoff_id):
            # A changed CFA3-owned recipient must prove its *inbound* bridge,
            # even if its source is unchanged or an external vendor product.
            # This tests the CFA3 interface, never the vendor's product.
            if edge.consumer_id in affected:
                source = self.nodes[edge.producer_id]
                target = self.nodes[edge.consumer_id]
                level = (Level.GLOBAL if source.ownership in CFA3_KINDS
                         and source.layer != target.layer else
                         Level.FOUNDATION if target.layer == "FOUNDATION" else Level.LAYER)
                ordered.append(Obligation(level, edge.consumer_id,
                                          TestKind.HANDOFF, edge.handoff_id))
        return Plan(mode, ids, tuple(sorted(affected)), tuple(ordered),
                    "GLOBAL_CONTRACT_CHANGED" if mode == Mode.FULL else "REAL_EDGE_IMPACT")


@dataclass(frozen=True)
class Proof:
    obligation: Obligation
    component_revision: str
    physical_host_id: str
    evidence_digest: str
    authority_receipt_id: str
    physical: bool
    result: str


class ExternalEvidenceVerifier:
    """Interface only. Supplied by the *real*, separately admitted CFA3 Evidence authority."""

    def verify_physical_proof(self, proof: Proof) -> bool:
        raise NotImplementedError


def assess_for_external_admission(plan: Plan, graph: Graph,
                                  proofs: tuple[Proof, ...],
                                  authority: ExternalEvidenceVerifier | None = None) -> dict:
    """Report evidence completeness, never claim or issue a physical PASS.

    Even when a real external verifier validates every proof, this routine
    returns READY_FOR_AUTHORITY_REVIEW, not Current Host PASS. Production
    admission remains exclusively with the external Evidence authority.
    """
    if plan.mode == Mode.NONE:
        return {"status": "NO_TEST_REQUIRED", "authority_pass": False,
                "checked": 0, "required": 0}
    by_obligation: dict[Obligation, Proof] = {}
    for proof in proofs:
        if proof.obligation in by_obligation:
            return {"status": "BLOCKED_DUPLICATE_PROOF", "authority_pass": False}
        by_obligation[proof.obligation] = proof
    for obligation in plan.obligations:
        proof = by_obligation.get(obligation)
        if proof is None:
            return {"status": "PENDING_MISSING_PROOFS", "authority_pass": False,
                    "required": len(plan.obligations), "checked": len(by_obligation)}
        node = graph.nodes[obligation.component_id]
        if (not proof.physical or proof.result != "PASS"
                or proof.component_revision != node.revision
                or any(not x for x in (
                    proof.physical_host_id, proof.evidence_digest, proof.authority_receipt_id
                ))):
            return {"status": "BLOCKED_UNQUALIFIED_PROOF", "authority_pass": False}
        if authority is None or not authority.verify_physical_proof(proof):
            return {"status": "PENDING_EXTERNAL_AUTHORITY", "authority_pass": False}
    return {"status": "READY_FOR_AUTHORITY_REVIEW", "authority_pass": False,
            "checked": len(plan.obligations), "required": len(plan.obligations)}
