"""CFA3 Qt6 Python frontend launch adapter for generic Linux.

This adapter configures a *child* application before Qt initialization.
It is not a replacement for CFA3 security, rights, Workload Mode, installer
or a real parent application. A successful preflight is NOT a physical GUI PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import sys
from typing import Callable, Mapping, Sequence

from .preferences import (
    RuntimeConfigurationError, environment_for_next_launch, load_preferences,
)
from .qt6_environment import inspect_runtime


class RuntimeLaunchBlocked(RuntimeError):
    """No child process was started, or the requested process failed to start."""


@dataclass(frozen=True)
class PreparedLaunch:
    """Validated request for a Python/PySide6 Qt6 GUI child, never a PASS."""

    argv: tuple[str, ...]
    environment: dict[str, str]
    platform: str
    qt_version: str
    readiness: str = "APP_RUNTIME_READY"
    physical_gui_pass: bool = False
    parent_integration_gui_pass: bool = False


def prepare_python_qt_launch(
    argv: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
    preferences: dict | None = None,
    probe: Callable[..., dict] = inspect_runtime,
    python_executable: str | None = None,
) -> PreparedLaunch:
    """Fail closed before launching the explicitly identified Qt6 child.

    The argument vector is supplied by the CFA3 parent/launcher:
    no command-line shell interpolation, auto package installation, or silent
    Wayland-to-X11 fallback. The probe uses the exact child environment.
    Python Qt6 preflight is not suitable to certify native Qt/C++ binaries.
    """
    if (not isinstance(argv, (list, tuple)) or not argv
            or any(not isinstance(x, str) or not x or "\x00" in x for x in argv)):
        raise RuntimeLaunchBlocked("INVALID_EXECUTABLE_ARGUMENT_VECTOR")
    env = dict(os.environ if environment is None else environment)
    try:
        configured = environment_for_next_launch(
            environment=env,
            preferences=load_preferences() if preferences is None else preferences,
        )
    except RuntimeConfigurationError as exc:
        raise RuntimeLaunchBlocked("QT6_CONFIGURATION_BLOCKED:" + str(exc)) from exc
    report = probe(environment=configured,
                   python_executable=python_executable or sys.executable)
    if not isinstance(report, dict) or report.get("status") != "APP_RUNTIME_READY":
        status = report.get("status", "MALFORMED_QT6_PROBE") if isinstance(report, dict) else "MALFORMED_QT6_PROBE"
        raise RuntimeLaunchBlocked("QT6_PREFLIGHT_BLOCKED:" + str(status))
    platform = report.get("qt_platform")
    version = report.get("qt_version")
    if (platform not in ("wayland", "xcb")
            or not isinstance(version, str) or not version
            or report.get("physical_gui_pass") is not False
            or report.get("parent_integration_gui_pass") is not False):
        raise RuntimeLaunchBlocked("UNTRUSTED_QT6_PREFLIGHT_REPORT")
    return PreparedLaunch(
        argv=tuple(argv),
        environment=configured,
        platform=platform,
        qt_version=version,
    )


def run_prepared_launch(
    plan: PreparedLaunch,
    *,
    runner: Callable[..., object] = subprocess.run,
) -> int:
    """Execute exactly once with a checked argv/environment, preserving exit code.

    This starts only a local process the calling CFA3 launcher explicitly
    selected. No shell and no GPU/Qt backend substitution are permitted.
    """
    if not isinstance(plan, PreparedLaunch) or plan.readiness != "APP_RUNTIME_READY":
        raise RuntimeLaunchBlocked("APP_RUNTIME_GATE_NOT_ADMITTED")
    if plan.physical_gui_pass or plan.parent_integration_gui_pass:
        raise RuntimeLaunchBlocked("INVALID_PHYSICAL_GUI_ATTESTATION")
    try:
        finished = runner(list(plan.argv), env=dict(plan.environment),
                          shell=False, check=False)
    except (OSError, ValueError) as exc:
        raise RuntimeLaunchBlocked("APP_PROCESS_START_FAILED") from exc
    code = getattr(finished, "returncode", None)
    if type(code) is not int:
        raise RuntimeLaunchBlocked("APP_PROCESS_RESULT_INVALID")
    return code


def launch_python_qt_frontend(
    argv: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
    preferences: dict | None = None,
    probe: Callable[..., dict] = inspect_runtime,
    python_executable: str | None = None,
    runner: Callable[..., object] = subprocess.run,
) -> int:
    """Perform one explicit Qt6 preflight, then launch the requested child."""
    plan = prepare_python_qt_launch(
        argv,
        environment=environment,
        preferences=preferences,
        probe=probe,
        python_executable=python_executable,
    )
    return run_prepared_launch(plan, runner=runner)
