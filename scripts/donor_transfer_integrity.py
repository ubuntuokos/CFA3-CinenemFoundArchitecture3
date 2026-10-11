"""Validated, read-only donor history inputs shared by lookup and lifecycle."""
from functools import lru_cache
import hashlib
import json
import marshal
from pathlib import Path

from transfer_donors import digest, current_owner_confirmations, OWNER_CONFIRMATION, STATES

REG = Path(__file__).resolve().parents[1] / "canonical/registries"
REJECTION_ARCHIVE = (Path(__file__).resolve().parents[1] /
    "archive/donor-source-migration/2026-10-09/FA3-DONOR-REJECTION-AUDIT-001.json")
REJECTION_ARCHIVE_BLOB = "1bb853ef2dc9a15231ab4acda136ee5c02c9e2c8"


def verified_rejection_audit():
    """Read and authenticate the unchanged, explicitly rejected history."""
    raw = REJECTION_ARCHIVE.read_bytes()
    git_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if git_blob != REJECTION_ARCHIVE_BLOB:
        raise ValueError("Preserved rejection audit Git blob changed")
    audit = json.loads(raw)
    if (audit.get("schema") != "fa3.donor-rejection-audit.v1"
            or audit.get("id") != "FA3-DONOR-REJECTION-AUDIT-001"
            or audit.get("authority") is not False
            or audit.get("active_donor_registry") is not False
            or not isinstance(audit.get("entries"), list)):
        raise ValueError("Preserved rejection audit authority invalid")
    return audit
TRANSFER_NAME = "CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"
CONFIRMATION_NAME = OWNER_CONFIRMATION.name


