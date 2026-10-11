"""Validated, read-only donor history inputs shared by lookup and lifecycle."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from transfer_donors import digest, current_owner_confirmations, OWNER_CONFIRMATION

REG = Path(__file__).resolve().parents[1] / "canonical/registries"
TRANSFER_NAME = "CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"
CONFIRMATION_NAME = OWNER_CONFIRMATION.name


def file_signature(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


@lru_cache(maxsize=4)
def _read_snapshot(path, signature):
    raw = path.read_bytes()
    data = json.loads(raw)
    if (data.get("schema") != "cfa3.donor-transfer-snapshot.v1"
            or data.get("runtime_admission") is not False
            or data.get("code_or_license_admission") is not False):
        raise ValueError("Historical source snapshot schema or authority is invalid")
    records = data["records"]
    if data["record_count"] != len(records) or digest(records) != data["record_set_sha256"]:
        raise ValueError("Historical record set digest or count mismatch")
    ids = {}
    for position, row in enumerate(records):
        sid = row["source_id"]
        if sid in ids or digest(row["historical_record"]) != row["historical_record_sha256"]:
            raise ValueError("Historical record digest or identity mismatch")
        if row["historical_record"]["donor_id"] != sid:
            raise ValueError("Historical donor identity mismatch")
        ids[sid] = position
    if ids != data["lookup_by_id"]:
        raise ValueError("Historical donor lookup index mismatch")
    return data, hashlib.sha256(raw).hexdigest()


def verified_snapshot():
    path = REG / TRANSFER_NAME
    return _read_snapshot(path, file_signature(path))


def confirmation_evidence():
    """Validate each current binding against the actual immutable history."""
    approvals = current_owner_confirmations()
    data, _ = verified_snapshot()
    pending = {
        row["source_id"]: row for row in data["records"]
        if row["pre_transfer_status"] == "OWNER_APPROVED_PENDING_PUBLICATION"
        and row["historical_record"].get("intake_provenance", {}).get(
            "canonical_approval_admitted") is False
    }
    if set(approvals) != set(pending):
        raise ValueError("Current owner confirmation coverage mismatch")
    for sid, row in pending.items():
        if approvals[sid] != (row["historical_record"]["source"]["locator"],
                              row["historical_record_sha256"]):
            raise ValueError("Current owner confirmation binding mismatch")
    raw = OWNER_CONFIRMATION.read_bytes()
    doc = json.loads(raw)
    evidence = {row["source_id"]: {
        "confirmation_id": doc["id"],
        "confirmation_file": CONFIRMATION_NAME,
        "record": row,
    } for row in doc["confirmed_records"]}
    return evidence, hashlib.sha256(raw).hexdigest()


def preserved_aliases(records):
    """Project explicit legacy aliases only; never infer redirects or identities."""
    aliases = {}
    for row in records:
        history = row["historical_record"]
        for values in (history.get("source", {}).get("previous_locators", []),
                       history.get("legacy_source_keys", [])):
            if not isinstance(values, list):
                raise ValueError("Historical aliases must be a list")
            for locator in values:
                if not isinstance(locator, str) or not locator:
                    raise ValueError("Invalid historical alias")
                if locator in aliases and aliases[locator] != row["source_id"]:
                    raise ValueError("Conflicting historical alias identities")
                aliases[locator] = row["source_id"]
    return aliases
