#!/usr/bin/env python3
"""Check EACH recorded legacy policy-source Git blob against one frozen Git tree.

This is only source-identity verification, never policy admission or a claim
that all relevant historical rules have been classified.
"""
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LEGACY_REPOSITORY = "ubuntuokos/Final-Architecture-v3.0"
FROZEN_COMMIT = "a9c724da62bf49f3353c694990fc51443e634b4a"
EXPECTED_TRACKED_BLOBS = 3159
SHA40 = re.compile(r"^[0-9a-f]{40}$")

def validate_frozen_tree(ledger, tree):
    """Pure validation: no network; negative tests may supply synthetic trees."""
    errors = []
    if not isinstance(ledger, dict) or not isinstance(tree, dict):
        return ["ledger/tree response must be objects"]
    if ledger.get("source_repository") != LEGACY_REPOSITORY:
        errors.append("source repository not the frozen historical repository")
    if ledger.get("source_main_commit") != FROZEN_COMMIT:
        errors.append("legacy source revision changed without reconciliation")
    if tree.get("sha") != FROZEN_COMMIT:
        errors.append("Git tree response does not match frozen revision")
    if tree.get("truncated") is not False:
        errors.append("Git tree response truncated or truncation unverified")
    entries = tree.get("tree")
    if not isinstance(entries, list):
        return errors + ["Git tree entries missing"]
    blobs = {}
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("malformed Git tree entry")
            continue
        if entry.get("type") != "blob":
            continue
        path, sha = entry.get("path"), entry.get("sha")
        if (not isinstance(path, str) or not path or not isinstance(sha, str)
                or SHA40.fullmatch(sha) is None):
            errors.append("malformed Git tree blob path or SHA")
            continue
        if path in blobs:
            errors.append("duplicate blob path in frozen Git tree: " + path)
        else:
            blobs[path] = sha
    if len(blobs) != EXPECTED_TRACKED_BLOBS:
        errors.append("frozen Git tree tracked blob count mismatch")
    records = ledger.get("source_records")
    if not isinstance(records, list) or not records:
        return errors + ["legacy source ledger has no records"]
    names = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append("malformed source record at row " + str(i))
            continue
        path, sha = record.get("path"), record.get("blob_sha")
        if not isinstance(path, str) or not path:
            errors.append("missing ledger file path at row " + str(i))
            continue
        if path in names:
            errors.append("duplicate ledger path: " + path)
        names.add(path)
        if not isinstance(sha, str) or SHA40.fullmatch(sha) is None:
            errors.append("invalid 40-character Git SHA: " + path)
            continue
        if path not in blobs:
            errors.append("ledger path absent from frozen Git tree: " + path)
        elif blobs[path] != sha:
            errors.append("ledger SHA mismatches frozen Git tree: " + path)
    return errors

def fetch_frozen_tree():
    """Single immutable-source GitHub API GET; missing network means fail closed."""
    url = ("https://api.github.com/repos/" + LEGACY_REPOSITORY +
           "/git/trees/" + FROZEN_COMMIT + "?recursive=1")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CFA3-legacy-rule-source-integrity",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    from check_bootstrap import load
    try:
        ledger = load("canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json")
        issues = validate_frozen_tree(ledger, fetch_frozen_tree())
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        issues = ["frozen historical source could not be verified: " +
                  type(exc).__name__]
    if issues:
        for issue in issues:
            print("LEGACY_SOURCE_BLOB_FAIL:", issue, file=sys.stderr)
        return 1
    print("LEGACY_SOURCE_BLOB_VERIFIED: all ledger entries match pinned Git tree; "
          "NOT full historical rule inventory or policy admission")
    return 0

if __name__ == "__main__":
    sys.exit(main())
