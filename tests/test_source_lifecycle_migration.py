"""Check production donor data through the lifecycle gate, including ambiguity."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_source_lifecycle_index import build, OUTPUT
from source_lifecycle import evaluate, validate_index, resolve_migrated_url


class LifecycleMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(OUTPUT.read_text())

    def test_projection_is_reproducible_and_covers_every_staged_identity(self):
        self.assertEqual(build(), self.index)
        staged = json.loads((ROOT / "canonical/registries/CFA3-DONOR-L1-STAGED-DIRECT-ACCESS-20261010.json").read_text())
        self.assertEqual({r["id"] for r in staged["sources"]},
                         {r["source_id"] for r in self.index["source_records"]})
        self.assertEqual(len(self.index["source_records"]), 1981)

    def test_all_original_routes_and_related_identities_survive(self):
        routing = json.loads((ROOT / "canonical/registries/CFA3-DONOR-L1-URL-ROUTING-20261010.json").read_text())
        exact = validate_index(self.index)
        self.assertEqual(self.index["locator_routes"], routing["entries"])
        for route in routing["entries"]:
            self.assertEqual(resolve_migrated_url(route["alias"], exact), route["preferred_source_id"])

    def test_all_81_registered_donors_return_their_original_83_urls_and_approval(self):
        registered = json.loads((ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
        for row in registered["records"]:
            for url in row["original_submitted_urls"]:
                result = evaluate(url, self.index)
                self.assertEqual(result["source_id"], row["donor_id"])
                self.assertEqual(result["disposition"], "CHANGE_CHECK_REQUIRED")
                self.assertEqual(result["prior_decision"]["canonical_reference_registration"], row)
                self.assertFalse(result["automatic_donor_registration"])

    def test_unknown_is_not_declared_new_and_no_upstream_version_is_invented(self):
        self.assertEqual(evaluate("https://unknown.invalid/unregistered", self.index)["disposition"],
                         "BLOCKED_INDEX_INCOMPLETE")
        self.assertTrue(all(r["observed_revision"] is None for r in self.index["source_records"]))
        bad = dict(self.index, complete=True)
        self.assertRaises(ValueError, validate_index, bad)

    def test_forged_route_or_runtime_admission_is_rejected(self):
        bad = copy.deepcopy(self.index)
        bad["locator_routes"][0]["preferred_source_id"] = "missing"
        self.assertRaises(ValueError, validate_index, bad)
        bad = copy.deepcopy(self.index)
        bad["source_records"][0]["runtime_admission"] = True
        self.assertRaises(ValueError, validate_index, bad)

    def test_normalization_does_not_silently_merge_conflicting_original_routes(self):
        routes = {"https://github.com/Example/Repo": "s1", "https://github.com/example/repo": "s2"}
        self.assertEqual(resolve_migrated_url("https://github.com/Example/Repo", routes), "s1")
        self.assertRaises(ValueError, resolve_migrated_url, "http://github.com/example/repo.git", routes)


if __name__ == "__main__":
    unittest.main()
