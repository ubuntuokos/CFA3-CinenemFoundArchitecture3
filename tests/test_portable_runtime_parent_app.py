"""CFA3-owned Qt6 runtime application parent: hosted reference, never physical PASS."""
import unittest
from unittest.mock import patch

try:
    from PySide6.QtWidgets import QApplication, QMainWindow
except ImportError:
    QApplication = None

from cfa3_runtime.control_center import CFA3RuntimeControlCenter
from cfa3_runtime.settings_panel import RuntimeSettingsUnavailable


@unittest.skipUnless(QApplication is not None, "PySide6 Qt6 not installed")
class RealRuntimeApplicationParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_actual_cfa3_runtime_shell_mounts_settings_in_qmainwindow(self):
        with patch("cfa3_runtime.settings_panel.load_preferences", return_value={
            "schema": "cfa3.runtime-preferences.v1", "qt_platform": "auto",
        }):
            shell = CFA3RuntimeControlCenter(workload_mode="EXTERNAL_PENDING")
        try:
            self.assertIsInstance(shell, QMainWindow)
            self.assertEqual(shell.objectName(), "cfa3_runtime_control_center")
            self.assertIs(shell.tabs.widget(0), shell.settings)
            self.assertIs(shell.settings.window(), shell)
            self.assertEqual(shell.tabs.tabText(0), "Grafikus környezet")
            self.assertIn("EXTERNAL_PENDING",
                          shell.settings.workload_mode_indicator.text())
            self.assertIn("PENDING", shell.status.text())
            self.assertNotIn("PHYSICAL PASS", shell.status.text().upper())
        finally:
            shell.close()

    def test_application_window_can_show_and_process_qt_events(self):
        with patch("cfa3_runtime.settings_panel.load_preferences", return_value={
            "schema": "cfa3.runtime-preferences.v1", "qt_platform": "auto",
        }):
            shell = CFA3RuntimeControlCenter()
        try:
            shell.show()
            self.app.processEvents()
            self.assertTrue(shell.isVisible())
            self.assertTrue(shell.settings.isVisible())
            self.assertIs(shell.settings.window(), shell)
        finally:
            shell.close()

    def test_empty_workload_indicator_blocks(self):
        with self.assertRaisesRegex(RuntimeSettingsUnavailable, "EXTERNAL_WORKLOAD_MODE"):
            CFA3RuntimeControlCenter(workload_mode="")

    def test_default_workload_indicator_is_not_a_granted_mode(self):
        with patch("cfa3_runtime.settings_panel.load_preferences", return_value={
            "schema": "cfa3.runtime-preferences.v1", "qt_platform": "auto",
        }):
            shell = CFA3RuntimeControlCenter()
        try:
            self.assertIn("UNKNOWN", shell.settings.workload_mode_indicator.text())
            self.assertIn("physical host evidence PENDING", shell.status.text())
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main()
