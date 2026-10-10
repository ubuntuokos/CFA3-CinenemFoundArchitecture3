"""Portable CFA3 Qt6 Runtime Broker: no KDE assumption or fabricated proof."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cfa3_runtime.qt6_environment import (
    _version, detect_display_hint, inspect_runtime, inspect_developer_tools,
)
from cfa3_runtime.preferences import (
    RuntimeConfigurationError, load_preferences, save_preferences,
    environment_for_next_launch, preference_path,
)
from cfa3_runtime.__main__ import main


def observed(platform="wayland", version="6.10.2", screens=None):
    return {
        "platform": platform,
        "qt_version": version,
        "pyside_version": "6.10.3",
        "screens": ["DP-2"] if screens is None else screens,
        "plugins_path": "/usr/lib/x86_64-linux-gnu/qt6/plugins",
        "widget_constructed": True,
    }


class RuntimeProbeTests(unittest.TestCase):
    def evaluate(self, observation, environment=None):
        with patch("cfa3_runtime.qt6_environment._run_qt_probe",
                   return_value=observation):
            return inspect_runtime(environment=environment or {})

    def test_user_wayland_with_qt_6_10_is_ready_not_physical_pass(self):
        report = self.evaluate(observed(), {"WAYLAND_DISPLAY": "wayland-0"})
        self.assertEqual(report["status"], "APP_RUNTIME_READY")
        self.assertEqual(report["qt_platform"], "wayland")
        self.assertEqual(report["screens"], ["DP-2"])
        self.assertFalse(report["physical_gui_pass"])
        self.assertFalse(report["standalone_gui_pass"])
        self.assertFalse(report["parent_integration_gui_pass"])

    def test_x11_without_kde_is_ready(self):
        report = self.evaluate(observed(platform="xcb", screens=["HDMI-1"]),
                               {"DISPLAY": ":1", "XDG_CURRENT_DESKTOP": "GNOME"})
        self.assertEqual(report["status"], "APP_RUNTIME_READY")
        self.assertEqual(report["qt_platform"], "xcb")

    def test_no_xdg_desktop_name_is_not_a_blocker(self):
        report = self.evaluate(observed(platform="xcb"),
                               {"DISPLAY": ":0"})
        self.assertEqual(report["status"], "APP_RUNTIME_READY")

    def test_offscreen_is_reference_only_never_interactive_ready(self):
        report = self.evaluate(observed(platform="offscreen"),
                               {"QT_QPA_PLATFORM": "offscreen"})
        self.assertEqual(report["status"], "REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY")
        self.assertFalse(report["physical_gui_pass"])

    def test_minimal_qt_platform_is_reference_only(self):
        self.assertEqual(self.evaluate(observed(platform="minimal"))["status"],
                         "REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY")

    def test_unknown_qt_platform_blocks_without_fallback(self):
        report = self.evaluate(observed(platform="unsupported-custom"))
        self.assertEqual(report["status"], "BLOCKED_QT6_PLATFORM")
        self.assertEqual(report["requested_platform"], "QT_AUTODETECT")

    def test_no_screens_is_not_runtime_ready(self):
        self.assertEqual(self.evaluate(observed(screens=[]))["status"],
                         "BLOCKED_QT6_PLATFORM")

    def test_old_qt6_version_fails(self):
        report = self.evaluate(observed(version="6.7.3"))
        self.assertEqual(report["status"], "BLOCKED_QT6_VERSION")

    def test_invalid_qt_version_fails(self):
        report = self.evaluate(observed(version="garbled"))
        self.assertEqual(report["status"], "BLOCKED_QT6_VERSION")

    def test_unavailable_native_qt_plugin_fails_closed(self):
        report = self.evaluate({"error": "QT6_PROCESS_OR_PLUGIN_FAILURE"})
        self.assertEqual(report["status"], "BLOCKED_QT6_PROBE")
        self.assertFalse(report["automatic_installation"])

    def test_widget_failure_blocks_even_if_version_is_good(self):
        record = observed()
        record["widget_constructed"] = False
        self.assertEqual(self.evaluate(record)["status"], "BLOCKED_QT6_WIDGET")

    def test_environment_hint_does_not_depend_on_kde(self):
        self.assertEqual(detect_display_hint({"WAYLAND_DISPLAY": "wayland-0"}),
                         "WAYLAND_AVAILABLE")
        self.assertEqual(detect_display_hint({"DISPLAY": ":0"}), "X11_AVAILABLE")
        self.assertEqual(detect_display_hint({}), "NO_GRAPHICAL_SESSION_HINT")

    def test_version_comparison_is_numeric(self):
        self.assertGreater(_version("6.10.2"), _version("6.8.3"))
        self.assertIsNone(_version("Qt-6.8.3"))

    def test_developer_toolchain_is_not_mandatory_end_user_runtime(self):
        with patch("cfa3_runtime.qt6_environment._tool_version",
                   return_value=None):
            report = inspect_developer_tools()
        self.assertEqual(report["status"], "DEV_ENV_MISSING_REQUIREMENTS")
        self.assertFalse(report["dev_env_ready"])
        self.assertFalse(report["end_user_runtime_requires_cargo_or_rustc"])

    def test_cli_unready_exit_is_not_silent_pass(self):
        with patch("cfa3_runtime.__main__.inspect_runtime",
                   return_value={"status": "BLOCKED_QT6_PROBE"}), \
             patch("builtins.print"):
            self.assertEqual(main(["inspect"]), 2)

    def test_cli_ready_report_remains_reference_only(self):
        with patch("cfa3_runtime.__main__.inspect_runtime",
                   return_value={"status": "APP_RUNTIME_READY",
                                 "physical_gui_pass": False}), \
             patch("builtins.print"):
            self.assertEqual(main(["inspect"]), 0)


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "cfa3" / "qt6-runtime.json"

    def test_missing_preference_defaults_to_native_qt_autodetection(self):
        self.assertEqual(load_preferences(path=self.path)["qt_platform"], "auto")

    def test_save_and_load_is_user_scoped_and_atomic(self):
        target = save_preferences("wayland", path=self.path)
        self.assertEqual(target, self.path)
        self.assertEqual(load_preferences(path=self.path)["qt_platform"], "wayland")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_explicit_x11_is_next_launch_only(self):
        env = {"DISPLAY": ":0"}
        choice = {"schema": "cfa3.runtime-preferences.v1", "qt_platform": "xcb"}
        result = environment_for_next_launch(environment=env, preferences=choice)
        self.assertEqual(result["QT_QPA_PLATFORM"], "xcb")
        self.assertNotIn("QT_QPA_PLATFORM", env)

    def test_automatic_mode_does_not_override_existing_explicit_platform(self):
        env = {"QT_QPA_PLATFORM": "wayland"}
        auto = {"schema": "cfa3.runtime-preferences.v1", "qt_platform": "auto"}
        self.assertEqual(environment_for_next_launch(
            environment=env, preferences=auto)["QT_QPA_PLATFORM"], "wayland")

    def test_platform_preference_conflict_fails_closed(self):
        choice = {"schema": "cfa3.runtime-preferences.v1", "qt_platform": "wayland"}
        with self.assertRaisesRegex(RuntimeConfigurationError, "CONFLICT"):
            environment_for_next_launch(
                environment={"QT_QPA_PLATFORM": "xcb"}, preferences=choice)

    def test_unrecognized_platform_cannot_be_saved(self):
        with self.assertRaises(RuntimeConfigurationError):
            save_preferences("kde-only", path=self.path)

    def test_corrupted_config_does_not_silently_reset_to_auto(self):
        self.path.parent.mkdir()
        self.path.write_text("{not-json", encoding="utf-8")
        with self.assertRaises(RuntimeConfigurationError):
            load_preferences(path=self.path)

    def test_unrecognized_config_fields_fail_closed(self):
        self.path.parent.mkdir()
        self.path.write_text(json.dumps({
            "schema": "cfa3.runtime-preferences.v1",
            "qt_platform": "wayland", "injected_extra": True,
        }))
        with self.assertRaises(RuntimeConfigurationError):
            load_preferences(path=self.path)

    def test_config_symlink_is_not_followed(self):
        elsewhere = Path(self.temp.name) / "outside"
        elsewhere.write_text("sensitive")
        self.path.parent.mkdir()
        self.path.symlink_to(elsewhere)
        with self.assertRaises(RuntimeConfigurationError):
            load_preferences(path=self.path)
        with self.assertRaises(RuntimeConfigurationError):
            save_preferences("auto", path=self.path)
        self.assertEqual(elsewhere.read_text(), "sensitive")

    def test_relative_xdg_config_home_rejected(self):
        with self.assertRaises(RuntimeConfigurationError):
            preference_path({"XDG_CONFIG_HOME": "relative/location"})

    def test_valid_xdg_path_avoids_kde_assumptions(self):
        target = preference_path({"XDG_CONFIG_HOME": self.temp.name})
        self.assertEqual(target, Path(self.temp.name) / "cfa3" / "qt6-runtime.json")


if __name__ == "__main__":
    unittest.main()
