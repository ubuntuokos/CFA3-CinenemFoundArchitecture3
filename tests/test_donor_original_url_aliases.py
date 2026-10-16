"""Exact historical donor source URLs are independently searchable without re-admission."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import donor_reference_lookup as lookup_module

UNION = ROOT / "archive/donor-source-migration/2026-10-09/CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json"
PUBLISHED = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json"
EXTRA = ROOT / "canonical/registries/CFA3-DONOR-PUBLISHED-ORIGINAL-URL-ALIASES-20261012.json"
AI_TEXT = ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-AI-TEXT-MINDMAP-RENDER-SHADER-2026-09-29.json"
UNION_PIN = "d22dce8bfe3d9697a1121033ff7b387d051a638a"
AI_TEXT_PIN = "c18710d41f48bc4bf542c2f591ab916ff65cd6c9"
PUBLISHED_PIN = "7de979fd2d975ff99573f41e4a0035a57925bb52"


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class OriginalUrlAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.union_raw = UNION.read_bytes()
        cls.published_raw = PUBLISHED.read_bytes()
        cls.union = json.loads(cls.union_raw)
        cls.published = json.loads(cls.published_raw)
        cls.extra = json.loads(EXTRA.read_text(encoding="utf-8"))
        cls.ai_text_raw = AI_TEXT.read_bytes()
        cls.ai_text = json.loads(cls.ai_text_raw)
        if (git_blob_sha(cls.union_raw) != UNION_PIN
                or git_blob_sha(cls.published_raw) != PUBLISHED_PIN
                or git_blob_sha(cls.ai_text_raw) != AI_TEXT_PIN):
            raise AssertionError("Historical input or published first-file snapshot changed")

    def test_all_original_445_urls_have_one_unmodified_source_identity(self):
        coverage = self.union["source_coverage"]
        self.assertEqual(len(coverage), 445)
        self.assertEqual(len({item["canonical_locator"] for item in coverage}), 445)
        by_id = self.published["lookup_by_id"]
        direct = self.published["lookup_by_locator"]
        extension = {row["original_url"]: row["donor_id"] for row in self.extra["aliases"]}
        self.assertEqual(len(extension), 15)
        missing = {}
        counts = {"A": 0, "B": 0}
        for item in coverage:
            url, sid = item["canonical_locator"], item["donor_id"]
            counts[item["source_sets"][0]] += 1
            row = self.published["records"][by_id[sid]]
            self.assertEqual(row["donor_id"], sid)
            self.assertEqual(row["historical_status"], item["status"])
            self.assertEqual(row["normalized_key"], item["normalized_key"])
            resolved = direct.get(url)
            if resolved is None:
                missing[url] = sid
                resolved = extension.get(url)
            self.assertEqual(resolved, sid, url)
        self.assertEqual(counts, {"A": 133, "B": 312})
        self.assertEqual(missing, extension)
        self.assertEqual(len(direct), 1997)
        self.assertEqual(self.published["source_count"], 1919)
        self.assertEqual(self.published["approved_reference_count"], 825)

    def test_all_fifteen_missing_exact_url_variants_resolve_by_public_api(self):
        self.assertEqual(len(self.extra["aliases"]), 15)
        sources = {"A": 0, "B": 0}
        for entry in self.extra["aliases"]:
            sources[entry["source_set"]] += 1
            with self.subTest(url=entry["original_url"]):
                row = lookup_module.lookup_published(original_url=entry["original_url"])
                self.assertEqual(row["donor_id"], entry["donor_id"])
                self.assertEqual(row["historical_status"], entry["historical_status"])
                self.assertEqual(row, lookup_module.lookup_published(donor_id=entry["donor_id"]))
                for key in ("runtime_admission", "code_copy_authorized",
                            "license_authorized", "model_provider_admission"):
                    self.assertIs(row[key], False)
        self.assertEqual(sources, {"A": 5, "B": 10})

    def test_all_fifty_ai_text_delta_urls_resolve_to_existing_published_donors(self):
        delta = self.ai_text
        self.assertEqual(delta["source_count"], 50)
        self.assertEqual(delta["unique_source_key_count"], 39)
        self.assertEqual(
            sum(len(source["urls"]) for source in delta["sources"]),
            delta["source_count"],
        )
        ids = {row["key"]: row["id"] for row in delta["new_ids"]}
        self.assertEqual(len(ids), 39)
        urls = set()
        missing_direct = 0
        for source in delta["sources"]:
            donor_id = ids[source["normalized_source_key"]]
            self.assertEqual(
                self.published["records"][self.published["lookup_by_id"][donor_id]]["normalized_key"],
                source["normalized_source_key"],
            )
            for url in source["urls"]:
                with self.subTest(url=url):
                    self.assertNotIn(url, urls)
                    urls.add(url)
                    if url not in self.published["lookup_by_locator"]:
                        missing_direct += 1
                    row = lookup_module.lookup_published(original_url=url)
                    self.assertIsNotNone(row, url)
                    self.assertEqual(row["donor_id"], donor_id)
                    self.assertEqual(row["historical_status"], "ACCEPTED_REFERENCE")
                    self.assertEqual(row, lookup_module.lookup_published(donor_id=donor_id))
                    for key in ("runtime_admission", "code_copy_authorized",
                                "license_authorized", "model_provider_admission"):
                        self.assertIs(row[key], False)
        self.assertEqual(len(urls), 50)
        self.assertEqual(missing_direct, 17)

    def test_superseded_historical_source_stays_superseded(self):
        url = "https://github.com/Ascend/triton-ascend"
        source = lookup_module.lookup_published(original_url=url)
        self.assertEqual(source["donor_id"], "FA3-DONOR-ASCEND-TRITON-ASCEND-LEGACY-001")
        self.assertEqual(source["historical_status"], "SUPERSEDED")
        self.assertEqual(source["donor_registration"], "HISTORICAL_SUPERSEDED_NOT_ACTIVE")
        self.assertIs(source["runtime_admission"], False)

    def test_alias_tamper_cannot_replace_an_existing_donor(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = json.loads(EXTRA.read_text(encoding="utf-8"))
            bad_url = copy["aliases"][0]["original_url"]
            copy["aliases"][0]["donor_id"] = "FA3-DONOR-OTHER-001"
            altered = Path(tmp) / "altered.json"
            altered.write_text(json.dumps(copy), encoding="utf-8")
            with patch.object(lookup_module, "PUBLISHED_EXACT_ALIASES", altered):
                with self.assertRaises(ValueError):
                    lookup_module.lookup_published(original_url=bad_url)

    def test_cli_original_url_search(self):
        url = self.extra["aliases"][0]["original_url"]
        expected = self.extra["aliases"][0]["donor_id"]
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/donor_reference_lookup.py"),
             "--published-only", "--url", url],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["donor_id"], expected)


if __name__ == "__main__":
    unittest.main()
