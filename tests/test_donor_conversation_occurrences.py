"""Direct ChatGPT USER-message donor URL occurrence preservation tests."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("donor_l1", ROOT / "scripts/donor_l1.py")
donor_l1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor_l1)

LEDGER = ROOT / "canonical/registries/CFA3-DONOR-CONVERSATION-LINK-OCCURRENCES-001.json"


class DonorConversationOccurrenceTests(unittest.TestCase):
    def test_earliest_user_url_occurrence_is_preserved_and_searchable(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(ledger["occurrence_count"], 1)
        self.assertFalse(ledger["global_complete"])
        first = ledger["entries"][0]
        self.assertEqual(first["conversation_timestamp"], "2026-03-27T21:10:28Z")
        self.assertEqual(first["exact_url"], "http://www.ubuntu.com/support")
        self.assertEqual(first["source_id"], "FA3-DONOR-WWW-UBUNTU-COM-SUPPORT-1040BD88-001")

        with tempfile.TemporaryDirectory() as tmp:
            dbpath = Path(tmp) / "conversation-occurrence.sqlite"
            donor_l1.stage(dbpath, "conversation-occurrence-001")
            with sqlite3.connect(dbpath) as db:
                row = db.execute(
                    "SELECT occurrence_index,source_id,original_url,evidence_ref "
                    "FROM historical_link_occurrences WHERE source_group=?",
                    ("CHATGPT_USER_CONVERSATIONS",)
                ).fetchone()
                self.assertEqual(row, (
                    1,
                    "FA3-DONOR-WWW-UBUNTU-COM-SUPPORT-1040BD88-001",
                    "http://www.ubuntu.com/support",
                    "CHATGPT_USER_MESSAGE:2026-03-27T21:10:28Z#1",
                ))
                provenance = db.execute(
                    "SELECT 1 FROM source_provenance WHERE source_id=? AND original_url=? "
                    "AND source_set=? AND historical_evidence=?",
                    (
                        first["source_id"],
                        first["exact_url"],
                        "CHATGPT_USER_CONVERSATIONS",
                        first["evidence_ref"],
                    ),
                ).fetchone()
                self.assertEqual(provenance, (1,))


if __name__ == "__main__":
    unittest.main()
