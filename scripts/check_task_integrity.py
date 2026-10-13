#!/usr/bin/env python3
"""Fail-closed CFA3 PR task/scope and changed-policy lifecycle CI guard.

PR body is a *task declaration*, not an independently verified owner grant.
The runner's GitHub token is read-only. Main-protection and owner approval are
independent requirements; this check never asserts seven-gate finalization.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "ubuntuokos/CFA3-CinenemFoundArchitecture3"
SCHEMA = "cfa3.task-scope.v1"
MARKER = re.compile(r"```cfa3-task\s*\n(.*?)\n```", re.S)
TASK_ID = re.compile(r"^CFA3-[A-Z0-9-]{10,120}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
SECTION = re.compile(r"^## (\d+)\. §", re.M)
APPROVED = {"OWNER_APPROVED", "OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE", "FINALIZED"}
DONOR_PREFIXES = (
    "canonical/registries/CFA3-DONOR-",
    "archive/donor", "docs/governance/donor",
)
# PRs created before the new task manifest was specified are not retroactively
# subject to its syntax, unless they modify a canonical policy or this guard.
EFFECTIVE_FROM = "2026-10-13T06:13:00Z"
GUARDED_FILES = {
    ".github/workflows/cfa3-bootstrap.yml",
    "scripts/check_task_integrity.py",
    "scripts/execution_guard.py",
    "tests/test_task_integrity.py",
}
SURFACE = "canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json"


class IntegrityError(ValueError):
    pass


def normalized_path(path):
    if not isinstance(path, str) or not path or "\\" in path:
        raise IntegrityError("invalid task path")
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or str(p) != path:
        raise IntegrityError("unsafe task path")
    return path


def strict_json(data):
    def no_duplicate(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise IntegrityError("duplicate JSON key: " + key)
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=no_duplicate)
    except (TypeError, ValueError) as exc:
        raise IntegrityError("invalid task JSON") from exc


def task_manifest(body):
    matches = MARKER.findall(body if isinstance(body, str) else "")
    if len(matches) != 1:
        raise IntegrityError("one cfa3-task JSON block is required in the PR description")
    task = strict_json(matches[0])
    required = {"schema", "task_id", "task_kind", "allowed_paths", "approval_reference"}
    if not isinstance(task, dict) or set(task) != required or task.get("schema") != SCHEMA:
        raise IntegrityError("invalid task declaration schema")
    if not isinstance(task.get("task_id"), str) or not TASK_ID.fullmatch(task["task_id"]):
        raise IntegrityError("invalid task identifier")
    if task.get("task_kind") not in ("POLICY", "POLICY_ENFORCEMENT", "DONOR", "DEVELOPMENT"):
        raise IntegrityError("invalid task kind")
    if not isinstance(task.get("approval_reference"), str) or not task["approval_reference"].strip():
        raise IntegrityError("missing owner-approval reference (not independent approval proof)")
    paths = task.get("allowed_paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths):
        raise IntegrityError("missing scoped paths")
    paths = [normalized_path(p) for p in paths]
    if len(paths) != len(set(paths)):
        raise IntegrityError("duplicate scoped paths")
    task["allowed_paths"] = set(paths)
    return task


def is_donor_record(path):
    return path.startswith(DONOR_PREFIXES) or (
        path.startswith("canonical/registries/") and "DONOR" in path
    )


def validate_scope(task, changed_paths):
    changed = set(changed_paths)
    if not changed or any(normalized_path(p) != p for p in changed):
        raise IntegrityError("empty or invalid PR diff")
    if changed != task["allowed_paths"]:
        missing = sorted(changed - task["allowed_paths"])
        extra = sorted(task["allowed_paths"] - changed)
        raise IntegrityError("task scope differs from exact PR diff: unapproved=" +
                             repr(missing) + "; undeployed=" + repr(extra))
    if task["task_kind"] in ("POLICY", "POLICY_ENFORCEMENT") and any(
        is_donor_record(p) for p in changed
    ):
        raise IntegrityError("policy task cannot modify donor records")
    if task["task_kind"] == "POLICY_ENFORCEMENT" and not changed.issubset(GUARDED_FILES):
        raise IntegrityError("enforcement-only task escaped its technical file boundary")


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise IntegrityError("exact Git state unavailable: " + " ".join(args[:2])) from exc


def local_changed_files(base_sha):
    if not isinstance(base_sha, str) or not SHA.fullmatch(base_sha):
        raise IntegrityError("invalid PR base SHA")
    # --no-renames exposes BOTH removed and added paths for a rename.
    raw = git("diff", "--name-only", "-z", "--no-renames", base_sha, "HEAD")
    try:
        return set(p for p in raw.decode("utf-8").split("\x00") if p)
    except UnicodeError as exc:
        raise IntegrityError("non-UTF-8 changed file path") from exc


def api_get(path, token):
    if not token:
        raise IntegrityError("read-only GitHub token unavailable")
    request = Request(
        "https://api.github.com/repos/" + REPO + path,
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + token,
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "CFA3-task-integrity-CI"},
    )
    try:
        with urlopen(request, timeout=20) as reply:
            return strict_json(reply.read().decode("utf-8"))
    except Exception as exc:
        raise IntegrityError("live GitHub state unavailable: " + path.split("?")[0]) from exc


def api_pages(path, token):
    result = []
    for page in range(1, 51):
        sep = "&" if "?" in path else "?"
        batch = api_get(path + sep + "per_page=100&page=" + str(page), token)
        if not isinstance(batch, list):
            raise IntegrityError("incomplete GitHub list")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise IntegrityError("GitHub PR inventory exceeds verified pagination")


def github_changed_files(number, token):
    rows = api_pages("/pulls/" + str(number) + "/files", token)
    output = set()
    for row in rows:
        p = normalized_path(row["filename"])
        output.add(p)
        if row.get("previous_filename"):
            output.add(normalized_path(row["previous_filename"]))
    return output


def validate_live_pr(event, task, changed, token):
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise IntegrityError("PR payload missing")
    number = pr.get("number")
    if type(number) is not int or number < 1:
        raise IntegrityError("invalid PR number")
    live = api_get("/pulls/" + str(number), token)
    if (live.get("number") != number or live.get("state") != "open" or
            live.get("base", {}).get("ref") != "main" or
            live.get("head", {}).get("sha") != pr.get("head", {}).get("sha") or
            live.get("base", {}).get("sha") != pr.get("base", {}).get("sha")):
        raise IntegrityError("PR identity/head/base drift")
    if github_changed_files(number, token) != changed:
        raise IntegrityError("local Git diff and live PR files disagree")
    open_prs = api_pages("/pulls?state=open", token)
    for other in open_prs:
        if other.get("number") == number:
            continue
        # Actual file intersection, not another PR's mere existence.
        if github_changed_files(other["number"], token) & changed:
            raise IntegrityError("proven cross-PR file collision with #" + str(other["number"]))
    # Body is mutable GitHub metadata. It MUST NOT be treated as proof of
    # user approval, and cannot mark the policy FINALIZED.
    if task["task_id"] not in (live.get("body") or ""):
        raise IntegrityError("live PR body lost the task identity")


def policy_paths(changed):
    for path in changed:
        if path.startswith("canonical/policies/") and path.endswith((".json", ".md")):
            yield path.removesuffix(".json").removesuffix(".md")


def validate_policy_lifecycle(changed, root=ROOT):
    for stem in sorted(set(policy_paths(changed))):
        js, md = root / (stem + ".json"), root / (stem + ".md")
        if not js.is_file() or not md.is_file():
            raise IntegrityError("changed policy has no paired JSON/Markdown: " + stem)
        policy = strict_json(js.read_text("utf-8"))
        if not isinstance(policy, dict) or policy.get("id") != Path(stem).name:
            raise IntegrityError("canonical policy ID mismatch: " + stem)
        status = policy.get("status")
        text = md.read_text("utf-8")
        matches = re.findall(r"^\*\*Státusz:\*\*\s*(.*?)\s*$", text, re.M)
        if len(matches) != 1:
            raise IntegrityError("policy missing unique visible status: " + stem)
        visible = matches[0].strip()
        if status in APPROVED and visible != "JÓVÁHAGYVA":
            raise IntegrityError("approved policy published as non-approved: " + stem)
        if status in ("DRAFT", "PENDING_APPROVAL") and visible != "JÓVÁHAGYÁSRA VÁR":
            raise IntegrityError("draft/pending policy falsely presented as approved: " + stem)
        if status == "FINALIZED":
            raise IntegrityError("seven-gate finalization cannot be independently proven in PR CI")
        count = policy.get("approved_section_count")
        if count is not None:
            sections = [int(v) for v in SECTION.findall(text)]
            if type(count) is not int or sections != list(range(1, count + 1)):
                raise IntegrityError("policy paragraph inventory changed: " + stem)
        published = policy.get("published_text_sha256")
        if published is not None and hashlib.sha256(md.read_bytes()).hexdigest() != published:
            raise IntegrityError("published policy text digest mismatch: " + stem)


def validate_registry_preservation(changed, base_sha, root=ROOT):
    if SURFACE not in changed:
        return
    try:
        original = strict_json(git("show", base_sha + ":" + SURFACE).decode("utf-8"))
        current = strict_json((root / SURFACE).read_text("utf-8"))
        old_rows = {v["path"]: v for v in original["sources"]}
        new_rows = {v["path"]: v for v in current["sources"]}
    except (KeyError, OSError, UnicodeError, TypeError) as exc:
        raise IntegrityError("canonical registry inventory unreadable") from exc
    if len(old_rows) != len(original["sources"]) or len(new_rows) != len(current["sources"]):
        raise IntegrityError("duplicate policy registry record")
    for path, row in old_rows.items():
        if path not in changed and new_rows.get(path) != row:
            raise IntegrityError("unrelated canonical rule registry record changed: " + path)


def check_event(event, changed, token, root=ROOT):
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise IntegrityError("GitHub pull_request event missing")
    if event.get("repository", {}).get("full_name") != REPO:
        raise IntegrityError("wrong repository")
    required = (pr.get("created_at", "") >= EFFECTIVE_FROM or
                any(p.startswith("canonical/policies/") or p in GUARDED_FILES
                    for p in changed))
    if not required:
        return "LEGACY_UNRELATED_PR_NOT_RETROACTIVELY_GATED"
    task = task_manifest(pr.get("body"))
    validate_scope(task, changed)
    validate_policy_lifecycle(changed, root)
    validate_registry_preservation(changed, pr["base"]["sha"], root)
    validate_live_pr(event, task, changed, token)
    return "TASK_SCOPE_AND_POLICY_LIFECYCLE_PASS_NOT_OWNER_APPROVAL_OR_FINALIZATION"


def main():
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request":
        print("TASK_INTEGRITY_NOT_APPLICABLE: PR identity is checked on PR events only")
        return 0
    try:
        file = os.environ["GITHUB_EVENT_PATH"]
        event = strict_json(Path(file).read_text("utf-8"))
        base = event["pull_request"]["base"]["sha"]
        changed = local_changed_files(base)
        result = check_event(event, changed, os.getenv("GITHUB_TOKEN"), ROOT)
        print(result)
        return 0
    except (IntegrityError, KeyError, OSError, TypeError) as exc:
        print("TASK_INTEGRITY_FAIL:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
