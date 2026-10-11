#!/usr/bin/env python3
"""Read-only, independently verified search of historical donor source-file 002.

This returns the original source-union provenance, not a new donor approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "archive/donor-source-migration/2026-10-09/CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json"
PUBLISHED = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-002.json"
PIN = "d22dce8bfe3d9697a1121033ff7b387d051a638a"


def verified_catalog():
    raw = SOURCE.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if sha != PIN:
        raise ValueError("Historical second donor source changed")
    source = json.loads(raw)
    doc = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    required = {
        "schema": "cfa3.donor-source-file-publication.v1",
        "id": "CFA3-DONOR-SOURCE-FILE-002",
        "source_file_sequence": 2,
        "source_git_blob_sha": PIN,
        "publication_state": "CANONICAL_REFERENCE_SEARCHABLE_PARTIAL_L1",
        "source_count": 445,
        "unique_donor_ids": 444,
        "approved_reference_count": 444,
        "status_counts": {"ACCEPTED_REFERENCE": 444, "SUPERSEDED": 1},
        "source_set_counts": {"A": 133, "B": 312},
        "original_locator_routes": 494,
        "global_l1_completed": False,
        "original_l1_B": None,
        "no_new_approval": True,
        "historical_decisions_preserved": True,
        "runtime_admission": False,
        "code_copy_authorized": False,
        "license_authorized": False,
        "model_provider_admission": False,
        "source_records_are_existing_identities_only": True,
    }
    if any(doc.get(k) != v or type(doc.get(k)) is not type(v) for k, v in required.items()):
        raise ValueError("Second donor file publication metadata changed")
    if source.get("normalized_union_count") != 445 or doc.get("records") != source.get("source_coverage"):
        raise ValueError("Historical second source-file records changed")
    by_id, routes = {}, {}
    count = {"A": 0, "B": 0}
    statuses = {}
    for pos, row in enumerate(doc["records"]):
        source_id = row["donor_id"]
        by_id.setdefault(source_id, []).append(pos)
        if row["source_sets"] not in (["A"], ["B"]):
            raise ValueError("Invalid owner source set")
        count[row["source_sets"][0]] += 1
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
        for url in [row["canonical_locator"], *row["original_locators"]]:
            if url in routes and routes[url] != pos:
                raise ValueError("Conflicting original URL route")
            routes[url] = pos
    if (count != required["source_set_counts"]
            or statuses != required["status_counts"]
            or by_id != doc.get("lookup_by_id")
            or routes != doc.get("lookup_by_locator")):
        raise ValueError("Second file search index does not match source")
    return doc


def lookup_source_file_02(*, donor_id=None, original_url=None):
    """Search original source-file 002 by canonical donor ID or exact owner URL."""
    if (donor_id is None) == (original_url is None):
        raise ValueError("Supply exactly one donor ID or original URL")
    doc = verified_catalog()
    if donor_id is not None:
        indexes = doc["lookup_by_id"].get(donor_id, [])
        rows = [doc["records"][n] for n in indexes]
    else:
        n = doc["lookup_by_locator"].get(original_url)
        rows = [] if n is None else [doc["records"][n]]
    if not rows:
        return None
    from donor_reference_lookup import lookup_published
    for row in rows:
        record = lookup_published(donor_id=row["donor_id"])
        if (record is None or record["donor_id"] != row["donor_id"]
                or record["historical_status"] != row["status"]):
            raise ValueError("Second source file disagrees with published donor identity")
        if original_url is not None:
            resolved = lookup_published(original_url=original_url)
            if resolved is None or resolved["donor_id"] != row["donor_id"]:
                raise ValueError("Second source URL not searchable in canonical donor registry")
    return rows if donor_id is not None else rows[0]


def main():
    parser = argparse.ArgumentParser(description="Search published donor source file 002")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", dest="donor_id")
    group.add_argument("--url", dest="original_url")
    args = parser.parse_args()
    try:
        row = lookup_source_file_02(donor_id=args.donor_id, original_url=args.original_url)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if row is None:
        print("No published second-file source match", file=sys.stderr)
        return 1
    print(json.dumps(row, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
