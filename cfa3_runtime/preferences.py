"""Desktop-neutral CFA3 runtime preferences; no host/global Qt environment changes.

Application settings are explicit, persisted only on the user's Save action.
The launcher can call environment_for_next_launch *before* QApplication exists.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Mapping

_VALID = frozenset(("auto", "wayland", "xcb"))
_SCHEMA = "cfa3.runtime-preferences.v1"


class RuntimeConfigurationError(ValueError):
    pass


def preference_path(environment: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environment is None else environment
    xdg = env.get("XDG_CONFIG_HOME")
    if xdg:
        root = Path(xdg).expanduser()
        if not root.is_absolute():
            raise RuntimeConfigurationError("XDG_CONFIG_HOME_MUST_BE_ABSOLUTE")
    else:
        root = Path.home() / ".config"
    return root / "cfa3" / "qt6-runtime.json"


def load_preferences(*, path: Path | None = None) -> dict:
    destination = Path(path) if path is not None else preference_path()
    if destination.is_symlink():
        raise RuntimeConfigurationError("SYMLINK_CONFIG_NOT_ADMITTED")
    try:
        content = destination.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"schema": _SCHEMA, "qt_platform": "auto"}
    except (OSError, UnicodeError) as exc:
        raise RuntimeConfigurationError("CONFIG_READ_ERROR") from exc
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise RuntimeConfigurationError("CONFIG_INVALID_JSON") from exc
    if (not isinstance(data, dict) or set(data) != {"schema", "qt_platform"}
            or data["schema"] != _SCHEMA
            or not isinstance(data["qt_platform"], str)
            or data["qt_platform"] not in _VALID):
        raise RuntimeConfigurationError("CONFIG_SCHEMA_OR_PLATFORM_INVALID")
    return data


def save_preferences(qt_platform: str, *, path: Path | None = None) -> Path:
    if not isinstance(qt_platform, str) or qt_platform not in _VALID:
        raise RuntimeConfigurationError("UNSUPPORTED_QT_PLATFORM_SELECTION")
    destination = Path(path) if path is not None else preference_path()
    if destination.is_symlink():
        raise RuntimeConfigurationError("SYMLINK_CONFIG_NOT_ADMITTED")
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, staging = tempfile.mkstemp(dir=destination.parent, prefix=".qt6-config-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": _SCHEMA, "qt_platform": qt_platform},
                      stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(staging, 0o600)
        os.replace(staging, destination)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)
    return destination


def environment_for_next_launch(
    *, environment: Mapping[str, str] | None = None,
    preferences: dict | None = None,
) -> dict[str, str]:
    """Return child-process environment; caller decides when to launch.

    Do not override an explicit existing QT_QPA_PLATFORM. Never auto-fallback
    between Wayland/X11 after a plugin startup failure.
    """
    env = dict(os.environ if environment is None else environment)
    selected = load_preferences() if preferences is None else preferences
    if (not isinstance(selected, dict) or set(selected) != {"schema", "qt_platform"}
            or selected["schema"] != _SCHEMA
            or not isinstance(selected["qt_platform"], str)
            or selected["qt_platform"] not in _VALID):
        raise RuntimeConfigurationError("CONFIG_SCHEMA_OR_PLATFORM_INVALID")
    requested = selected["qt_platform"]
    if requested == "auto":
        return env
    if env.get("QT_QPA_PLATFORM") not in (None, "", requested):
        raise RuntimeConfigurationError("EXPLICIT_QT_PLATFORM_CONFLICT")
    env["QT_QPA_PLATFORM"] = requested
    return env
