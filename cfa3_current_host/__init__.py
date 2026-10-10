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

from .developer_sdk import build_bundle, run_static_testkit, scaffold_plugin
from .local_runner import LocalTestError, run_cfa3_owned_reference_tests
from .qt6_dashboard import CurrentHostDashboard, GuiDependencyMissing, standalone

__all__ = [
    "Component", "ContractError", "ExternalEvidenceVerifier", "Graph", "Handoff",
    "Level", "Mode", "Obligation", "Ownership", "Plan", "Proof", "TestKind",
    "assess_for_external_admission", "ExternalAdmissionAuthority",
    "ExternalSandboxAuthority", "Inspection", "Manifest", "PluginError",
    "Registry", "State", "inspect_package",
    "build_bundle", "run_static_testkit", "scaffold_plugin",
    "LocalTestError", "run_cfa3_owned_reference_tests",
    "CurrentHostDashboard", "GuiDependencyMissing", "standalone",
]
