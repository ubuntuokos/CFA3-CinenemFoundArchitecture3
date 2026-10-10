"""CFA3 generic Linux Qt6 diagnostics and guarded Python frontend launcher.

The source checkout provides a standalone settings panel and a reusable
launch-module adapter, not a fabricated real CFA3 parent GUI or installer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from .launcher import RuntimeLaunchBlocked, launch_python_qt_frontend
from .qt6_environment import inspect_runtime, inspect_developer_tools


_MODULE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z", re.ASCII)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cfa3_runtime")
    command = parser.add_subparsers(dest="action", required=True)
    command.add_parser("inspect", help="inspect real Qt6 runtime and display platform")
    command.add_parser("developer-tools", help="inspect Python/Rust/Cargo developer tools")
    command.add_parser("settings", help="open Qt6 settings after guarded child preflight")
    command.add_parser("settings-window", help=argparse.SUPPRESS)
    entry = command.add_parser(
        "launch-module",
        help="launch an explicitly identified Python/Qt6 module after Qt6 preflight",
    )
    entry.add_argument("module", help="Python Qt6 frontend module")
    entry.add_argument("arguments", nargs=argparse.REMAINDER,
                       help="optional module arguments after --")
    args = parser.parse_args(argv)

    if args.action == "inspect":
        report = inspect_runtime()
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["status"] == "APP_RUNTIME_READY" else 2

    if args.action == "developer-tools":
        report = inspect_developer_tools()
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0  # Never issues DEV_ENV_READY or application admission.

    if args.action in ("settings", "launch-module"):
        if args.action == "settings":
            commandline = [sys.executable, "-m", "cfa3_runtime", "settings-window"]
        else:
            if not _MODULE.fullmatch(args.module):
                print(json.dumps({"status": "BLOCKED_INVALID_PYTHON_MODULE",
                                  "physical_gui_pass": False}))
                return 2
            extra = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
            commandline = [sys.executable, "-m", args.module, *extra]
        try:
            return launch_python_qt_frontend(commandline)
        except RuntimeLaunchBlocked as exc:
            print(json.dumps({"status": "BLOCKED_QT6_LAUNCH",
                              "reason": str(exc), "physical_gui_pass": False}))
            return 2

    if args.action == "settings-window":
        from PySide6.QtWidgets import QApplication
        from .settings_panel import Qt6RuntimeSettingsPanel
        app = QApplication([])
        window = Qt6RuntimeSettingsPanel(workload_mode="UNKNOWN")
        window.show()
        return app.exec()

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
