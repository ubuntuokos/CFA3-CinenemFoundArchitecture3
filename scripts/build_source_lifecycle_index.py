#!/usr/bin/env python3
"""Reproducible offline lifecycle projection of preserved donor evidence.

This publishes lookup data only, never L1 completeness or runtime authority.
"""
import argparse
import hashlib
import json
from pathlib import Path

from donor_l1 import frozen_sources
from source_lifecycle import validate_index

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "canonical/registries"
OUTPUT = REG / "CFA3-SOURCE-LIFECYCLE-INDEX-001.json"


def build():
    names = ["CFA3-DONOR-L1-STAGED-DIRECT-ACCESS-20261010.json",
             "CFA3-DONOR-L1-URL-ROUTING-20261010.json",
             "CFA3-DONOR-OWNER-APPROVAL-19-26-20261010.json",
             "CFA3-DONOR-REFERENCE-REGISTRY-001.json",
             "CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"]
    inputs = {name: json.loads((REG / name).read_text()) for name in names}
    staged, routing, approvals, registered, transfer = (inputs[name] for name in names)
    originals = {entry["donor_id"]: entry for entry, _, _ in frozen_sources()}
    approval_by_id = {r["id"]: r for r in approvals["records"]}
    registered_by_id = {r["source_id"]: r["reference_record"] for r in transfer["records"]}
    if set(registered_by_id) != set(originals):
        raise ValueError("Active transferred and historical donor identities differ")
    if any(registered_by_id.get(r["donor_id"]) != r for r in registered["records"]):
        raise ValueError("Previously registered donor reference was changed")
    records = []
    if {r["id"] for r in staged["sources"]} != set(originals):
        raise ValueError("Staged and original donor identities differ")
    for row in staged["sources"]:
        sid = row["id"]
        original = originals[sid]
        digest = hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()
        records.append({
            "source_id": sid, "canonical_url": row["url"], "normalized_key": row["key"],
            "prior_decision": {
                "decision_id": "preserved-donor-record:" + sid,
                "revision": digest, "outcome": row["status"],
                "historical_outcome": original["status"],
                "submission_review": original.get("submission_review", {}),
                "intake_provenance": original.get("intake_provenance", {}),
                "owner_approval": approval_by_id.get(sid),
                "canonical_reference_registration": registered_by_id.get(sid),
            },
            "observed_revision": None, "support_status": "UNKNOWN",
            "rights": {"verified": False, "may_modify_and_distribute": False},
            "runtime_admission": False,
            "reference_state": registered_by_id[sid]["donor_registration"],
        })
    index = {
        "schema": "cfa3.source-lifecycle-index.v2",
        "id": "CFA3-SOURCE-LIFECYCLE-INDEX-001",
        "source_status": "KNOWN_DONOR_LOOKUP_AVAILABLE_GLOBAL_COVERAGE_PENDING",
        "complete": False, "global_l1_completed": False,
        "repository_snapshot_transfer_complete": True,
        "active_reference_snapshot": transfer["id"],
        "migration_authority": "PRESERVED_EXISTING_RECORDS_NO_NEW_DONOR_APPROVAL",
        "input_sha256": {name: hashlib.sha256((REG / name).read_bytes()).hexdigest() for name in names},
        "source_records": records, "locator_routes": routing["entries"],
    }
    validate_index(index)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if OUTPUT.read_text() != rendered:
            raise SystemExit("Lifecycle projection differs from preserved inputs")
    else:
        OUTPUT.write_text(rendered)


if __name__ == "__main__":
    main()
