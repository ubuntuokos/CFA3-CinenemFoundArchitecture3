"""CFA3 Community Plugin integration: SDK manifest, safe package intake and lifecycle.

Only CFA3-owned interfaces are qualified here. Plugin code is NEVER imported,
executed, or certified. External Security/Identity, Rights and the runtime
sandbox authority must approve before enabling; absent authorities fail closed.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from zipfile import ZipFile, BadZipFile


_ID = re.compile(r"^[a-z][a-z0-9_.-]{2,127}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_API = "cfa3-plugin/v1"
_MAX_ENTRIES = 128
_MAX_ARCHIVE = 16 * 1024 * 1024
_MAX_UNCOMPRESSED = 48 * 1024 * 1024


class PluginError(ValueError):
    pass


@dataclass(frozen=True)
class Manifest:
    plugin_id: str
    version: str
    publisher: str
    license_expression: str
    api: str
    apps: tuple[str, ...]
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...]
    dependencies: tuple[str, ...]
    gui: bool = False

    @staticmethod
    def parse(data: dict) -> "Manifest":
        required = {"plugin_id", "version", "publisher", "license", "api",
                    "apps", "capabilities", "permissions", "dependencies", "gui"}
        if not isinstance(data, dict) or set(data) != required:
            raise PluginError("manifest schema mismatch")
        if (not isinstance(data["plugin_id"], str) or not _ID.fullmatch(data["plugin_id"])
                or not isinstance(data["version"], str) or not _VERSION.fullmatch(data["version"])
                or not isinstance(data["publisher"], str) or not data["publisher"].strip()
                or not isinstance(data["license"], str) or not data["license"].strip()
                or data["api"] != _API or type(data["gui"]) is not bool):
            raise PluginError("invalid identity, publisher, license, API or GUI declaration")
        seqs = []
        for key in ("apps", "capabilities", "permissions", "dependencies"):
            v = data[key]
            if (not isinstance(v, list) or any(not isinstance(x, str) or not x.strip() for x in v)
                    or len(set(v)) != len(v) or len(v) > 256):
                raise PluginError("invalid or duplicate " + key)
            seqs.append(tuple(v))
        if not seqs[0]:
            raise PluginError("at least one consuming CFA3 application required")
        return Manifest(data["plugin_id"], data["version"], data["publisher"],
                        data["license"], data["api"], *seqs, data["gui"])


@dataclass(frozen=True)
class Inspection:
    manifest: Manifest
    bundle_digest: str
    contained_paths: tuple[str, ...]
    size_bytes: int
    provenance_status: str = "UNVERIFIED"
    rights_status: str = "UNVERIFIED"


def inspect_package(bundle: bytes) -> Inspection:
    """Statically inspect archive. No extraction, imports or evaluation.

    Validates bounds and archive path safety but does NOT establish publisher
    identity, rights, malware freedom or third-party functional quality.
    """
    if not isinstance(bundle, bytes) or not 0 < len(bundle) <= _MAX_ARCHIVE:
        raise PluginError("invalid or oversized plugin bundle")
    try:
        with ZipFile(io.BytesIO(bundle), "r") as archive:
            entries = archive.infolist()
            if not entries or len(entries) > _MAX_ENTRIES:
                raise PluginError("too many or missing bundle entries")
            paths = []
            total = 0
            for item in entries:
                name = item.filename
                part = PurePosixPath(name)
                if (not name or name.startswith("/") or "\\" in name
                        or any(s in ("..", "", ".") for s in name.split("/"))
                        or part.is_absolute() or ":" in name.split("/")[0]):
                    raise PluginError("unsafe bundle path")
                if ((item.external_attr >> 16) & 0o170000) == stat.S_IFLNK:
                    raise PluginError("symlink entries forbidden")
                if name in paths:
                    raise PluginError("duplicate bundle path")
                total += item.file_size
                if total > _MAX_UNCOMPRESSED:
                    raise PluginError("oversized decompressed payload")
                paths.append(name)
            if "manifest.json" not in paths or paths.count("manifest.json") != 1:
                raise PluginError("root manifest.json required")
            info = archive.getinfo("manifest.json")
            if info.file_size > 65536:
                raise PluginError("oversized manifest")
            try:
                metadata = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (ValueError, UnicodeError, RuntimeError) as exc:
                raise PluginError("invalid JSON manifest") from exc
            manifest = Manifest.parse(metadata)
    except (BadZipFile, OSError, RuntimeError, EOFError) as exc:
        raise PluginError("invalid plugin archive") from exc
    return Inspection(manifest, "sha256:" + hashlib.sha256(bundle).hexdigest(),
                      tuple(paths), len(bundle))


class State(str, Enum):
    DISCOVERED = "DISCOVERED"
    INSPECTED = "INSPECTED"
    ADMITTED = "ADMITTED"
    INSTALLED = "INSTALLED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    QUARANTINED = "QUARANTINED"
    REMOVED = "REMOVED"


class ExternalAdmissionAuthority(Protocol):
    """Implementation lives in externally admitted CFA3 Security/Rights/Identity."""

    def verify_plugin_admission(self, inspection: Inspection) -> bool: ...


class ExternalSandboxAuthority(Protocol):
    """Implementation lives in approved CFA3 sandbox/runtime fabric."""

    def verify_runtime_isolation(self, inspection: Inspection, package_path: Path) -> bool: ...


class Registry:
    """Content-addressed, non-executing plugin package manager.

    No automatic host process spawning or script execution. The record and
    installed bundle are separate from external sandbox launch capabilities.
    """

    def __init__(self, storage_root: Path):
        self.root = Path(storage_root)
        self._records: dict[tuple[str, str], Inspection] = {}
        self._states: dict[tuple[str, str], State] = {}
        self._active: dict[str, tuple[str, str]] = {}

    def inspect(self, bundle: bytes) -> Inspection:
        report = inspect_package(bundle)
        key = (report.manifest.plugin_id, report.manifest.version)
        old = self._records.get(key)
        if old is not None and old.bundle_digest != report.bundle_digest:
            raise PluginError("same plugin version cannot silently change digest")
        # A repeat inspection must never downgrade ADMITTED, INSTALLED,
        # ENABLED, DISABLED or QUARANTINED to a weaker lifecycle state.
        if key in self._states and self._states[key] != State.INSPECTED:
            raise PluginError("already processed plugin version requires lifecycle action")
        self._records[key] = report
        self._states[key] = State.INSPECTED
        return report

    def state(self, plugin_id: str, version: str) -> State:
        return self._states.get((plugin_id, version), State.DISCOVERED)

    def admit(self, plugin_id: str, version: str,
              authority: ExternalAdmissionAuthority | None = None):
        key = (plugin_id, version)
        if self._states.get(key) != State.INSPECTED:
            raise PluginError("inspection required before admission")
        if authority is None or not authority.verify_plugin_admission(self._records[key]):
            raise PluginError("external security/rights admission missing")
        self._states[key] = State.ADMITTED

    def _storage_path(self, inspection: Inspection) -> Path:
        # Path controlled entirely by SHA-256 digest, not by arbitrary names.
        return self.root / (inspection.bundle_digest[7:] + ".cfa3-plugin")

    def install(self, plugin_id: str, version: str, bundle: bytes) -> Path:
        key = (plugin_id, version)
        if self._states.get(key) != State.ADMITTED:
            raise PluginError("admission required before installation")
        report = inspect_package(bundle)
        if report != self._records[key]:
            raise PluginError("bundle changed after external admission")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination = self._storage_path(report)
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != report.bundle_digest[7:]:
                raise PluginError("existing package digest mismatch")
        else:
            fd, temp = tempfile.mkstemp(prefix=".cfa3-staging-", dir=self.root)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(bundle)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temp, 0o600)
                os.replace(temp, destination)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        self._states[key] = State.INSTALLED
        return destination

    def enable(self, plugin_id: str, version: str,
               sandbox: ExternalSandboxAuthority | None = None):
        key = (plugin_id, version)
        if self._states.get(key) not in (State.INSTALLED, State.DISABLED):
            raise PluginError("installed or disabled package required")
        report = self._records[key]
        path = self._storage_path(report)
        if (sandbox is None or not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != report.bundle_digest[7:]
                or not sandbox.verify_runtime_isolation(report, path)):
            raise PluginError("externally verified sandbox isolation required")
        if plugin_id in self._active and self._active[plugin_id] != key:
            raise PluginError("another version is enabled")
        self._states[key] = State.ENABLED
        self._active[plugin_id] = key

    def disable(self, plugin_id: str, version: str):
        key = (plugin_id, version)
        if self._states.get(key) != State.ENABLED:
            raise PluginError("only enabled plugin can be disabled")
        self._states[key] = State.DISABLED
        self._active.pop(plugin_id, None)

    def quarantine(self, plugin_id: str, version: str):
        key = (plugin_id, version)
        if key not in self._records:
            raise PluginError("unknown plugin")
        self._active.pop(plugin_id, None)
        self._states[key] = State.QUARANTINED

    def remove(self, plugin_id: str, version: str):
        key = (plugin_id, version)
        if self._states.get(key) == State.ENABLED:
            raise PluginError("disable before removal")
        if key not in self._records:
            raise PluginError("unknown plugin")
        if self._states.get(key) in (State.INSTALLED, State.DISABLED, State.QUARANTINED):
            self._storage_path(self._records[key]).unlink(missing_ok=True)
        self._states[key] = State.REMOVED

    def affected_consumers(self, plugin_id: str, version: str, available_apps: frozenset[str]):
        """Return only explicitly declared, existing application consumers."""
        report = self._records.get((plugin_id, version))
        if report is None:
            raise PluginError("unknown plugin")
        return tuple(app for app in report.manifest.apps if app in available_apps)
