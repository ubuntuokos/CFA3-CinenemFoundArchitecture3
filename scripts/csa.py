#!/usr/bin/env python3
"""CSA internal development archive. Never part of CFA3 application packages.

Only operates on an explicitly supplied archive directory; GitHub publication
and ChatGPT conversation access are outside this local tool's authority.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

JSON_LIMIT = 996147
APPROVAL = {"PENDING", "APPROVED", "DEFERRED", "REJECTED", "SUPERSEDED"}
IMPLEMENTATION = {"UNKNOWN", "NOT_STARTED", "PLANNING", "APPROVED_TO_START",
                  "IN_PROGRESS", "BLOCKED", "PARTIALLY_IMPLEMENTED",
                  "IMPLEMENTED", "CANCELLED"}
START = "<!-- CSA-METADATA-BEGIN\n"
END = "\nCSA-METADATA-END -->"
IDENTITY = re.compile(r"^CSA-[0-9]{6,}$")
PROJECT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$")

def abort(message):
    raise ValueError(message)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def safe_root(path):
    root = Path(path).expanduser().resolve()
    # A standard checkout of the CFA3 application code must not be used as data.
    checkout = Path(__file__).resolve().parents[1]
    if root == checkout or checkout in root.parents:
        abort("CSA data root may not be inside the CFA3 application repository")
    if (root / "crates").exists() or (root / "canonical" / "policies").exists():
        abort("CSA data root may not be the CFA3 application repository root")
    return root

def record_path(root, project, ident):
    if not PROJECT.fullmatch(project) or not IDENTITY.fullmatch(ident):
        abort("invalid project or record ID")
    return root / "projects" / project / "suggestions" / (ident + ".md")

def render(meta):
    title = meta["title"].replace("\n", " ")
    raw = meta["original_text"]
    return ("# " + meta["id"] + " – " + title + "\n\n" + START
            + json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2)
            + END + "\n\n## Eredeti javaslat\n\n" + raw + "\n")

def parse(path):
    text = path.read_text(encoding="utf-8")
    begin = text.find(START)
    end = text.find(END, begin + len(START))
    if begin < 0 or end < 0:
        abort("missing CSA metadata: " + str(path))
    data = json.loads(text[begin + len(START):end])
    if not isinstance(data, dict) or not IDENTITY.fullmatch(data.get("id", "")):
        abort("invalid canonical metadata")
    if text != render(data):
        abort("record content drift: " + str(path))
    return data

def all_records(root):
    rows = []
    for p in sorted((root / "projects").glob("*/suggestions/CSA-*.md")):
        meta = parse(p)
        if p != record_path(root, meta["project"], meta["id"]):
            abort("record path/identity mismatch: " + str(p))
        rows.append((p, meta))
    ids = [r["id"] for _, r in rows]
    if len(set(ids)) != len(ids):
        abort("duplicate canonical IDs")
    return rows

def atomic_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

def init(root):
    if any(root.iterdir()) if root.exists() else False:
        abort("initialize only into an empty data directory")
    root.mkdir(parents=True, exist_ok=True)
    rebuild(root)

def rebuild(root):
    rows = all_records(root)
    manifest = "# CSA Manifest\n\nInternal development data, never application payload.\n\n"
    manifest += "Records: " + str(len(rows)) + "\n\n"
    index = "# CSA Javaslatindex\n\n| ID | Projekt | Cím | Döntés | Megvalósítás |\n|---|---|---|---|---|\n"
    projects = {}
    for p, r in rows:
        projects.setdefault(r["project"], []).append(r)
        def cell(value):
            return str(value).replace("|", "\\|").replace("\n", " ")
        index += "| " + " | ".join(map(cell, [r["id"], r["project"], r["title"],
                     r["approval"], r["implementation"]])) + " |\n"
    atomic_text(root / "CSA-MANIFEST.md", manifest)
    atomic_text(root / "indexes" / "CSA-INDEX.md", index)
    atomic_text(root / "CSA-PROJECT-INDEX.md",
                "# CSA Projektindex\n\n" + "".join(
                    "- " + k + ": " + str(len(v)) + "\n"
                    for k, v in sorted(projects.items())))
    for project, records in projects.items():
        atomic_text(root / "projects" / project / "INDEX.md",
                    "# " + project + "\n\n" + "".join(
                        "- " + r["id"] + ": " + r["title"] + "\n" for r in records))

def add(root, args):
    if not PROJECT.fullmatch(args.project):
        abort("invalid project")
    original = Path(args.suggestion_file).read_text("utf-8")
    if not original.strip():
        abort("empty suggestion")
    if re.search(r"(?i)(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN PRIVATE KEY-----)", original):
        abort("potential credential in suggestion")
    rows = all_records(root)
    fingerprint = sha256(original.encode("utf-8"))
    matches = [r for _, r in rows if r["project"] == args.project
               and r.get("text_sha256") == fingerprint]
    if matches:
        abort("possible duplicate; review record " + matches[0]["id"])
    number = 1 + max((int(r["id"].split("-")[-1]) for _, r in rows), default=0)
    ident = "CSA-" + str(number).zfill(6)
    meta = {"schema": "csa.record.v1", "id": ident, "project": args.project,
            "title": args.title, "categories": args.category,
            "source": args.source, "conversation_id": args.conversation_id,
            "original_text": original, "text_sha256": fingerprint,
            "approval": "PENDING", "implementation": "UNKNOWN",
            "decisions": [], "implementation_events": [],
            "relations": [], "sources": [args.source] if args.source else []}
    path = record_path(root, args.project, ident)
    atomic_text(path, render(meta))
    rebuild(root)
    print(ident)

def find(root, args):
    term = args.query.casefold()
    for _, r in all_records(root):
        if args.project and r["project"] != args.project:
            continue
        haystack = " ".join([r["title"], r["original_text"], " ".join(r["categories"]),
                              r["project"]]).casefold()
        if term in haystack:
            print(r["id"] + "\t" + r["project"] + "\t" + r["title"]
                  + "\t" + r["approval"] + "\t" + r["implementation"])

def change(root, args):
    matches = [(p, r) for p, r in all_records(root) if r["id"] == args.id]
    if len(matches) != 1:
        abort("record not found")
    path, meta = matches[0]
    if not args.evidence:
        abort("decision evidence required")
    if args.kind == "approval":
        if args.state not in APPROVAL:
            abort("invalid approval status")
        meta["approval"] = args.state
        meta["decisions"].append({"state": args.state, "evidence": args.evidence})
    else:
        if args.state not in IMPLEMENTATION:
            abort("invalid implementation status")
        if args.state in ("IMPLEMENTED", "PARTIALLY_IMPLEMENTED"):
            abort("verified implementation requires independent authoritative verification")
        meta["implementation"] = args.state
        meta["implementation_events"].append({"state": args.state, "evidence": args.evidence})
    atomic_text(path, render(meta))
    rebuild(root)

def verify(root):
    rows = all_records(root)
    for path in sorted(root.rglob("*.json")):
        if path.stat().st_size > JSON_LIMIT:
            abort("JSON size exceeds 0.95 MiB: " + str(path))
        json.loads(path.read_text("utf-8"))
    for p, meta in rows:
        if not PROJECT.fullmatch(meta["project"]) or meta.get("approval") not in APPROVAL \
           or meta.get("implementation") not in IMPLEMENTATION:
            abort("invalid record state: " + str(p))
        if sha256(meta["original_text"].encode("utf-8")) != meta["text_sha256"]:
            abort("original suggestion digest mismatch")
    expected = (root / "CSA-MANIFEST.md").read_text("utf-8")
    if "Records: " + str(len(rows)) not in expected:
        abort("manifest count drift")
    print("CSA_LOCAL_STRUCTURAL_PASS: " + str(len(rows))
          + " records; not GitHub or ChatGPT access proof")

def export(root, args):
    matches = [(p, r) for p, r in all_records(root)
               if (not args.id or r["id"] == args.id)
               and (not args.project or r["project"] == args.project)]
    if not matches:
        abort("no matching archive records")
    dest = Path(args.output).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix.lower() == ".md":
        if len(matches) != 1:
            abort("a single Markdown export requires exactly one record")
        dest.write_bytes(matches[0][0].read_bytes())
    elif dest.suffix.lower() == ".zip":
        manifest = ["file,sha256"]
        with ZipFile(dest, "w", ZIP_DEFLATED) as z:
            for p, _ in matches:
                rel = p.relative_to(root).as_posix()
                data = p.read_bytes()
                z.writestr(rel, data)
                manifest.append(rel + "," + sha256(data))
            z.writestr("CSA-EXPORT-MANIFEST.csv", "\n".join(manifest) + "\n")
    else:
        abort("output must be .md or .zip")
    print(str(dest))

def main(argv=None):
    parser = argparse.ArgumentParser(description="CFA3 internal CSA development utility")
    parser.add_argument("--root", required=True, help="explicit data directory, never application package")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    a = sub.add_parser("add")
    a.add_argument("--project", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--category", action="append", default=[])
    a.add_argument("--suggestion-file", required=True)
    a.add_argument("--source", default="")
    a.add_argument("--conversation-id", default="")
    f = sub.add_parser("find")
    f.add_argument("query")
    f.add_argument("--project")
    s = sub.add_parser("status")
    s.add_argument("id")
    s.add_argument("kind", choices=["approval", "implementation"])
    s.add_argument("state")
    s.add_argument("--evidence", required=True)
    sub.add_parser("verify")
    e = sub.add_parser("export")
    e.add_argument("--id")
    e.add_argument("--project")
    e.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        root = safe_root(args.root)
        if args.cmd == "init":
            init(root)
        elif args.cmd == "add":
            add(root, args)
        elif args.cmd == "find":
            find(root, args)
        elif args.cmd == "status":
            change(root, args)
        elif args.cmd == "verify":
            verify(root)
        elif args.cmd == "export":
            export(root, args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("CSA_ERROR: " + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
