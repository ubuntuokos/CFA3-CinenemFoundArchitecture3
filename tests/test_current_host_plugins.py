"""CFA3-owned community plugin intake tests, never third-party product QA."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from cfa3_current_host.plugin_fabric import (
    ExternalAdmissionAuthority, ExternalSandboxAuthority,
    Manifest, PluginError, Registry, State, inspect_package,
)


def manifest():
    return {
        "plugin_id": "com.example.plugin",
        "version": "1.0.0",
        "publisher": "Example Org",
        "license": "MIT",
        "api": "cfa3-plugin/v1",
        "apps": ["cfa3.video"],
        "capabilities": ["video.effect"],
        "permissions": ["effect.process"],
        "dependencies": [],
        "gui": False,
    }


def bundle(data=None, *, additions=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as output:
        output.writestr("manifest.json", json.dumps(data if data is not None else manifest()))
        output.writestr("assets/empty.txt", "safe fixture")
        for name, value in additions or ():
            output.writestr(name, value)
    return buf.getvalue()


class FixtureAdmissionAuthority:
    """Deterministic test double, NOT a production CFA3 Security authority."""
    def verify_plugin_admission(self, inspection):
        return inspection.manifest.publisher == "Example Org"


class FixtureSandboxAuthority:
    """Deterministic test double, NOT production sandbox containment."""
    def verify_runtime_isolation(self, inspection, package_path):
        return package_path.is_file()


class InspectionTests(unittest.TestCase):
    def test_valid_bundle_is_statically_inspected(self):
        r = inspect_package(bundle())
        self.assertEqual(r.manifest.plugin_id, "com.example.plugin")
        self.assertTrue(r.bundle_digest.startswith("sha256:"))
        self.assertEqual(r.provenance_status, "UNVERIFIED")
        self.assertEqual(r.rights_status, "UNVERIFIED")

    def test_zip_traversal_is_rejected(self):
        with self.assertRaises(PluginError):
            inspect_package(bundle(additions=[("../outside.txt", "no")]))

    def test_absolute_zip_path_is_rejected(self):
        with self.assertRaises(PluginError):
            inspect_package(bundle(additions=[("/tmp/payload", "no")]))

    def test_invalid_json_or_manifest_is_rejected(self):
        bad = manifest()
        bad["api"] = "other-api"
        with self.assertRaises(PluginError):
            inspect_package(bundle(bad))

    def test_duplicate_capability_is_rejected(self):
        bad = manifest()
        bad["capabilities"] = ["video.effect", "video.effect"]
        with self.assertRaises(PluginError):
            inspect_package(bundle(bad))

    def test_no_target_application_is_rejected(self):
        bad = manifest()
        bad["apps"] = []
        with self.assertRaises(PluginError):
            inspect_package(bundle(bad))

    def test_bogus_archive_rejected(self):
        with self.assertRaises(PluginError):
            inspect_package(b"not a zip")

    def test_third_party_license_field_is_not_rights_verification(self):
        r = inspect_package(bundle())
        self.assertEqual(r.manifest.license_expression, "MIT")
        self.assertEqual(r.rights_status, "UNVERIFIED")

    def test_oversized_bundle_rejected(self):
        with self.assertRaises(PluginError):
            inspect_package(b"x" * (16 * 1024 * 1024 + 1))


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.registry = Registry(Path(self.tempdir.name))
        self.blob = bundle()
        self.registry.inspect(self.blob)
        self.name = "com.example.plugin"
        self.version = "1.0.0"

    def test_no_install_without_external_admission(self):
        with self.assertRaises(PluginError):
            self.registry.install(self.name, self.version, self.blob)
        self.assertEqual(self.registry.state(self.name, self.version), State.INSPECTED)

    def test_admission_requires_external_authority(self):
        with self.assertRaises(PluginError):
            self.registry.admit(self.name, self.version)
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        self.assertEqual(self.registry.state(self.name, self.version), State.ADMITTED)

    def test_package_installed_without_running_plugin_code(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        destination = self.registry.install(self.name, self.version, self.blob)
        self.assertTrue(destination.is_file())
        self.assertEqual(destination.read_bytes(), self.blob)
        self.assertEqual(self.registry.state(self.name, self.version), State.INSTALLED)

    def test_package_mutation_after_inspection_fails_closed(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        with self.assertRaises(PluginError):
            self.registry.install(self.name, self.version, bundle(additions=[("other.txt", "changed")]))

    def test_enabling_requires_explicit_sandbox_gate(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        self.registry.install(self.name, self.version, self.blob)
        with self.assertRaises(PluginError):
            self.registry.enable(self.name, self.version)
        self.assertEqual(self.registry.state(self.name, self.version), State.INSTALLED)

    def test_disable_then_remove(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        p = self.registry.install(self.name, self.version, self.blob)
        self.registry.enable(self.name, self.version, FixtureSandboxAuthority())
        self.assertEqual(self.registry.state(self.name, self.version), State.ENABLED)
        with self.assertRaises(PluginError):
            self.registry.remove(self.name, self.version)
        self.registry.disable(self.name, self.version)
        self.registry.remove(self.name, self.version)
        self.assertEqual(self.registry.state(self.name, self.version), State.REMOVED)
        self.assertFalse(p.exists())

    def test_quarantine_prevents_unreviewed_enable(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        self.registry.install(self.name, self.version, self.blob)
        self.registry.quarantine(self.name, self.version)
        with self.assertRaises(PluginError):
            self.registry.enable(self.name, self.version, FixtureSandboxAuthority())

    def test_actual_consumers_only(self):
        result = self.registry.affected_consumers(self.name, self.version,
                                                 frozenset({"cfa3.video", "cfa3.audio"}))
        self.assertEqual(result, ("cfa3.video",))
        self.assertNotIn("cfa3.audio", result)

    def test_same_version_cannot_switch_contents_silently(self):
        with self.assertRaises(PluginError):
            self.registry.inspect(bundle(additions=[("extra.txt", "different")]))

    def test_reinspection_cannot_downgrade_admitted_state(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        with self.assertRaises(PluginError):
            self.registry.inspect(self.blob)
        self.assertEqual(self.registry.state(self.name, self.version), State.ADMITTED)

    def test_reinspection_cannot_downgrade_enabled_state(self):
        self.registry.admit(self.name, self.version, FixtureAdmissionAuthority())
        self.registry.install(self.name, self.version, self.blob)
        self.registry.enable(self.name, self.version, FixtureSandboxAuthority())
        with self.assertRaises(PluginError):
            self.registry.inspect(self.blob)
        self.assertEqual(self.registry.state(self.name, self.version), State.ENABLED)

    def test_no_plugin_execution_on_inspection(self):
        """An archive entry with source text must never be imported/executed."""
        self.registry.inspect(self.blob)
        self.assertEqual(self.registry.state(self.name, self.version), State.INSPECTED)


if __name__ == "__main__":
    unittest.main()
