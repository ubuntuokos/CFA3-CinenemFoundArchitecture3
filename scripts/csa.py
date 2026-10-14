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


KIND = re.compile(r"^[A-Z][A-Z0-9_]{1,79}$")
CAP_ID = re.compile(r"^CAP-([0-9]{3})$")

def canonical_roster(path):
    if not path:
        abort("baseline roster required; unverified baseline is not permitted")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (data.get("schema") != "cfa3.capability-name-roster.v1"
            or data.get("target_count") != 200
            or data.get("carried_legacy_names") != 175
            or type(data.get("numbered_unassigned_slots")) is not int):
        abort("unexpected baseline roster schema or counts")
    entries = data.get("names")
    if not isinstance(entries, list) or len(entries) != 200:
        abort("baseline roster must contain exactly 200 slots")
    roster = {}
    seen_names = set()
    reserved_seen = False
    reserved_count = 0
    for slot, row in enumerate(entries, 1):
        ident = "CAP-" + str(slot).zfill(3)
        if not isinstance(row, dict) or row.get("id") != ident:
            abort("baseline IDs are not in stable numbered order")
        name, state = row.get("name"), row.get("state")
        if not isinstance(name, str) or not name.strip():
            abort("unnamed baseline item")
        if slot <= 175 and state != "LEGACY_NAME_CARRIED_FORWARD":
            abort("initial 175 baseline states changed without reconciliation")
        if slot > 175 and state == "RESERVED_NUMBER_ONLY":
            if name != ident:
                abort("reserved baseline slot cannot carry a name")
            reserved_seen = True
            reserved_count += 1
        elif slot > 175:
            if reserved_seen:
                abort("new baseline names must allocate lowest reserved slot first")
            if name == ident:
                abort("allocated baseline slot must have an approved distinct name")
        if slot > 175 and state not in (
                "RESERVED_NUMBER_ONLY", "NAMED_PENDING_DESIGN_AND_ACCEPTANCE",
                "OWNER_APPROVED", "FINALIZED"):
            abort("unrecognized reserved-slot state")
        if name in seen_names:
            abort("duplicate baseline name")
        seen_names.add(name)
        roster[ident] = row
    if reserved_count != data["numbered_unassigned_slots"]:
        abort("baseline reserved-slot count does not match current roster")
    return roster

def active_baseline(roster, ident):
    row = roster.get(ident)
    if row is None or row["state"] in (
            "RESERVED_NUMBER_ONLY", "NAMED_PENDING_DESIGN_AND_ACCEPTANCE"):
        abort("baseline target is absent, reserved, or not accepted: " + str(ident))
    return row

def validated_relations(meta, known_ids, roster, donor_registry=None):
    if meta.get("schema") != "csa.record.v2":
        abort("legacy record lacks required baseline-bound v2 fields: " + meta["id"])
    if not isinstance(meta.get("source"), str) or not meta["source"].strip():
        abort("source/provenance reference required")
    kind = meta.get("record_kind")
    if not isinstance(kind, str) or not KIND.fullmatch(kind):
        abort("invalid record kind")
    if not isinstance(meta.get("purpose"), str) or not meta["purpose"].strip():
        abort("record purpose required")
    active_baseline(roster, meta.get("baseline_id"))
    relations = meta.get("relations")
    if not isinstance(relations, list) or len(set(relations)) != len(relations):
        abort("duplicate or invalid record relations")
    if any(x not in known_ids or x == meta["id"] for x in relations):
        abort("unknown or self-referencing record relation")
    allowed = meta.get("applicable_baselines")
    excluded = meta.get("excluded_baselines")
    if not isinstance(allowed, list) or not isinstance(excluded, list):
        abort("baseline applicability must be lists")
    if len(set(allowed)) != len(allowed) or len(set(excluded)) != len(excluded):
        abort("duplicate baseline applicability")
    if set(allowed) & set(excluded):
        abort("baseline cannot be both allowed and excluded")
    for item in allowed + excluded:
        active_baseline(roster, item)
    donors = meta.get("donor_ids")
    if not isinstance(donors, list) or len(set(donors)) != len(donors):
        abort("invalid or duplicate donor reference")
    if donors:
        if not donor_registry:
            abort("donor registry required for donor references")
        # Use the existing CFA3 canonical read-only donor resolver.
        from donor_reference_lookup import lookup
        for ident in donors:
            resolved = lookup(donor_id=ident, registry_path=Path(donor_registry))
            if (not resolved or resolved.get("donor_id") != ident or
                    resolved.get("donor_registration") not in (
                        "CANONICAL_REFERENCE_REGISTERED",
                        "ACCEPTED_REFERENCE")):
                abort("donor is not a published canonical reference: " + str(ident))

