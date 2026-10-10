"""200-target Current Host fixture tests. Synthetic evidence NEVER becomes PASS."""
import unittest
import json
import tempfile
from pathlib import Path

from cfa3_current_host.capability_catalog import (
    Capability, CapabilityCatalog, CatalogError, ScopedEvidence, load_capability_catalog,
)

DIGEST = "sha256:" + "a" * 64


def cap(i):
    return Capability("cfa3.capability.%03d" % i, "component.%03d" % i,
                      "FOUNDATION" if i < 10 else "LAYER", "rev:v1",
                      "CFA3_COMPONENT", "canonical:placeholder-fixture:%03d" % i)


def catalog(count=200):
    result = CapabilityCatalog()
    for i in range(count):
        result.register(cap(i))
    return result


def evidence(i=0, case="POSITIVE", physical=False, revision="rev:v1"):
    return ScopedEvidence("cfa3.capability.%03d" % i, case, revision,
                          DIGEST, DIGEST, "fixture:external-authority-pending",
                          physical, "PASS")


class CapabilityCatalogTests(unittest.TestCase):
    def test_unreconciled_catalog_cannot_claim_finished(self):
        r = catalog(175).reconciliation()
        self.assertEqual(r["status"], "BLOCKED_INCOMPLETE_200_CAPABILITY_CATALOG")
        self.assertEqual(r["missing"], 25)
        self.assertFalse(r["physical_current_host_pass"])

    def test_exact_target_does_not_equal_physical_pass(self):
        r = catalog().reconciliation()
        self.assertEqual(r["status"], "STRUCTURAL_200_READY_PENDING_CANONICAL_REVIEW")
        self.assertEqual(r["obligation_count"], 600)
        self.assertFalse(r["physical_current_host_pass"])

    def test_201_is_not_accepted_as_200(self):
        r = catalog(201).reconciliation()
        self.assertEqual(r["overflow"], 1)
        self.assertEqual(r["status"], "BLOCKED_INCOMPLETE_200_CAPABILITY_CATALOG")

    def test_external_vendor_plugin_cannot_be_cfa3_capability_record(self):
        for external in ("VENDOR_DRIVER", "COMMERCIAL_SOFTWARE", "COMMUNITY_PLUGIN"):
            with self.subTest(external=external), self.assertRaises(CatalogError):
                Capability("external", "plugin", "VIDEO", "v1", external, "source")

    def test_empty_input_is_explicitly_unreconciled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text(json.dumps({"schema": "cfa3.current-host.capabilities.v1",
                                        "capabilities": []}), encoding="utf-8")
            result = load_capability_catalog(path).reconciliation()
        self.assertEqual(result["missing"], 200)
        self.assertFalse(result["physical_current_host_pass"])

    def test_invalid_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text(json.dumps({"schema": "WRONG",
                                        "capabilities": []}), encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_capability_catalog(path)

    def test_external_catalog_record_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            item = dict(cap(0).__dict__)
            item["owner"] = "VENDOR_DRIVER"
            path.write_text(json.dumps({"schema": "cfa3.current-host.capabilities.v1",
                                        "capabilities": [item]}), encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_capability_catalog(path)

    def test_duplicate_identifier_rejected(self):
        c = catalog(1)
        with self.assertRaises(CatalogError):
            c.register(cap(0))

    def test_missing_physical_proofs_are_pending(self):
        self.assertEqual(catalog().review_evidence(())["status"], "PENDING_MISSING_PROOF_CASES")

    def test_nonphysical_reference_proof_is_rejected(self):
        self.assertEqual(
            catalog().review_evidence((evidence(),))["status"],
            "BLOCKED_INCORRECT_SCOPE_OR_NONPHYSICAL_PROOF")

    def test_stale_revision_is_rejected(self):
        self.assertEqual(
            catalog().review_evidence((evidence(physical=True, revision="old"),))["status"],
            "BLOCKED_INCORRECT_SCOPE_OR_NONPHYSICAL_PROOF")

    def test_duplicate_proofs_are_rejected(self):
        record = evidence(physical=True)
        self.assertEqual(catalog().review_evidence((record, record))["status"],
                         "BLOCKED_UNKNOWN_OR_DUPLICATE_PROOF")

    def test_even_600_claimed_proofs_require_external_evidence_authority(self):
        claims = tuple(evidence(i, kind, physical=True)
                       for i in range(200)
                       for kind in ("POSITIVE", "NEGATIVE", "ROLLBACK"))
        result = catalog().review_evidence(claims)
        self.assertEqual(result["received"], 600)
        self.assertEqual(result["status"], "PENDING_EXTERNAL_PHYSICAL_EVIDENCE_AUTHORITY")
        self.assertFalse(result["physical_current_host_pass"])


if __name__ == "__main__":
    unittest.main()
