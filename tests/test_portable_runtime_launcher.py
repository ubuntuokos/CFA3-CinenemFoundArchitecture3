"""CFA3 Qt6 launch integration; no shell fallback or fabricated GUI PASS."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from cfa3_runtime.launcher import (
    PreparedLaunch, RuntimeLaunchBlocked, launch_python_qt_frontend,
    prepare_python_qt_launch, run_prepared_launch,
)
from cfa3_runtime.preferences import save_preferences
from cfa3_runtime.__main__ import main


def observed(platform="wayland", status="APP_RUNTIME_READY"):
    return {
        "status": status,
        "qt_platform": platform,
        "qt_version": "6.10.2",
        "physical_gui_pass": False,
        "parent_integration_gui_pass": False,
    }


def pref(platform="auto"):
    return {"schema": "cfa3.runtime-preferences.v1", "qt_platform": platform}


class LaunchPreparationTests(unittest.TestCase):
    def test_wayland_is_preserved_exactly_and_no_physical_pass(self):
        witness = Mock(return_value=observed())
        env = {"WAYLAND_DISPLAY": "wayland-0", "QT_QPA_PLATFORM": "wayland"}
        plan = prepare_python_qt_launch(
            ["/usr/bin/python3", "-m", "cfa3.gui"], environment=env,
            preferences=pref("wayland"), probe=witness)
        self.assertEqual(plan.platform, "wayland")
        self.assertEqual(plan.environment["QT_QPA_PLATFORM"], "wayland")
        self.assertFalse(plan.physical_gui_pass)
        self.assertFalse(plan.parent_integration_gui_pass)
        self.assertIsInstance(plan, PreparedLaunch)
        witness.assert_called_once()
        self.assertEqual(witness.call_args.kwargs["environment"]["WAYLAND_DISPLAY"], "wayland-0")
        self.assertEqual(env, {"WAYLAND_DISPLAY": "wayland-0", "QT_QPA_PLATFORM": "wayland"})

    def test_gnome_xcb_does_not_depend_on_kde(self):
        plan = prepare_python_qt_launch(
            ["python3", "-m", "cfa3.video"], environment={
                "DISPLAY": ":0", "XDG_CURRENT_DESKTOP": "GNOME"},
            preferences=pref("xcb"), probe=Mock(return_value=observed("xcb")))
        self.assertEqual(plan.environment["QT_QPA_PLATFORM"], "xcb")
        self.assertEqual(plan.environment["XDG_CURRENT_DESKTOP"], "GNOME")

    def test_wayland_selected_but_xcb_loaded_is_blocked(self):
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "REQUESTED_PLATFORM_NOT_LOADED"):
            prepare_python_qt_launch(
                ["python3", "-m", "cfa3.gui"], environment={},
                preferences=pref("wayland"),
                probe=Mock(return_value=observed("xcb")))

    def test_explicit_backend_conflict_blocks_without_probe(self):
        witness = Mock(return_value=observed())
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "EXPLICIT_QT_PLATFORM_CONFLICT"):
            prepare_python_qt_launch(
                ["python3"], environment={"QT_QPA_PLATFORM": "xcb"},
                preferences=pref("wayland"), probe=witness)
        witness.assert_not_called()

    def test_offscreen_may_not_launch_interactive_application(self):
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "QT6_PREFLIGHT_BLOCKED"):
            prepare_python_qt_launch(
                ["python3"], environment={"QT_QPA_PLATFORM": "offscreen"},
                preferences=pref("auto"),
                probe=Mock(return_value=observed(
                    "offscreen", "REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY")))

    def test_proof_fields_must_remain_explicitly_false(self):
        for forged in (dict(observed(), physical_gui_pass=True),
                       dict(observed(), parent_integration_gui_pass=True),
                       {"status": "APP_RUNTIME_READY", "qt_platform": "xcb",
                        "qt_version": "6.10.2"}):
            with self.subTest(forged=forged):
                with self.assertRaisesRegex(RuntimeLaunchBlocked, "UNTRUSTED"):
                    prepare_python_qt_launch(
                        ["python3"], environment={}, preferences=pref(),
                        probe=Mock(return_value=forged))

    def test_invalid_commands_never_probe_or_start(self):
        witness = Mock(return_value=observed())
        for argv in ([], (), "python3", ["python3", ""], ["py\x00thon"]):
            with self.subTest(argv=argv):
                with self.assertRaisesRegex(RuntimeLaunchBlocked, "INVALID_EXECUTABLE"):
                    prepare_python_qt_launch(
                        argv, environment={}, preferences=pref(), probe=witness)
        witness.assert_not_called()

    def test_xdg_config_from_child_environment_is_authoritative(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "cfa3" / "qt6-runtime.json"
            save_preferences("xcb", path=config)
            plan = prepare_python_qt_launch(
                ["python3", "-m", "cfa3.video"],
                environment={"XDG_CONFIG_HOME": temporary},
                probe=Mock(return_value=observed("xcb")))
        self.assertEqual(plan.platform, "xcb")
        self.assertEqual(plan.environment["QT_QPA_PLATFORM"], "xcb")

    def test_corrupt_child_config_blocks_no_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "cfa3" / "qt6-runtime.json"
            config.parent.mkdir()
            config.write_text("{broken", encoding="utf-8")
            witness = Mock(return_value=observed())
            with self.assertRaisesRegex(RuntimeLaunchBlocked, "CONFIG_INVALID_JSON"):
                prepare_python_qt_launch(
                    ["python3"], environment={"XDG_CONFIG_HOME": temporary},
                    probe=witness)
            witness.assert_not_called()


class ExecuteTests(unittest.TestCase):
    def test_runner_has_no_shell_and_propagates_child_exit_code(self):
        runner = Mock(return_value=SimpleNamespace(returncode=17))
        original = {"DISPLAY": ":0"}
        plan = prepare_python_qt_launch(
            [sys.executable, "-m", "cfa3.gui", "--input", "scene"],
            environment=original, preferences=pref(),
            probe=Mock(return_value=observed("xcb")))
        self.assertEqual(run_prepared_launch(plan, runner=runner), 17)
        runner.assert_called_once_with(
            [sys.executable, "-m", "cfa3.gui", "--input", "scene"],
            env={"DISPLAY": ":0"}, shell=False, check=False)
        self.assertEqual(original, {"DISPLAY": ":0"})

    def test_failed_preflight_never_calls_runner(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0))
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "PREFLIGHT"):
            launch_python_qt_frontend(
                ["python3"], environment={}, preferences=pref(),
                probe=Mock(return_value={"status": "BLOCKED_QT6_PROBE"}),
                runner=runner)
        runner.assert_not_called()

    def test_successful_preflight_starts_child_exactly_once(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0))
        self.assertEqual(launch_python_qt_frontend(
            ["python3", "-m", "cfa3.video"], environment={},
            preferences=pref(), probe=Mock(return_value=observed()),
            runner=runner), 0)
        runner.assert_called_once()

    def test_process_start_error_does_not_silently_pass(self):
        plan = prepare_python_qt_launch(
            ["python3"], environment={}, preferences=pref(),
            probe=Mock(return_value=observed()))
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "APP_PROCESS_START_FAILED"):
            run_prepared_launch(plan, runner=Mock(side_effect=OSError("missing")))

    def test_bad_runner_result_cannot_be_success(self):
        plan = prepare_python_qt_launch(
            ["python3"], environment={}, preferences=pref(),
            probe=Mock(return_value=observed()))
        with self.assertRaisesRegex(RuntimeLaunchBlocked, "PROCESS_RESULT_INVALID"):
            run_prepared_launch(plan, runner=Mock(return_value=object()))


class CliBridgeTests(unittest.TestCase):
    def test_settings_preflight_starts_separate_child_before_qapplication(self):
        with patch("cfa3_runtime.__main__.launch_python_qt_frontend",
                   return_value=0) as start:
            self.assertEqual(main(["settings"]), 0)
        start.assert_called_once_with(
            [sys.executable, "-m", "cfa3_runtime", "settings-window"])

    def test_module_frontend_receives_exact_arguments(self):
        with patch("cfa3_runtime.__main__.launch_python_qt_frontend",
                   return_value=18) as start:
            self.assertEqual(main(["launch-module", "cfa3.video", "--",
                                   "--scene", "one movie.mov"]), 18)
        start.assert_called_once_with(
            [sys.executable, "-m", "cfa3.video", "--scene", "one movie.mov"])

    def test_invalid_module_cannot_start_any_child(self):
        with patch("cfa3_runtime.__main__.launch_python_qt_frontend") as start, \
             patch("builtins.print"):
            self.assertEqual(main(["launch-module", "invalid;rm"]), 2)
        start.assert_not_called()

    def test_blocked_launcher_returns_nonzero_and_emits_failure(self):
        with patch("cfa3_runtime.__main__.launch_python_qt_frontend",
                   side_effect=RuntimeLaunchBlocked("QT6_PROBE_FAILED")), \
             patch("builtins.print") as output:
            self.assertEqual(main(["settings"]), 2)
            self.assertIn("BLOCKED_QT6_LAUNCH", output.call_args.args[0])
            self.assertIn("false", output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