def computed_indexes(root, rows):
    manifest = "# CSA Manifest\n\nInternal development data; never an application payload.\n\n"
    manifest += "Records: " + str(len(rows)) + "\n\n"
    columns = ["ID", "Markdown path", "Baseline ID", "Type", "Project",
               "Title", "Purpose", "Approval", "Implementation"]
    index = "# CSA tervezési index\n\n| " + " | ".join(columns) + " |\n"
    index += "|" + "|".join("---" for _ in columns) + "|\n"
    projects = {}
    inverse = {}
    for p, r in rows:
        projects.setdefault(r["project"], []).append((p, r))
        for target in r.get("relations", []):
            inverse.setdefault(target, []).append(r["id"])
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    for p, r in rows:
        rel = p.relative_to(root).as_posix()
        values = ["[" + r["id"] + "](../" + rel + ")",
                  "[file](../" + rel + ")", r.get("baseline_id", "UNBOUND"),
                  r.get("record_kind", "LEGACY"), r["project"], r["title"],
                  r.get("purpose", ""), r["approval"], r["implementation"]]
        index += "| " + " | ".join(map(cell, values)) + " |\n"
    relationships = "# CSA kapcsolatok (előre és vissza)\n\n"
    relationships += "| Rekord | Kapcsolódó rekordok | Bejövő hivatkozások | Donor ID-k |\n"
    relationships += "|---|---|---|---|\n"
    for p, r in rows:
        values = [r["id"], ", ".join(r.get("relations", [])),
                  ", ".join(sorted(inverse.get(r["id"], []))),
                  ", ".join(r.get("donor_ids", []))]
        relationships += "| " + " | ".join(map(cell, values)) + " |\n"
    expected = {
        root / "CSA-MANIFEST.md": manifest,
        root / "indexes" / "CSA-INDEX.md": index,
        root / "indexes" / "CSA-RELATIONS.md": relationships,
        root / "CSA-PROJECT-INDEX.md":
            "# CSA Projektindex\n\n" + "".join(
                "- " + k + ": " + str(len(v)) + "\n"
                for k, v in sorted(projects.items()))
    }
    for project, records in projects.items():
        expected[root / "projects" / project / "INDEX.md"] = (
            "# " + project + "\n\n" + "".join(
                "- [" + r["id"] + "](suggestions/" + r["id"] +
                ".md): " + r["title"] + "\n" for _, r in records))
    return expected


def rebuild(root):
    for path, content in computed_indexes(root, all_records(root)).items():
        atomic_text(path, content)

def add(root, args):
    if not PROJECT.fullmatch(args.project):
        abort("invalid project")
    original = Path(args.suggestion_file).read_text("utf-8")
    if not original.strip():
        abort("empty record content")
    if not isinstance(args.source, str) or not args.source.strip():
        abort("a nonempty source/provenance reference is required")
    if re.search(r"(?i)(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN PRIVATE KEY-----)", original):
        abort("potential credential in record")
    roster = canonical_roster(getattr(args, "baseline_roster", None))
    baseline_id = getattr(args, "baseline_id", None)
    active_baseline(roster, baseline_id)
    kind = getattr(args, "kind", "RECOMMENDATION")
    purpose = getattr(args, "purpose", None)
    if not isinstance(kind, str) or not KIND.fullmatch(kind):
        abort("invalid record kind")
    if not isinstance(purpose, str) or not purpose.strip():
        abort("record purpose required")
    applicable = list(getattr(args, "applies_to", []))
    excluded = list(getattr(args, "excludes", []))
    refs = list(getattr(args, "relation", []))
    donors = list(getattr(args, "donor_id", []))
    rows = all_records(root)
    fingerprint = sha256(original.encode("utf-8"))
    matches = [r for _, r in rows if r["project"] == args.project
               and r.get("text_sha256") == fingerprint]
    if matches:
        abort("possible duplicate; review record " + matches[0]["id"])
    number = 1 + max((int(r["id"].split("-")[-1]) for _, r in rows), default=0)
    ident = "CSA-" + str(number).zfill(6)
    meta = {"schema": "csa.record.v2", "id": ident, "project": args.project,
            "title": args.title, "record_kind": kind, "purpose": purpose.strip(),
            "baseline_id": baseline_id, "applicable_baselines": applicable,
            "excluded_baselines": excluded, "donor_ids": donors,
            "categories": args.category, "source": args.source,
            "conversation_id": args.conversation_id, "original_text": original,
            "text_sha256": fingerprint, "approval": "PENDING",
            "implementation": "UNKNOWN", "decisions": [],
            "implementation_events": [], "relations": refs,
            "sources": [args.source] if args.source else []}
    validated_relations(meta, {r["id"] for _, r in rows}, roster,
                        getattr(args, "donor_registry", None))
    path = record_path(root, args.project, ident)
    atomic_text(path, render(meta))
    rebuild(root)
    print(ident)

