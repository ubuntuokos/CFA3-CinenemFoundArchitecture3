#!/usr/bin/env python3
"""Read-only CFA3 source-identity / prior-decision gate. Never fetches or registers."""
import argparse
import json
import pathlib
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

def result(state, *, source=None, **details):
    value = {"disposition": state, "automatic_code_import": False,
             "automatic_donor_registration": False, "prior_decision_overwritten": False}
    if source is not None:
        value["source_id"] = source["source_id"]
        value["prior_decision"] = source["prior_decision"]
    value.update(details)
    return value

def observation_verified(observation):
    return (isinstance(observation, dict) and
            observation.get("verification") == "VERIFIED_BY_AUTHORIZED_REVIEW" and
            isinstance(observation.get("evidence_ref"), str) and bool(observation["evidence_ref"].strip()) and
            isinstance(observation.get("checked_at"), str) and bool(observation["checked_at"].strip()))

def evaluate(url, index, observation=None):
    try:
        key = normalize_url(url)
        alias_map = validate_index(index)
    except (TypeError, ValueError, AttributeError) as exc:
        return result("BLOCKED_INDEX_CONFLICT", reason=str(exc))
    by_id = {x["source_id"]: x for x in index["source_records"]}
    source = by_id.get(alias_map[key]) if key in alias_map else None
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
    if observation.get("event") in ("VERSION_UPDATE", "FUNCTIONAL_MODERNIZATION") or (
            observation["observed_revision"] != source.get("observed_revision")):
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
