"""Direct canonical integrity checks for the owner-approved 16-section rule.

Structural CI is not proof of runtime-wide enforcement or physical-host PASS.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
IDENT = "CFA3-POLICY-MANDATORY-RULE-CREATION-INTEGRITY-001"
POLICY = ROOT / "canonical" / "policies" / (IDENT + ".json")
DOCUMENT = ROOT / "canonical" / "policies" / (IDENT + ".md")
APPROVED_DIGEST = "3e590e20f3d50e04297776b43e22d91cbd9b0a417c4687810e75992913c10ba8"
PUBLISHED_DIGEST = "c1c177c260b46f0139cb9d435b96bf301d65f94e003903be815a41667c070157"
PREAPPROVAL_HEADER = b"**Státusz:** J\xc3\x93V\xc3\x81HAGY\xc3\x81SRA V\xc3\x81R  "
APPROVED_HEADER = b"**Státusz:** J\xc3\x93V\xc3\x81HAGYVA  "


class MandatoryRuleCreationIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.published = DOCUMENT.read_bytes()

    def test_full_approved_original_preserved_except_lifecycle_header(self):
        self.assertEqual(1, self.published.count(APPROVED_HEADER))
        original = self.published.replace(APPROVED_HEADER, PREAPPROVAL_HEADER, 1)
        self.assertEqual(APPROVED_DIGEST, hashlib.sha256(original).hexdigest())
        self.assertEqual(self.policy["approved_original_text_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(PUBLISHED_DIGEST, hashlib.sha256(self.published).hexdigest())
        self.assertEqual(self.policy["published_text_sha256"], hashlib.sha256(self.published).hexdigest())

    def test_full_sixteen_sections_and_owner_approval_state(self):
        text = self.published.decode("utf-8")
        sections = [int(x) for x in re.findall(r"^## (\d+)\. §", text, re.M)]
        self.assertEqual(list(range(1, 17)), sections)
        self.assertEqual(IDENT, self.policy["id"])
        self.assertEqual("1.0", self.policy["version"])
        self.assertEqual("OWNER_APPROVED", self.policy["status"])
        self.assertEqual("2026-10-13", self.policy["owner_decision_date"])
        self.assertEqual(16, self.policy["approved_section_count"])
        self.assertEqual(["TEXT", "STRUCTURE", "REGISTRY", "STATUS", "CI", "MERGE", "MAIN", "SCOPE"],
                         self.policy["finalization_gates"])
        self.assertTrue(all(x is True for x in self.policy["requirements"].values()))
        self.assertTrue(all(x is False for x in self.policy["admission_boundary"].values()))

    def test_tampering_with_normative_text_is_detected(self):
        tampered = self.published.replace(b"## 9. ", b"## 8. ", 1)
        self.assertNotEqual(self.published, tampered)
        self.assertNotEqual(PUBLISHED_DIGEST, hashlib.sha256(tampered).hexdigest())

    def test_registry_indexed_once_and_coverage_total_consistent(self):
        reg = json.loads((ROOT / "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json").read_text("utf-8"))
        coverage = json.loads((ROOT / "canonical/registries/CFA3-EXECUTION-GUARD-COVERAGE-001.json").read_text("utf-8"))
        target = "canonical/policies/" + IDENT + ".json"
        matches = [row for row in reg["sources"] if row["path"] == target]
        self.assertEqual(1, len(matches))
        self.assertEqual("OWNER_APPROVED", matches[0]["source_status"])
        self.assertEqual(reg["source_policy_count"], len(reg["sources"]))
        self.assertEqual(1, coverage["policy_files"].count(target))
        self.assertEqual(sum(row["leaf_count"] for row in reg["sources"]),
                         coverage["canonical_policy_leaf_fields_enumerated"])


if __name__ == "__main__":
    unittest.main()
