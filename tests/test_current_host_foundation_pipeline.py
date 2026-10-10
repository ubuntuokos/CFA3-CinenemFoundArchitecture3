"""Actual in-process CPU Foundation admission applied to Current Host test plan."""
import unittest

from cfa3_current_host.core import Component, Graph, Handoff, Ownership, Mode, Plan, TestKind
from cfa3_current_host.foundation_runtime import (
    CpuResourceBroker, FoundationRuntime, ModelRouter, RightsAuthority,
    SecurityAuthority, WorkloadModeBroker, Mode as WorkloadMode,
)
from cfa3_current_host.foundation_pipeline import (
    BoundOperation, FoundationPipeline, PipelineBlocked,
)

HASH = "sha256:" + "1" * 64


def make():
    graph = Graph()
    graph.register_component(Component("host", "FOUNDATION", "rev:1",
                                       Ownership.CFA3_COMPONENT))
    graph.register_component(Component("vendor", "EXTERNAL", "vendor:1",
                                       Ownership.COMMERCIAL_SOFTWARE))
    ops = ("positive", "negative", "rollback")
    grants = [("tester", "host", "current-host." + op, "cfa3.current-host")
              for op in ops]
    foundation = FoundationRuntime(
        security=SecurityAuthority(grants),
        rights=RightsAuthority([HASH]), model_router=ModelRouter(["model:cpu"]),
        hrb=CpuResourceBroker(2), modes=WorkloadModeBroker(),
    )
    return graph, foundation, FoundationPipeline(graph, foundation)


