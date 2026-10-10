"""Qt6 read-only Current Host dashboard for standalone/real-parent integration.

No mock parent, no automatic evidence PASS, no driver/product QA. Every tab
carries the mandatory *externally sourced* Workload Mode status indicator.
"""
from __future__ import annotations

from .core import Level, Mode, Plan

try:
    from PySide6.QtWidgets import (
        QAbstractItemView, QApplication, QLabel, QMainWindow, QTabWidget, QTableWidget,
        QTableWidgetItem, QVBoxLayout, QWidget,
    )
except ImportError:
    QApplication = None


class GuiDependencyMissing(RuntimeError):
    pass


if QApplication is not None:
    class CurrentHostDashboard(QMainWindow):
        """Read-only UI: it displays planned obligations, NOT validated results."""

        def __init__(self, plan: Plan, *, workload_mode: str = "UNKNOWN",
                     parent: QWidget | None = None):
            if QApplication.instance() is None:
                raise GuiDependencyMissing("an actual Qt6 QApplication must already exist")
            if not isinstance(plan, Plan):
                raise TypeError("a verified structural Plan instance is required")
            if not isinstance(workload_mode, str) or not workload_mode.strip():
                raise ValueError("externally supplied Workload Mode display must not be empty")
            super().__init__(parent)
            self.setWindowTitle("CFA3 Current Host — pending physical verification")
            root = QWidget(self)
            layout = QVBoxLayout(root)
            self.workload_indicator = QLabel(
                "Workload Mode (external authority): " + workload_mode
            )
            self.workload_indicator.setObjectName("cfa3_global_workload_mode")
            layout.addWidget(self.workload_indicator)
            layout.addWidget(QLabel(
                "Current Host: NOT VERIFIED — structural obligations only; "
                "no physical PASS issued here."
            ))
            tabs = QTabWidget()
            self.tabs = tabs
            for title, level in [
                ("Foundation", Level.FOUNDATION),
                ("Layer", Level.LAYER),
                ("Global", Level.GLOBAL),
            ]:
                widget = QWidget()
                block = QVBoxLayout(widget)
                indicator = QLabel("Workload Mode (external authority): " + workload_mode)
                indicator.setObjectName("workload_mode_" + title.lower())
                block.addWidget(indicator)
                rows = [o for o in plan.obligations if o.level == level]
                table = QTableWidget(len(rows), 4)
                table.setHorizontalHeaderLabels(["Component", "Test", "Handoff", "Evidence"])
                table.setObjectName("obligations_" + title.lower())
                for i, obligation in enumerate(rows):
                    for col, value in enumerate([
                        obligation.component_id, obligation.test.value,
                        obligation.handoff_id or "—", "PENDING",
                    ]):
                        table.setItem(i, col, QTableWidgetItem(value))
                table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                block.addWidget(table)
                tabs.addTab(widget, title)
            plugin_tab = QWidget()
            p_layout = QVBoxLayout(plugin_tab)
            p_layout.addWidget(QLabel("Workload Mode (external authority): " + workload_mode))
            p_layout.addWidget(QLabel(
                "Community plugins: inspect/qualify CFA3-owned host interfaces only. "
                "External product functionality, vendor drivers and commercial "
                "software are NOT tested by Current Host."
            ))
            p_layout.addWidget(QLabel(
                "Plugin enablement: PENDING external Security/Rights/Sandbox admission."
            ))
            tabs.addTab(plugin_tab, "Community Plugins")
            layout.addWidget(tabs)
            self.setCentralWidget(root)
            self.plan = plan
            self.integrated_with_actual_parent = parent is not None

else:
    class CurrentHostDashboard:
        def __init__(self, *args, **kwargs):
            raise GuiDependencyMissing(
                "PySide6 (Qt6) is not installed; no fake GUI test or parent PASS"
            )


def standalone(plan: Plan, *, workload_mode: str = "UNKNOWN") -> int:
    """Run the actual standalone Qt6 panel; no physical proof issued."""
    if QApplication is None:
        raise GuiDependencyMissing("PySide6/Qt6 runtime unavailable")
    app = QApplication.instance()
    own_app = app is None
    if own_app:
        app = QApplication([])
    if not own_app:
        raise GuiDependencyMissing("existing Qt6 application must manage its own dashboard instance")
    window = CurrentHostDashboard(plan, workload_mode=workload_mode)
    window.show()
    # Never treat a rendered window as a full Current Host acceptance proof.
    return app.exec()