def find(root, args):
    term = args.query.casefold()
    for _, r in all_records(root):
        if args.project and r["project"] != args.project:
            continue
        if getattr(args, "baseline_id", None) and r.get("baseline_id") != args.baseline_id:
            continue
        if getattr(args, "kind", None) and r.get("record_kind") != args.kind:
            continue
        haystack = " ".join([
            r["title"], r["original_text"], " ".join(r["categories"]),
            r["project"], r.get("baseline_id", ""), r.get("record_kind", ""),
            r.get("purpose", ""), " ".join(r.get("applicable_baselines", [])),
            " ".join(r.get("excluded_baselines", []))]).casefold()
        if term in haystack:
            print(r["id"] + "\\t" + r["project"] + "\\t" + r["title"]
                  + "\\t" + r["approval"] + "\\t" + r["implementation"])

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

def verify(root, roster_path=None, donor_registry=None, *, quiet=False):
    rows = all_records(root)
    known = {r["id"] for _, r in rows}
    roster = canonical_roster(roster_path) if rows else None
    for path in sorted(root.rglob("*.json")):
        if path.stat().st_size > JSON_LIMIT:
            abort("JSON size exceeds 0.95 MiB: " + str(path))
        json.loads(path.read_text("utf-8"))
    for p, meta in rows:
        if (not PROJECT.fullmatch(meta["project"])
                or meta.get("approval") not in APPROVAL
                or meta.get("implementation") not in IMPLEMENTATION):
            abort("invalid record state: " + str(p))
        if sha256(meta["original_text"].encode("utf-8")) != meta["text_sha256"]:
            abort("original suggestion digest mismatch")
        validated_relations(meta, known, roster, donor_registry)
        if meta["approval"] != "PENDING" and not meta.get("decisions"):
            abort("non-pending record has no approval evidence")
    for path, content in computed_indexes(root, rows).items():
        if not path.is_file() or path.read_text("utf-8") != content:
            abort("index or manifest drift: " + str(path))
    if not quiet:
        print("CSA_LOCAL_STRUCTURAL_PASS: " + str(len(rows))
              + " records; not GitHub, donor completeness, or ChatGPT proof")

def context(root, args):
    """Read-only, scope-bound retrieval for an authorized design task.

    Does not finalize a proposal or claim it was implemented.
    """
    ident = args.record_id
    baseline = args.baseline_id
    if bool(ident) == bool(baseline):
        abort("choose exactly one record ID or baseline ID for context")
    # Reject inconsistent local manifests, links, donor references and roster
    # before exposing records to a new design task.
    verify(root, args.baseline_roster, args.donor_registry, quiet=True)
    rows = all_records(root)
    roster = canonical_roster(args.baseline_roster)
    if baseline:
        active_baseline(roster, baseline)
    inbound = {}
    for _, record in rows:
        for target in record["relations"]:
            inbound.setdefault(target, []).append(record["id"])
    matches = []
    for path, record in rows:
        if ident:
            if record["id"] != ident:
                continue
            role = "EXACT_RECORD"
        elif record["baseline_id"] == baseline:
            role = "PRIMARY_BASELINE"
        elif baseline in record["applicable_baselines"]:
            role = "APPLICABLE_BASELINE"
        else:
            continue
        matches.append({
            "relative_markdown_path": path.relative_to(root).as_posix(),
            "match_role": role,
            "inbound_record_ids": sorted(inbound.get(record["id"], [])),
            "is_nonfinal_proposal": record["record_kind"] in
                ("RECOMMENDATION", "PRELIMINARY_PLAN"),
            "record": record,
        })
    if not matches:
        abort("no verified planning records found for requested scope")
    result = {
        "schema": "csa.planning-context.v1",
        "scope": {"record_id": ident, "baseline_id": baseline},
        "note": "Archive status and approval are not proof of a finalized application or implementation",
        "records": matches,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


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
    a.add_argument("--source", required=True)
    a.add_argument("--conversation-id", default="")
    a.add_argument("--kind", default="RECOMMENDATION")
    a.add_argument("--purpose", required=True)
    a.add_argument("--baseline-id", required=True)
    a.add_argument("--baseline-roster", required=True)
    a.add_argument("--applies-to", action="append", default=[])
    a.add_argument("--excludes", action="append", default=[])
    a.add_argument("--relation", action="append", default=[])
    a.add_argument("--donor-id", action="append", default=[])
    a.add_argument("--donor-registry")
    f = sub.add_parser("find")
    f.add_argument("query")
    f.add_argument("--project")
    f.add_argument("--kind")
    f.add_argument("--baseline-id")
    s = sub.add_parser("status")
    s.add_argument("id")
    s.add_argument("kind", choices=["approval", "implementation"])
    s.add_argument("state")
    s.add_argument("--evidence", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--baseline-roster")
    v.add_argument("--donor-registry")
    c = sub.add_parser("context")
    c.add_argument("--record-id")
    c.add_argument("--baseline-id")
    c.add_argument("--baseline-roster", required=True)
    c.add_argument("--donor-registry")
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
            verify(root, args.baseline_roster, args.donor_registry)
        elif args.cmd == "context":
            context(root, args)
        elif args.cmd == "export":
            export(root, args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("CSA_ERROR: " + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
