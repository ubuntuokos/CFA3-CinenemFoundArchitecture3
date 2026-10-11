#!/usr/bin/env python3
"""Read-only CFA3 source-identity / prior-decision gate. Never fetches or registers."""
import argparse
import json
import pathlib
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from donor_delta_routes import delta_aliases
from donor_transfer_integrity import (verified_snapshot, confirmation_evidence,
                                      TRANSFER_NAME, CONFIRMATION_NAME)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json"
TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid"}

def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a nonempty string")
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only absolute HTTP(S) source URLs are accepted")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credential-bearing URLs are not accepted")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid source port") from exc
    host = parsed.hostname.lower().rstrip(".")
    if host.startswith("www.") and host[4:] == "github.com":
        host = "github.com"
    if not host or any(c.isspace() for c in host):
        raise ValueError("Invalid host")
    if ":" in host and not host.startswith("["):
        host = "[" + host + "]"
    if port and not ((parsed.scheme.lower() == "http" and port == 80) or
                     (parsed.scheme.lower() == "https" and port == 443)):
        host += ":" + str(port)
    path = parsed.path.rstrip("/") or "/"
    if host == "github.com":
        sections = path.strip("/").split("/")
        if len(sections) == 2 and sections[1].endswith(".git"):
            sections[1] = sections[1][:-4]
        path = "/" + "/".join(sections).lower()
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in TRACKING]
    return urlunsplit(("https" if host == "github.com" else parsed.scheme.lower(),
                       host, path, urlencode(query), ""))

def validate_index(index):
    if isinstance(index, dict) and index.get("schema") == "cfa3.source-lifecycle-index.v2":
        return validate_migrated_index(index)
    if not isinstance(index, dict) or index.get("schema") != "cfa3.source-lifecycle-index.v1":
        raise ValueError("Source index schema missing or wrong")
    if not isinstance(index.get("complete"), bool) or not isinstance(index.get("source_records"), list):
        raise ValueError("Index must explicitly declare completeness and a record list")
    names, urls = set(), {}
    for record in index["source_records"]:
        sid = record.get("source_id")
        decision = record.get("prior_decision")
        if not isinstance(sid, str) or not sid or sid in names:
            raise ValueError("Missing or duplicated source_id")
        names.add(sid)
        if not isinstance(decision, dict) or not all(decision.get(k) for k in ("decision_id", "revision", "outcome")):
            raise ValueError("Missing previous decision record")
        if not isinstance(record.get("canonical_url"), str):
            raise ValueError("Missing canonical URL")
        aliases = record.get("aliases", [])
        if not isinstance(aliases, list):
            raise ValueError("Aliases must be a list")
        for locator in [record["canonical_url"], *aliases]:
            key = normalize_url(locator)
            if key in urls and urls[key] != sid:
                raise ValueError("Conflicting source identities for " + key)
            urls[key] = sid
    return urls

