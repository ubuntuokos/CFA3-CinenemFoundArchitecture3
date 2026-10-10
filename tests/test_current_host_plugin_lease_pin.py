"""CPU resource pinning across the CFA3 plugin sandbox trust boundary.

Only the wrapper is tested with a synthetic sandbox callable; no claim of
actual Linux namespace isolation, security certification or physical PASS.
"""
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cfa3_current_host.foundation_runtime import (
    CpuResourceBroker, FoundationDenied, FoundationRuntime,
    ModelRouter, Request, RightsAuthority, SecurityAuthority,
    WorkloadModeBroker, Mode,
)
from cfa3_current_host.plugin_sandbox import (
    SandboxUnavailable, execute_plugin_cpu,
)

DIGEST = 'sha256:' + 'd' * 64


def setup_host(actor='Community Publisher'):
    foundation = FoundationRuntime(
        security=SecurityAuthority(((actor, 'cfa3.plugin-host',
                                     'plugin.execute', 'cfa3.community-plugin.run'),)),
        rights=RightsAuthority((DIGEST,)),
        model_router=ModelRouter(), hrb=CpuResourceBroker(1),
        modes=WorkloadModeBroker(),
    )
    session = foundation.start(Request(
        actor=actor, component='cfa3.plugin-host', operation='plugin.execute',
        capability='cfa3.community-plugin.run', artifact_digest=DIGEST,
        cpu_threads=1, mode=Mode.INTERACTIVE, ttl_seconds=10,
    ))
    record = SimpleNamespace(
        manifest=SimpleNamespace(publisher='Community Publisher'),
        bundle_digest=DIGEST,
    )
    registry = SimpleNamespace(_records={('com.example.plugin', '1.0.0'): record})
    return foundation, session, registry


class PluginLeasePinTests(unittest.TestCase):
    def test_active_sandbox_keeps_cpu_and_mode_lease(self):
        foundation, session, registry = setup_host()

        def fake_isolation(*args, **kwargs):
            self.assertEqual(foundation.hrb.allocated, 1)
            self.assertEqual(foundation.modes.indicator, 'INTERACTIVE')
            with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                       return_value=session.deadline_monotonic + 1):
                self.assertEqual(foundation.reap_expired(), 0)
                with self.assertRaisesRegex(FoundationDenied, 'RUNNING_SESSION_CANNOT_BE_RELEASED'):
                    foundation.finish(session)
            return {'status': 'MOCK_EXECUTED', 'physical_current_host_pass': False}

        with patch('cfa3_current_host.plugin_sandbox._execute_in_bwrap',
                   side_effect=fake_isolation):
            result = execute_plugin_cpu(registry, 'com.example.plugin', '1.0.0',
                                        entrypoint='entry.py', foundation=foundation,
                                        session=session)
        self.assertEqual(result['status'], 'MOCK_EXECUTED')
        self.assertFalse(result['physical_current_host_pass'])
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, 'NONE')

    def test_sandbox_failure_cleans_up_all_leases(self):
        foundation, session, registry = setup_host()
        with patch('cfa3_current_host.plugin_sandbox._execute_in_bwrap',
                   side_effect=SandboxUnavailable('BWRAP_REQUIRED')):
            with self.assertRaises(SandboxUnavailable):
                execute_plugin_cpu(registry, 'com.example.plugin', '1.0.0',
                                   entrypoint='entry.py', foundation=foundation,
                                   session=session)
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, 'NONE')

    def test_publisher_mismatch_blocks_before_process_and_releases(self):
        foundation, session, registry = setup_host(actor='Impersonator')
        with patch('cfa3_current_host.plugin_sandbox._execute_in_bwrap') as attempted:
            with self.assertRaisesRegex(FoundationDenied, 'PLUGIN_SCOPE_OR_RIGHTS_MISMATCH'):
                execute_plugin_cpu(registry, 'com.example.plugin', '1.0.0',
                                   entrypoint='entry.py', foundation=foundation,
                                   session=session)
            attempted.assert_not_called()
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, 'NONE')

    def test_sandbox_timeout_expiry_cannot_become_reference_success(self):
        foundation, session, registry = setup_host()
        was_executed = [False]
        original_monotonic = time.monotonic

        def fake_isolation(*args, **kwargs):
            was_executed[0] = True
            return {'status': 'MOCK_EXECUTED'}

        with patch('cfa3_current_host.plugin_sandbox._execute_in_bwrap',
                   side_effect=fake_isolation), \
             patch('cfa3_current_host.foundation_runtime.time.monotonic',
                   side_effect=lambda: session.deadline_monotonic + 1
                   if was_executed[0] else original_monotonic()):
            with self.assertRaisesRegex(FoundationDenied, 'EXPIRED_SESSION'):
                execute_plugin_cpu(registry, 'com.example.plugin', '1.0.0',
                                   entrypoint='entry.py', foundation=foundation,
                                   session=session)
        self.assertTrue(was_executed[0])
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, 'NONE')

    def test_actual_missing_bwrap_has_no_unsandboxed_fallback(self):
        foundation, session, registry = setup_host()
        with patch('cfa3_current_host.plugin_sandbox.shutil.which',
                   return_value=None):
            with self.assertRaisesRegex(SandboxUnavailable, 'BUBBLEWRAP_REQUIRED'):
                execute_plugin_cpu(registry, 'com.example.plugin', '1.0.0',
                                   entrypoint='entry.py', foundation=foundation,
                                   session=session)
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, 'NONE')


if __name__ == '__main__':
    unittest.main()
