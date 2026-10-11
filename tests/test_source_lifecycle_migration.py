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
from donor_delta_routes import delta_aliases


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
        self.assertEqual(self.index["locator_routes"][:len(routing["entries"])], routing["entries"])
        for route in routing["entries"]:
            self.assertEqual(resolve_migrated_url(route["alias"], exact), route["preferred_source_id"])

    def test_project_locators_use_exact_historical_route_in_public_gate(self):
        project_routes = [r for r in self.index["locator_routes"]
                          if r["alias"].startswith("project:")]
        self.assertTrue(project_routes, "Historical project: locators must be preserved")
        for route in project_routes[:10]:
            result = evaluate(route["alias"], self.index)
            self.assertEqual(result["source_id"], route["preferred_source_id"])
            self.assertEqual(result["disposition"], "CHANGE_CHECK_REQUIRED")
            self.assertFalse(result["automatic_donor_registration"])

    def test_original_odbc_delta_urls_resolve_via_public_lifecycle_gate(self):
        aliases = delta_aliases(self.index["source_records"])
        self.assertEqual(len(aliases), 574)
        for url, sid in aliases.items():
            result = evaluate(url, self.index)
            self.assertEqual(result["source_id"], sid)
            self.assertEqual(result["disposition"], "CHANGE_CHECK_REQUIRED")
            self.assertFalse(result["automatic_donor_registration"])

    def test_mentor_evidence_urls_resolve_through_lifecycle_gate(self):
        original_urls = {
            "https://github.com/HKUDS/DeepTutor/blob/main/LICENSE": "FA3-DONOR-HKUDS-DEEPTUTOR-001",
            "https://github.com/jupyterlab/jupyterlab/blob/main/LICENSE": "FA3-DONOR-JUPYTERLAB-001",
            "https://github.com/h5p/h5p-interactive-book/blob/master/library.json": "FA3-DONOR-H5P-INTERACTIVE-BOOK-001",
            "https://github.com/h5p/h5p-interactive-video/blob/master/package.json": "FA3-DONOR-H5P-INTERACTIVE-VIDEO-001",
        }
        for url, sid in original_urls.items():
            response = evaluate(url, self.index)
            self.assertEqual(response["source_id"], sid)
            self.assertEqual(response["disposition"], "CHANGE_CHECK_REQUIRED")

    def test_original_owner_union_raw_urls_are_searchable(self):
        from donor_delta_routes import archived_baseline_union
        rows = archived_baseline_union()["source_coverage"]
        self.assertEqual(len(rows), 445)
        indexed = validate_index(self.index)
        for row in rows:
            for url in (row["canonical_locator"], *row["original_locators"],
                        row["canonical_locator_in_registry"]):
                self.assertEqual(indexed[url], row["resolved_donor_id"])
        # Original URL variants that were not in the initial transfer snapshot
        # must also resolve through the public lifecycle entry point.
        missing_variants = (
            "https://humanaigc.github.io/animate-anyone",
            "https://humanaigc.github.io/wan-animate",
            "https://nilooy.github.io/character-animation-combiner",
            "https://research.nvidia.com/labs/sil/projects/kimodo",
            "http://www.misfitcode.com/misfitmodel3d",
            "https://alternativeto.net/software/octane-render?p=1",
            "https://haiminluo.github.io/hairgpt",
            "https://chufengxiao.github.io/SketchHairSalon",
            "https://devblogs.microsoft.com/directx/directx-heart-linux",
        )
        for url in missing_variants:
            answer = evaluate(url, self.index)
            self.assertEqual(answer["source_id"], indexed[url])
            self.assertEqual(answer["disposition"], "CHANGE_CHECK_REQUIRED")

    def test_all_81_registered_donors_return_their_original_83_urls_and_approval(self):
        registered = json.loads((ROOT / "canonical/registries/CFA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
        for row in registered["records"]:
            for url in row["original_submitted_urls"]:
                result = evaluate(url, self.index)
                self.assertEqual(result["source_id"], row["donor_id"])
                self.assertEqual(result["disposition"], "CHANGE_CHECK_REQUIRED")
                self.assertEqual(result["prior_decision"]["canonical_reference_registration"], row)
                self.assertFalse(result["automatic_donor_registration"])

    def test_historical_upstream_commit_is_exposed_without_current_version_claim(self):
        recut = evaluate("https://github.com/6174/recut", self.index)
        self.assertEqual(recut["source_id"], "FA3-DONOR-6174-RECUT-001")
        historical = recut["prior_decision"]["historical_upstream_evidence"]
        self.assertEqual(historical["upstream_snapshot"]["commit_sha"],
                         "adc8b2583c872d78539ef87f8b179e9fde877113")
        row = next(r for r in self.index["source_records"]
                   if r["source_id"] == "FA3-DONOR-6174-RECUT-001")
        self.assertIsNone(row["observed_revision"])

    def test_verified_unchanged_historical_upstream_revision_reuses_prior_decision(self):
        observation = {
            "verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
            "evidence_ref": "verified-upstream-commit-20261011",
            "checked_at": "2026-10-11",
            "support_status": "SUPPORTED",
            "observed_revision": "adc8b2583c872d78539ef87f8b179e9fde877113",
        }
        same = evaluate("https://github.com/6174/recut", self.index, observation)
        self.assertEqual(same["disposition"], "REUSE_PRIOR_DECISION")
        changed = dict(observation, observed_revision="0" * 40)
        self.assertEqual(evaluate("https://github.com/6174/recut", self.index, changed)["disposition"],
                         "CHANGE_REVIEW_REQUIRED")
        unverified = dict(observation, verification="UNVERIFIED")
        self.assertEqual(evaluate("https://github.com/6174/recut", self.index, unverified)["disposition"],
                         "BLOCKED_UNVERIFIED_OBSERVATION")

    def test_all_preserved_historical_commit_forms_reuse_a_verified_revision(self):
        known = {row["source_id"]: row for row in self.index["source_records"]}
        cases = {
            "FA3-DONOR-CATPPUCCIN-RENOISE-001":
                "47d7b7ba9f282ae0b310b2b6186bed95466fecac",
            "FA3-DONOR-JBSOFTWARE-GEN-AI-STARTER-001":
                "a274dee5f55670e1c63e2d8777baf9714ca287ce",
            "FA3-DONOR-PIXAR-OPENUSD-001":
                "2a9a571d0f9957bad5c4a59ba859ebb8df518c51",
            "FA3-DONOR-CIMG-001":
                "b89ff2b8f1b6cbfbbfb5100d8d5b6897b9294c6e",
        }
        for donor_id, revision in cases.items():
            with self.subTest(donor=donor_id):
                row = known[donor_id]
                observation = {
                    "verification": "VERIFIED_BY_AUTHORIZED_REVIEW",
                    "evidence_ref": "verified-historical-commit-regression",
                    "checked_at": "2026-10-11",
                    "support_status": "SUPPORTED",
                    "observed_revision": revision,
                }
                response = evaluate(row["canonical_url"], self.index, observation)
                self.assertEqual(response["disposition"], "REUSE_PRIOR_DECISION")
                self.assertEqual(response["source_id"], donor_id)
                changed = dict(observation, observed_revision="0" * 40)
                self.assertEqual(evaluate(row["canonical_url"], self.index, changed)["disposition"],
                                 "CHANGE_REVIEW_REQUIRED")

    def test_rejected_historical_source_is_searchable_but_never_admitted(self):
        for locator in ("project:donutbrowser",):
            response = evaluate(locator, self.index)
            self.assertEqual(response["disposition"], "BLOCKED_REJECTED_SOURCE")
            self.assertEqual(response["source_id"], "FA3-DONOR-DONUTBROWSER-001")
            self.assertEqual(response["prior_decision"]["outcome"], "REJECTED")
            self.assertEqual(response["prior_decision"]["historical_rejection"]
                             ["donor"]["status"], "REJECTED")
            self.assertFalse(response["automatic_donor_registration"])
            self.assertFalse(response["automatic_code_import"])

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
