#!/usr/bin/env python3
"""Search immutable PR #545 donor proposals; never approve or rekey them.

This read-only supplement is deliberately outside the 1,981-record active
historical transfer snapshot. It cannot change any earlier donor decision.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive/donor-source-migration/2026-10-11/FA3-DONOR-LEGACY-OPEN-PR-RECONCILIATION-2026-09-29.json"
GAPS = ROOT / "canonical/registries/CFA3-DONOR-L1-HISTORICAL-PR-OPEN-GAPS-20261010.json"
ARCHIVE_BLOB_SHA = "de73168d3f0cf4834ad0604f689d95cb4b5bf1fd"
GAPS_BLOB_SHA = "20ef086e67c399cd6968a23b15bc749877984c99"

def _pinned_json(path, expected_blob):
    raw = path.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if digest != expected_blob:
        raise ValueError("Donor PR545 immutable evidence digest changed: " + path.name)
    return json.loads(raw)

def _repo_url(key):
    if not isinstance(key, str) or not key.startswith("github:"):
        raise ValueError("Invalid historical GitHub source key")
    slug = key[len("github:"):]
    parts = slug.split("/")
    if len(parts) != 2 or any(not p or p in (".", "..") or "?" in p or "#" in p for p in parts):
        raise ValueError("Invalid proposed source identity")
    return "https://github.com/" + slug

def _normalized_query_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or parsed.netloc.lower() != "github.com":
        return None
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        return None
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if len(path.strip("/").split("/")) != 2:
        return None
    return "https://github.com/" + path.strip("/").lower()

def proposal_records():
    """Authenticate and project the old proposals as non-admitted search hits."""
    doc = _pinned_json(ARCHIVE, ARCHIVE_BLOB_SHA)
    gaps = _pinned_json(GAPS, GAPS_BLOB_SHA)
    group = next((x for x in gaps["groups"] if x.get("pr") == 545), None)
    if (doc.get("schema") != "fa3.donor-legacy-pr-reconciliation.v1"
            or doc.get("mode") != "DONOR_MAINTENANCE_ONLY"
            or doc.get("release_ready") is not False
            or group is None
            or group.get("type") != "UNMERGED_MAINTENANCE_PROPOSALS_UNVERIFIED"
            or len(doc.get("additions", [])) != 17
            or len(doc.get("rekeys", [])) != 3):
        raise ValueError("Unapproved donor proposal source boundary changed")
    expected = {
        (row["proposed_donor_id"], row["source_key"], row["source_pr"])
        for row in group["missing_from_1919"]
    }
    actual = {(row["id"], row["key"], row["source_pr"]) for row in doc["additions"]}
    expected_rekeys = {
        (row["id"], row["old_key"], row["proposed_new_key"])
        for row in group["proposed_rekeys"]
    }
    actual_rekeys = {(row["id"], row["old_key"], row["new_key"]) for row in doc["rekeys"]}
    if (len(expected) != 17 or len(actual) != 17 or expected != actual
            or len(expected_rekeys) != 3 or actual_rekeys != expected_rekeys):
        raise ValueError("Historical proposal or rekey evidence does not reconcile")
    records = []
    for row in doc["additions"]:
        records.append({
            "donor_id": row["id"],
            "donor_registration": "UNMERGED_PROPOSAL_NOT_OWNER_APPROVED",
            "source_key": row["key"],
            "proposed_locator_not_original_submission": _repo_url(row["key"]),
            "historical_source_pr": row["source_pr"],
            "historical_proposal_pr": 545,
            "historical_observation_pin_not_current_version": row.get("pinned_observation"),
            "historical_declared_license_not_verified": row.get("license_declared", "UNKNOWN"),
            "previous_decision": "UNMERGED_PROPOSAL_PENDING_OWNER_APPROVAL_EVIDENCE_NOT_ADMITTED",
            "runtime_admission": False,
            "code_copy_authorized": False,
            "license_authorized": False,
            "model_provider_admission": False,
        })
    for row in doc["rekeys"]:
        records.append({
            "donor_id": row["id"],
            "donor_registration": "UNVERIFIED_REKEY_PROPOSAL_NOT_APPLIED",
            "source_key": row["old_key"],
            "proposed_new_key": row["new_key"],
            "proposed_locator_not_verified_alias": _repo_url(row["new_key"]),
            "historical_proposal_pr": 545,
            "historical_observation_pin_not_current_version": row.get("pinned_observation"),
            "previous_decision": "HISTORICAL_SOURCE_KEY_RETAINED",
            "runtime_admission": False,
            "code_copy_authorized": False,
            "license_authorized": False,
            "model_provider_admission": False,
        })
    locators = [row.get("proposed_locator_not_original_submission",
                        row.get("proposed_locator_not_verified_alias")) for row in records]
    if len(locators) != 20 or len(set(locators)) != 20:
        raise ValueError("Proposed donor locators collide")
    return records

def lookup_proposal(*, donor_id=None, original_url=None):
    """Return a non-authoritative historical proposal, not an admitted donor."""
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one proposal query is required")
    records = proposal_records()
    if donor_id is not None:
        matches = [row for row in records if row["donor_id"] == donor_id
                   and row["donor_registration"] == "UNMERGED_PROPOSAL_NOT_OWNER_APPROVED"]
    else:
        url = _normalized_query_url(original_url)
        matches = [row for row in records
                   if url is not None and url == row.get(
                       "proposed_locator_not_original_submission",
                       row.get("proposed_locator_not_verified_alias"))]
    if len(matches) > 1:
        raise ValueError("Conflicting unmerged donor proposal lookup")
    return dict(matches[0]) if matches else None
