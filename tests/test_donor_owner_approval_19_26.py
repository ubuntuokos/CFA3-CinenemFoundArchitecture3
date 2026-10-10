"""New-CFA3 direct owner donor approval: historical sources 19–26, no L1 publication."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "canonical/registries/CFA3-DONOR-OWNER-APPROVAL-19-26-20261010.json"
CATALOG = ROOT / "canonical/registries/CFA3-DONOR-L1-STAGED-DIRECT-ACCESS-20261010.json"
ROUTING = ROOT / "canonical/registries/CFA3-DONOR-L1-URL-ROUTING-20261010.json"
MANIFEST = ROOT / "canonical/registries/CFA3-DONOR-L1-SOURCE-ARCHIVE-MANIFEST-001.json"
spec = importlib.util.spec_from_file_location("donor_l1", ROOT / "scripts/donor_l1.py")
donor_l1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class DirectOwnerApproval1926Tests(unittest.TestCase):
    def test_no_omitted_or_duplicated_reference_and_original_url(self):
        ledger, catalog, routing, manifest = (
            read(LEDGER), read(CATALOG), read(ROUTING), read(MANIFEST))
        self.assertEqual(ledger["authority"], "EXPLICIT_CURRENT_USER_DONOR_REGISTRATION_DIRECTIVE")
        self.assertEqual(ledger["registration_status"], "OWNER_APPROVED_PENDING_L1_PUBLICATION")
        self.assertFalse(ledger["canonical_l1_published"])
        self.assertFalse(ledger["runtime_or_code_admission"])
        self.assertFalse(catalog["canonical_level_published"])
        self.assertEqual(ledger["owner_approved_donor_identity_count"], 82)
        self.assertEqual(ledger["original_valid_url_occurrences_19_26"], 83)
        self.assertEqual(len(ledger["source_groups"]), 8)
        self.assertEqual(len(ledger["records"]), 82)
        self.assertEqual(len({x["id"] for x in ledger["records"]}), 82)
        historical = {x["source_path"]: x["source_blob_sha"]
                      for x in manifest["per_file_completion_receipts"]
                      if "source_blob_sha" in x}
        self.assertTrue(all(
            historical.get(x["source_path"]) == x["old_source_blob_sha"]
            for x in ledger["source_groups"]))
        self.assertEqual(
            [x["original_valid_url_occurrences"] for x in ledger["source_groups"]],
            [20, 23, 12, 5, 15, 1, 6, 1])
        indexed = {x["id"]: x for x in catalog["sources"]}
        routes = {x["alias"]: x for x in routing["entries"]}
        count = 0
        for row in ledger["records"]:
            with self.subTest(donor=row["id"]):
                item = indexed[row["id"]]
                self.assertEqual(item["key"], row["normalized_source_key"])
                self.assertEqual(item["url"], row["canonical_locator"])
                self.assertEqual(item["status"], row["previous_status"])
                self.assertEqual(item["legacy_status"], row["legacy_status"])
                self.assertEqual(item["status"], "ACCEPTED_REFERENCE")
                self.assertEqual(row["owner_donor_approval"], "OWNER_APPROVED_PENDING_L1_PUBLICATION")
                self.assertFalse(row["runtime_admission"])
                for original in row["original_submitted_urls"]:
                    url = original["url"]
                    self.assertIn(url, [item["url"], *item.get("discovery_urls", [])])
                    self.assertEqual(routes[url]["preferred_source_id"], row["id"])
                    count += 1
        self.assertEqual(count, 84)
        vanessik = next(x for x in ledger["records"] if x["id"] == "FA3-DONOR-VANESSIK-001")
        self.assertEqual(vanessik["historical_resolution"]["original_malformed_url"],
                         "https://github.com/Vanessi k")
        self.assertEqual(vanessik["canonical_locator"], "https://github.com/Vanessik")
        self.assertNotIn("https://github.com/Vanessi k", routes)

    def test_sqlite_owner_approval_readback_is_durable_and_no_status_is_overwritten(self):
        ledger = read(LEDGER)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owner-approved-19-26.sqlite"
            donor_l1.stage(path, "new-cfa3-owner-approved-19-26")
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM sources").fetchone()[0], 1981)
                self.assertEqual(db.execute(
                    "SELECT count(*) FROM donor_owner_approvals").fetchone()[0], 82)
                self.assertEqual(db.execute(
                    "SELECT value FROM metadata WHERE key="
                    "'new_cfa3_explicit_owner_approved_donor_references_19_26'"
                ).fetchone(), ("82",))
                self.assertEqual(db.execute(
                    "SELECT value FROM metadata WHERE key='publication_gate'"
                ).fetchone(), ("PENDING",))
                count = 0
                for record in ledger["records"]:
                    sid = record["id"]
                    self.assertEqual(db.execute(
                        "SELECT approval_status,approved_on FROM donor_owner_approvals "
                        "WHERE source_id=?", (sid,)).fetchone(),
                        ("OWNER_APPROVED_PENDING_L1_PUBLICATION", "2026-10-10"))
                    self.assertEqual(db.execute(
                        "SELECT historical_status,current_status FROM sources "
                        "WHERE source_id=?", (sid,)).fetchone(),
                        (record["legacy_status"], record["previous_status"]))
                    for view in record["original_submitted_urls"]:
                        url = view["url"]
                        self.assertIsNotNone(db.execute(
                            "SELECT 1 FROM source_provenance WHERE source_id=? AND original_url=? "
                            "AND source_set='NEW_CFA3_OWNER_APPROVAL_19_26_20261010'",
                            (sid, url)).fetchone())
                        self.assertEqual(db.execute(
                            "SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                            (url,)).fetchone(), (sid,))
                        count += 1
                self.assertEqual(count, 84)
                self.assertIsNone(db.execute(
                    "SELECT source_id FROM aliases WHERE alias='https://github.com/Vanessi k'"
                ).fetchone())


if __name__ == "__main__":
    unittest.main()
