"""Community Plugin SDK v1: developer scaffolding and static host-contract testkit.

No third-party source code executes during scaffolding, packaging or checking.
Developers remain responsible for their plugin's own functional QA and rights.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .plugin_fabric import Manifest, PluginError, Inspection, inspect_package


DEFAULT_API = "cfa3-plugin/v1"


def scaffold_plugin(destination: Path, *, plugin_id: str, app: str,
                    publisher: str, license_expression: str) -> tuple[Path, Path]:
    """Create a fresh, non-executable manifest/README template, never overwrite."""
    manifest = {
        "plugin_id": plugin_id, "version": "0.1.0", "publisher": publisher,
        "license": license_expression, "api": DEFAULT_API,
        "apps": [app], "capabilities": [], "permissions": [],
        "dependencies": [], "gui": False,
    }
    Manifest.parse(manifest)
    destination = Path(destination)
    if destination.exists():
        raise PluginError("target already exists; no overwrite of existing plugin work")
    destination.mkdir(parents=True, exist_ok=False)
    meta_path = destination / "manifest.json"
    readme_path = destination / "README.md"
    meta_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme_path.write_text(
        "# Community Plugin SDK developer starter\n\n"
        "Declare capabilities and permissions before requesting CFA3 host integration.\n"
        "Do not claim CFA3 admission from a locally passing testkit.\n"
        "Write and run your own plugin functional tests separately; supply licenses, "
        "provenance and publisher identity to the CFA3 admission service.\n"
        "Plugin GUI integrations must follow the real host's Qt6 and GUI-test requirements.\n",
        encoding="utf-8",
    )
    return meta_path, readme_path


def build_bundle(root: Path) -> bytes:
    """Build a bounded deterministic zip containing declarative plugin artifacts.

    This SDK does not sign, install, import, execute or sandbox community code.
    Disallow symlinks and paths escaping the declared build directory.
    """
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise PluginError("plugin build root must be a real directory")
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise PluginError("a real manifest.json is required")
    try:
        Manifest.parse(json.loads(manifest_path.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        raise PluginError("invalid plugin manifest") from exc
    paths = sorted(x for x in root.rglob("*") if x.is_file() or x.is_symlink())
    if not paths or len(paths) > 128:
        raise PluginError("invalid bundle file count")
    files = []
    total = 0
    for path in paths:
        if path.is_symlink():
            raise PluginError("plugin bundle symlink is not supported")
        if not path.resolve().is_relative_to(root.resolve()):
            raise PluginError("out-of-root plugin file")
        relative = path.relative_to(root).as_posix()
        if not relative or any(x in (".", "..") for x in relative.split("/")):
            raise PluginError("unsafe relative bundle path")
        blob = path.read_bytes()
        total += len(blob)
        if total > 16 * 1024 * 1024:
            raise PluginError("developer bundle exceeds maximum raw size")
        files.append((relative, blob))
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, blob in files:
            info = ZipInfo(filename=name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, blob)
    candidate = buffer.getvalue()
    inspect_package(candidate)
    return candidate


def run_static_testkit(bundle: bytes, *, available_cfa3_apps: frozenset[str]) -> dict:
    """Pure static CFA3-host contract result. Not plugin functional certification."""
    inspection: Inspection = inspect_package(bundle)
    declared = set(inspection.manifest.apps)
    available = declared.intersection(available_cfa3_apps)
    missing = declared - available_cfa3_apps
    return {
        "plugin_id": inspection.manifest.plugin_id,
        "version": inspection.manifest.version,
        "bundle_digest": inspection.bundle_digest,
        "host_contract_result": "COMPATIBLE_REFERENCE" if not missing else "MISSING_CFA3_CONSUMER",
        "actual_consumers": sorted(available),
        "missing_consumers": sorted(missing),
        "plugin_functional_qa": "DEVELOPER_RESPONSIBILITY",
        "license_admission": "UNVERIFIED",
        "runtime_admission": "NOT_ADMITTED",
        "physical_current_host_pass": False,
    }
