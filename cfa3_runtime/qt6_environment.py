"""Portable Qt6 environment broker for the CFA3 Linux application shell.

Reads the current desktop environment; never installs dependencies, changes
QT_QPA_PLATFORM, starts a vendor driver, or asserts physical GUI evidence.
PySide6 here is the Qt6 GUI bridge, not a required Python developer toolchain
for end users of packaged/native CFA3 applications.
"""
from __future__ import annotations

from ctypes.util import find_library
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Mapping

MIN_QT = (6, 8)
INTERACTIVE_PLATFORMS = frozenset(("wayland", "xcb"))

_QT_PROBE_SCRIPT = r"""
import json
from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QLibraryInfo, qVersion
from PySide6.QtWidgets import QApplication, QWidget
app = QApplication([])
widget = QWidget()
report = {
    "qt_version": qVersion(),
    "pyside_version": pyside_version,
    "platform": app.platformName(),
    "screens": [s.name() for s in app.screens()],
    "plugins_path": QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath),
    "widget_constructed": widget is not None,
}
widget.close()
print(json.dumps(report, ensure_ascii=False))
"""


def _version(value: str) -> tuple[int, int, int] | None:
    matched = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", str(value))
    if not matched:
        return None
    return (int(matched[1]), int(matched[2]), int(matched[3] or 0))


def _run_qt_probe(python: str, environment: Mapping[str, str]) -> dict:
    """Isolate native Qt plugin loading from the main CFA3 application."""
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout, tempfile.TemporaryFile(mode="w+b") as stderr:
            completed = subprocess.run(
                [python, "-c", _QT_PROBE_SCRIPT],
                env=dict(environment), stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, timeout=10, check=False,
                shell=False,
            )
            stdout.seek(0)
            stderr.seek(0)
            raw = stdout.read(16385)
            details = stderr.read(1025)
        if completed.returncode or len(raw) > 16384 or len(details) > 1024:
            return {"error": "QT6_PROCESS_OR_PLUGIN_FAILURE"}
        report = json.loads(raw.decode("utf-8"))
        if not isinstance(report, dict):
            return {"error": "QT6_INVALID_PROBE_RESULT"}
        return report
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        return {"error": "QT6_PROBE_UNAVAILABLE"}


def detect_display_hint(environment: Mapping[str, str]) -> str:
    """Informational hint only: the Qt platform plugin is authoritative."""
    if environment.get("WAYLAND_DISPLAY"):
        return "WAYLAND_AVAILABLE"
    if environment.get("DISPLAY"):
        return "X11_AVAILABLE"
    return "NO_GRAPHICAL_SESSION_HINT"


def inspect_runtime(*, environment: Mapping[str, str] | None = None,
                    python_executable: str | None = None) -> dict:
    """Return an explicit APP_RUNTIME gate, distinct from DEV_ENV_READY.

    This checks only the *current Python/Qt6 bridge*. Native Qt/C++ apps may
    use different bundling and must have their own validated runtime adapter.
    """
    env = dict(os.environ if environment is None else environment)
    requested = env.get("QT_QPA_PLATFORM", "")
    report = {
        "schema": "cfa3.portable-qt6-runtime.v1",
        "scope": "PYTHON_QT6_FRONTEND",
        "desktop_hint": detect_display_hint(env),
        "requested_platform": requested or "QT_AUTODETECT",
        "qt_platform": "UNKNOWN",
        "qt_version": None,
        "pyside_version": None,
        "plugin_path": None,
        "screens": [],
        "egl_library_detected": bool(find_library("EGL")),
        "opengl_library_detected": bool(find_library("OpenGL")),
        "status": "BLOCKED_QT6_PROBE",
        "reason": "QT6_NOT_VERIFIED",
        "automatic_installation": False,
        "physical_gui_pass": False,
        "standalone_gui_pass": False,
        "parent_integration_gui_pass": False,
    }
    observed = _run_qt_probe(python_executable or sys.executable, env)
    if observed.get("error"):
        report["reason"] = observed["error"]
        return report
    platform = observed.get("platform")
    version = _version(observed.get("qt_version", ""))
    screens = observed.get("screens")
    if not isinstance(screens, list) or any(not isinstance(x, str) for x in screens):
        report["reason"] = "QT6_MALFORMED_SCREEN_LIST"
        return report
    report.update({
        "qt_platform": platform if isinstance(platform, str) else "UNKNOWN",
        "qt_version": observed.get("qt_version"),
        "pyside_version": observed.get("pyside_version"),
        "plugin_path": observed.get("plugins_path"),
        "screens": screens,
    })
    if version is None or version[:2] < MIN_QT:
        report.update(status="BLOCKED_QT6_VERSION", reason="QT6_6_8_OR_NEWER_REQUIRED")
    elif not observed.get("widget_constructed"):
        report.update(status="BLOCKED_QT6_WIDGET", reason="QT6_WIDGET_NOT_CONSTRUCTED")
    elif platform in ("offscreen", "minimal", "vnc"):
        report.update(status="REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY",
                      reason="NONINTERACTIVE_QT_PLATFORM")
    elif platform not in INTERACTIVE_PLATFORMS or not screens:
        report.update(status="BLOCKED_QT6_PLATFORM",
                      reason="NO_SUPPORTED_LINUX_DESKTOP_OR_SCREEN")
    else:
        report.update(status="APP_RUNTIME_READY",
                      reason="QT6_WIDGET_AND_INTERACTIVE_PLATFORM_OBSERVED")
    return report


def _tool_version(program: str) -> str | None:
    location = shutil.which(program)
    if not location:
        return None
    try:
        result = subprocess.run([location, "--version"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, timeout=5, check=False, shell=False)
        return result.stdout.splitlines()[0][:160] if result.returncode == 0 and result.stdout else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def inspect_developer_tools() -> dict:
    """Developer-only tool inventory. Not an end-user runtime requirement."""
    python_ok = sys.version_info >= (3, 10)
    versions = {name: _tool_version(name) for name in ("cargo", "rustc", "cmake")}
    versions["python"] = ".".join(str(x) for x in sys.version_info[:3])
    available = python_ok and all(versions[name] for name in ("cargo", "rustc", "cmake"))
    return {
        "schema": "cfa3.developer-environment.v1",
        "tools": versions,
        "status": ("TOOLS_PRESENT_PENDING_BUILD_AND_QT_SDK_VERIFICATION"
                   if available else "DEV_ENV_MISSING_REQUIREMENTS"),
        "dev_env_ready": False,
        "end_user_runtime_requires_cargo_or_rustc": False,
    }
