"""Linux bubblewrap execution boundary for admitted community plugin packages.

No direct unsandboxed fallback. Requires a separately admitted, exact-digest
plugin and an external sandbox authority at Registry.enable(). A missing
bubblewrap tool or unsupported host is an explicit blocker, not bypass.
This is a host implementation candidate, NOT yet security-certified.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import resource
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from .plugin_fabric import PluginError, Registry, State, inspect_package


class SandboxUnavailable(RuntimeError):
    pass


class SandboxExecutionFailed(RuntimeError):
    pass


def _resource_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    os.umask(0o077)


def _execute_in_bwrap(
    registry: Registry, plugin_id: str, version: str, *,
    entrypoint: str, timeout_seconds: float = 8, argv: tuple[str, ...] = (),
) -> dict:
    """Run one declared Python entrypoint isolated by bubblewrap on Linux.

    No filesystem access beyond /usr, read-only package directory, minimum
    required loader libraries and private /tmp. Network/user/PID/IPC namespaces
    are unshared. This does not certify arbitrary native host drivers or apps.
    """
    if sys.platform != "linux":
        raise SandboxUnavailable("LINUX_SANDBOX_REQUIRED")
    binary = shutil.which("bwrap")
    if binary is None or not Path(binary).is_file():
        raise SandboxUnavailable("BUBBLEWRAP_REQUIRED_NO_UNSANDBOXED_FALLBACK")
    if registry.state(plugin_id, version) != State.ENABLED:
        raise PluginError("PLUGIN_NOT_ENABLED_OR_ADMITTED")
    record = registry._records.get((plugin_id, version))
    if record is None or "plugin.run" not in record.manifest.permissions:
        raise PluginError("EXPLICIT_PLUGIN_EXECUTION_PERMISSION_REQUIRED")
    path = PurePosixPath(entrypoint)
    if (path.is_absolute() or not entrypoint.endswith(".py")
            or any(part in (".", "..", "") for part in entrypoint.split("/"))
            or entrypoint not in record.contained_paths):
        raise PluginError("UNDECLARED_OR_UNSAFE_ENTRYPOINT")
    if (type(timeout_seconds) not in (int, float) or
            not 0 < timeout_seconds <= 30):
        raise ValueError("bounded timeout required")
    if (not isinstance(argv, tuple) or len(argv) > 16
            or any(not isinstance(x, str) or len(x) > 256 for x in argv)):
        raise ValueError("bounded positional arguments required")
    package = registry._storage_path(record)
    if (not package.is_file() or
            "sha256:" + hashlib.sha256(package.read_bytes()).hexdigest()
            != record.bundle_digest):
        raise PluginError("INSTALLED_BUNDLE_DIGEST_MISMATCH")
    candidate = inspect_package(package.read_bytes())
    if candidate.bundle_digest != record.bundle_digest:
        raise PluginError("PACKAGE_REINSPECTION_FAILED")
    # Extract exactly ONE vetted Python file into a fresh directory.
    # No archive-wide extraction, no symlinks, no upload to shared directories.
    with tempfile.TemporaryDirectory(prefix="cfa3-plugin-run-") as work:
        workdir = Path(work)
        script = workdir / "entry.py"
        with ZipFile(package) as archive:
            # Check the ZIP directory size before inflating into the host.
            if archive.getinfo(entrypoint).file_size > 1024 * 1024:
                raise PluginError("ENTRYPOINT_SIZE_LIMIT")
            raw = archive.read(entrypoint)
        if len(raw) > 1024 * 1024:
            raise PluginError("ENTRYPOINT_SIZE_LIMIT")
        script.write_bytes(raw)
        script.chmod(0o400)
        command = [
            binary, "--die-with-parent", "--new-session", "--unshare-all",
            "--cap-drop", "ALL",
        ]
        for system_path in ("/usr", "/bin", "/lib", "/lib64"):
            if Path(system_path).exists():
                command.extend(("--ro-bind", system_path, system_path))
        command.extend((
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
            "--ro-bind", str(workdir), "/cfa3-plugin",
            "--chdir", "/cfa3-plugin", "--setenv", "HOME", "/tmp",
            "--setenv", "PYTHONPATH", "",
            "--", "/usr/bin/python3", "-I", "-S", "/cfa3-plugin/entry.py", *argv
        ))
        # Do not use subprocess.run(capture_output=True): an untrusted plugin
        # could exhaust the host process memory by writing unlimited output.
        # Temporary files are backed by the child RLIMIT_FSIZE (64 KiB each),
        # and the host reads at most 64 KiB + 1 from each file.
        with tempfile.TemporaryFile(mode="w+b") as stdout_file, \
             tempfile.TemporaryFile(mode="w+b") as stderr_file:
            try:
                result = subprocess.run(
                    command, shell=False, timeout=timeout_seconds, check=False,
                    stdin=subprocess.DEVNULL, stdout=stdout_file,
                    stderr=stderr_file,
                    env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
                    preexec_fn=_resource_limits,
                )
            except subprocess.TimeoutExpired as exc:
                raise SandboxExecutionFailed("SANDBOX_TIMEOUT") from exc
            except OSError as exc:
                raise SandboxUnavailable("BUBBLEWRAP_CANNOT_LAUNCH") from exc
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(65537)
            stderr = stderr_file.read(65537)
    if len(stdout) > 65536 or len(stderr) > 65536:
        raise SandboxExecutionFailed("SANDBOX_OUTPUT_LIMIT")
    if result.returncode:
        raise SandboxExecutionFailed("SANDBOX_PROCESS_FAILED")
    return {
        "status": "ISOLATED_EXECUTION_OBSERVED",
        "exit_code": result.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "physical_current_host_pass": False,
        "plugin_product_qa": "DEVELOPER_RESPONSIBILITY",
        "security_certification": "PENDING_EXTERNAL_VALIDATION",
    }


def execute_plugin_cpu(
    registry: Registry, plugin_id: str, version: str, *,
    entrypoint: str, foundation, session, timeout_seconds: float = 8,
    argv: tuple[str, ...] = (),
) -> dict:
    """Require live CPU Foundation authority/HRB/mode and then confine a plugin.

    The caller cannot substitute a plugin manifest for an actual Foundation
    admission. Every branch releases the lease; no retry or unconfined fallback.
    """
    from .foundation_runtime import FoundationDenied, FoundationRuntime, Session
    if not isinstance(foundation, FoundationRuntime) or not isinstance(session, Session):
        raise FoundationDenied("LIVE_FOUNDATION_SESSION_REQUIRED")
    # Pin the HRB/mode lease for the *entire* sandbox operation. Reapers must
    # never reallocate these CPU resources while the plugin subprocess runs.
    with foundation.bound_operation(session):
        request = session.request
        record = registry._records.get((plugin_id, version))
        if (record is None
                or request.actor != record.manifest.publisher
                or request.component != "cfa3.plugin-host"
                or request.operation != "plugin.execute"
                or request.capability != "cfa3.community-plugin.run"
                or request.artifact_digest != record.bundle_digest
                or request.model_id is not None
                or session.route != "NO_MODEL_REQUIRED"):
            raise FoundationDenied("PLUGIN_SCOPE_OR_RIGHTS_MISMATCH")
        return _execute_in_bwrap(
            registry, plugin_id, version,
            entrypoint=entrypoint, timeout_seconds=timeout_seconds, argv=argv
        )
