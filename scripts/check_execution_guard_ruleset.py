#!/usr/bin/env python3
"""Fail-closed read-only verification of the real GitHub main-protection ruleset.

This does not modify GitHub settings, establish full CFA3 rule coverage,
or replace branch protection / an independent privileged gateway.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = "ubuntuokos"
REPOSITORY = "CFA3-CinenemFoundArchitecture3"
RULESET_ID = 24804719
RULESET_NAME = "CFA3-MAIN-PROTECTION"
EXPECTED_CONTEXTS = {"bootstrap", "qt68-linux"}
ACTIONS_INTEGRATION_ID = 15368

def validate_ruleset(obj, *, require_bypass_proof=True):
    errors = []
    if not isinstance(obj, dict):
        return ["ruleset must be a JSON object"]
    if obj.get("id") != RULESET_ID or obj.get("name") != RULESET_NAME:
        errors.append("wrong ruleset identity")
    if obj.get("enforcement") != "active":
        errors.append("main protection ruleset not active")
    if "bypass_actors" not in obj:
        if require_bypass_proof:
            errors.append("bypass actors unavailable: privileged Ruleset verification required")
    elif obj["bypass_actors"] != []:
        errors.append("ruleset bypass actors are not an empty list")
    refs = obj.get("conditions", {}).get("ref_name", {})
    if refs.get("include") != ["~DEFAULT_BRANCH"] or refs.get("exclude") != []:
        errors.append("ruleset default branch scope changed")
    rules = obj.get("rules")
    if not isinstance(rules, list):
        return errors + ["ruleset rules missing"]
    by_type = {}
    for item in rules:
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            errors.append("malformed ruleset rule")
            continue
        if item["type"] in by_type:
            errors.append("duplicate ruleset rule type: " + item["type"])
        by_type[item["type"]] = item
    for required in ("deletion", "non_fast_forward", "pull_request",
                     "required_status_checks"):
        if required not in by_type:
            errors.append("missing protection: " + required)
    pr = by_type.get("pull_request", {}).get("parameters", {})
    if pr.get("required_review_thread_resolution") is not True:
        errors.append("unresolved PR review threads not blocked")
    if pr.get("require_extra_approval_for_unattributed_changes") is not True:
        errors.append("unattributed change approval requirement removed")
    checks = by_type.get("required_status_checks", {}).get("parameters", {})
    if checks.get("strict_required_status_checks_policy") is not True:
        errors.append("strict required status checks disabled")
    required = checks.get("required_status_checks")
    if not isinstance(required, list):
        errors.append("required status checks missing")
    else:
        seen = set()
        for entry in required:
            if not isinstance(entry, dict):
                errors.append("invalid required check entry")
                continue
            name = entry.get("context")
            if not isinstance(name, str) or not name:
                errors.append("invalid check context")
                continue
            if name in seen:
                errors.append("duplicate required check: " + name)
            seen.add(name)
            if name in EXPECTED_CONTEXTS and entry.get("integration_id") != ACTIONS_INTEGRATION_ID:
                errors.append("required check not bound to verified GitHub Actions integration: " + name)
        if not EXPECTED_CONTEXTS.issubset(seen):
            errors.append("bootstrap/Qt 6.8 required checks incomplete")
    return errors

def fetch_ruleset():
    url = ("https://api.github.com/repos/" + OWNER + "/" + REPOSITORY +
           "/rulesets/" + str(RULESET_ID))
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CFA3-Execution-Guard-ReadOnly-Ruleset-Check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)

def main():
    # GitHub intentionally omits bypass_actors for a caller without ruleset-write
    # permission. An omitted field is UNKNOWN, not equivalent to an empty list.
    if sys.argv[1:] == ["--ci-visible"]:
        full_proof_required = False
    elif sys.argv[1:] in ([], ["--full"]):
        full_proof_required = True
    else:
        print("RULESET_GUARD_BLOCKER: expected --ci-visible or --full", file=sys.stderr)
        return 2
    try:
        response = fetch_ruleset()
        problems = validate_ruleset(response, require_bypass_proof=full_proof_required)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        problems = ["GitHub live ruleset unavailable: " + type(exc).__name__]
        response = {}
    if problems:
        for issue in problems:
            print("RULESET_GUARD_BLOCKER:", issue, file=sys.stderr)
        return 1
    if not full_proof_required:
        if "bypass_actors" not in response:
            print("RULESET_VISIBLE_PASS_BYPASS_UNVERIFIED: visible main protection "
                  "and required GitHub CI contexts verified; bypass list hidden "
                  "by insufficient GitHub API permission. Privileged --full "
                  "verification REQUIRED before full admission.")
        else:
            print("RULESET_VISIBLE_PASS: all visible protections verified, "
                  "including an empty bypass list; independent full admission "
                  "still required.")
    else:
        print("RULESET_PRIVILEGED_CONFIG_VERIFIED: verified empty bypass actor "
              "list and main required CI checks; NOT full CFA3 execution "
              "admission or physical Current Host PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
