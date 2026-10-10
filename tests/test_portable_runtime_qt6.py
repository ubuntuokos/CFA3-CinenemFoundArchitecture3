"""Real Qt6 GUI reference tests. NEVER physical standalone/parent GUI PASS."""
import os
import unittest
from unittest.mock import patch

try:
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError:
    QApplication = None

from cfa3_runtime.qt6_environment import inspect_runtime
from cfa3_runtime.settings_panel import Qt6RuntimeSettingsPanel
from cfa3_runtime.preferences import RuntimeConfigurationError


@unittest.skipUnless(QApplication is not None, "PySide6 Qt6 not available")
class RealQt6SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_offscreen_reference_is_not_normal_user_runtime_admission(self):
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            self.skipTest("Only applicable to offscreen CI")
        report = inspect_runtime()
        self.assertEqual(report["status"], "REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY")
        self.assertEqual(report["qt_platform"], "offscreen")
        self.assertFalse(report["standalone_gui_pass"])
        self.assertFalse(report["parent_integration_gui_pass"])

    def test_real_qwidget_parent_and_workload_mode_indicator(self):
        parent = QWidget()
        with patch("cfa3_runtime.settings_panel.load_preferences",
                   return_value={"schema": "cfa3.runtime-preferences.v1",
                                 "qt_platform": "auto"}):
            panel = Qt6RuntimeSettingsPanel(parent, workload_mode="UNKNOWN")
        try:
            self.assertIs(panel.parent(), parent)
            self.assertEqual(panel.objectName(), "cfa3_portable_qt6_settings")
            self.assertIn("UNKNOWN", panel.workload_mode_indicator.text())
            self.assertIn("Qt6 runtime:", panel.status_label.text())
            self.assertFalse(panel.status_label.text().endswith("PASS"))
        finally:
            panel.close()
            parent.close()

    def test_platform_save_does_not_change_running_process(self):
        before = os.environ.get("QT_QPA_PLATFORM")
        with patch("cfa3_runtime.settings_panel.load_preferences",
                   return_value={"schema": "cfa3.runtime-preferences.v1",
                                 "qt_platform": "auto"}), \
             patch("cfa3_runtime.settings_panel.save_preferences") as save:
            panel = Qt6RuntimeSettingsPanel(workload_mode="UNKNOWN")
            try:
                panel.platform_choice.setCurrentIndex(
                    panel.platform_choice.findData("xcb"))
                panel.save_button.click()
                save.assert_called_once_with("xcb")
                self.assertIn("next CFA3 launch", panel.message_label.text())
                self.assertEqual(os.environ.get("QT_QPA_PLATFORM"), before)
            finally:
                panel.close()

    def test_invalid_config_never_silently_replaces_user_setting(self):
        with patch("cfa3_runtime.settings_panel.load_preferences",
                   side_effect=RuntimeConfigurationError("CONFIG_INVALID_JSON")):
            panel = Qt6RuntimeSettingsPanel(workload_mode="UNKNOWN")
        try:
            self.assertFalse(panel.save_button.isEnabled())
            self.assertIn("blocked", panel.message_label.text())
        finally:
            panel.close()

    def test_real_application_object_is_mandatory(self):
        self.assertIsNotNone(QApplication.instance())
        self.assertTrue(self.app is QApplication.instance())


if __name__ == "__main__":
    unittest.main()
