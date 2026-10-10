#!/usr/bin/env python3
"""Read-only lookup of transferred donor references, candidates and historical aliases.

A donor reference is not a license, download, model, provider or runtime admission.
This does not mark the global L1 migration as complete.
"""
import argparse
import json
from pathlib import Path
import sys

REGISTRY = Path(__file__).resolve().parents[1] / "canonical/registries/CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"


def lookup_snapshot(data, *, donor_id=None, original_url=None):
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one of donor_id or original_url must be supplied")
    if (data.get("schema") != "cfa3.donor-transfer-snapshot.v1"
            or data.get("runtime_admission") is not False
            or data.get("code_or_license_admission") is not False):
        raise ValueError("Unsafe donor transfer snapshot")
    for rejected in data["rejection_audit"]["entries"]:
        original = rejected["donor"]
        if (donor_id == original["donor_id"] or
                original_url is not None and original_url in
                (original["source"]["locator"], original["source"]["normalized_key"])):
            if original["donor_id"] in data["lookup_by_id"] or original.get("status") != "REJECTED":
                raise ValueError("Rejected source was reactivated")
            return {"donor_id": original["donor_id"], "donor_registration": "REJECTED_REFERENCE_NOT_ACTIVE",
                    "runtime_admission": False, "code_copy_authorized": False, "license_authorized": False,
                    "model_provider_admission": False, "rejection_history": rejected}
    if donor_id is None:
        position = data["lookup_by_locator"].get(original_url)
        if position is None:
            return None
        if type(position) is not int or not 0 <= position < len(data["locator_routes"]):
            raise ValueError("Corrupted locator route index")
        route = data["locator_routes"][position]
        if route["alias"] != original_url or route["preferred_source_id"] not in route["related_source_ids"]:
            raise ValueError("Inconsistent locator route")
        donor_id = route["preferred_source_id"]
    position = data["lookup_by_id"].get(donor_id)
    if position is None:
        return None
    if type(position) is not int or not 0 <= position < len(data["records"]):
        raise ValueError("Corrupted donor ID index")
    envelope = data["records"][position]
    record = envelope["reference_record"]
    from transfer_donors import STATES
    if (envelope["source_id"] != donor_id or record["donor_id"] != donor_id
            or envelope.get("runtime_admission") is not False
            or STATES.get(envelope.get("pre_transfer_status")) != envelope.get("reference_state")
            or record.get("donor_registration") != envelope.get("reference_state")
            or (original_url is not None and original_url not in envelope["aliases"])):
        raise ValueError("Inconsistent donor identity or alias")
    if any(record.get(k) is not False for k in
           ("runtime_admission", "code_copy_authorized", "license_authorized", "model_provider_admission")):
        raise ValueError("Unexpected runtime/license authority in donor reference")
    return record


def lookup(*, donor_id=None, original_url=None, registry_path=REGISTRY):
    """Resolve an exact canonical donor ID or an original submitted URL."""
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one of donor_id or original_url must be supplied")
    data = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    if data.get("schema") == "cfa3.donor-transfer-snapshot.v1":
        return lookup_snapshot(data, donor_id=donor_id, original_url=original_url)
    if data.get("schema") != "cfa3.canonical-donor-reference-registry.v1":
        raise ValueError("Unexpected canonical donor registry schema")
    if data.get("registration_state") != "PARTIAL_CANONICAL_REFERENCES_REGISTERED":
        raise ValueError("Reference registration state not recognized")
    if data.get("runtime_admission") is not False or data.get("code_or_license_admission") is not False:
        raise ValueError("Unsafe donor registry authority boundary")
    if donor_id is None:
        donor_id = data["lookup_by_original_url"].get(original_url)
        if donor_id is None:
            return None
    index = data["lookup_by_id"].get(donor_id)
    if index is None:
        return None
    records = data["records"]
    if type(index) is not int or index < 0 or index >= len(records):
        raise ValueError("Corrupted donor ID lookup index")
    record = records[index]
    if record["donor_id"] != donor_id or record.get("donor_registration") != "CANONICAL_REFERENCE_REGISTERED":
        raise ValueError("Inconsistent canonical donor lookup entry")
    if original_url is not None and original_url not in record["original_submitted_urls"]:
        raise ValueError("Original URL does not resolve to expected donor")
    if any(record.get(k) is not False for k in
           ("runtime_admission", "code_copy_authorized", "license_authorized", "model_provider_admission")):
        raise ValueError("Unexpected runtime/license authority in donor reference")
    return record


def main():
    parser = argparse.ArgumentParser(description="Read-only lookup of registered CFA3 donor references")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", dest="donor_id", help="Exact donor identifier")
    group.add_argument("--url", dest="original_url", help="Exact original submitted URL")
    args = parser.parse_args()
    try:
        record = lookup(donor_id=args.donor_id, original_url=args.original_url)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if record is None:
        print("Donor reference not found", file=sys.stderr)
        return 1
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
