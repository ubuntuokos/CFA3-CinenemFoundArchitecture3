"""Read-only ruleset hardening regression tests (offline synthetic fixtures)."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_execution_guard_ruleset import validate_ruleset

def protected_ruleset():
    return {
        "id": 24804719, "name": "CFA3-MAIN-PROTECTION",
        "enforcement": "active", "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"}, {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": {
                "required_review_thread_resolution": True,
                "require_extra_approval_for_unattributed_changes": True
            }},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "do_not_enforce_on_create": True,
                "required_status_checks": [
                    {"context": "bootstrap", "integration_id": 15368},
                    {"context": "qt68-linux", "integration_id": 15368}
                ]
            }}
        ]
    }

class RulesetGuardTests(unittest.TestCase):
    def test_verified_ruleset_configuration(self):
        self.assertEqual([], validate_ruleset(protected_ruleset()))

    def test_disabled_ruleset_denied(self):
        obj = protected_ruleset()
        obj["enforcement"] = "disabled"
        self.assertTrue(validate_ruleset(obj))

    def test_bypass_denied(self):
        obj = protected_ruleset()
        obj["bypass_actors"] = [{"actor_id": 1}]
        self.assertTrue(validate_ruleset(obj))

    def test_required_checks_removal_denied(self):
        obj = protected_ruleset()
        obj["rules"][3]["parameters"]["required_status_checks"].pop()
        self.assertTrue(validate_ruleset(obj))

    def test_wrong_ci_integration_denied(self):
        obj = protected_ruleset()
        obj["rules"][3]["parameters"]["required_status_checks"][0]["integration_id"] = 2
        self.assertTrue(validate_ruleset(obj))

    def test_non_strict_checks_denied(self):
        obj = protected_ruleset()
        obj["rules"][3]["parameters"]["strict_required_status_checks_policy"] = False
        self.assertTrue(validate_ruleset(obj))

    def test_wrong_default_branch_target_denied(self):
        obj = protected_ruleset()
        obj["conditions"]["ref_name"]["include"] = ["refs/heads/other"]
        self.assertTrue(validate_ruleset(obj))

    def test_unresolved_pr_threads_allowed_denied(self):
        obj = protected_ruleset()
        obj["rules"][2]["parameters"]["required_review_thread_resolution"] = False
        self.assertTrue(validate_ruleset(obj))

    def test_unsafe_force_push_allowed_denied(self):
        obj = protected_ruleset()
        obj["rules"] = [r for r in obj["rules"] if r["type"] != "non_fast_forward"]
        self.assertTrue(validate_ruleset(obj))

    def test_empty_or_invalid_payload_denied(self):
        for obj in ({}, None, [], {"rules": None}):
            self.assertTrue(validate_ruleset(obj))

if __name__ == "__main__":
    unittest.main()
