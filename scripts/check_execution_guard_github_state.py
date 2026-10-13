#!/usr/bin/env python3
"""Read-only GitHub exact-state evidence for CFA3 Execution Guard.

This checks actual REST and GraphQL responses. A verified GitHub snapshot is
NOT owner scope approval, runtime gate admission or authorization to write.
All privileged credentials must remain in a separately controlled service.
"""
import json
import re
from urllib.request import Request, urlopen

from check_execution_guard_ruleset import validate_ruleset
from check_execution_guard_owner_grant import verify_owner_grant, OwnerGrantBlocked

OWNER = "ubuntuokos"
REPO = "CFA3-CinenemFoundArchitecture3"
RULESET = 24804719
REQUIRED = {"bootstrap", "qt68-linux"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class LiveStateBlocked(RuntimeError):
    pass

def _sha(value):
    return isinstance(value, str) and SHA40.fullmatch(value) is not None

def validate_snapshot(task, snapshot):
    """Pure, replayable negative gates. Snapshots must come from the trusted reader."""
    if not isinstance(task, dict) or not isinstance(snapshot, dict):
        raise LiveStateBlocked("missing task or trusted live snapshot")
    main = snapshot.get("main")
    pr = snapshot.get("target_pr")
    ruleset = snapshot.get("ruleset")
    open_prs = snapshot.get("open_prs")
    runs = snapshot.get("head_checks")
    threads = snapshot.get("review_threads")
    if not (_sha(main) and isinstance(pr, dict) and isinstance(open_prs, list)
            and isinstance(runs, list) and isinstance(threads, list)):
        raise LiveStateBlocked("incomplete GitHub snapshot")
    if task.get("operation") not in ("REPOSITORY_WRITE", "WORKFLOW_START"):
        raise LiveStateBlocked("GitHub live verifier only covers branch operations")
    if task.get("main_sha") != main:
        raise LiveStateBlocked("target main changed")
    head = pr.get("head_sha")
    branch = pr.get("head_ref")
    number = pr.get("number")
    if (not _sha(head) or head != task.get("head_sha")
            or branch != task.get("branch") or type(number) is not int or number < 1
            or pr.get("base_ref") != "main" or pr.get("base_sha") != main
            or pr.get("state") != "open"):
        raise LiveStateBlocked("target PR head, base, state or branch drift")
    if snapshot.get("target_branch_commit") != head:
        raise LiveStateBlocked("target branch ref changed")
    if validate_ruleset(ruleset, require_bypass_proof=True):
        raise LiveStateBlocked("required full Ruleset protection cannot be verified")
    if any(type(x) is not bool for x in threads):
        raise LiveStateBlocked("review thread data unavailable")
    if any(not x for x in threads):
        raise LiveStateBlocked("unresolved review thread")
    checked = set()
    for run in runs:
        if not isinstance(run, dict):
            raise LiveStateBlocked("invalid GitHub check run")
        name = run.get("name")
        if name in REQUIRED:
            if name in checked:
                raise LiveStateBlocked("ambiguous duplicate required check")
            checked.add(name)
            if (run.get("head_sha") != head or run.get("status") != "completed"
                or run.get("conclusion") != "success" or run.get("app_id") != 15368):
                raise LiveStateBlocked("failed or foreign required check: " + name)
    if checked != REQUIRED:
        raise LiveStateBlocked("required check missing for exact head")
    targets = task.get("scope_targets")
    if (not isinstance(targets, list) or not targets
            or any(not isinstance(x, str) or not x for x in targets)
            or len(set(targets)) != len(targets)):
        raise LiveStateBlocked("invalid scoped changed-file list")
    target_files = set(targets)
    listed_numbers = set()
    seen_self = False
    for row in open_prs:
        if not isinstance(row, dict) or type(row.get("number")) is not int:
            raise LiveStateBlocked("incomplete open PR inventory")
        n = row["number"]
        if n in listed_numbers:
            raise LiveStateBlocked("duplicated open PR")
        listed_numbers.add(n)
        files = row.get("changed_files")
        if not isinstance(files, list) or any(not isinstance(f, str) for f in files):
            raise LiveStateBlocked("open PR changed file inventory unavailable")
        if len(set(files)) != len(files):
            raise LiveStateBlocked("ambiguous changed files")
        if n == number:
            seen_self = True
            if row.get("head_sha") != head:
                raise LiveStateBlocked("target PR changed during collision verification")
            if task["target"] not in files:
                raise LiveStateBlocked("target is not a changed file on target PR")
            if set(files) != target_files:
                raise LiveStateBlocked("target PR files differ from signed exact scope")
        elif target_files.intersection(files):
            raise LiveStateBlocked("concurrent PR modifies an in-scope file")
    if not seen_self:
        raise LiveStateBlocked("target PR absent from complete open PR listing")
    return {
        "main_current": True, "head_current": True, "no_overlap": True,
        "checks_passed": True, "review_threads_clear": True,
        "main_ruleset_verified": True,
        "privileged_bypass_actors_verified": True,
        "actual_main_sha": main, "actual_head_sha": head,
        # Authorization cannot come from GitHub state, an AI, or this verifier.
        "owner_scope_approved": False,
    }

def _verified_changed_paths(file_rows, expected_count):
    """Expand rename paths only after the complete GitHub PR file inventory is proven."""
    if type(expected_count) is not int or not 0 < expected_count < 3000:
        raise LiveStateBlocked("PR changed-file count unavailable or at GitHub API cap")
    if not isinstance(file_rows, list) or len(file_rows) != expected_count:
        raise LiveStateBlocked("PR file inventory incomplete or changed")
    paths = []
    for row in file_rows:
        if not isinstance(row, dict) or not isinstance(row.get("filename"), str) or not row["filename"]:
            raise LiveStateBlocked("invalid PR filename")
        paths.append(row["filename"])
        previous = row.get("previous_filename")
        if row.get("status") == "renamed" and previous is None:
            raise LiveStateBlocked("renamed PR file missing source path")
        if previous is not None:
            if not isinstance(previous, str) or not previous:
                raise LiveStateBlocked("invalid previous PR filename")
            paths.append(previous)
    return paths

class TrustedGithubReader:
    """Synchronous read-only API client. The owner must isolate its token."""
    def __init__(self, token):
        if not isinstance(token, str) or not token.strip():
            raise LiveStateBlocked("GitHub read-only token not provisioned")
        self.token = token

    def request(self, path, graphql=None):
        if graphql is None:
            url = "https://api.github.com/repos/" + OWNER + "/" + REPO + path
            data = None
        else:
            url = "https://api.github.com/graphql"
            data = json.dumps({"query": graphql["query"], "variables": graphql["variables"]}).encode()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "CFA3-Execution-Guard-Live-Read",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        req = Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
        try:
            with urlopen(req, timeout=20) as response:
                parsed = json.load(response)
        except Exception as exc:
            raise LiveStateBlocked("fresh GitHub read failed") from exc
        if not isinstance(parsed, (dict, list)):
            raise LiveStateBlocked("GitHub response invalid")
        return parsed

    def pages(self, path, key=None):
        """Never infer completion when the API truncated the paged listing."""
        rows = []
        for page in range(1, 51):
            sep = "&" if "?" in path else "?"
            reply = self.request(path + sep + "per_page=100&page=" + str(page))
            values = reply.get(key) if key and isinstance(reply, dict) else reply
            if not isinstance(values, list):
                raise LiveStateBlocked("GitHub pagination response invalid")
            rows.extend(values)
            if len(values) < 100:
                return rows
        raise LiveStateBlocked("GitHub pagination limit reached")

    def review_threads(self, number):
        query = """query($owner:String!,$repo:String!,$pr:Int!,$cursor:String) {
          repository(owner:$owner,name:$repo) {pullRequest(number:$pr) {
            reviewThreads(first:100,after:$cursor) {
              pageInfo {hasNextPage endCursor}
              nodes {isResolved}
            }}}}"""
        verdicts = []
        cursor = None
        for _ in range(50):
            response = self.request("", graphql={"query": query, "variables": {
                "owner": OWNER, "repo": REPO, "pr": number, "cursor": cursor}})
            if not isinstance(response, dict) or response.get("errors"):
                raise LiveStateBlocked("review-thread GraphQL access denied")
            try:
                section = response["data"]["repository"]["pullRequest"]["reviewThreads"]
                nodes, page = section["nodes"], section["pageInfo"]
                if not isinstance(nodes, list):
                    raise ValueError()
                for n in nodes:
                    if not isinstance(n, dict) or type(n.get("isResolved")) is not bool:
                        raise ValueError()
                    verdicts.append(n["isResolved"])
                if page["hasNextPage"] is False:
                    return verdicts
                if page["hasNextPage"] is not True or not page["endCursor"]:
                    raise ValueError()
                cursor = page["endCursor"]
            except (KeyError, TypeError, ValueError) as exc:
                raise LiveStateBlocked("incomplete review-thread page") from exc
        raise LiveStateBlocked("review thread pagination exceeded")

    def snapshot(self, task, pr_number):
        """Fetch all facts without changing a repository or starting a workflow."""
        if type(pr_number) is not int or pr_number < 1:
            raise LiveStateBlocked("PR number missing")
        main = self.request("/git/ref/heads/main")["object"]["sha"]
        target = self.request("/pulls/" + str(pr_number))
        branch = target["head"]["ref"]
        if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
            raise LiveStateBlocked("invalid branch name in response")
        ref = self.request("/git/ref/heads/" + branch)["object"]["sha"]
        opened = self.pages("/pulls?state=open")
        summaries = []
        for item in opened:
            n = item["number"]
            # The list-PR response has no changed_files count. Read the full
            # PR record for every open PR before treating its file list as complete.
            detail = target if n == pr_number else self.request("/pulls/" + str(n))
            if (detail.get("number") != n or detail.get("state") != "open"
                    or detail.get("head", {}).get("sha") != item["head"]["sha"]):
                raise LiveStateBlocked("open PR detail changed during snapshot")
            expected = detail.get("changed_files")
            if type(expected) is not int or not 0 < expected < 3000:
                raise LiveStateBlocked("PR changed-file count unavailable or at GitHub API cap")
            file_rows = self.pages("/pulls/" + str(n) + "/files")
            summaries.append({"number": n, "head_sha": detail["head"]["sha"],
                              "changed_files": _verified_changed_paths(file_rows, expected)})
        check_runs = self.pages("/commits/" + target["head"]["sha"] + "/check-runs", key="check_runs")
        return {"main": main, "target_pr": {
                "number": pr_number, "head_sha": target["head"]["sha"],
                "head_ref": branch, "base_ref": target["base"]["ref"],
                "base_sha": target["base"]["sha"], "state": target["state"]},
                "target_branch_commit": ref,
                "open_prs": summaries,
                "review_threads": self.review_threads(pr_number),
                "head_checks": [{"name": x.get("name"), "head_sha": x.get("head_sha"),
                                 "status": x.get("status"), "conclusion": x.get("conclusion"),
                                 "app_id": (x.get("app") or {}).get("id")} for x in check_runs],
                "ruleset": self.request("/rulesets/" + str(RULESET))}

def live_state_callback(token, pr_number, owner_grant_loader, owner_grant_key):
    """Independently verify the exact owner signature; a bare True cannot authorize.

    Loader, signing key and GitHub token belong to a separate trusted service.
    """
    if not callable(owner_grant_loader) or type(owner_grant_key) is not bytes or len(owner_grant_key) < 32:
        raise LiveStateBlocked("trusted owner grant loader and signing key missing")
    reader = TrustedGithubReader(token)
    def verify(task):
        proof = validate_snapshot(task, reader.snapshot(task, pr_number))
        try:
            receipt = owner_grant_loader(task)
            verify_owner_grant(task, receipt, owner_grant_key)
        except OwnerGrantBlocked as exc:
            raise LiveStateBlocked("independent owner-signed authorization failed") from exc
        proof["owner_scope_approved"] = True
        proof["owner_grant_signature_verified"] = True
        return proof
    return verify
