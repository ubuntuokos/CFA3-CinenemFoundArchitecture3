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
from weakref import WeakKeyDictionary

from donor_delta_routes import delta_aliases
from donor_transfer_integrity import preserved_aliases, validate_snapshot, verified_rejection_audit

REGISTRY = Path(__file__).resolve().parents[1] / "canonical/registries/CFA3-DONOR-TRANSFER-SNAPSHOT-001.json"


def _freeze(value):
    """No caller-owned mutable child may survive in the validated handle."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(child) for child in value)
    return value


def _detach(value):
    """Only the requested row is copied; the 8 MB snapshot is never copied per hit."""
    if isinstance(value, Mapping):
        return {key: _detach(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_detach(child) for child in value]
    return value


# The registry owns every trusted handle's state. A fake object created via
# object.__new__ or a bypassed constructor is NOT registered and fails closed.
# Weak keys prevent a long-lived process from retaining discarded 8 MB handles.
_VALIDATED_HANDLES = WeakKeyDictionary()


class ValidatedSnapshot:
    """Opaque, write-once validated handle for safe indexed batch reads.

    A tuple subclass is unsafe here: tuple.__new__ bypasses validation. Instances
    have no mutable fields; only the authentic constructor can add their private,
    deeply frozen lookup state to the identity-keyed weak registry.
    """
    __slots__ = ("__weakref__",)

    def __new__(cls, data):
        if cls is not ValidatedSnapshot:
            raise TypeError("ValidatedSnapshot does not allow subclasses")
        copied = copy.deepcopy(data)
        validate_snapshot(copied)
        previous = MappingProxyType(preserved_aliases(copied["records"]))
        delta = MappingProxyType(delta_aliases(copied["records"]))
        handle = object.__new__(cls)
        _VALIDATED_HANDLES[handle] = (_freeze(copied), previous, delta)
        return handle

    def _trusted(self):
        state = _VALIDATED_HANDLES.get(self)
        if state is None:
            raise ValueError("Unvalidated donor snapshot handle")
        return state

    @property
    def _data(self):
        return self._trusted()[0]

    @property
    def _previous(self):
        return self._trusted()[1]

    @property
    def _delta(self):
        return self._trusted()[2]


def lookup_snapshot(data, *, donor_id=None, original_url=None):
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one of donor_id or original_url must be supplied")
    if isinstance(data, ValidatedSnapshot) and type(data) is not ValidatedSnapshot:
        raise ValueError("Unvalidated donor snapshot handle subclass")
    prepared = data if type(data) is ValidatedSnapshot else None
    if prepared is None:
        validate_snapshot(data)
    else:
        # Accessing the trusted registry MUST precede the fast path. Constructor
        # bypass and malformed cloned handles have no entry and are rejected.
        data = prepared._data
        verified_rejection_audit()  # fail closed if the pinned archive changed
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
        current = lookup_snapshot(ValidatedSnapshot(data), donor_id=donor_id,
                                  original_url=original_url)
        if current is not None or Path(registry_path).resolve() != REGISTRY.resolve():
            return current
        # Existing canonical sources always win. Unmerged PR545 records are
        # searchable as NON-ADMITTED proposals only, never transfer mutations.
        from donor_unmerged_proposals import lookup_proposal
        return lookup_proposal(donor_id=donor_id, original_url=original_url)
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



# A source-file publication is searchable independently of global L1 admission.
# The legacy transfer snapshot remains available through the unchanged default path.
PUBLISHED_FIRST = Path(__file__).resolve().parents[1] / (
    "canonical/registries/CFA3-DONOR-SOURCE-FILE-001.json"
)
PUBLISHED_FIRST_ARCHIVE = Path(__file__).resolve().parents[1] / (
    "archive/donor-source-migration/2026-10-09/FA3-DONOR-REFERENCE-REGISTRY-001.json"
)

PUBLISHED_SOURCE_UNION = Path(__file__).resolve().parents[1] / (
    "archive/donor-source-migration/2026-10-09/CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json"
)
PUBLISHED_EXACT_ALIASES = Path(__file__).resolve().parents[1] / (
    "canonical/registries/CFA3-DONOR-PUBLISHED-ORIGINAL-URL-ALIASES-20261012.json"
)


def _verified_published_original_aliases(doc):
    """Verify every A/B source URL and the exact 15 missing routes, fail closed."""
    import hashlib

    def blob_sha(raw):
        return hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()

    union_raw = PUBLISHED_SOURCE_UNION.read_bytes()
    catalog_raw = PUBLISHED_FIRST.read_bytes()
    union_pin = "d22dce8bfe3d9697a1121033ff7b387d051a638a"
    catalog_pin = "7de979fd2d975ff99573f41e4a0035a57925bb52"
    if blob_sha(union_raw) != union_pin or blob_sha(catalog_raw) != catalog_pin:
        raise ValueError("Published donor source or original URL evidence changed")
    if json.loads(catalog_raw) != doc:
        raise ValueError("Published donor catalog changed during alias lookup")
    union = json.loads(union_raw)
    supplement = json.loads(PUBLISHED_EXACT_ALIASES.read_text(encoding="utf-8"))
    if (union.get("schema") != "cfa3.donor-baseline-user-source-union.v1"
            or union.get("normalized_union_count") != 445
            or supplement.get("schema") != "cfa3.donor-published-original-url-alias-supplement.v1"
            or supplement.get("id") != "CFA3-DONOR-PUBLISHED-ORIGINAL-URL-ALIASES-20261012"
            or supplement.get("publication_state") != "CANONICAL_REFERENCE_URL_SEARCH_EXTENSION"
            or supplement.get("publication_scope") != "TWO_RECOVERED_OWNER_SOURCE_FILES_ONLY"
            or supplement.get("historical_union_git_blob_sha") != union_pin
            or supplement.get("first_published_catalog_git_blob_sha") != catalog_pin
            or supplement.get("historical_source_url_counts") != {"A": 133, "B": 312}
            or supplement.get("already_searchable_urls") != 430
            or supplement.get("added_exact_url_alias_count") != 15
            or supplement.get("alias_registration_only") is not True
            or supplement.get("existing_donor_id_and_status_preserved") is not True
            or supplement.get("global_l1_completed") is not False
            or any(supplement.get(key) is not False for key in (
                "new_owner_donor_approval", "runtime_admission", "code_copy_authorized",
                "license_authorized", "model_provider_admission"))):
        raise ValueError("Donor original URL alias scope or authority changed")

    existing = doc["lookup_by_locator"]
    by_id = doc["lookup_by_id"]
    records = doc["records"]
    expected = []
    seen = set()
    source_counts = {"A": 0, "B": 0}
    for item in union["source_coverage"]:
        url, source_id = item["canonical_locator"], item["donor_id"]
        sets = item["source_sets"]
        if (url in seen or sets not in (["A"], ["B"])
                or source_id not in by_id
                or type(by_id[source_id]) is not int
                or not 0 <= by_id[source_id] < len(records)):
            raise ValueError("Original URL coverage has duplicate or unknown donor")
        seen.add(url)
        source_counts[sets[0]] += 1
        donor = records[by_id[source_id]]
        if (donor["donor_id"] != source_id
                or donor["historical_status"] != item["status"]
                or donor["normalized_key"] != item["normalized_key"]
                or donor["donor_registration"] != (
                    "CANONICAL_REFERENCE_REGISTERED" if item["status"] == "ACCEPTED_REFERENCE"
                    else "NOT_CANONICALLY_REGISTERED")):
            # Superseded and non-accepted sources must never be promoted.
            if item["status"] == "ACCEPTED_REFERENCE" or donor["donor_registration"] == "CANONICAL_REFERENCE_REGISTERED":
                raise ValueError("Original URL alias would change a donor decision")
        route = existing.get(url)
        if route is not None:
            if route != source_id:
                raise ValueError("Original URL conflicts with an existing canonical identity")
        else:
            expected.append({
                "original_url": url, "donor_id": source_id,
                "source_set": sets[0], "historical_status": item["status"]
            })
    if (len(seen) != 445 or source_counts != {"A": 133, "B": 312}
            or len(expected) != 15
            or sorted(expected, key=lambda x: x["original_url"]) != sorted(
                supplement.get("aliases", []), key=lambda x: x["original_url"])):
        raise ValueError("Published donor original URL alias coverage mismatch")
    return {item["original_url"]: item["donor_id"] for item in expected}



def lookup_published(*, donor_id=None, original_url=None):
    """Read the first canonically available file, excluding other staged sources."""
    if (donor_id is None) == (original_url is None):
        raise ValueError("Exactly one donor ID or original URL is required")
    import hashlib
    doc = json.loads(PUBLISHED_FIRST.read_text(encoding="utf-8"))
    raw = PUBLISHED_FIRST_ARCHIVE.read_bytes()
    old_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    records = doc.get("records", [])
    index = doc.get("lookup_by_id", {})
    routes = doc.get("lookup_by_locator", {})
    if (doc.get("schema") != "cfa3.donor-source-file-publication.v1"
            or doc.get("source_file_sequence") != 1
            or doc.get("source_git_blob_sha") != old_blob
            or old_blob != "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b"
            or doc.get("publication_state") != "CANONICAL_REFERENCE_SEARCHABLE_PARTIAL_L1"
            or doc.get("global_l1_completed") is not False
            or doc.get("runtime_admission") is not False
            or len(records) != doc.get("source_count") or len(records) != 1919
            or len(index) != 1919 or len(routes) != 1997
            or doc.get("alias_index_size") != len(routes)):
        raise ValueError("Published donor source-file integrity check failed")
    supplementary_alias = False
    if original_url is not None:
        donor_id = routes.get(original_url)
        if donor_id is None:
            donor_id = _verified_published_original_aliases(doc).get(original_url)
            supplementary_alias = donor_id is not None
            if donor_id is None:
                return None
    position = index.get(donor_id)
    if position is None:
        return None
    if type(position) is not int or not 0 <= position < len(records):
        raise ValueError("Invalid published donor index entry")
    row = records[position]
    if (row.get("donor_id") != donor_id
            or (original_url is not None and not supplementary_alias
                and original_url not in row.get("lookup_aliases", []))
            or row.get("runtime_admission") is not False
            or row.get("code_copy_authorized") is not False
            or row.get("license_authorized") is not False
            or row.get("model_provider_admission") is not False):
        raise ValueError("Inconsistent published donor record")
    return row

def main():
    parser = argparse.ArgumentParser(description="Read-only lookup of registered CFA3 donor references")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", dest="donor_id", help="Exact donor identifier")
    group.add_argument("--url", dest="original_url", help="Exact original submitted URL")
    parser.add_argument("--published-only", action="store_true",
                        help="Search only canonically published donor source files")
    args = parser.parse_args()
    try:
        query = lookup_published if args.published_only else lookup
        record = query(donor_id=args.donor_id, original_url=args.original_url)
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
