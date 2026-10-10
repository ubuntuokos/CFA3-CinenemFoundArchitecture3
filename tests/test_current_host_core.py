"""Deterministic, non-physical CFA3 Current Host reference tests."""
import unittest

from cfa3_current_host.core import (
    Component, ContractError, ExternalEvidenceVerifier, Graph, Handoff,
    Level, Mode, Ownership, Proof, TestKind, assess_for_external_admission,
)


def component(name, layer, kind=Ownership.CFA3_COMPONENT, *, gui=False, parent=None):
    return Component(name, layer, "r1", kind, ("cap:" + name,), gui, parent)


def handoff(name, src, dst):
    return Handoff(name, src, dst, "asset", "r1", dst, "accept:1", "rollback:1")


class CurrentHostPlanningTests(unittest.TestCase):
    def setUp(self):
        self.g = Graph()
        for n in (
            component("foundation", "FOUNDATION"),
            component("3d", "3D"),
            component("video", "VIDEO", gui=True, parent="foundation"),
            component("audio", "AUDIO"),
            component("plugin-host", "VIDEO", Ownership.CFA3_PLUGIN_HOST),
            component("external-driver", "EXTERNAL", Ownership.VENDOR_DRIVER),
            component("vendor-app", "EXTERNAL", Ownership.COMMERCIAL_SOFTWARE),
            component("community-plugin", "EXTERNAL", Ownership.COMMUNITY_PLUGIN),
        ):
            self.g.register_component(n)
        self.g.register_handoff(handoff("render-video", "3d", "video"))
        self.g.register_handoff(handoff("detach-audio", "video", "audio"))
        self.g.register_handoff(handoff("video-plugin-host", "video", "plugin-host"))

    def test_scoped_delta_only_real_outgoing_edges(self):
        plan = self.g.plan(["3d"])
        self.assertEqual(plan.mode, Mode.SCOPED)
        self.assertEqual(set(plan.affected), {"3d", "video", "audio", "plugin-host"})
        self.assertEqual(set(x.handoff_id for x in plan.obligations if x.test == TestKind.HANDOFF),
                         {"render-video", "detach-audio", "video-plugin-host"})
        self.assertNotIn("foundation", plan.affected)

    def test_audio_change_does_not_force_video_or_3d(self):
        plan = self.g.plan(["audio"])
        self.assertEqual(plan.affected, ("audio",))
        self.assertTrue(all(x.component_id == "audio" for x in plan.obligations))

    def test_no_unrelated_connections_are_inferred(self):
        plan = self.g.plan(["plugin-host"])
        self.assertEqual(plan.affected, ("plugin-host",))
        self.assertEqual({x.handoff_id for x in plan.obligations if x.test == TestKind.HANDOFF},
                         {"video-plugin-host"})

    def test_external_driver_software_and_plugin_product_are_not_tested(self):
        for item in ("external-driver", "vendor-app", "community-plugin"):
            with self.subTest(item=item):
                plan = self.g.plan([item])
                self.assertEqual(plan.mode, Mode.NONE)
                self.assertEqual(plan.affected, ())
                self.assertEqual(plan.obligations, ())

    def test_cfa3_owned_plugin_host_must_be_tested(self):
        plan = self.g.plan(["plugin-host"])
        self.assertEqual({x.test for x in plan.obligations},
                         {TestKind.POSITIVE, TestKind.NEGATIVE, TestKind.ROLLBACK, TestKind.HANDOFF})

    def test_gui_standalone_and_actual_parent_are_both_required(self):
        tests = {x.test for x in self.g.plan(["video"]).obligations if x.component_id == "video"}
        self.assertIn(TestKind.STANDALONE_GUI, tests)
        self.assertIn(TestKind.PARENT_GUI, tests)

    def test_gui_without_parent_has_only_standalone(self):
        self.g.register_component(component("isolated-gui", "VIDEO", gui=True))
        tests = {x.test for x in self.g.plan(["isolated-gui"]).obligations}
        self.assertIn(TestKind.STANDALONE_GUI, tests)
        self.assertNotIn(TestKind.PARENT_GUI, tests)

    def test_global_full_only_on_explicit_platform_trigger(self):
        plan = self.g.plan(["foundation"], trigger="GLOBAL_SECURITY_POLICY")
        self.assertEqual(plan.mode, Mode.FULL)
        self.assertEqual(set(plan.affected), {"foundation", "3d", "video", "audio", "plugin-host"})
        self.assertNotIn("vendor-app", plan.affected)

    def test_default_foundation_code_change_is_not_arbitrary_full(self):
        plan = self.g.plan(["foundation"])
        self.assertEqual(plan.mode, Mode.SCOPED)

    def test_interlayer_handoff_is_global_level(self):
        plan = self.g.plan(["3d"])
        self.assertEqual({x.level for x in plan.obligations if x.handoff_id == "render-video"},
                         {Level.GLOBAL})

    def test_local_cases_require_positive_negative_and_rollback(self):
        plan = self.g.plan(["audio"])
        self.assertEqual({x.test for x in plan.obligations},
                         {TestKind.POSITIVE, TestKind.NEGATIVE, TestKind.ROLLBACK, TestKind.HANDOFF})

    def test_stale_revision_or_unknown_target_fail_closed(self):
        with self.assertRaises(ContractError):
            self.g.register_handoff(Handoff("stale", "3d", "audio", "asset", "r0", "audio", "accept", "rollback"))
        with self.assertRaises(ContractError):
            self.g.plan(["nonexistent"])
        with self.assertRaises(ContractError):
            self.g.register_handoff(handoff("unknown", "3d", "missing"))

    def test_inbound_handoff_is_tested_without_retesting_upstream_component(self):
        plan = self.g.plan(["video"])
        self.assertNotIn("3d", plan.affected)
        self.assertIn("render-video", {x.handoff_id for x in plan.obligations
                                        if x.test == TestKind.HANDOFF})

    def test_vendor_product_is_not_certified_but_cfa3_connector_is(self):
        self.g.register_handoff(handoff("external-to-host", "external-driver", "plugin-host"))
        plan = self.g.plan(["plugin-host"])
        self.assertEqual(plan.affected, ("plugin-host",))
        self.assertIn("external-to-host",
                      {x.handoff_id for x in plan.obligations if x.test == TestKind.HANDOFF})
        self.assertNotIn("external-driver", plan.affected)
        self.assertEqual(self.g.plan(["external-driver"]).mode, Mode.NONE)

    def test_duplicate_component_or_handoff_rejected(self):
        with self.assertRaises(ContractError):
            self.g.register_component(component("video", "VIDEO"))
        with self.assertRaises(ContractError):
            self.g.register_handoff(handoff("render-video", "3d", "video"))

    def test_non_cfa3_recipient_not_qualified(self):
        with self.assertRaises(ContractError):
            self.g.register_handoff(handoff("vendor", "video", "vendor-app"))

    def test_no_fabricated_physical_pass_from_reference_results(self):
        plan = self.g.plan(["audio"])
        self.assertEqual(assess_for_external_admission(plan, self.g, ())["status"], "PENDING_MISSING_PROOFS")
        fake = tuple(
            Proof(o, "r1", "fake-host", "digest", "receipt", False, "PASS") for o in plan.obligations
        )
        self.assertEqual(assess_for_external_admission(plan, self.g, fake)["status"],
                         "BLOCKED_UNQUALIFIED_PROOF")

    def test_authority_required_even_for_physical_claim(self):
        plan = self.g.plan(["audio"])
        claims = tuple(
            Proof(o, "r1", "real-host", "digest", "receipt", True, "PASS") for o in plan.obligations
        )
        result = assess_for_external_admission(plan, self.g, claims)
        self.assertEqual(result["status"], "PENDING_EXTERNAL_AUTHORITY")
        self.assertFalse(result["authority_pass"])

    def test_even_external_proof_check_does_not_issue_pass(self):
        plan = self.g.plan(["audio"])
        claims = tuple(
            Proof(o, "r1", "physical-host", "digest", "receipt", True, "PASS") for o in plan.obligations
        )
        class LocalTestVerifier(ExternalEvidenceVerifier):
            def verify_physical_proof(self, proof):
                return True
        result = assess_for_external_admission(plan, self.g, claims, LocalTestVerifier())
        self.assertEqual(result["status"], "READY_FOR_AUTHORITY_REVIEW")
        self.assertFalse(result["authority_pass"])

    def test_proofs_cannot_be_replayed_for_different_revision(self):
        plan = self.g.plan(["audio"])
        claims = tuple(
            Proof(o, "r0", "physical-host", "digest", "receipt", True, "PASS") for o in plan.obligations
        )
        self.assertEqual(assess_for_external_admission(plan, self.g, claims)["status"],
                         "BLOCKED_UNQUALIFIED_PROOF")

    def test_duplicate_evidence_record_rejected(self):
        plan = self.g.plan(["audio"])
        item = Proof(plan.obligations[0], "r1", "physical-host", "digest", "receipt", True, "PASS")
        self.assertEqual(assess_for_external_admission(plan, self.g, (item, item))["status"],
                         "BLOCKED_DUPLICATE_PROOF")


if __name__ == "__main__":
    unittest.main()
