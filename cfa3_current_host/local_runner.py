"""Local CFA3-owned reference test runner, not a physical PASS issuer.

For execution ON the actual target host. Test selection is strictly limited to
the CFA3 Current Host's own Python and native Rust tests. It does not inspect
or qualify any installed vendor driver, commercial app or community plugin.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from .foundation_runtime import (
    CpuResourceBroker, FoundationRuntime, Mode, ModelRouter, Request,
    RightsAuthority, SecurityAuthority, WorkloadModeBroker,
)


class LocalTestError(ValueError):
    pass


def _run(argv, root: Path, timeout: int = 120):
    try:
        p = subprocess.run(
            argv, cwd=root, shell=False, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", check=False,
        )
        return {"result": "REFERENCE_PASS" if p.returncode == 0 else "REFERENCE_FAIL",
                "returncode": p.returncode, "transcript_tail": p.stdout[-20000:]}
    except subprocess.TimeoutExpired:
        return {"result": "TIMEOUT", "returncode": None,
                "transcript_tail": "test exceeded bounded runtime"}


def run_cfa3_owned_reference_tests(repo_root: Path) -> dict:
    """Collect scoped observed process results with no authority promotion.

    The report is a reference result, not proof of physical hardware identity,
    code provenance, trusted runtime admission or real host compliance. The
    external Evidence authority must separately inspect and attest it.
    """
    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise LocalTestError("repository root does not exist")
    required = [
        "Cargo.toml", "cfa3_current_host/core.py",
        "cfa3_current_host/plugin_fabric.py",
        "crates/cfa3-current-host/Cargo.toml",
        "tests/test_current_host_core.py",
    ]
    if any(not (root / file).is_file() for file in required):
        raise LocalTestError("not a full CFA3 Current Host source checkout")
    # This source locator is informational only, not an authority signature.
    try:
        git = _run(["git", "rev-parse", "HEAD"], root, timeout=10)
        commit = git["transcript_tail"].strip() if git["result"] == "REFERENCE_PASS" else None
    except FileNotFoundError:
        commit = None
    if not commit or len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
        commit = "UNVERIFIED_CHECKOUT"
    # The test runner itself operates under the locally enforced CPU
    # Foundation mode/HRB/security/rights lease. These are explicit *reference*
    # grants for CFA3-owned source, NOT production rights or physical PASS.
    digest = "sha256:" + hashlib.sha256(
        (root / "cfa3_current_host/core.py").read_bytes()
    ).hexdigest()
    foundation = FoundationRuntime(
        security=SecurityAuthority([
            ("current-host-selftest", "cfa3-current-host", "run", "cfa3.current-host"),
        ]),
        rights=RightsAuthority([digest]),
        model_router=ModelRouter(),
        hrb=CpuResourceBroker(1),
        modes=WorkloadModeBroker(),
    )
    session = foundation.start(Request(
        actor="current-host-selftest", component="cfa3-current-host",
        operation="run", capability="cfa3.current-host",
        artifact_digest=digest, cpu_threads=1, mode=Mode.INTERACTIVE,
        ttl_seconds=600,
    ))
    active_mode = foundation.modes.indicator
    try:
        python_suite = _run([
            sys.executable, "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_current_host*.py", "-v",
        ], root)
        cargo = shutil.which("cargo")
        rust_suite = (_run([cargo, "test", "--package", "cfa3-current-host"],
                           root, timeout=240) if cargo else
                      {"result": "NOT_RUN_MISSING_CARGO", "returncode": None,
                       "transcript_tail": "Rust verification pending (cargo not installed)"})
    finally:
        foundation.finish(session)
    # Deliberately no driver scanning, GPU probing or third-party binary runs.
    environment = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_only_reference_path": True,
        "manufacturer_drivers_qualified": False,
        "commercial_software_qualified": False,
        "community_plugin_product_qa": False,
    }
    digest_input = json.dumps(environment, sort_keys=True).encode("utf-8")
    return {
        "schema": "cfa3.current-host.local-observation.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": commit,
        "environment_digest": "sha256:" + hashlib.sha256(digest_input).hexdigest(),
        "environment": environment,
        "local_foundation": {
            "mode_during_tests": active_mode,
            "mode_after_release": foundation.modes.indicator,
            "cpu_threads_after_release": foundation.hrb.allocated,
            "authority": "LOCAL_REFERENCE_ONLY",
        },
        "python_tests": python_suite,
        "rust_tests": rust_suite,
        "evidence_status": "REFERENCE_ONLY_PENDING_EXTERNAL_AUTHORITY",
        "physical_current_host_pass": False,
        "admission": "NOT_ADMITTED",
    }
