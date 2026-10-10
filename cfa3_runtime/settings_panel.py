"""Optional Qt6 CFA3 Runtime Settings panel for a real QApplication parent.

No fake parent, no automatic package installation and no physical evidence PASS.
Preferences take effect only on the application's next launch.
"""
from __future__ import annotations

from .preferences import RuntimeConfigurationError, load_preferences, save_preferences
from .qt6_environment import inspect_runtime, inspect_developer_tools

try:
    from PySide6.QtWidgets import (
        QApplication, QComboBox, QFormLayout, QHBoxLayout,
        QLabel, QPushButton, QVBoxLayout, QWidget,
    )
except ImportError:
    QApplication = None


class RuntimeSettingsUnavailable(RuntimeError):
    pass


if QApplication is not None:
    class Qt6RuntimeSettingsPanel(QWidget):
        def __init__(self, parent: QWidget | None = None, *,
                     workload_mode: str = "UNKNOWN"):
            if QApplication.instance() is None:
                raise RuntimeSettingsUnavailable("REAL_QAPPLICATION_REQUIRED")
            if not isinstance(workload_mode, str) or not workload_mode.strip():
                raise RuntimeSettingsUnavailable("EXTERNAL_WORKLOAD_MODE_REQUIRED")
            super().__init__(parent)
            self.setObjectName("cfa3_portable_qt6_settings")
            self.setWindowTitle("CFA3 — Grafikus környezet")
            self.setAccessibleName("CFA3 Qt6 futtatókörnyezet beállításai")
            root = QVBoxLayout(self)
            self.workload_mode_indicator = QLabel(
                "Workload Mode (external authority): " + workload_mode)
            self.workload_mode_indicator.setObjectName("cfa3_global_workload_mode")
            root.addWidget(self.workload_mode_indicator)
            self.status_label = QLabel("Qt6 runtime: NOT_VERIFIED")
            self.status_label.setObjectName("cfa3_qt_runtime_status")
            root.addWidget(self.status_label)
            form = QFormLayout()
            self.platform_choice = QComboBox()
            self.platform_choice.setObjectName("cfa3_qt_platform_preference")
            self.platform_choice.addItem("Automatic / system default", "auto")
            self.platform_choice.addItem("Wayland (on next launch)", "wayland")
            self.platform_choice.addItem("X11 / xcb (on next launch)", "xcb")
            form.addRow("Qt6 platform selection:", self.platform_choice)
            self.actual_platform = QLabel("PENDING")
            self.actual_platform.setObjectName("cfa3_actual_qt_platform")
            form.addRow("Qt6 active platform:", self.actual_platform)
            self.qt_version_label = QLabel("PENDING")
            form.addRow("Qt6 runtime version:", self.qt_version_label)
            self.screens_label = QLabel("PENDING")
            form.addRow("Screens:", self.screens_label)
            self.developer_label = QLabel(
                "Developer toolchains are not required for packaged CFA3.")
            form.addRow("Development environment:", self.developer_label)
            root.addLayout(form)
            buttons = QHBoxLayout()
            self.save_button = QPushButton("Save for next launch")
            self.save_button.setObjectName("cfa3_qt_save_preference")
            self.save_button.clicked.connect(self.save_selection)
            buttons.addWidget(self.save_button)
            self.refresh_button = QPushButton("Recheck current environment")
            self.refresh_button.clicked.connect(self.refresh_status)
            buttons.addWidget(self.refresh_button)
            root.addLayout(buttons)
            self.message_label = QLabel(
                "Changing the Qt6 platform does not alter the running QApplication.")
            self.message_label.setWordWrap(True)
            root.addWidget(self.message_label)
            self.load_selection()
            self.refresh_status()

        def load_selection(self) -> None:
            try:
                choice = load_preferences()["qt_platform"]
            except RuntimeConfigurationError as exc:
                self.message_label.setText(
                    "Qt6 configuration blocked: " + str(exc))
                self.save_button.setEnabled(False)
                return
            index = self.platform_choice.findData(choice)
            if index < 0:
                raise RuntimeSettingsUnavailable("INVALID_QT6_PLATFORM_PREFERENCE")
            self.platform_choice.setCurrentIndex(index)

        def save_selection(self) -> None:
            try:
                save_preferences(self.platform_choice.currentData())
            except (RuntimeConfigurationError, OSError) as exc:
                self.message_label.setText("Qt6 settings not saved: " + str(exc))
                return
            self.message_label.setText(
                "Saved. Qt6 platform preference applies on next CFA3 launch; "
                "no running Qt application was modified.")

        def refresh_status(self) -> None:
            snapshot = inspect_runtime()
            self.status_label.setText("Qt6 runtime: " + snapshot["status"])
            self.actual_platform.setText(snapshot["qt_platform"])
            self.qt_version_label.setText(str(snapshot["qt_version"] or "UNAVAILABLE"))
            self.screens_label.setText(", ".join(snapshot["screens"]) or "NONE")
            developer = inspect_developer_tools()
            self.developer_label.setText(
                developer["status"] + " (developer-only; not an end-user requirement)")

else:
    class Qt6RuntimeSettingsPanel:
        def __init__(self, *args, **kwargs):
            raise RuntimeSettingsUnavailable("PYSIDE6_QT6_RUNTIME_NOT_INSTALLED")
