"""No physical Current Host claims from local test mocks."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cfa3_current_host.local_runner import LocalTestError, _run, run_cfa3_owned_reference_tests


class RunnerBoundaryTests(unittest.TestCase):
    def make_checkout(self, root):
        for relative in (
            "Cargo.toml",
            "cfa3_current_host/core.py",
            "cfa3_current_host/plugin_fabric.py",
            "crates/cfa3-current-host/Cargo.toml",
            "tests/test_current_host_core.py",
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")

    def test_missing_checkout_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(LocalTestError):
                run_cfa3_owned_reference_tests(Path(directory))

    def test_nonphysical_process_observation_never_grants_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_checkout(root)
            commands = []
            def fake_run(args, cwd, timeout):
                commands.append(tuple(args))
                if args[:3] == ["git", "rev-parse", "HEAD"]:
                    return {"result": "REFERENCE_PASS", "returncode": 0,
                            "transcript_tail": "a" * 40}
                return {"result": "REFERENCE_PASS", "returncode": 0,
                        "transcript_tail": "Ran reference tests"}
            with patch("cfa3_current_host.local_runner._run", side_effect=fake_run), \
                 patch("cfa3_current_host.local_runner.shutil.which", return_value=None):
                result = run_cfa3_owned_reference_tests(root)
            self.assertFalse(result["physical_current_host_pass"])
            self.assertEqual(result["evidence_status"],
                             "REFERENCE_ONLY_PENDING_EXTERNAL_AUTHORITY")
            self.assertEqual(result["rust_tests"]["result"], "NOT_RUN_MISSING_CARGO")
            self.assertEqual(result["source_revision"], "a" * 40)
            self.assertFalse(result["environment"]["manufacturer_drivers_qualified"])
            self.assertFalse(result["environment"]["commercial_software_qualified"])
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[1][-1], "-v")

    def test_reference_failure_not_converted_into_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_checkout(root)
            def fake_run(args, cwd, timeout):
                if args[0] == "git":
                    return {"result": "REFERENCE_FAIL", "returncode": 1, "transcript_tail": ""}
                return {"result": "REFERENCE_FAIL", "returncode": 2, "transcript_tail": "FAILED"}
            with patch("cfa3_current_host.local_runner._run", side_effect=fake_run), \
                 patch("cfa3_current_host.local_runner.shutil.which", return_value=None):
                result = run_cfa3_owned_reference_tests(root)
            self.assertEqual(result["python_tests"]["result"], "REFERENCE_FAIL")
            self.assertEqual(result["source_revision"], "UNVERIFIED_CHECKOUT")
            self.assertFalse(result["physical_current_host_pass"])

    def test_timeout_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("cfa3_current_host.local_runner.subprocess.run",
                       side_effect=subprocess.TimeoutExpired(["test"], 2)):
                report = _run(["test"], Path(directory), timeout=2)
        self.assertEqual(report["result"], "TIMEOUT")
        self.assertIsNone(report["returncode"])


if __name__ == "__main__":
    unittest.main()
