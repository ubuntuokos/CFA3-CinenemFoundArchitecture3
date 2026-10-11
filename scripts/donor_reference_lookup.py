#!/usr/bin/env python3
"""Read-only lookup of transferred donor references, candidates and historical aliases.

A donor reference is not a license, download, model, provider or runtime admission.
This does not mark the global L1 migration as complete.
"""
import argparse
import copy
import json
from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType

from donor_delta_routes import delta_aliases
from donor_transfer_integrity import preserved_aliases, validate_snapshot, verified_rejection_audit

REGISTRY = Path(__file__).resolve().parents[1] / "canonical/registries/CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"


def _freeze(value):
    """No caller-owned mutable child may survive in the validated handle."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def _detach(value):
    """Only the requested row is copied; the 8 MB snapshot is never copied per hit."""
    if isinstance(value, Mapping):
        return {key: _detach(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_detach(child) for child in value]
    return value


class ValidatedSnapshot:
    """Explicitly validated, deeply immutable batch lookup input.

    Mutable dictionaries still undergo full value validation on EVERY lookup.
    This handle first takes its own copy, then validates and freezes it; its
    lookup indexes and historical aliases cannot be poisoned by callers.
    """
    __slots__ = ("_data", "_previous", "_delta")

    def __init__(self, data):
        copied = copy.deepcopy(data)
        validate_snapshot(copied)
        self._previous = MappingProxyType(preserved_aliases(copied["records"]))
        self._delta = MappingProxyType(delta_aliases(copied["records"]))
        self._data = _freeze(copied)


def lookup_snapshot(data, *, donor_id=None, original_url=None):
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one of donor_id or original_url must be supplied")
    prepared = data if isinstance(data, ValidatedSnapshot) else None
    if prepared is None:
        validate_snapshot(data)
    else:
        verified_rejection_audit()  # fail closed if the pinned archive changed
        data = prepared._data
    def alias_id(alias):
        if prepared is not None:
            return prepared._previous.get(alias) or prepared._delta.get(alias)
        return (preserved_aliases(data["records"]).get(alias)
                or delta_aliases(data["records"]).get(alias))
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
                    "model_provider_admission": False, "rejection_history": _detach(rejected) if prepared is not None else rejected}
    if donor_id is None:
        position = data["lookup_by_locator"].get(original_url)
        if position is None:
            # Preserve original delta URL variants without introducing donor IDs.
            donor_id = alias_id(original_url)
            if donor_id is None:
                return None
        else:
            if type(position) is not int or not 0 <= position < len(data["locator_routes"]):
                raise ValueError("Corrupted locator route index")
            route = data["locator_routes"][position]
            if route["alias"] != original_url or route["preferred_source_id"] not in route["related_source_ids"]:
                raise ValueError("Inconsistent locator route")
            donor_id = route["preferred_source_id"]
    position = data["lookup_by_id"].get(donor_id)
    if position is None:
        if original_url is not None:
            raise ValueError("Resolved locator targets a missing donor identity")
        return None
    if type(position) is not int or not 0 <= position < len(data["records"]):
        raise ValueError("Corrupted donor ID index")
    envelope = data["records"][position]
    record = envelope["reference_record"]
    from transfer_donors import STATES, current_owner_confirmations, digest
    if (prepared is None and
            digest(envelope["historical_record"]) != envelope["historical_record_sha256"]):
        raise ValueError("Historical donor record digest mismatch")
    if (envelope.get("pre_transfer_status") == "OWNER_APPROVED_PENDING_PUBLICATION"
            and envelope.get("historical_record", {}).get("intake_provenance", {}).get(
                "canonical_approval_admitted") is False):
        observed = (envelope["historical_record"]["source"]["locator"],
                    envelope["historical_record_sha256"])
        if current_owner_confirmations().get(donor_id) != observed:
            raise ValueError("Pending historical donor lacks current owner confirmation")
    if (envelope["source_id"] != donor_id or record["donor_id"] != donor_id
            or envelope.get("runtime_admission") is not False
            or STATES.get(envelope.get("pre_transfer_status")) != envelope.get("reference_state")
            or record.get("donor_registration") != envelope.get("reference_state")
            or (original_url is not None and original_url not in envelope["aliases"]
                and alias_id(original_url) != donor_id)):
        raise ValueError("Inconsistent donor identity or alias")
    if any(record.get(k) is not False for k in
           ("runtime_admission", "code_copy_authorized", "license_authorized", "model_provider_admission")):
        raise ValueError("Unexpected runtime/license authority in donor reference")
    return _detach(record) if prepared is not None else record


def lookup(*, donor_id=None, original_url=None, registry_path=REGISTRY):
    """Resolve an exact canonical donor ID or an original submitted URL."""
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one of donor_id or original_url must be supplied")
    data = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    if data.get("schema") == "cfa3.donor-transfer-snapshot.v1":
        return lookup_snapshot(ValidatedSnapshot(data), donor_id=donor_id, original_url=original_url)
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
