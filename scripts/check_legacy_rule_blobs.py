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

def validate_complete_inventory(manifest, tree):
    """Verify exhaustive, path-by-path frozen blob inventory; no policy admission."""
    issues = []
    if not isinstance(manifest, dict) or not isinstance(tree, dict):
        return ["frozen inventory and tree must be objects"]
    if (manifest.get("schema") != "cfa3.legacy-frozen-tree.v1"
            or manifest.get("repository") != LEGACY_REPOSITORY
            or manifest.get("commit") != FROZEN_COMMIT):
        issues.append("frozen inventory authority mismatch")
    if (manifest.get("review_status_default") != "UNREVIEWED_RULE_APPLICABILITY"
            or manifest.get("no_files_excluded_from_rule_review") is not True):
        issues.append("unreviewed source files cannot be excluded or admitted")
    if tree.get("sha") != FROZEN_COMMIT or tree.get("truncated") is not False:
        issues.append("Git response not the complete pinned historical tree")
    entries = tree.get("tree")
    rows = manifest.get("files")
    if not isinstance(entries, list) or not isinstance(rows, list):
        return issues + ["historical tree rows not supplied"]
    if (manifest.get("blob_count") != EXPECTED_TRACKED_BLOBS or
            len(rows) != EXPECTED_TRACKED_BLOBS or
            manifest.get("tree_entry_count") != len(entries) or
            manifest.get("git_tree_truncated") is not False or
            manifest.get("file_tuple") != ["path", "git_blob_sha1", "size_bytes"]):
        issues.append("frozen tree manifest structure or count mismatch")
    blobs = {}
    for entry in entries:
        if not isinstance(entry, dict):
            issues.append("malformed Git tree element")
            continue
        if entry.get("type") != "blob":
            continue
        path, sha, size = (entry.get(k) for k in ("path", "sha", "size"))
        if (not isinstance(path, str) or not isinstance(sha, str)
                or SHA40.fullmatch(sha) is None or
                type(size) is not int or size < 0):
            issues.append("invalid Git blob record")
            continue
        if path in blobs:
            issues.append("duplicate historical Git blob")
        blobs[path] = (sha, size)
    if len(blobs) != EXPECTED_TRACKED_BLOBS:
        issues.append("frozen Git tree count mismatch")
    previous = None
    seen = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != 3:
            issues.append("malformed manifest row")
            continue
        path, sha, size = row
        if (not isinstance(path, str) or not path or
                not isinstance(sha, str) or SHA40.fullmatch(sha) is None or
                type(size) is not int or size < 0):
            issues.append("manifest row has invalid path/SHA/size")
            continue
        if path in seen or (previous is not None and path <= previous):
            issues.append("manifest paths not unique and strictly sorted")
        seen.add(path)
        previous = path
        if blobs.get(path) != (sha, size):
            issues.append("manifest path/SHA/size differs from Git tree: " + path)
    if seen != set(blobs):
        issues.append("manifest omits or invents historical Git paths")
    return issues

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
        from check_bootstrap import load as load_json
        manifest = load_json("canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json")
        observed = fetch_frozen_tree()
        issues = validate_frozen_tree(ledger, observed)
        issues.extend(validate_complete_inventory(manifest, observed))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        issues = ["frozen historical source could not be verified: " +
                  type(exc).__name__]
    if issues:
        for issue in issues:
            print("LEGACY_SOURCE_BLOB_FAIL:", issue, file=sys.stderr)
        return 1
    print("LEGACY_SOURCE_TREE_VERIFIED: 3159 Git blobs and all ledger seeds match frozen tree; "
          "NOT complete rule classification, policy admission or enforcement")
    return 0

if __name__ == "__main__":
    sys.exit(main())
