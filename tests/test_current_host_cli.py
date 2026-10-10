"""Command-line integration tests for the non-admitting CFA3 Current Host tool."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from cfa3_current_host.__main__ import main, plan_file


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph = self.root / "graph.json"
        self.graph.write_text(json.dumps({
            "components": [
                {"component_id": "cfa3-video", "layer": "VIDEO", "revision": "v1",
                 "ownership": "CFA3_COMPONENT", "gui": True},
                {"component_id": "vendor", "layer": "EXTERNAL", "revision": "v1",
                 "ownership": "VENDOR_DRIVER"}
            ],
            "handoffs": []
        }), encoding="utf-8")

    def capture(self, args):
        out = io.StringIO()
        with redirect_stdout(out):
            status = main(args)
        self.assertEqual(status, 0)
        return json.loads(out.getvalue())

    def test_plan_produces_host_obligations_without_physical_pass(self):
        plan = self.capture(["plan", "--graph", str(self.graph), "--changed", "cfa3-video"])
        self.assertEqual(plan["mode"], "SCOPED")
        self.assertEqual(plan["affected"], ["cfa3-video"])
        self.assertFalse(plan["physical_current_host_pass"])
        self.assertFalse(plan["vendor_drivers_qualified"])
        self.assertEqual(len(plan["obligations"]), 4)

    def test_vendor_driver_change_not_owned(self):
        plan = plan_file(self.graph, ["vendor"], "CODE")
        self.assertEqual(plan["mode"], "NONE")
        self.assertEqual(plan["obligations"], [])

    def test_unknown_component_fails_closed(self):
        with self.assertRaises(ValueError):
            plan_file(self.graph, ["does-not-exist"], "CODE")

    def test_scaffold_build_inspect_end_to_end_without_execution(self):
        folder = self.root / "template"
        report = self.capture([
            "plugin-scaffold", "--target", str(folder), "--id", "com.example.community",
            "--app", "cfa3-video", "--publisher", "Community", "--license", "MIT",
        ])
        self.assertEqual(report["admission"], "NOT_ADMITTED")
        output = self.root / "test.cfa3-plugin"
        build = self.capture(["plugin-build", "--root", str(folder), "--output", str(output)])
        self.assertEqual(build["bundle"], str(output))
        inspect = self.capture(["plugin-inspect", "--bundle", str(output),
                                "--available-app", "cfa3-video"])
        self.assertEqual(inspect["host_contract_result"], "COMPATIBLE_REFERENCE")
        self.assertEqual(inspect["plugin_functional_qa"], "DEVELOPER_RESPONSIBILITY")
        self.assertFalse(inspect["physical_current_host_pass"])

    def test_bundle_overwrite_is_rejected(self):
        folder = self.root / "template"
        self.capture([
            "plugin-scaffold", "--target", str(folder), "--id", "com.example.community",
            "--app", "cfa3-video", "--publisher", "Community", "--license", "MIT",
        ])
        output = self.root / "test.cfa3-plugin"
        self.capture(["plugin-build", "--root", str(folder), "--output", str(output)])
        with self.assertRaises(ValueError):
            self.capture(["plugin-build", "--root", str(folder), "--output", str(output)])

    def test_catalog_check_rejects_missing_component_mapping(self):
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps({
            "schema": "cfa3.current-host.capabilities.v1",
            "capabilities": [],
        }), encoding="utf-8")
        report = self.capture([
            "catalog-check", "--catalog", str(catalog),
            "--graph", str(self.graph),
        ])
        self.assertEqual(report["status"], "BLOCKED_CAPABILITY_GRAPH_MISMATCH")
        self.assertFalse(report["physical_current_host_pass"])

    def test_catalog_check_cannot_omit_real_graph(self):
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps({
            "schema": "cfa3.current-host.capabilities.v1",
            "capabilities": [],
        }), encoding="utf-8")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failed:
            main(["catalog-check", "--catalog", str(catalog)])
        self.assertEqual(failed.exception.code, 2)

    def test_unknown_trigger_fails_closed(self):
        with self.assertRaises(ValueError):
            plan_file(self.graph, ["cfa3-video"], "RANDOM")


if __name__ == "__main__":
    unittest.main()
