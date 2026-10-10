"""Real CPU Foundation lease expiry and in-flight preservation regressions.

These tests are local/reference evidence only; no physical Current Host PASS.
"""
import threading
import unittest
from unittest.mock import patch

from cfa3_current_host.foundation_runtime import (
    CpuResourceBroker, FoundationDenied, FoundationRuntime, Mode,
    ModelRouter, Request, RightsAuthority, SecurityAuthority, WorkloadModeBroker,
)

DIGEST = 'sha256:' + 'a' * 64
GRANT = ('tester', 'cfa3-host', 'reference', 'cfa3.current-host')


def fixture():
    return FoundationRuntime(
        security=SecurityAuthority((GRANT,)),
        rights=RightsAuthority((DIGEST,)),
        model_router=ModelRouter(),
        hrb=CpuResourceBroker(1),
        modes=WorkloadModeBroker(),
    )


def request(mode=Mode.INTERACTIVE):
    return Request(actor='tester', component='cfa3-host', operation='reference',
                   capability='cfa3.current-host', artifact_digest=DIGEST,
                   cpu_threads=1, mode=mode, ttl_seconds=10)


class LeaseExpiryTests(unittest.TestCase):
    def test_expired_idle_session_released_and_audited(self):
        host = fixture()
        session = host.start(request())
        with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                   return_value=session.deadline_monotonic + 1):
            self.assertEqual(host.reap_expired(), 1)
        self.assertEqual(host.hrb.allocated, 0)
        self.assertEqual(host.modes.indicator, 'NONE')
        self.assertTrue(any(e['event'] == 'EXPIRED_RECLAIMED' for e in host.audit))
        with self.assertRaises(FoundationDenied):
            host.validate(session)

    def test_start_auto_reclaims_expired_idle_mode(self):
        host = fixture()
        original = host.start(request(Mode.AI))
        with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                   return_value=original.deadline_monotonic + 1):
            new = host.start(request(Mode.RENDER))
        self.assertEqual(host.modes.indicator, 'RENDER')
        self.assertEqual(host.hrb.allocated, 1)
        host.finish(new)
        self.assertEqual(host.hrb.allocated, 0)

    def test_active_execution_not_reclaimed_or_force_finished(self):
        host = fixture()
        session = host.start(request())
        entered = threading.Event()
        exit_gate = threading.Event()
        observed = []

        def work():
            entered.set()
            if not exit_gate.wait(timeout=4):
                raise RuntimeError('test worker did not release')
            return 42

        def worker():
            try:
                observed.append(host.run_owned_callable(session, work))
            except Exception as exc:
                observed.append(exc)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        try:
            self.assertTrue(entered.wait(timeout=2))
            with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                       return_value=session.deadline_monotonic + 1):
                self.assertEqual(host.reap_expired(), 0)
                with self.assertRaisesRegex(FoundationDenied, 'RUNNING_SESSION_CANNOT_BE_RELEASED'):
                    host.finish(session)
            self.assertEqual(host.hrb.allocated, 1)
        finally:
            exit_gate.set()
            t.join(timeout=5)
        self.assertFalse(t.is_alive())
        self.assertEqual(host.hrb.allocated, 0)
        self.assertEqual(host.modes.indicator, 'NONE')
        self.assertEqual(observed[0]['value'], 42)

    def test_concurrent_duplicate_run_denied(self):
        host = fixture()
        session = host.start(request())
        with host.bound_operation(session):
            with self.assertRaisesRegex(FoundationDenied, 'SESSION_ALREADY_EXECUTING'):
                host.run_owned_callable(session, lambda: 1)
            self.assertEqual(host.hrb.allocated, 1)
        self.assertEqual(host.hrb.allocated, 0)

    def test_result_that_expires_during_execution_is_not_pass(self):
        host = fixture()
        session = host.start(request())
        def work():
            with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                       return_value=session.deadline_monotonic + 1):
                host.validate(session)
            return 'should-not-return'
        with self.assertRaisesRegex(FoundationDenied, 'EXPIRED_SESSION'):
            host.run_owned_callable(session, work)
        self.assertEqual(host.hrb.allocated, 0)

    def test_second_reap_is_idempotent(self):
        host = fixture()
        session = host.start(request())
        with patch('cfa3_current_host.foundation_runtime.time.monotonic',
                   return_value=session.deadline_monotonic + 1):
            self.assertEqual(host.reap_expired(), 1)
            self.assertEqual(host.reap_expired(), 0)
        self.assertEqual(host.hrb.allocated, 0)


if __name__ == '__main__':
    unittest.main()
