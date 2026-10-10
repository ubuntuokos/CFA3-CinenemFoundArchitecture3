"""Community plugin Registry thread races: activation must not override quarantine.

These are CFA3 host-contract tests, not third-party plugin product QA.
"""
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from cfa3_current_host.plugin_fabric import Registry, PluginError, State


def archive(version: str) -> bytes:
    manifest = {
        "plugin_id": "com.example.parallel", "version": version,
        "publisher": "CFA3 test publisher", "license": "MIT",
        "api": "cfa3-plugin/v1", "apps": ["cfa3.video"],
        "capabilities": ["video.test"], "permissions": [],
        "dependencies": [], "gui": False,
    }
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))
    return buffer.getvalue()


class Approve:
    def verify_plugin_admission(self, report):
        return True


class AllowSandbox:
    def verify_runtime_isolation(self, report, stored_path):
        return stored_path.is_file()


class BlockingSandbox:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()

    def verify_runtime_isolation(self, report, stored_path):
        self.entered.set()
        if not self.release.wait(timeout=4):
            raise TimeoutError("fixture sandbox verifier timed out")
        return True


class PluginConcurrencyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.registry = Registry(Path(tmp.name))
        self.name = "com.example.parallel"

    def install(self, version):
        binary = archive(version)
        self.registry.inspect(binary)
        self.registry.admit(self.name, version, Approve())
        self.registry.install(self.name, version, binary)

    def test_quarantine_cannot_be_overwritten_by_inflight_activation(self):
        self.install("1.0.0")
        sandbox = BlockingSandbox()
        errors = []
        quarantine_done = threading.Event()

        def activate():
            try:
                self.registry.enable(self.name, "1.0.0", sandbox)
            except Exception as exc:
                errors.append(exc)

        def revoke():
            try:
                self.registry.quarantine(self.name, "1.0.0")
            except Exception as exc:
                errors.append(exc)
            finally:
                quarantine_done.set()

        a = threading.Thread(target=activate, daemon=True)
        b = threading.Thread(target=revoke, daemon=True)
        a.start()
        try:
            self.assertTrue(sandbox.entered.wait(timeout=2))
            b.start()
            # The transition lock must keep revocation from mutating state
            # midway through admission verification.
            self.assertFalse(quarantine_done.wait(timeout=0.1))
        finally:
            sandbox.release.set()
            a.join(timeout=3)
            if b.ident is not None:
                b.join(timeout=3)
        self.assertFalse(a.is_alive())
        self.assertFalse(b.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(quarantine_done.is_set())
        self.assertEqual(self.registry.state(self.name, "1.0.0"), State.QUARANTINED)
        self.assertNotIn(self.name, self.registry._active)
        with self.assertRaises(PluginError):
            self.registry.enable(self.name, "1.0.0", AllowSandbox())

    def test_exactly_one_version_can_be_enabled(self):
        self.install("1.0.0")
        self.install("1.0.1")
        failures = []
        barrier = threading.Barrier(3)

        def activate(version):
            barrier.wait(timeout=3)
            try:
                self.registry.enable(self.name, version, AllowSandbox())
            except PluginError as exc:
                failures.append(str(exc))

        left = threading.Thread(target=activate, args=("1.0.0",), daemon=True)
        right = threading.Thread(target=activate, args=("1.0.1",), daemon=True)
        left.start()
        right.start()
        barrier.wait(timeout=3)
        left.join(timeout=3)
        right.join(timeout=3)
        self.assertFalse(left.is_alive())
        self.assertFalse(right.is_alive())
        self.assertEqual(len(failures), 1)
        self.assertEqual(len(self.registry._active), 1)
        enabled = [
            version for version in ("1.0.0", "1.0.1")
            if self.registry.state(self.name, version) == State.ENABLED
        ]
        self.assertEqual(len(enabled), 1)
        other = "1.0.0" if enabled[0] == "1.0.1" else "1.0.1"
        self.assertEqual(self.registry.state(self.name, other), State.INSTALLED)


if __name__ == "__main__":
    unittest.main()
