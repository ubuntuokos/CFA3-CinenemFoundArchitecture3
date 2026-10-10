"""Host-memory-safe capture and checked ZIP-inflation of community plugins.

Mock subprocess fixtures do not constitute real Linux namespace security PASS.
"""
import hashlib
import io
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from cfa3_current_host.plugin_sandbox import (
    _execute_in_bwrap, PluginError, SandboxExecutionFailed,
)
from cfa3_current_host.plugin_fabric import State


class FakeRegistry:
    def __init__(self, root: Path, source: bytes):
        self.file = root / 'exact.cfa3-plugin'
        self.file.write_bytes(source)
        digest = 'sha256:' + hashlib.sha256(source).hexdigest()
        self.report = SimpleNamespace(
            manifest=SimpleNamespace(permissions=('plugin.run',)),
            contained_paths=('plugin/main.py',), bundle_digest=digest,
        )
        self._records = {('com.example', '1.0'): self.report}

    def state(self, ident, version):
        return State.ENABLED

    def _storage_path(self, record):
        return self.file


def fixture(size=16):
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w') as archive:
        archive.writestr('plugin/main.py', b'p' * size)
    return buffer.getvalue()


class BoundedOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.registry = FakeRegistry(Path(self.temp.name), fixture())

    def invoke(self, fake_run):
        with patch('cfa3_current_host.plugin_sandbox.shutil.which',
                   return_value='/usr/bin/python3'), \
             patch('cfa3_current_host.plugin_sandbox.inspect_package',
                   return_value=self.registry.report), \
             patch('cfa3_current_host.plugin_sandbox.subprocess.run',
                   side_effect=fake_run):
            return _execute_in_bwrap(self.registry, 'com.example', '1.0',
                                     entrypoint='plugin/main.py')

    def test_regular_stdout_captured_using_files_not_memory_pipes(self):
        def run(argv, **kwargs):
            self.assertNotIn('capture_output', kwargs)
            self.assertNotIn('PIPE', repr(kwargs['stdout']))
            self.assertIn('--unshare-all', argv)
            self.assertEqual(kwargs['shell'], False)
            kwargs['stdout'].write(b'hello plugin\n')
            kwargs['stderr'].write(b'warning\n')
            return subprocess.CompletedProcess(argv, 0)
        result = self.invoke(run)
        self.assertEqual(result['stdout'], 'hello plugin\n')
        self.assertFalse(result['physical_current_host_pass'])

    def test_excessive_stdout_is_rejected_with_bounded_read(self):
        def run(argv, **kwargs):
            kwargs['stdout'].write(b'x' * 70000)
            return subprocess.CompletedProcess(argv, 0)
        with self.assertRaisesRegex(SandboxExecutionFailed, 'SANDBOX_OUTPUT_LIMIT'):
            self.invoke(run)

    def test_excessive_stderr_is_rejected_with_bounded_read(self):
        def run(argv, **kwargs):
            kwargs['stderr'].write(b'e' * 70000)
            return subprocess.CompletedProcess(argv, 0)
        with self.assertRaisesRegex(SandboxExecutionFailed, 'SANDBOX_OUTPUT_LIMIT'):
            self.invoke(run)

    def test_failed_process_is_not_mislabeled_as_isolated_success(self):
        def run(argv, **kwargs):
            kwargs['stdout'].write(b'not successful')
            return subprocess.CompletedProcess(argv, 3)
        with self.assertRaisesRegex(SandboxExecutionFailed, 'SANDBOX_PROCESS_FAILED'):
            self.invoke(run)

    def test_oversize_zip_member_is_rejected_before_inflate(self):
        archive = fixture(size=1024 * 1024 + 1)
        reg = FakeRegistry(Path(self.temp.name), archive)
        self.registry = reg
        with patch('cfa3_current_host.plugin_sandbox.shutil.which',
                   return_value='/usr/bin/python3'), \
             patch('cfa3_current_host.plugin_sandbox.inspect_package',
                   return_value=reg.report), \
             patch('cfa3_current_host.plugin_sandbox.subprocess.run') as never_run:
            with self.assertRaisesRegex(PluginError, 'ENTRYPOINT_SIZE_LIMIT'):
                _execute_in_bwrap(reg, 'com.example', '1.0',
                                  entrypoint='plugin/main.py')
            never_run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
