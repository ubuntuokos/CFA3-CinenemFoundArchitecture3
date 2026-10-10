"""Exact historical URL routes from the verified archived ODBC/SQL/vector/media donor delta.

This adds source aliases only. It never creates an identity, donor approval or runtime authority.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-ODBC-SQL-VECTOR-MEDIA-2026-09-29.json"
EXPECTED_BLOB = "47c51315ab68339a85a3b720674f5e9734c0dc38"
MENTOR_ARCHIVE = ROOT / "archive/donor-source-migration/2026-10-09/FA3-DONOR-MENTOR-ENHANCEMENT-DELTA-001.json"
MENTOR_BLOB = "6d9cc999b671297c9f1b009b0d429ee612916140"


@lru_cache(maxsize=1)
def archived_delta():
    raw = ARCHIVE.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != EXPECTED_BLOB:
        raise ValueError("Historical ODBC donor delta was modified")
    doc = json.loads(raw)
    if (doc.get("schema") != "fa3.donor-intake-delta.v1"
            or doc.get("source_count") != 56
            or doc.get("unique_source_key_count") != 50
            or len(doc.get("sources", [])) != 50):
        raise ValueError("Invalid archived donor delta")
    return doc


@lru_cache(maxsize=1)
def archived_mentor_delta():
    raw = MENTOR_ARCHIVE.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != MENTOR_BLOB:
        raise ValueError("Historical Mentor donor delta was modified")
    doc = json.loads(raw)
    if (doc.get("schema") != "FA3-DONOR-SCHEMA-001"
            or len(doc.get("records", [])) != 15):
        raise ValueError("Invalid Mentor donor delta")
    return doc


def delta_aliases(records):
    """Map all raw input URLs to the existing source IDs, refusing identity conflicts."""
    doc = archived_delta()
    by_key, by_id = {}, set()
    for row in records:
        sid = row["source_id"]
        historical = row.get("historical_record", {})
        key = row.get("normalized_key") or historical.get("source", {}).get("normalized_key")
        if not isinstance(sid, str) or not sid or sid in by_id:
            raise ValueError("Invalid source identity in donor route index")
        by_id.add(sid)
        if isinstance(key, str) and key:
            if key in by_key and by_key[key] != sid:
                raise ValueError("Conflicting normalized donor source identities")
            by_key[key] = sid
    previously_matched = {row["key"]: row["id"] for row in doc["matched_existing_parent"]}
    aliases = {}
    for source in doc["sources"]:
        key = source["normalized_source_key"]
        sid = by_key.get(key) or previously_matched.get(key)
        if sid not in by_id:
            raise ValueError("Missing existing source for historical delta " + key)
        for url in source["urls"]:
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError("Invalid original historical URL")
            if url in aliases and aliases[url] != sid:
                raise ValueError("Conflicting original historical URLs")
            aliases[url] = sid
    if len(aliases) != 56:
        raise ValueError("Historical ODBC donor delta link coverage incomplete")
    for record in archived_mentor_delta()["records"]:
        sid = record["donor_id"]
        if sid not in by_id:
            raise ValueError("Mentor donor identity missing from existing source index")
        for url in (record.get("source_url"), record.get("license_evidence_url")):
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError("Mentor historical source or evidence URL is invalid")
            if url in aliases and aliases[url] != sid:
                raise ValueError("Historical Mentor URL identity conflict")
            aliases[url] = sid
    if len(aliases) != 75:
        raise ValueError("Historical donor delta URL coverage incomplete")
    return aliases
