import tempfile
import unittest
from pathlib import Path

from cfa3_current_host.developer_sdk import build_bundle, run_static_testkit, scaffold_plugin
from cfa3_current_host.plugin_fabric import PluginError, inspect_package


class DeveloperSdkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "community-example"

    def scaffold(self):
        return scaffold_plugin(self.target, plugin_id="com.community.effect",
                               app="cfa3.video", publisher="Community Developer",
                               license_expression="MIT")

    def test_new_project_has_valid_manifest(self):
        manifest, readme = self.scaffold()
        self.assertTrue(manifest.is_file())
        self.assertIn("DEVELOPER", readme.read_text().upper())
        self.assertEqual(inspect_package(build_bundle(self.target)).manifest.plugin_id,
                         "com.community.effect")

    def test_scaffold_is_no_overwrite(self):
        self.scaffold()
        with self.assertRaises(PluginError):
            self.scaffold()

    def test_invalid_application_is_not_accepted(self):
        with self.assertRaises(PluginError):
            scaffold_plugin(self.target, plugin_id="x", app="cfa3.video",
                            publisher="Developer", license_expression="MIT")

    def test_build_is_byte_reproducible(self):
        self.scaffold()
        self.assertEqual(build_bundle(self.target), build_bundle(self.target))

    def test_contract_testkit_checks_only_real_consumers(self):
        self.scaffold()
        report = run_static_testkit(build_bundle(self.target),
                                    available_cfa3_apps=frozenset({"cfa3.video", "cfa3.audio"}))
        self.assertEqual(report["actual_consumers"], ["cfa3.video"])
        self.assertEqual(report["missing_consumers"], [])
        self.assertEqual(report["host_contract_result"], "COMPATIBLE_REFERENCE")
        self.assertFalse(report["physical_current_host_pass"])
        self.assertEqual(report["runtime_admission"], "NOT_ADMITTED")

    def test_unknown_consumer_requires_review(self):
        self.scaffold()
        report = run_static_testkit(build_bundle(self.target),
                                    available_cfa3_apps=frozenset({"cfa3.audio"}))
        self.assertEqual(report["host_contract_result"], "MISSING_CFA3_CONSUMER")

    def test_plugin_product_quality_not_certified(self):
        self.scaffold()
        report = run_static_testkit(build_bundle(self.target),
                                    available_cfa3_apps=frozenset({"cfa3.video"}))
        self.assertEqual(report["plugin_functional_qa"], "DEVELOPER_RESPONSIBILITY")
        self.assertEqual(report["license_admission"], "UNVERIFIED")

    def test_symlink_into_build_tree_rejected(self):
        self.scaffold()
        (self.target / "unsafe").symlink_to(self.target / "README.md")
        with self.assertRaises(PluginError):
            build_bundle(self.target)


if __name__ == "__main__":
    unittest.main()
