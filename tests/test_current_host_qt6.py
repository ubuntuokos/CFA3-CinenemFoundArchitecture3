"""Only standalone Qt6 reference evidence, never physical-host GUI PASS."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cfa3_current_host.core import Component, Graph, Ownership
from cfa3_current_host.qt6_dashboard import (
    QApplication, CurrentHostDashboard, GuiDependencyMissing,
)


def fixture():
    graph = Graph()
    graph.register_component(Component("video", "VIDEO", "v1",
                                       Ownership.CFA3_COMPONENT, (), True))
    return graph.plan(["video"])


class DashboardAvailabilityTests(unittest.TestCase):
    def test_missing_qt6_is_explicit_blocker_not_fake_pass(self):
        if QApplication is not None:
            self.skipTest("Qt6 available — actual widget tests apply")
        with self.assertRaises(GuiDependencyMissing):
            CurrentHostDashboard(fixture())

    @unittest.skipUnless(QApplication is not None, "Qt6 not installed: NOT_VERIFIED")
    def test_standalone_widget_has_all_panels_and_workload_mode(self):
        app = QApplication.instance() or QApplication([])
        window = CurrentHostDashboard(fixture(), workload_mode="EXTERNAL_PENDING")
        self.assertEqual(window.tabs.count(), 4)
        self.assertIn("EXTERNAL_PENDING", window.workload_indicator.text())
        self.assertFalse(window.integrated_with_actual_parent)
        self.assertIn("pending", window.windowTitle().lower())
        window.close()

    @unittest.skipUnless(QApplication is not None, "Qt6 not installed: NOT_VERIFIED")
    def test_requires_real_qt_application(self):
        if QApplication.instance() is not None:
            self.skipTest("an existing application prevents this negative case")
        with self.assertRaises(GuiDependencyMissing):
            CurrentHostDashboard(fixture())


if __name__ == "__main__":
    unittest.main()
