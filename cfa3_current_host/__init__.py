"""CFA3 Current Host — structural planning and community-plugin host reference.

Real physical admission, external rights/security authorities and sandbox
execution are deliberately NOT implemented here.
"""
from .core import (
    Component, ContractError, ExternalEvidenceVerifier, Graph, Handoff,
    Level, Mode, Obligation, Ownership, Plan, Proof, TestKind,
    assess_for_external_admission,
)
from .plugin_fabric import (
    ExternalAdmissionAuthority, ExternalSandboxAuthority, Inspection,
    Manifest, PluginError, Registry, State, inspect_package,
)

__all__ = [
    "Component", "ContractError", "ExternalEvidenceVerifier", "Graph", "Handoff",
    "Level", "Mode", "Obligation", "Ownership", "Plan", "Proof", "TestKind",
    "assess_for_external_admission", "ExternalAdmissionAuthority",
    "ExternalSandboxAuthority", "Inspection", "Manifest", "PluginError",
    "Registry", "State", "inspect_package",
]
