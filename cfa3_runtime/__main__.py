"""CFA3 portable Linux runtime diagnostics and settings launcher.

No installation, no sudo, no platform fallback and no physical GUI admission.
"""
from __future__ import annotations

import argparse
import json

from .qt6_environment import inspect_runtime, inspect_developer_tools


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cfa3_runtime")
    command = parser.add_subparsers(dest="action", required=True)
    command.add_parser("inspect", help="inspect real Qt6 runtime and display platform")
    command.add_parser("developer-tools", help="inspect Python/Rust/Cargo developer tools")
    command.add_parser("settings", help="open Qt6 settings panel in standalone reference mode")
    args = parser.parse_args(argv)
    if args.action == "inspect":
        report = inspect_runtime()
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["status"] == "APP_RUNTIME_READY" else 2
    if args.action == "developer-tools":
        report = inspect_developer_tools()
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0  # Report output is NOT DEV_ENV_READY or application admission.
    if args.action == "settings":
        from PySide6.QtWidgets import QApplication
        from .settings_panel import Qt6RuntimeSettingsPanel
        app = QApplication([])
        window = Qt6RuntimeSettingsPanel(workload_mode="UNKNOWN")
        window.show()
        return app.exec()
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