def validate_migrated_index(index):
    """Validate explicit historical routes without collapsing related identities."""
    if index.get("complete") is not False or index.get("global_l1_completed") is not False:
        raise ValueError("Migrated reference lookup cannot certify global completeness")
    records, routes = index.get("source_records"), index.get("locator_routes")
    if not isinstance(records, list) or not isinstance(routes, list):
        raise ValueError("Missing migrated records or routes")
    transfer, transfer_sha = verified_snapshot()
    confirmations, confirmation_sha = confirmation_evidence()
    inputs = index.get("input_sha256", {})
    if inputs.get(TRANSFER_NAME) != transfer_sha:
        raise ValueError("Lifecycle transfer-file digest mismatch")
    if inputs.get(CONFIRMATION_NAME) != confirmation_sha:
        raise ValueError("Lifecycle owner-confirmation digest mismatch")
    history = {row["source_id"]: row for row in transfer["records"]}
    names = set()
    for record in records:
        sid, decision = record.get("source_id"), record.get("prior_decision")
        if not isinstance(sid, str) or not sid or sid in names:
            raise ValueError("Missing or duplicated source_id")
        names.add(sid)
        if not isinstance(record.get("canonical_url"), str) or not record["canonical_url"]:
            raise ValueError("Missing historical source locator")
        if not isinstance(decision, dict) or not all(decision.get(k) for k in ("decision_id", "revision", "outcome")):
            raise ValueError("Missing prior decision provenance")
        if record.get("runtime_admission") is not False:
            raise ValueError("Lookup cannot grant runtime admission")
        archived = history.get(sid)
        if (archived is None or decision["revision"] != archived["historical_record_sha256"]
                or record.get("reference_state") != archived["reference_state"]
                or decision.get("canonical_reference_registration") != archived["reference_record"]):
            raise ValueError("Lifecycle decision differs from preserved donor history")
        if sid in confirmations and decision.get("owner_approval") != confirmations[sid]:
            raise ValueError("Lifecycle decision lacks current owner confirmation")
    if names != set(history):
        raise ValueError("Lifecycle donor identity coverage mismatch")
    exact = {}
    for route in routes:
        alias, preferred = route.get("alias"), route.get("preferred_source_id")
        related = route.get("related_source_ids")
        if (not isinstance(alias, str) or not alias or alias in exact
                or not isinstance(related, list) or not related
                or any(sid not in names for sid in related)
                or len(set(related)) != len(related) or preferred not in related
                or not route.get("authority")):
            raise ValueError("Invalid historical locator route")
        exact[alias] = preferred
    if any(r["canonical_url"] not in exact for r in records):
        raise ValueError("Historical source locator is not routed")
    if index.get("active_reference_snapshot") == "CFA3-DONOR-TRANSFER-SNAPSHOT-001":
        for alias, sid in delta_aliases(records).items():
            if alias in exact and exact[alias] != sid:
                raise ValueError("Historical delta URL conflicts with canonical locator route")
            exact[alias] = sid
    return exact

def resolve_migrated_url(url, exact):
    # Original URL spelling is authoritative. Normalization may be used only
    # when all matching historical routes select the same preferred identity.
    if url in exact:
        return exact[url]
    key = normalize_url(url)
    matches = set()
    for alias, sid in exact.items():
        try:
            if normalize_url(alias) == key:
                matches.add(sid)
        except ValueError:
            continue  # non-HTTP source keys are preserved, not fabricated URLs
    if len(matches) > 1:
        raise ValueError("Normalized URL matches different historical decisions")
    return next(iter(matches), None)

def transferred_snapshot():
    """Unmodified archival data; never an authority for runtime admission."""
    return verified_snapshot()[0]


def historical_rejections():
    """Exact rejected identities remain blocked but searchable as decisions."""
    transfer = transferred_snapshot()
    routes = {}
    for history in transfer["rejection_audit"]["entries"]:
        item = history["donor"]
        sid = item["donor_id"]
        if item.get("status") != "REJECTED" or sid in transfer["lookup_by_id"]:
            raise ValueError("Invalid rejected-source history or active reentry")
        source = {
            "source_id": sid,
            "prior_decision": {
                "decision_id": "preserved-rejection:" + sid,
                "outcome": "REJECTED",
                "historical_rejection": history,
            },
            "runtime_admission": False,
        }
        for locator in (item["source"]["locator"], item["source"]["normalized_key"]):
            if locator in routes and routes[locator]["source_id"] != sid:
                raise ValueError("Conflicting historical rejection locators")
            routes[locator] = source
    return routes


def historical_upstream_evidence():
    """Use exact preserved records; never infer a current upstream revision."""
    transfer = transferred_snapshot()
    keys = ("upstream_snapshot", "upstream_observation", "source_snapshot",
            "observed_commit", "upstream_repository_references", "notes")
    return {
        row["source_id"]: (
            row["historical_record_sha256"],
            {key: row["historical_record"][key] for key in keys
             if key in row["historical_record"]})
        for row in transfer["records"]
    }


