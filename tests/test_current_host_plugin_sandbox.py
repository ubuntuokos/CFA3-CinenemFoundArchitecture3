"""Negative sandbox tests, plus command contract fixture; not real containment PASS."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from cfa3_current_host.plugin_fabric import PluginError, Registry
from cfa3_current_host.plugin_sandbox import (
    SandboxExecutionFailed, SandboxUnavailable, execute_plugin_cpu,
)
from cfa3_current_host.foundation_runtime import (
    CpuResourceBroker, FoundationRuntime, FoundationDenied, ModelRouter,
    RightsAuthority, SecurityAuthority, WorkloadModeBroker, Request, Mode,
)


def package(*, permission=True):
    metadata = {
        "plugin_id": "com.example.cpu", "version": "1.0.0",
        "publisher": "Publisher", "license": "MIT",
        "api": "cfa3-plugin/v1", "apps": ["cfa3.video"],
        "capabilities": [], "permissions": ["plugin.run"] if permission else [],
        "dependencies": [], "gui": False,
    }
    stream = io.BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr("manifest.json", json.dumps(metadata))
        archive.writestr("plugin/main.py", 'print("sandbox fixture")\n')
    return stream.getvalue()


class Authority:
    def verify_plugin_admission(self, report): return True


class Sandbox:
    def verify_runtime_isolation(self, report, path): return True


class SandboxTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.registry = Registry(Path(temp.name))
        self.plugin_id = "com.example.cpu"
        self.blob = package()
        self.registry.inspect(self.blob)

    def access(self, registry=None, *, actor="Publisher"):
        reg = registry or self.registry
        digest = reg._records[(self.plugin_id, "1.0.0")].bundle_digest
        runtime = FoundationRuntime(
            security=SecurityAuthority([(actor, "cfa3.plugin-host",
                                         "plugin.execute", "cfa3.community-plugin.run")]),
            rights=RightsAuthority([digest]), model_router=ModelRouter(),
            hrb=CpuResourceBroker(1), modes=WorkloadModeBroker(),
        )
        session = runtime.start(Request(
            actor=actor, component="cfa3.plugin-host", operation="plugin.execute",
            capability="cfa3.community-plugin.run", artifact_digest=digest,
            cpu_threads=1, mode=Mode.INTERACTIVE
        ))
        return {"foundation": runtime, "session": session}

    def enable(self):
        self.registry.admit(self.plugin_id, "1.0.0", Authority())
        self.registry.install(self.plugin_id, "1.0.0", self.blob)
        self.registry.enable(self.plugin_id, "1.0.0", Sandbox())

    def test_missing_bubblewrap_does_not_fallback(self):
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value=None):
            with self.assertRaisesRegex(SandboxUnavailable, "BUBBLEWRAP_REQUIRED"):
                execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                   entrypoint="plugin/main.py", **self.access())

    def test_enabled_admission_required(self):
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"):
            with self.assertRaisesRegex(PluginError, "PLUGIN_NOT_ENABLED"):
                execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                   entrypoint="plugin/main.py", **self.access())

    def test_permission_denial(self):
        self.registry.inspect(self.blob)
        self.enable()
        self.registry._records[(self.plugin_id, "1.0.0")].manifest
        # Explicit permission required for execution; separate isolated fixture.
        other = Registry(self.registry.root / "other")
        blob = package(permission=False)
        other.inspect(blob); other.admit(self.plugin_id, "1.0.0", Authority())
        other.install(self.plugin_id, "1.0.0", blob)
        other.enable(self.plugin_id, "1.0.0", Sandbox())
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"):
            with self.assertRaisesRegex(PluginError, "EXECUTION_PERMISSION_REQUIRED"):
                execute_plugin_cpu(other, self.plugin_id, "1.0.0", entrypoint="plugin/main.py", **self.access(other))

    def test_entrypoint_must_be_declared_and_no_traversal(self):
        self.enable()
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"):
            for path in ("../private.py", "/etc/passwd", "unknown.py", "manifest.json"):
                with self.subTest(path=path), self.assertRaises(PluginError):
                    execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0", entrypoint=path, **self.access())

    def test_positive_command_isolated_flags_but_not_containment_pass(self):
        self.enable()
        captured = []
        def fake_run(command, **kwargs):
            captured.extend(command)
            self.assertFalse(kwargs["shell"])
            self.assertIn("--unshare-all", command)
            self.assertIn("--die-with-parent", command)
            self.assertIn("--cap-drop", command)
            kwargs["stdout"].write(b"fixture\n")
            kwargs["stderr"].write(b"")
            self.assertNotIn("capture_output", kwargs)
            return subprocess.CompletedProcess(command, 0)
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"), \
             patch("cfa3_current_host.plugin_sandbox.subprocess.run", side_effect=fake_run):
            result = execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                        entrypoint="plugin/main.py", **self.access())
        self.assertEqual(result["stdout"], "fixture\n")
        self.assertFalse(result["physical_current_host_pass"])
        self.assertEqual(result["security_certification"], "PENDING_EXTERNAL_VALIDATION")
        self.assertIn("--unshare-all", captured)

    def test_timeout_is_explicit_failure(self):
        self.enable()
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"), \
             patch("cfa3_current_host.plugin_sandbox.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["bwrap"], 1)):
            with self.assertRaisesRegex(SandboxExecutionFailed, "TIMEOUT"):
                execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                   entrypoint="plugin/main.py", **self.access())

    def test_oversized_timeout_rejected(self):
        self.enable()
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"):
            with self.assertRaises(ValueError):
                execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                   entrypoint="plugin/main.py", timeout_seconds=60, **self.access())

    def test_foundation_session_is_mandatory(self):
        with self.assertRaises(TypeError):
            execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                               entrypoint="plugin/main.py")

    def test_scope_mismatch_releases_lease(self):
        self.enable()
        ticket = self.access(actor="Untrusted")
        with self.assertRaisesRegex(FoundationDenied, "PLUGIN_SCOPE_OR_RIGHTS_MISMATCH"):
            execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                               entrypoint="plugin/main.py", **ticket)
        self.assertEqual(ticket["foundation"].hrb.allocated, 0)
        self.assertEqual(ticket["foundation"].modes.indicator, "NONE")

    def test_changed_install_package_rejected(self):
        self.enable()
        path = self.registry._storage_path(self.registry._records[(self.plugin_id, "1.0.0")])
        path.write_bytes(b"tampered")
        with patch("cfa3_current_host.plugin_sandbox.shutil.which", return_value="/usr/bin/python3"):
            with self.assertRaisesRegex(PluginError, "BUNDLE_DIGEST_MISMATCH"):
                execute_plugin_cpu(self.registry, self.plugin_id, "1.0.0",
                                   entrypoint="plugin/main.py", **self.access())


if __name__ == "__main__":
    unittest.main()
