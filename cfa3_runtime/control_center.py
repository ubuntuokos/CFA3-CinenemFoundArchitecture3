"""Standalone CFA3 runtime control centre, embedding actual Qt6 settings.

This is a *CFA3-owned* minimal Qt application shell (not a test QWidget and
not the eventual complete CFA3 Platform GUI). Neither its creation nor its
parent-child linkage asserts physical Current Host or GUI acceptance.
"""
from __future__ import annotations

from .settings_panel import Qt6RuntimeSettingsPanel, RuntimeSettingsUnavailable

try:
    from PySide6.QtWidgets import (
        QApplication, QLabel, QMainWindow, QTabWidget,
        QVBoxLayout, QWidget,
    )
except ImportError:
    QApplication = None


if QApplication is not None:
    class CFA3RuntimeControlCenter(QMainWindow):
        """Own application window hosting CFA3 Runtime Settings as a real child."""

        def __init__(self, *, workload_mode: str = "UNKNOWN"):
            if QApplication.instance() is None:
                raise RuntimeSettingsUnavailable("REAL_QAPPLICATION_REQUIRED")
            if not isinstance(workload_mode, str) or not workload_mode.strip():
                raise RuntimeSettingsUnavailable("EXTERNAL_WORKLOAD_MODE_REQUIRED")
            super().__init__()
            self.setObjectName("cfa3_runtime_control_center")
            self.setWindowTitle("CFA3 — Runtime Control Center")
            root = QWidget(self)
            layout = QVBoxLayout(root)
            self.status = QLabel(
                "CFA3 Runtime: reference integration; physical host evidence PENDING"
            )
            self.status.setObjectName("cfa3_current_host_pending")
            layout.addWidget(self.status)
            self.tabs = QTabWidget(root)
            self.tabs.setObjectName("cfa3_runtime_tabs")
            layout.addWidget(self.tabs)
            self.settings = Qt6RuntimeSettingsPanel(
                parent=self.tabs, workload_mode=workload_mode
            )
            self.tabs.addTab(self.settings, "Grafikus környezet")
            self.setCentralWidget(root)

else:
    class CFA3RuntimeControlCenter:
        def __init__(self, *args, **kwargs):
            raise RuntimeSettingsUnavailable("PYSIDE6_QT6_RUNTIME_NOT_INSTALLED")