class CurrentHostPipelineTests(unittest.TestCase):
    def bind_all(self, graph, bridge, fn=lambda: "cpu-ok"):
        plan = graph.plan(["host"])
        for item in plan.obligations:
            bridge.register(BoundOperation("host", item.test.value,
                                           item.handoff_id, "rev:1", HASH, fn))
        return plan

    def test_all_three_cases_execute_with_cpu_lease(self):
        graph, foundation, bridge = make()
        seen = []
        plan = self.bind_all(graph, bridge, lambda: seen.append("ok") or 42)
        result = bridge.execute(plan, actor="tester", mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "REFERENCE_TESTS_EXECUTED")
        self.assertEqual(len(result["observations"]), 3)
        self.assertEqual(len(seen), 3)
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, "NONE")
        self.assertFalse(result["physical_current_host_pass"])

    def test_missing_rollback_blocks_before_any_side_effect(self):
        graph, foundation, bridge = make()
        plan = graph.plan(["host"])
        seen = []
        for item in plan.obligations[:2]:
            bridge.register(BoundOperation("host", item.test.value,
                                           item.handoff_id, "rev:1", HASH,
                                           lambda: seen.append("ran")))
        result = bridge.execute(plan, actor="tester", mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_MISSING_OR_STALE_CFA3_TESTS")
        self.assertEqual(seen, [])
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_external_product_never_accepted_as_owned_runner(self):
        graph, _, bridge = make()
        with self.assertRaises(PipelineBlocked):
            bridge.register(BoundOperation("vendor", "POSITIVE", None,
                                           "vendor:1", HASH, lambda: None))
        plan = graph.plan(["vendor"])
        self.assertEqual(plan.mode, Mode.NONE)
        self.assertEqual(bridge.execute(plan, actor="tester",
                                        mode=WorkloadMode.INTERACTIVE)["status"],
                         "NO_CFA3_TEST_REQUIRED")

    def test_unknown_actor_fails_closed(self):
        graph, foundation, bridge = make()
        plan = self.bind_all(graph, bridge)
        result = bridge.execute(plan, actor="untrusted", mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_OR_FAILED_CFA3_TEST")
        self.assertEqual(result["observations"], ())
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_unknown_model_is_not_silently_routed(self):
        graph, _, bridge = make()
        plan = self.bind_all(graph, bridge)
        result = bridge.execute(plan, actor="tester", mode=WorkloadMode.AI,
                                model_id="unregistered")
        self.assertEqual(result["status"], "BLOCKED_OR_FAILED_CFA3_TEST")

    def test_failing_case_does_not_consume_remaining_tests(self):
        graph, foundation, bridge = make()
        count = [0]
        def fail():
            count[0] += 1
            raise ValueError("fixture failure")
        plan = self.bind_all(graph, bridge, fail)
        result = bridge.execute(plan, actor="tester", mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_OR_FAILED_CFA3_TEST")
        self.assertEqual(count[0], 1)
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_caller_cannot_omit_negative_or_rollback(self):
        graph, foundation, bridge = make()
        correct = self.bind_all(graph, bridge)
        truncated = Plan(correct.mode, correct.changed, correct.affected,
                         correct.obligations[:1], correct.reason)
        result = bridge.execute(truncated, actor="tester",
                                mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_NONCANONICAL_CURRENT_HOST_PLAN")
        self.assertEqual(foundation.hrb.allocated, 0)
        self.assertEqual(foundation.modes.indicator, "NONE")

    def test_caller_cannot_forge_none_for_cfa3_source(self):
        graph, foundation, bridge = make()
        forged = Plan(Mode.NONE, ("host",), (), (),
                      "EXTERNAL_PRODUCT_OUTSIDE_CFA3_SCOPE")
        result = bridge.execute(forged, actor="tester",
                                mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_NONCANONICAL_CURRENT_HOST_PLAN")
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_caller_cannot_drop_affected_handoff_obligation(self):
        graph, foundation, bridge = make()
        graph.register_component(Component("consumer", "VIDEO", "rev:1",
                                           Ownership.CFA3_CONNECTOR))
        graph.register_handoff(Handoff("host-video", "host", "consumer",
                                       "frame", "rev:1", "consumer",
                                       "accept", "rollback"))
        complete = graph.plan(["host"])
        missing_handoff = Plan(
            complete.mode, complete.changed, complete.affected,
            tuple(x for x in complete.obligations if x.test != TestKind.HANDOFF),
            complete.reason,
        )
        result = bridge.execute(missing_handoff, actor="tester",
                                mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "BLOCKED_NONCANONICAL_CURRENT_HOST_PLAN")
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_caller_cannot_inject_unrecognized_changed_component(self):
        graph, foundation, bridge = make()
        forged = Plan(Mode.SCOPED, ("made-up",), ("host",),
                      graph.plan(["host"]).obligations, "REAL_EDGE_IMPACT")
        with self.assertRaisesRegex(PipelineBlocked, "UNRECONCILED_OR_STALE"):
            bridge.execute(forged, actor="tester", mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(foundation.hrb.allocated, 0)

    def test_valid_full_impact_plan_can_run_all_owned_obligations(self):
        graph, foundation, bridge = make()
        expected = graph.plan(["host"], trigger="GLOBAL_SECURITY_POLICY")
        for item in expected.obligations:
            bridge.register(BoundOperation("host", item.test.value,
                                           item.handoff_id, "rev:1", HASH,
                                           lambda: "reference-only"))
        result = bridge.execute(expected, actor="tester",
                                mode=WorkloadMode.INTERACTIVE)
        self.assertEqual(result["status"], "REFERENCE_TESTS_EXECUTED")
        self.assertEqual(len(result["observations"]), len(expected.obligations))
        self.assertFalse(result["physical_current_host_pass"])

    def test_duplicate_binding_rejected(self):
        graph, _, bridge = make()
        binding = BoundOperation("host", "POSITIVE", None, "rev:1", HASH, lambda: 1)
        bridge.register(binding)
        with self.assertRaises(PipelineBlocked):
            bridge.register(binding)

    def test_stale_revision_rejected(self):
        graph, _, bridge = make()
        with self.assertRaises(PipelineBlocked):
            bridge.register(BoundOperation("host", "POSITIVE", None, "rev:old", HASH, lambda: 1))


if __name__ == "__main__":
    unittest.main()
