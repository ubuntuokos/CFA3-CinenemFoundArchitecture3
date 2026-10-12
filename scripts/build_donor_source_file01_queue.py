#!/usr/bin/env python3
"""Reproducible, lossless phase queue for donor source-file 001.

This is a type prefilter only: it does NOT verify upstream freshness, make
admission decisions, crawl collections, or mark either phase complete.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json"
OUTPUT = ROOT / "canonical/registries/CFA3-DONOR-SOURCE-FILE-001-TWO-PHASE-QUEUE-001.json"
SOURCE_GIT_BLOB = "7de979fd2d975ff99573f41e4a0035a57925bb52"
HISTORICAL_GIT_BLOB = "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b"
LIMIT_BYTES = 996147
GROUPS = ("direct_candidates", "collection_candidates", "needs_classification", "non_network_references")
COLLECTION_KINDS = frozenset((
    "GITHUB_ORGANIZATION", "GITHUB_ORG", "GITHUB_PROFILE", "GITHUB_TOPIC",
    "GITHUB_CATALOG", "DISCOVERY_INDEX", "RESEARCH_DISCOVERY_INDEX", "GITHUB_MARKETPLACE"
))
DIRECT_KINDS = frozenset((
    "GITHUB", "GITHUB_REPOSITORY", "GIST", "PROJECT", "GIT", "GITLAB",
    "GITHUB_SOURCE_FILE", "GITHUB_FILE", "HUGGINGFACE_MODEL",
    "RESEARCH_PROJECT", "STANDARD", "SPECIFICATION"
))

def classify(row):
    """Conservative source-type prefilter; not a claim about website content."""
    url = row["original_url"]
    kind = row["source_kind"]
    parsed = urlsplit(url)
    if kind == "LOCAL_ENDPOINT" or parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return "non_network_references"
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "non_network_references"
    parts = [part for part in parsed.path.split("/") if part]
    collection_url = (
        parsed.hostname.lower() == "github.com" and
        (len(parts) == 1 or (len(parts) >= 2 and parts[0].lower() == "topics")
         or (len(parts) >= 3 and parts[0].lower() == "orgs"
             and parts[2].lower() == "repositories"))
    )
    if kind in COLLECTION_KINDS or collection_url:
        return "collection_candidates"
    if kind in DIRECT_KINDS:
        return "direct_candidates"
    return "needs_classification"

def build():
    raw = SOURCE.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != SOURCE_GIT_BLOB:
        raise ValueError("Published source-file 001 digest changed")
    source = json.loads(raw)
    if (source.get("source_git_blob_sha") != HISTORICAL_GIT_BLOB
            or source.get("source_file_sequence") != 1
            or source.get("source_count") != 1919
            or len(source.get("records", [])) != 1919
            or len(source.get("lookup_by_id", {})) != 1919
            or source.get("global_l1_completed") is not False):
        raise ValueError("Published historical source-file 001 changed")
    groups = {name: [] for name in GROUPS}
    for i, row in enumerate(source["records"]):
        if source["lookup_by_id"].get(row["donor_id"]) != i:
            raise ValueError("Historical source identity/index mismatch")
        groups[classify(row)].append(i)
    if sum(map(len, groups.values())) != 1919:
        raise ValueError("Every source record must be accounted for exactly once")
    return {
        "schema": "cfa3.donor-source-file-two-phase-queue.v1",
        "id": "CFA3-DONOR-SOURCE-FILE-001-TWO-PHASE-QUEUE-001",
        "source_catalog": "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json",
        "source_catalog_git_blob_sha1": SOURCE_GIT_BLOB,
        "historical_source_git_blob_sha1": HISTORICAL_GIT_BLOB,
        "source_file_sequence": 1,
        "record_count": 1919,
        "group_positions_are_zero_based_source_record_indices": True,
        "index_only_no_duplicated_donor_records": True,
        "source_ids_and_prior_owner_decisions_unchanged": True,
        "new_donor_approval": False,
        "runtime_or_license_admission": False,
        "type_prefilter_is_live_source_verification": False,
        "new_discoveries_must_pass_three_year_activity_review": True,
        "existing_historical_sources_are_not_deleted_by_freshness_filter": True,
        "unverified_activity_is_not_assumed_stale_or_active": True,
        "arbitrary_depth_or_15_percent_expansion_quota": False,
        "phase_1": {
            "name": "DIRECT_RESOURCE_VERIFICATION_CLASSIFICATION_PUBLICATION_AND_READBACK",
            "state": "PENDING_DIRECT_RESOURCE_AND_MANUAL_REVIEW",
            "includes": ["direct_candidates", "needs_classification", "non_network_references"],
            "verified_direct_sources": 0,
            "completeness_pass": False
        },
        "phase_2": {
            "name": "COLLECTION_EXPANSION_PARENT_CHILD_PROVENANCE_AND_VERIFIED_PUBLICATION",
            "state": "NOT_STARTED_REQUIRES_PHASE_1_VERIFIED_PASS",
            "includes": ["collection_candidates"],
            "crawled_collections": 0,
            "completeness_pass": False
        },
        "classification_groups": groups,
        "global_donor_database_complete": False
    }

def rendered():
    return (json.dumps(build(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")

def validated_queue():
    expected = build()
    existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if existing != expected or len(rendered()) > LIMIT_BYTES:
        raise ValueError("Source-file 001 two-phase queue mismatch or oversized")
    return existing

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = rendered()
    if len(payload) > LIMIT_BYTES:
        raise SystemExit("STOP: donor queue exceeds 0.95 MiB")
    if args.check:
        validated_queue()
        print("DONOR_SOURCE_001_PHASE_QUEUE_PASS (not source verification)")
    else:
        OUTPUT.write_bytes(payload)
        print("DONOR_SOURCE_001_PHASE_QUEUE_STAGED (not phase 1 or phase 2 PASS)")

if __name__ == "__main__":
    main()
