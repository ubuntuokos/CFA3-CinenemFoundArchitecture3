# CFA3 Portable Qt6 Runtime Broker — staged application integration

Status: **STAGED_REFERENCE_IMPLEMENTATION**, not physically admitted.

Scope: user-approved generic Linux Qt6 runtime recognition, platform
configuration and developer-tool distinction. No donor, legacy or
Current Host modifications.

## Generic Linux platform contract

- KDE is **not** mandatory. GNOME, KDE, Xfce, Cinnamon, MATE, LXQt and
  other desktop environments are not discriminated by vendor/brand.
- The actual Qt6 platform plugin, determined through a separate
  QApplication/QWidget subprocess, is authoritative. Desktop and display
  environment variables are informational, not proof.
- Qt6 6.8+ with Wayland or xcb (Qt's X11 bridge), and a recognized display,
  can return APP_RUNTIME_READY for the **Python/PySide6 GUI bridge**.
  It does NOT grant physical standalone or parent GUI PASS.
- Offscreen, minimal and VNC Qt platforms return
  REFERENCE_ONLY_NO_INTERACTIVE_DISPLAY, never interactive readiness.
- Incompatible version or unavailable/crashing platform plugin blocks.
  Silent Wayland-to-X11 fallback is forbidden.
- EGL/OpenGL loader presence is reported, not enforced as a GPU prerequisite
  for CPU-only Qt Widgets use.

## Application settings and launch boundary

The reusable Qt6RuntimeSettingsPanel can be mounted under an actual CFA3
QWidget settings parent after a real QApplication is initialized. It displays
the externally supplied Workload Mode (UNKNOWN when not admitted), the
runtime gate, platform, version, screens and developer-only tool state.

User-selectable Qt platform preference: auto, wayland, xcb.
Preferences are saved on explicit user action only. Storage:
XDG_CONFIG_HOME/cfa3/qt6-runtime.json or the normal user-scoped
home/.config/cfa3/qt6-runtime.json. Records are schema-validated, staged
atomically and written with permission mode 0600. Malformed configurations
block; a running QApplication is not modified.

Launcher integration when the actual new CFA3 launcher exists:
1. Call cfa3_runtime.environment_for_next_launch() BEFORE constructing Qt.
2. Pass its returned environment to the launched application process.
3. An existing contradictory QT_QPA_PLATFORM blocks; no silent fallback.
4. Call inspect_runtime() for runtime diagnostics; then mount the settings
   panel into the actual application parent.
5. Perform physical standalone and actual-parent GUI tests before FINAL.

No admitted full CFA3 parent GUI/Launcher/Installer exists in the current
new-CFA3 main. Therefore actual parent integration, Linux packaging and
physical host visual proof are all PENDING. CI parent QWidget is only a
reference, not application integration PASS.

## Development tools are distinct from end-user runtime

End users of native/bundled CFA3 do not need to install rustc, cargo or a
Python development toolchain. Python/PySide6-specific applications include
their runtime through packaging. inspect_developer_tools() reports Python,
Rust/Cargo and CMake availability as a separate developer-only inventory;
even a full inventory does not issue DEV_ENV_READY without build/SDK proof.

The existing main Qt 6.8 C++ build workflow remains the independent
development-SDK reference: .github/workflows/qt68-linux.yml.

## GitHub reference evidence, 2026-10-10

Workflow: .github/workflows/portable-runtime.yml
Run: https://github.com/ubuntuokos/CFA3-CinenemFoundArchitecture3/actions/runs/38087227564

- Python 3.13: 32 tests, 27 PASS and 5 Qt6-unavailable SKIP.
- Linux Qt6/PySide6-Essentials with actual offscreen QApplication/QWidget:
  32 tests PASS, zero skips. Actual panel and QWidget test parent worked.
- Rust/Cargo workspace: 3 PASS.
- CFA3 bootstrap policy guard and Python syntax compilation: PASS.
- All three GitHub-hosted CI jobs: SUCCESS.

No hosted result or mocked status issues physical Current Host PASS.

## Remaining acceptance scope

- The actual CFA3 launcher, installer and native distro packages: PENDING.
- Integration inside a real CFA3 settings-parent application: PENDING.
- Real user-machine visible GUI proof and desktop matrix: PENDING.
- Connection to central Workload Mode, Identity and Evidence authorities:
  PENDING; this component does not create parallel authorities.
- The separate Current Host bubblewrap CI failure remains unresolved,
  and does not imply a Qt6 platform error.


## 2026-10-10 continuation: actual guarded launch and installable adapter

This branch now includes cfa3_runtime/launcher.py, a launcher adapter that
prepares a Python/PySide6 Qt6 application process **before QApplication is
constructed**. It resolves the user-scoped XDG configuration against the
actual child environment and runs an isolated Qt6 frontend probe. If the
selected Wayland/xcb plugin is not the observed plugin, or the probe cannot
verify APP_RUNTIME_READY, the child is **not** started. The current shell
environment is not mutated; process creation uses argv with shell=False.

Available source checkout commands:

    python3 -m cfa3_runtime inspect
    python3 -m cfa3_runtime developer-tools
    python3 -m cfa3_runtime settings
    python3 -m cfa3_runtime launch-module cfa3.gui -- --example-argument

The last launch-module example requires a real future installed Python Qt6
module (the new CFA3 GUI application is not yet admitted or present on main).
This command does not claim that such a module exists now.

The settings command performs an isolated preflight, then starts its own Qt6
settings-window child, applying the user preference before Qt initialization.
The settings panel itself is still standalone/reference until it can be
mounted inside a real CFA3 parent application. Launch failures are explicit
nonzero exit codes, not silent Wayland/X11 fallbacks.

pyproject.toml packages the adapter as cfa3-portable-qt6-runtime with
a cfa3-runtime console entrypoint and optional Qt6 Python bridge. Python,
Rust and Cargo **developer toolchains are not runtime requirements** of
compiled CFA3 end-user applications; the optional Python GUI bridge must be
included where that particular frontend is actually used.

### Independent GitHub reference evidence

Full workflow run:
https://github.com/ubuntuokos/CFA3-CinenemFoundArchitecture3/actions/runs/38087980763

- 50 Python test cases: **45 PASS + 5 Qt6-unavailable skips**, no failures.
- 50 Qt6-enabled tests: **50 PASS**, no failures/skips, with actual offscreen
  Qt6 QWidget settings controls.
- Rust workspace: **3 PASS**, no failures.
- Wheel built, installed into the GitHub runner and the installed
  cfa3-runtime executable verified **outside the checkout directory**.
- All four GitHub CI jobs: **SUCCESS**.
- These are reference/hosted results; no actual physical Current Host PASS.

### Still outside the current finished implementation

- CFA3 production application parent GUI does not yet exist in the
  admitted main repository: real parent integration remains PENDING.
- Generic-Linux installer, signed application package and distribution
  admission: PENDING. The wheel is only the reusable development adapter.
- Real-user Wayland/X11 visible rendering, multi-desktop support matrix
  and physical STANDALONE_GUI_PASS/PARENT_INTEGRATION_GUI_PASS: PENDING.
- Central Security/Identity/Workload Mode/Current Host real authority
  integration: PENDING; do not create substitute local authorities.