def file_signature(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


@lru_cache(maxsize=4)
def _read_snapshot(path, signature):
    raw = path.read_bytes()
    data = json.loads(raw)
    validate_snapshot(data)
    return data, hashlib.sha256(raw).hexdigest()


def validate_snapshot(data):
    # Cache by the complete serialized VALUE, never by mutable object identity.
    # Any mutation, including outside the requested row, gets a different key.
    # marshal is only an in-process typed value key here. Never load external
    # marshal bytes. Unlike dict equality it distinguishes 1, 1.0 and True,
    # without serializing the entire JSON text for each lookup in a batch.
    # Version 2 has no reference-sharing flags: retaining a returned object
    # cannot change the encoding of otherwise identical JSON values.
    # Authentication of the archived audit is deliberately outside the cache:
    # changing the archive must fail even after a warm snapshot cache hit.
    expected_audit_digest = digest(verified_rejection_audit())
    payload = marshal.dumps(data, 2)
    _validate_snapshot_payload(payload, expected_audit_digest)


@lru_cache(maxsize=2)
def _validate_snapshot_payload(payload, expected_audit_digest):
    data = marshal.loads(payload)
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
        reference = row["reference_record"]
        if (reference["donor_id"] != sid
                or STATES.get(row["pre_transfer_status"]) != row["reference_state"]
                or reference["donor_registration"] != row["reference_state"]
                or row["runtime_admission"] is not False
                or any(reference.get(k) is not False for k in (
                    "runtime_admission", "code_copy_authorized", "license_authorized",
                    "model_provider_admission"))):
            raise ValueError("Historical donor authority mismatch")
        ids[sid] = position
    if ids != data["lookup_by_id"] or any(type(v) is not int for v in data["lookup_by_id"].values()):
        raise ValueError("Historical donor lookup index mismatch")
    locators = {}
    for position, route in enumerate(data["locator_routes"]):
        alias, preferred, related = route["alias"], route["preferred_source_id"], route["related_source_ids"]
        if preferred not in ids:
            raise ValueError("Resolved locator targets a missing donor identity")
        if (not isinstance(alias, str) or not alias or alias in locators
                or not isinstance(related, list) or not related
                or len(set(related)) != len(related) or any(sid not in ids for sid in related)
                or preferred not in related or not route.get("authority")
                or alias not in data["records"][ids[preferred]]["aliases"]):
            raise ValueError("Historical locator route integrity mismatch")
        locators[alias] = position
    if (locators != data["lookup_by_locator"]
            or any(type(v) is not int for v in data["lookup_by_locator"].values())):
        raise ValueError("Historical locator lookup index mismatch")
    # Records-only digests do not authenticate negative donor decisions.
    # Bind the COMPLETE rejection audit to the pinned historical Git blob.
    if digest(data.get("rejection_audit")) != expected_audit_digest:
        raise ValueError("Historical rejection audit differs from preserved evidence")
    rejected_ids, rejected_locators = set(), set()
    for entry in data["rejection_audit"]["entries"]:
        rejected = entry["donor"]
        sid = rejected["donor_id"]
        source = rejected["source"]
        if (rejected.get("status") != "REJECTED" or sid in rejected_ids
                or sid in ids or not isinstance(sid, str) or not sid):
            raise ValueError("Historical rejected source identity was altered or reactivated")
        rejected_ids.add(sid)
        locators_for_rejected = {source["locator"], source["normalized_key"]}
        if (any(not isinstance(locator, str) or not locator or locator in locators
                for locator in locators_for_rejected)
                or locators_for_rejected & rejected_locators):
            raise ValueError("Historical rejected locator was reactivated or duplicated")
        rejected_locators.update(locators_for_rejected)


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
    if (doc.get("source_commit") != data["source_commit"]
            or doc.get("transfer_snapshot_id") != data["id"]):
        raise ValueError("Current owner confirmation snapshot binding mismatch")
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


PROJECTION_INPUTS = (
    "CFA3-DONOR-L1-STAGED-DIRECT-ACCESS-20261010.json",
    "CFA3-DONOR-L1-URL-ROUTING-20261010.json",
    "CFA3-DONOR-OWNER-APPROVAL-19-26-20261010.json",
    "CFA3-DONOR-REFERENCE-REGISTRY-001.json", TRANSFER_NAME, CONFIRMATION_NAME,
)


def expected_lifecycle_projection():
    signatures = tuple(file_signature(REG / name) for name in PROJECTION_INPUTS)
    return _expected_lifecycle_projection(REG, signatures)


@lru_cache(maxsize=2)
def _expected_lifecycle_projection(reg, signatures):
    raw = {name: (reg / name).read_bytes() for name in PROJECTION_INPUTS}
    staged, routing, approvals, registered, transfer, confirmation = (
        json.loads(raw[name]) for name in PROJECTION_INPUTS)
    validated, transfer_sha = verified_snapshot()
    confirmations, confirmation_sha = confirmation_evidence()
    if (transfer != validated or hashlib.sha256(raw[TRANSFER_NAME]).hexdigest() != transfer_sha
            or hashlib.sha256(raw[CONFIRMATION_NAME]).hexdigest() != confirmation_sha):
        raise ValueError("Donor evidence changed during projection read")
    rows = {row["source_id"]: row for row in transfer["records"]}
    approval_by_id = {row["id"]: row for row in approvals["records"]}
    if any(rows[row["donor_id"]]["reference_record"] != row for row in registered["records"]):
        raise ValueError("Existing canonical donor subset differs from transfer")
    if {row["id"] for row in staged["sources"]} != set(rows):
        raise ValueError("Staged source identity coverage mismatch")
    records = []
    for row in staged["sources"]:
        sid = row["id"]
        archived = rows[sid]
        original = archived["historical_record"]
        if row["status"] != archived["pre_transfer_status"]:
            raise ValueError("Staged donor status differs from transferred history")
        records.append({
            "source_id": sid, "canonical_url": row["url"], "normalized_key": row["key"],
            "prior_decision": {
                "decision_id": "preserved-donor-record:" + sid,
                "revision": archived["historical_record_sha256"], "outcome": row["status"],
                "historical_outcome": original["status"],
                "submission_review": original.get("submission_review", {}),
                "intake_provenance": original.get("intake_provenance", {}),
                "owner_approval": confirmations.get(sid, approval_by_id.get(sid)),
                "canonical_reference_registration": archived["reference_record"],
            },
            "observed_revision": None, "support_status": "UNKNOWN",
            "rights": {"verified": False, "may_modify_and_distribute": False},
            "runtime_admission": False, "reference_state": archived["reference_state"],
        })
    if routing["entries"] != transfer["locator_routes"]:
        raise ValueError("Staged lifecycle routes differ from transferred routes")
    routes = [dict(route) for route in transfer["locator_routes"]]
    by_alias = {route["alias"]: route for route in routes}
    for alias, sid in sorted(preserved_aliases(transfer["records"]).items()):
        if alias in by_alias:
            if by_alias[alias]["preferred_source_id"] != sid:
                raise ValueError("Preserved alias conflicts with transferred route")
        else:
            routes.append({"alias": alias, "preferred_source_id": sid,
                           "related_source_ids": [sid], "authority": "PRESERVED_HISTORICAL_LOCATOR"})
    return {"input_sha256": {name: hashlib.sha256(raw[name]).hexdigest() for name in PROJECTION_INPUTS},
            "source_records": records, "locator_routes": routes}
