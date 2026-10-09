#!/usr/bin/env python3
"""CFA3 L1 archival-source importer and versioned searchable publication.

No network activity, no source approval, no dependency/runtime admission.
Requires explicit audited coverage evidence before publishing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "archive/donor-source-migration/2026-10-09"
REGISTRY = ARCH / "FA3-DONOR-REFERENCE-REGISTRY-001.json"
EXTRAS = [ARCH / f"PR-{n}-ADDITIONAL-REFERENCE.json" for n in (744, 745)]
EXPECTED = {
    "FA3-DONOR-REFERENCE-REGISTRY-001.json": "062b7b27aeeaf74819ac315f30c5cbde4ed2c95b",
}
CLASS_MAP = (
    ("SDK_API", ("SDK", "API", "LIBRARY")),
    ("SHARED_MODULE", ("SHARED", "FABRIC", "FRAMEWORK")),
    ("ENGINE", ("ENGINE", "RENDER", "BACKEND")),
    ("PLUGIN_EXTENSION", ("PLUGIN", "EXTENSION", "ADDON")),
    ("AI_MODEL_PROVIDER", ("MODEL", "PROVIDER", "LLM")),
    ("APPLICATION_REFERENCE", ("APPLICATION", "APP", "GUI")),
    ("RESEARCH_DOCUMENTATION", ("DOCUMENTATION", "RESEARCH", "GUIDE")),
    ("DISCOVERY_SOURCE", ("DISCOVERY", "TOPIC", "CATALOG", "AWESOME")),
)

def sha_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def json_read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def classify(entry):
    hints = " ".join(str(v) for key in ("donor_modes", "capability_hints", "domain_hints",
                                        "problem_hints", "target_hints", "tags") for v in entry.get(key, []))
    hints = hints.upper()
    out = [label for label, tokens in CLASS_MAP if any(token in hints for token in tokens)]
    # Absence of sufficient evidence must not manufacture an authoritative class.
    return out or ["RESEARCH_DOCUMENTATION"]

def frozen_sources():
    raw = REGISTRY.read_bytes()
    if sha_blob(raw) != EXPECTED[REGISTRY.name]:
        raise ValueError("Immutable donor archive Git blob mismatch")
    entries = json.loads(raw)["entries"]
    if len(entries) != 1919:
        raise ValueError("Unexpected root source registry size")
    sources = [(e, "OLD_MAIN_ARCHIVE", True) for e in entries]
    for n, file in zip((744, 745), EXTRAS):
        record = json_read(file)
        if record["pr"] != n or record["state"] != "UNMERGED_HISTORICAL_PR_PRESERVED_NOT_CFA3_CANONICAL_ADMITTED":
            raise ValueError("Unverified historical PR source")
        sources.append((record["entry"], f"UNMERGED_PR_{n}", False))
    ids, keys = set(), set()
    for record, _, _ in sources:
        ident = record["donor_id"]
        key = record["source"]["normalized_key"]
        if not ident or not key or ident in ids or key in keys:
            raise ValueError(f"Conflicting source identity: {ident}: {key}")
        ids.add(ident)
        keys.add(key)
    return sources

def prepare(db, sources, run_id):
    db.executescript("""
      PRAGMA foreign_keys=ON;
      CREATE TABLE sources(
        source_id TEXT PRIMARY KEY, normalized_key TEXT NOT NULL UNIQUE,
        locator TEXT NOT NULL, name TEXT NOT NULL, historical_status TEXT NOT NULL,
        current_status TEXT NOT NULL, source_kind TEXT, source_origin TEXT NOT NULL,
        global_level INTEGER NOT NULL CHECK(global_level=1),
        original_record TEXT NOT NULL, original_digest TEXT NOT NULL,
        run_id TEXT NOT NULL
      );
      CREATE TABLE aliases(alias TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources(source_id),
        PRIMARY KEY(alias,source_id));
      CREATE INDEX alias_lookup ON aliases(alias);
      CREATE TABLE classes(source_id TEXT NOT NULL REFERENCES sources(source_id),
        class TEXT NOT NULL, evidence_state TEXT NOT NULL, PRIMARY KEY(source_id,class));
      CREATE INDEX class_lookup ON classes(class);
      CREATE TABLE relations(parent_id TEXT NOT NULL, child_id TEXT NOT NULL,
        evidence TEXT NOT NULL, PRIMARY KEY(parent_id,child_id,evidence));
      CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    for entry, origin, from_main in sources:
        sid = entry["donor_id"]
        src = entry["source"]
        original = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
        status = entry["status"] if from_main else "BLOCKED"
        db.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid,src["normalized_key"],src["locator"],entry.get("name",""),entry["status"],
             status,src.get("kind"),origin,1,original,digest,run_id))
        for alias in {src["normalized_key"],src["locator"]}:
            db.execute("INSERT INTO aliases VALUES(?,?)",(alias,sid))
        for klass in classify(entry):
            db.execute("INSERT INTO classes VALUES(?,?,?)",(sid,klass,"HINT_BASED_UNVERIFIED"))
    db.executemany("INSERT INTO metadata VALUES(?,?)",(
        ("schema","cfa3.donor-l1-index.v1"),
        ("run_id",run_id),
        ("input_link_occurrences_B",str(len(sources))),
        ("expansion_raw_limit",str(len(sources)*115//100)),
        ("level","L1"),
        ("approval_completeness","UNVERIFIED"),
        ("publication_gate","PENDING"),
    ))

def verify(path, expected):
    with sqlite3.connect(path) as db:
        total = db.execute("SELECT count(*) FROM sources").fetchone()[0]
        if total != expected:
            raise ValueError("Read-back source cardinality mismatch")
        if db.execute("SELECT count(*) FROM aliases").fetchone()[0] < expected:
            raise ValueError("Read-back locator index incomplete")
        if db.execute("SELECT count(DISTINCT source_id) FROM classes").fetchone()[0] != expected:
            raise ValueError("Read-back class index incomplete")
        for sid, locator, key, content, digest in db.execute(
                "SELECT source_id,locator,normalized_key,original_record,original_digest FROM sources"):
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
                raise ValueError("Source record digest mismatch")
            for alias in (locator, key):
                row = db.execute("SELECT source_id FROM aliases WHERE alias=? AND source_id=?",
                                 (alias,sid)).fetchone()
                if row is None:
                    raise ValueError("Source lookup failure")
    return {"rows":total,"locator_index":"PASS","class_index":"PASS","record_integrity":"PASS"}

def stage(output, run_id):
    sources = frozen_sources()
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="cfa3-l1-",suffix=".sqlite",dir=output.parent,delete=False) as tmp:
        provisional = Path(tmp.name)
    try:
        with sqlite3.connect(provisional) as db:
            with db:
                prepare(db,sources,run_id)
        evidence = verify(provisional,len(sources))
        # Candidate index only: incomplete historical submission coverage blocks canonical publication.
        os.replace(provisional,output)
        return {"state":"STAGED_NOT_PUBLISHED","run_id":run_id,"B":len(sources),
                "raw_link_limit":len(sources)*115//100,
                "index_evidence":evidence,
                "reason":"UNVERIFIED_ALL_OWNER_APPROVED_SUBMISSIONS"}
    finally:
        provisional.unlink(missing_ok=True)

def lookup(path, term, by):
    column = {"id":"source_id","key":"normalized_key","url":"locator"}[by] if by in ("id","key","url") else None
    with sqlite3.connect(path) as db:
        if by == "alias":
            query = "SELECT s.source_id,s.locator,s.current_status FROM sources s JOIN aliases a ON a.source_id=s.source_id WHERE a.alias=?"
        elif by == "class":
            query = "SELECT s.source_id,s.locator,s.current_status FROM sources s JOIN classes c ON c.source_id=s.source_id WHERE c.class=?"
        elif column:
            query = f"SELECT source_id,locator,current_status FROM sources WHERE {column}=?"
        else:
            raise ValueError("Unsupported search key")
        return [dict(zip(("id","url","status"),row)) for row in db.execute(query,(term,))]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",choices=("stage","search"))
    parser.add_argument("--db",required=True)
    parser.add_argument("--run-id",default="CFA3-L1-20261009")
    parser.add_argument("--by",choices=("id","url","key","alias","class"),default="id")
    parser.add_argument("--term")
    args = parser.parse_args()
    if args.command == "stage":
        result = stage(args.db,args.run_id)
    else:
        if not args.term:
            parser.error("--term required")
        result = lookup(args.db,args.term,args.by)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
