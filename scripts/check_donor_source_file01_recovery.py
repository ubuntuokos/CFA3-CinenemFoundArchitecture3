#!/usr/bin/env python3
"""Read back source-file 001; report bounded coverage without certifying L1/L2."""
import hashlib
import json
from pathlib import Path

import donor_reference_lookup as donor
import source_lifecycle as lifecycle
from build_donor_source_file01_queue import validated_queue

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "canonical/registries"


def audit():
    inputs = {}

    def read(path):
        raw = path.read_bytes()
        inputs[path.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    catalog = read(donor.PUBLISHED_FIRST)
    historical = read(donor.PUBLISHED_FIRST_ARCHIVE)
    canonical = read(REG / "CFA3-DONOR-REFERENCE-REGISTRY-001.json")
    snapshot_doc = read(donor.REGISTRY)
    snapshot = donor.ValidatedSnapshot(snapshot_doc)
    index = read(lifecycle.DEFAULT_INDEX)
    lifecycle_routes = lifecycle.validate_index(index)
    queue = validated_queue()
    read(REG / "CFA3-DONOR-SOURCE-FILE-001-TWO-PHASE-QUEUE-001.json")
    extra = read(donor.PUBLISHED_EXACT_ALIASES)
    read(donor.PUBLISHED_SOURCE_UNION)
    donor._verified_published_original_aliases(catalog)
    missing, conflicts, preserved_routes = [], [], []
    transfer_routes = {row["alias"]: row for row in snapshot_doc["locator_routes"]}

    def compare(label, result, expected):
        if result is None:
            missing.append(label)
        elif result != expected:
            conflicts.append(label)

    for position, original in enumerate(historical["entries"]):
        sid = original["donor_id"]
        row = catalog["records"][position]
        compare("historical identity:" + sid, row["donor_id"], sid)
        compare("historical status:" + sid, row["historical_status"], original["status"])
        compare("historical locator:" + sid, row["original_url"], original["source"]["locator"])
        compare("published ID:" + sid, donor.lookup_published(donor_id=sid), row)
        compare("transfer ID:" + sid, donor.lookup_snapshot(snapshot, donor_id=sid)["donor_id"], sid)

    urls = dict(catalog["lookup_by_locator"])
    urls.update({r["original_url"]: r["donor_id"] for r in extra["aliases"]})
    for url, sid in urls.items():
        row = catalog["records"][catalog["lookup_by_id"][sid]]
        compare("published URL:" + url, donor.lookup_published(original_url=url), row)
        current = donor.lookup_snapshot(snapshot, original_url=url)
        current_id = None if current is None else current["donor_id"]
        resolved = lifecycle.resolve_migrated_url(url, lifecycle_routes)
        compare("lifecycle vs transfer:" + url, resolved, current_id)
        if current_id != sid:
            route = transfer_routes.get(url, {})
            if (row["historical_status"] == "SUPERSEDED"
                    and route.get("preferred_source_id") == current_id
                    and sid in route.get("related_source_ids", [])
                    and current_id in route.get("related_source_ids", [])
                    and route.get("authority")):
                preserved_routes.append({"url": url, "historical_id": sid,
                                         "preferred_id": current_id, "authority": route["authority"]})
            else:
                compare("transfer URL:" + url, current_id, sid)

    for row in canonical["records"]:
        actual = donor.lookup_published(donor_id=row["donor_id"])
        compare("canonical registration:" + row["donor_id"],
                None if actual is None else actual["donor_registration"], row["donor_registration"])

    observations = []
    for path in sorted(REG.glob("CFA3-DONOR-SOURCE-FILE-001-PHASE1-UPSTREAM-OBSERVATIONS-*.json")):
        doc = read(path)
        for observation in doc["records"]:
            row = catalog["records"][observation["source_file_position"]]
            for key, old_key in (("donor_id", "donor_id"), ("original_url", "original_url"),
                                 ("prior_historical_decision", "historical_status")):
                compare("observation:" + observation["donor_id"] + ":" + key,
                        observation[key], row[old_key])
            observations.append(observation)
    positions = [r["source_file_position"] for r in observations]
    if len(set(positions)) != len(positions):
        conflicts.append("duplicate observation positions")

    oversized = []
    for path in sorted([*REG.glob("*DONOR*.json"), lifecycle.DEFAULT_INDEX,
                        *(ROOT / "archive/donor-source-migration").rglob("*.json")]):
        if path.stat().st_size > 996147:
            oversized.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size})

    return {
        "schema": "cfa3.donor-source-file-recovery-audit.v1",
        "scope": "SOURCE_FILE_001_PRESERVED_RECORDS_AND_PUBLISHED_LOOKUP_ONLY",
        "source_file_sequence": 1,
        "input_sha256": inputs,
        "canonical_registry_records": len(canonical["records"]),
        "source_records_read_back": len(historical["entries"]),
        "published_url_readbacks": len(urls),
        "queue_records": queue["record_count"],
        "queue_groups": {k: len(v) for k, v in queue["classification_groups"].items()},
        "historical_metadata_observations": len(observations),
        "observed_metadata_returned": sum(r["github_repository_metadata"] == "RETURNED" for r in observations),
        "observed_metadata_not_found_at_check": [r["original_url"] for r in observations
                                                if r["github_repository_metadata"] == "NOT_FOUND_AT_CHECK"],
        "observations_are_full_processing_or_current_upstream_proof": False,
        "MISSING": len(missing),
        "missing": missing,
        "UNRESOLVED_CONFLICT": len(conflicts),
        "unresolved_conflicts": conflicts,
        "preserved_supersession_routes": preserved_routes,
        "preexisting_oversize_files": oversized,
        "global_missing_owner_submissions": "UNPROVEN",
        "global_unresolved_identity_conflicts": "UNPROVEN",
        "original_frozen_L1_B": catalog["original_l1_B"],
        "lifecycle_index_complete": index["complete"],
        "L1_PUBLISHED_AND_VERIFIED_PASS": False,
        "L2_started_by_this_task": False,
        "L3_L5_started_by_this_task": False,
        "new_donor_approvals": 0,
        "donor_records_changed": 0,
        "legacy_repository_writes": 0,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(1 if report["MISSING"] or report["UNRESOLVED_CONFLICT"] else 0)
