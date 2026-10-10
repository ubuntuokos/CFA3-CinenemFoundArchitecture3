"""Real CPU reference tests for separate Foundation authority boundaries."""
import unittest
from unittest.mock import patch

from cfa3_current_host.foundation_runtime import (
    CpuResourceBroker, FoundationDenied, FoundationRuntime, Mode,
    ModelRouter, Request, RightsAuthority, SecurityAuthority, WorkloadModeBroker
)

DIGEST = "sha256:" + "a" * 64
GRANT = ("developer", "current-host", "selftest", "cfa3.current-host")
def request(**kwargs):
    default = dict(actor="developer", component="current-host", operation="selftest",
                   capability="cfa3.current-host", artifact_digest=DIGEST,
                   cpu_threads=1, mode=Mode.INTERACTIVE, model_id=None, ttl_seconds=30.0)
    default.update(kwargs)
    return Request(**default)

def runtime(threads=2, models=("cpu-model",)):
    return FoundationRuntime(
        security=SecurityAuthority([GRANT]),
        rights=RightsAuthority([DIGEST]),
        model_router=ModelRouter(models),
        hrb=CpuResourceBroker(threads),
        modes=WorkloadModeBroker(),
    )


class FoundationRuntimeTests(unittest.TestCase):
    def test_cpu_operation_actually_runs_and_releases_resources(self):
        f = runtime()
        session = f.start(request())
        self.assertEqual(f.hrb.allocated, 1)
        self.assertEqual(f.modes.indicator, "INTERACTIVE")
        result = f.run_owned_callable(session, lambda: 11 * 7)
        self.assertEqual(result["value"], 77)
        self.assertFalse(result["physical_current_host_pass"])
        self.assertEqual(f.hrb.allocated, 0)
        self.assertEqual(f.modes.indicator, "NONE")

    def test_no_implicit_model_fallback(self):
        f = runtime()
        with self.assertRaisesRegex(FoundationDenied, "MODEL_ROUTE_NOT_ADMITTED"):
            f.start(request(model_id="unknown-model"))
        self.assertEqual(f.hrb.allocated, 0)
        approved = f.start(request(model_id="cpu-model"))
        self.assertEqual(approved.route, "CPU:cpu-model")
        f.finish(approved)

    def test_no_grant(self):
        f = runtime()
        with self.assertRaisesRegex(FoundationDenied, "SECURITY_GRANT_DENIED"):
            f.start(request(actor="unknown"))
        self.assertEqual(f.hrb.allocated, 0)

    def test_artifact_rights_are_not_inferred_from_license_text(self):
        f = runtime()
        with self.assertRaisesRegex(FoundationDenied, "ARTIFACT_RIGHTS_NOT_ADMITTED"):
            f.start(request(artifact_digest="sha256:" + "b" * 64))

    def test_cpu_capacity_blocks_without_hidden_fallback(self):
        f = runtime(threads=1)
        first = f.start(request())
        with self.assertRaisesRegex(FoundationDenied, "HRB_CAPACITY_EXHAUSTED"):
            f.start(request())
        self.assertEqual(f.hrb.allocated, 1)
        f.finish(first)
        self.assertEqual(f.hrb.allocated, 0)

    def test_workload_mode_conflict_releases_no_extra_lease(self):
        f = runtime()
        first = f.start(request(mode=Mode.AI))
        with self.assertRaisesRegex(FoundationDenied, "WORKLOAD_MODE_CONFLICT"):
            f.start(request(mode=Mode.RENDER))
        self.assertEqual(f.hrb.allocated, 1)
        self.assertEqual(f.modes.indicator, "AI")
        f.finish(first)

    def test_resource_exhaustion_restores_workload_mode_token(self):
        f = runtime(threads=1)
        first = f.start(request(mode=Mode.AI))
        with self.assertRaisesRegex(FoundationDenied, "HRB_CAPACITY_EXHAUSTED"):
            f.start(request(mode=Mode.AI))
        f.finish(first)
        self.assertEqual(f.modes.indicator, "NONE")

    def test_bad_operation_cleans_up(self):
        f = runtime()
        session = f.start(request())
        with self.assertRaisesRegex(RuntimeError, "fixture"):
            f.run_owned_callable(session, lambda: (_ for _ in ()).throw(RuntimeError("fixture")))
        self.assertEqual(f.hrb.allocated, 0)
        self.assertEqual(f.modes.indicator, "NONE")
        self.assertTrue(any(record["event"] == "REFERENCE_FAILED" for record in f.audit))

    def test_double_release_denied(self):
        f = runtime()
        session = f.start(request())
        f.finish(session)
        with self.assertRaises(FoundationDenied):
            f.finish(session)

    def test_invalid_request_is_rejected(self):
        for options in (
            {"mode": Mode.NONE}, {"cpu_threads": 0}, {"cpu_threads": True},
            {"ttl_seconds": 0}, {"artifact_digest": "not-sha256"}
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                request(**options)

    def test_lapsed_lease_is_not_valid_for_operation(self):
        f = runtime()
        session = f.start(request())
        with patch("cfa3_current_host.foundation_runtime.time.monotonic",
                   return_value=session.deadline_monotonic + 1):
            with self.assertRaisesRegex(FoundationDenied, "EXPIRED_SESSION"):
                f.validate(session)
        # Cleanup must also work WHILE the lease is expired.
        with patch("cfa3_current_host.foundation_runtime.time.monotonic",
                   return_value=session.deadline_monotonic + 1):
            f.finish(session)
        self.assertEqual(f.hrb.allocated, 0)

    def test_invalid_operation_still_releases_lease(self):
        f = runtime()
        session = f.start(request())
        with self.assertRaisesRegex(FoundationDenied, "INVALID_CFA3_TEST_OPERATION"):
            f.run_owned_callable(session, None)
        self.assertEqual(f.hrb.allocated, 0)
        self.assertEqual(f.modes.indicator, "NONE")

    def test_invalid_raw_hrb_and_mode_acquisitions_denied(self):
        broker = CpuResourceBroker(3)
        with self.assertRaises(ValueError):
            broker.acquire(0)
        with self.assertRaises(ValueError):
            broker.acquire(1.5)
        modes = WorkloadModeBroker()
        with self.assertRaises(FoundationDenied):
            modes.acquire(Mode.NONE)

    def test_nan_ttl_is_rejected(self):
        with self.assertRaises(ValueError):
            request(ttl_seconds=float("nan"))

    def test_audit_cannot_claim_physical_pass(self):
        f = runtime()
        s = f.start(request())
        f.finish(s)
        self.assertEqual([x["event"] for x in f.audit], ["ADMITTED_REFERENCE", "RELEASED"])
        self.assertTrue(all("PHYSICAL_PASS" not in event["event"] for event in f.audit))

    def test_explicit_cpu_capacity_rejects_invalid_values(self):
        for invalid in (0, -1, True):
            with self.assertRaises(ValueError):
                CpuResourceBroker(invalid)


if __name__ == "__main__":
    unittest.main()