def note_revisions(notes):
    """Conservative fallback: explicit upstream/inspected commits, never PR SHAs.

    Keep all notes in the response; ambiguous revisions do not authorize reuse.
    Structured observations take precedence over separately dated note snapshots.
    """
    if isinstance(notes, str):
        notes = [notes]
    if not isinstance(notes, list):
        return set()
    revisions = set()
    for note in notes:
        if not isinstance(note, str):
            continue
        for sentence in re.split(r"(?<=[.;])\s+", note):
            if not (re.search(r"\bupstream\b", sentence, re.I)
                    or re.match(r"Inspected commit\b", sentence, re.I)):
                continue
            if re.search(r"\b(?:PR|pull request|donor.intake)\s*#?\d", sentence, re.I):
                continue
            revisions.update(v.lower() for v in re.findall(
                r"(?<![a-zA-Z0-9])[a-fA-F0-9]{40}(?![a-zA-Z0-9])", sentence))
    return revisions


def result(state, *, source=None, **details):
    value = {"disposition": state, "automatic_code_import": False,
             "automatic_donor_registration": False, "prior_decision_overwritten": False}
    if source is not None:
        value["source_id"] = source["source_id"]
        prior = source["prior_decision"]
        if "reference_state" in source:  # migrated v2 source
            archived = historical_upstream_evidence().get(source["source_id"])
            if archived is not None and archived[0] == prior.get("revision"):
                prior = {**prior, "historical_upstream_evidence": archived[1]}
        value["prior_decision"] = prior
    value.update(details)
    return value

def observation_verified(observation):
    return (isinstance(observation, dict) and
            observation.get("verification") == "VERIFIED_BY_AUTHORIZED_REVIEW" and
            isinstance(observation.get("evidence_ref"), str) and bool(observation["evidence_ref"].strip()) and
            isinstance(observation.get("checked_at"), str) and bool(observation["checked_at"].strip()))

