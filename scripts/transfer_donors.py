#!/usr/bin/env python3
"""Transfer frozen historical donor metadata into the active reference snapshot.

No crawling, new donor approval, source-code copying or runtime admission.
Historical candidates and unresolved proposals retain their original authority.
"""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

from donor_l1 import ROOT, REGISTRY, frozen_sources, stage, sha_blob

REG = ROOT / "canonical/registries"
OUTPUT = REG / "CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"
STATES = {
    "ACCEPTED_REFERENCE": "CANONICAL_REFERENCE_REGISTERED",
    "OWNER_APPROVED_PENDING_PUBLICATION": "CANONICAL_REFERENCE_REGISTERED",
    "CANDIDATE": "CANDIDATE_PRESERVED",
    "ANALYZED": "ANALYZED_SOURCE_PRESERVED",
    "SUPERSEDED": "SUPERSEDED_REFERENCE_PRESERVED",
    "BLOCKED": "UNAPPROVED_SOURCE_PRESERVED",
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def build():
    subset = json.loads((REG / "CFA3-DONOR-REFERENCE-REGISTRY-001.json").read_text())
    preserved = {r["donor_id"]: r for r in subset["records"]}
    originals = {r["donor_id"]: r for r, _, _ in frozen_sources()}
    gaps = json.loads((REG / "CFA3-DONOR-L1-HISTORICAL-PR-OPEN-GAPS-20261010.json").read_text())
    rejection_raw = (REGISTRY.parent / "FA3-DONOR-REJECTION-AUDIT-001.json").read_bytes()
    if sha_blob(rejection_raw) != "1bb853ef2dc9a15231ab4acda136ee5c02c9e2c8":
        raise ValueError("Historical rejection evidence changed")
    rejection_audit = json.loads(rejection_raw)
    with tempfile.TemporaryDirectory() as tmp:
        dbpath = Path(tmp) / "transfer.sqlite"
        evidence = stage(dbpath, "CFA3-DONOR-TRANSFER-20261010")
        with closing(sqlite3.connect(dbpath)) as db:
            routes = [{"alias": alias, "preferred_source_id": preferred,
                       "authority": authority, "related_source_ids": json.loads(related)}
                      for alias, preferred, authority, related in db.execute(
                          "SELECT * FROM url_resolution ORDER BY alias")]
            records = []
            for sid, key, locator, name, historical, current, origin in db.execute(
                    "SELECT source_id,normalized_key,locator,name,historical_status,current_status,source_origin "
                    "FROM sources ORDER BY source_id"):
                aliases = [r[0] for r in db.execute("SELECT alias FROM aliases WHERE source_id=? ORDER BY alias", (sid,))]
                provenance = [dict(zip(("original_url", "source_set", "historical_evidence"), r))
                              for r in db.execute("SELECT original_url,source_set,historical_evidence FROM source_provenance "
                                                  "WHERE source_id=? ORDER BY original_url,source_set,historical_evidence", (sid,))]
                approvals = [dict(zip(("evidence_id", "approval_status", "approved_on"), r))
                             for r in db.execute("SELECT evidence_id,approval_status,approved_on FROM donor_owner_approvals "
                                                 "WHERE source_id=?", (sid,))]
                # Keep the previously published 19–26 view byte-for-byte as JSON values.
                reference = preserved.get(sid, {
                    "donor_id": sid, "normalized_key": key, "original_url": locator,
                    "original_submitted_urls": sorted({r["original_url"] for r in provenance}),
                    "historical_status": historical, "donor_registration": STATES[current],
                    "runtime_admission": False, "code_copy_authorized": False,
                    "license_authorized": False, "model_provider_admission": False,
                })
                records.append({
                    "source_id": sid, "name": name, "origin": origin,
                    "historical_status": historical, "pre_transfer_status": current,
                    "reference_state": STATES[current],
                    "historical_record": originals[sid], "historical_record_sha256": digest(originals[sid]),
                    "reference_record": reference, "aliases": aliases,
                    "provenance": provenance, "owner_approvals": approvals,
                    "runtime_admission": False,
                })
    legacy_ids = {r["donor_id"] for r in json.loads(REGISTRY.read_text())["entries"]}
    ids = {r["source_id"] for r in records}
    if not legacy_ids <= ids or len(ids) != len(records):
        raise ValueError("Historical donor loss or duplicate identity")
    if any(r["donor"]["donor_id"] in ids for r in rejection_audit["entries"]):
        raise ValueError("Rejected source must not reenter the active registry")
    proposed = [r for g in gaps["groups"] for r in g.get("missing_from_1919", [])]
    rekeys = [r for g in gaps["groups"] for r in g.get("proposed_rekeys", [])]
    return {
        "schema": "cfa3.donor-transfer-snapshot.v1",
        "id": "CFA3-DONOR-TRANSFER-SNAPSHOT-001",
        "scope": "FROZEN_OLD_MAIN_AND_PREVIOUSLY_RECOVERED_SOURCES",
        "source_repository": "ubuntuokos/Final-Architecture-v3.0",
        "source_commit": "a9c724da62bf49f3353c694990fc51443e634b4a",
        "source_registry_blob": "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b",
        "snapshot_transfer_complete": True,
        "global_l1_completed": False, "all_historical_submissions_complete": False,
        "runtime_admission": False, "code_or_license_admission": False,
        "legacy_main_records": len(legacy_ids), "additional_recovered_records": len(ids - legacy_ids),
        "record_count": len(records), "missing_legacy_main_ids": sorted(legacy_ids - ids),
        "reference_state_counts": dict(sorted(Counter(r["reference_state"] for r in records).items())),
        "record_set_sha256": digest(records),
        "records": records, "lookup_by_id": {r["source_id"]: i for i, r in enumerate(records)},
        "locator_routes": routes, "lookup_by_locator": {r["alias"]: i for i, r in enumerate(routes)},
        "unadmitted_historical_proposals": proposed,
        "unapplied_historical_rekeys": rekeys,
        "rejection_audit": rejection_audit,
        "rejection_audit_blob": "1bb853ef2dc9a15231ab4acda136ee5c02c9e2c8",
        "staged_readback_evidence": evidence["index_evidence"],
        "remaining_scope": "Original conversation-only inputs, final L1 classification and L2-L5 discovery are not certified by this repository transfer.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    snapshot = build()
    rendered = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if OUTPUT.read_text() != rendered:
            raise SystemExit("Transferred donor snapshot differs from original evidence")
    else:
        # Atomic replacement; a failed build leaves the previous snapshot intact.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=OUTPUT.parent,
                                         prefix="donor-transfer-", delete=False) as f:
            pending = Path(f.name)
            f.write(rendered)
        try:
            pending.replace(OUTPUT)
        finally:
            pending.unlink(missing_ok=True)
    print(json.dumps({k: snapshot[k] for k in ("record_count", "legacy_main_records",
                      "additional_recovered_records", "reference_state_counts", "missing_legacy_main_ids")}, indent=2))


if __name__ == "__main__":
    main()