def evaluate(url, index, observation=None):
    try:
        alias_map = validate_index(index)
        migrated = index.get("schema") == "cfa3.source-lifecycle-index.v2"
        if migrated:
            rejected = historical_rejections().get(url)
            if rejected is not None:
                return result("BLOCKED_REJECTED_SOURCE", source=rejected,
                              action="PRESERVE_REJECTION_NO_REACTIVATION")
            # Exact historical locators include non-HTTP project:* identifiers.
            sid = resolve_migrated_url(url, alias_map)
            key = normalize_url(url) if sid is None else None
        else:
            key = normalize_url(url)
            sid = alias_map.get(key)
    except (TypeError, ValueError, AttributeError, KeyError, OSError) as exc:
        return result("BLOCKED_INDEX_CONFLICT", reason=str(exc))
    by_id = {x["source_id"]: x for x in index["source_records"]}
    source = by_id.get(sid)
    if observation is not None and not observation_verified(observation):
        return result("BLOCKED_UNVERIFIED_OBSERVATION", source=source)
    if source is None:
        if observation and observation.get("event") == "RELOCATED":
            previous = by_id.get(observation.get("previous_source_id"))
            if previous is None:
                return result("BLOCKED_UNVERIFIED_RELOCATION")
            if key in alias_map:
                return result("BLOCKED_INDEX_CONFLICT", reason="Relocation collides with another source")
            return result("RELOCATION_REVIEW_REQUIRED", source=previous,
                          proposed_new_url=key, operation="APPEND_VERIFIED_ALIAS_AFTER_APPROVAL")
        if not index["complete"]:
            return result("BLOCKED_INDEX_INCOMPLETE", reason="Cannot prove source was never processed")
        return result("NEW_SOURCE_ANALYSIS_ALLOWED", normalized_url=key,
                      action="ANALYZE_WITHOUT_AUTOMATIC_DONOR_ADMISSION")
    if observation is None:
        return result("CHANGE_CHECK_REQUIRED", source=source,
                      action="VERIFY_UPSTREAM_BEFORE_REUSING_PRIOR_DECISION")
    if observation.get("previous_source_id") and observation["previous_source_id"] != source["source_id"]:
        return result("BLOCKED_INDEX_CONFLICT", source=source, reason="Observation uses another source identity")
    if observation.get("event") == "RELOCATED":
        return result("RELOCATION_REVIEW_REQUIRED", source=source,
                      action="APPEND_VERIFIED_RELOCATION_RECORD_KEEP_DECISION")
    support = observation.get("support_status")
    if support not in ("SUPPORTED", "UNMAINTAINED", "UNKNOWN"):
        return result("BLOCKED_UNVERIFIED_OBSERVATION", source=source,
                      reason="Verified observation must classify upstream support")
    if support == "UNMAINTAINED":
        rights = observation.get("rights", source.get("rights", {}))
        may_reuse = isinstance(rights, dict) and rights.get("verified") is True and rights.get("may_modify_and_distribute") is True
        return result("REPLACEMENT_PLAN_REQUIRED", source=source,
                      replacement_strategy=("MODERNIZE_AND_ADAPT_TO_CFA3_AFTER_RIGHTS_REVIEW"
                                            if may_reuse else "INDEPENDENT_CFA3_REPLACEMENT_NO_CODE_IMPORT"),
                      action="VERIFY_RETAINED_CAPABILITY_AND_REQUEST_IMPLEMENTATION_APPROVAL")
    if support == "UNKNOWN":
        return result("CHANGE_CHECK_REQUIRED", source=source, reason="Upstream support remains unknown")
    if not isinstance(observation.get("observed_revision"), str) or not observation["observed_revision"]:
        return result("BLOCKED_UNVERIFIED_OBSERVATION", source=source, reason="No upstream revision proof")
    previous_revision = source.get("observed_revision")
    if previous_revision is None and "reference_state" in source:
        archived = historical_upstream_evidence().get(source["source_id"])
        if archived is not None and archived[0] == source["prior_decision"].get("revision"):
            evidence = archived[1]
            versions = []
            upstream = evidence.get("upstream_snapshot")
            if isinstance(upstream, dict):
                if upstream.get("checked_at") and upstream.get("source") == "GitHub repository API":
                    versions.append(upstream.get("commit_sha"))
                if upstream.get("observed_at"):
                    versions.append(upstream.get("head_sha"))
            snapshot = evidence.get("source_snapshot")
            if isinstance(snapshot, dict) and snapshot.get("observed_at"):
                versions.extend((snapshot.get("commit"), snapshot.get("default_branch_commit")))
            versions.append(evidence.get("observed_commit"))
            revisions = {v.lower() for v in versions
                         if isinstance(v, str) and len(v) == 40
                         and all(c in "0123456789abcdefABCDEF" for c in v)}
            if not revisions:
                revisions = note_revisions(evidence.get("notes", []))
            if len(revisions) == 1:
                previous_revision = next(iter(revisions))
    if observation.get("event") in ("VERSION_UPDATE", "FUNCTIONAL_MODERNIZATION") or (
            observation["observed_revision"] != previous_revision):
        return result("CHANGE_REVIEW_REQUIRED", source=source,
                      new_revision=observation["observed_revision"],
                      action="APPEND_ASSESSMENT_KEEP_PREVIOUS_DECISION")
    return result("REUSE_PRIOR_DECISION", source=source,
                  action="NO_REANALYSIS_OR_DECISION_OVERRIDE")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="External source URL")
    parser.add_argument("--index", type=pathlib.Path, default=DEFAULT_INDEX)
    parser.add_argument("--observation", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        index = json.loads(args.index.read_text(encoding="utf-8"))
        observation = (json.loads(args.observation.read_text(encoding="utf-8"))
                       if args.observation else None)
        outcome = evaluate(args.url, index, observation)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        outcome = result("BLOCKED_INDEX_UNAVAILABLE", reason=str(exc))
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    disposition = outcome["disposition"]
    if disposition in ("NEW_SOURCE_ANALYSIS_ALLOWED", "REUSE_PRIOR_DECISION"):
        return 0
    if disposition.endswith("_REQUIRED"):
        return 3
    return 2

if __name__ == "__main__":
    sys.exit(main())
