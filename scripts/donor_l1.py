#!/usr/bin/env python3
"""CFA3 L1 archival-source importer and staged searchable reference index.

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
UNION = ARCH / "CFA3-DONOR-BASELINE-USER-SOURCE-UNION-2026-10-05.json"
SUPPLEMENT = ROOT / "canonical/registries/CFA3-DONOR-L1-UNRECONCILED-OWNER-SOURCES-001.json"
ADDITIONAL_LEADS = ROOT / "canonical/registries/CFA3-DONOR-L1-ADDITIONAL-UNRECONCILED-OWNER-SOURCES-20261010.json"
TRIPO_RECOVERY = ROOT / "canonical/registries/CFA3-DONOR-L1-HISTORICAL-TRIPO-UNITY-DCC-POSE-RECOVERY-20261010.json"
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
    return out

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
    supplement = json_read(SUPPLEMENT)
    if (supplement.get("schema") != "cfa3.donor-l1-unreconciled-owner-submissions.v1"
            or supplement.get("status") != "CANDIDATE_STAGED_NOT_CANONICAL_PUBLISHED"
            or len(supplement.get("entries", [])) != 23
            or supplement.get("verification_bounds", {}).get("all_past_chats_exhaustively_audited") is not False):
        raise ValueError("Unreconciled owner-source supplement must remain bounded and non-admitted")
    for record in supplement["entries"]:
        if (record.get("status") != "OWNER_APPROVAL_REPORTED_PENDING_SOURCE_EVIDENCE"
                or record.get("submission_review", {}).get("exact_submitted_URL_and_approval_pair_independently_verified") is not False
                or record.get("intake_provenance", {}).get("canonical_approval_admitted") is not False):
            raise ValueError("Unverified owner-source record must not be promoted")
        sources.append((record, "HISTORICAL_OWNER_APPROVAL_RECONCILIATION_PENDING", False))
    leads = json_read(ADDITIONAL_LEADS)
    if (leads.get("schema") != "cfa3.donor-l1-supplemental-owner-approval-leads.v1"
            or leads.get("status") != "CANDIDATE_STAGED_NOT_CANONICAL_PUBLISHED"
            or leads.get("archived_registry_blob_sha") != EXPECTED[REGISTRY.name]
            or leads.get("preexisting_staged_source_count") != 1944
            or leads.get("existing_23_supplement_preserved") is not True
            or len(leads.get("entries", [])) != 4
            or leads.get("original_L1_B") is not None
            or leads.get("all_user_approvals_exhaustively_verified") is not False
            or leads.get("publication_gate") != "BLOCKED"
            or leads.get("runtime_admission") is not False):
        raise ValueError("Additional owner-source leads require non-admitting evidence")
    for record in leads["entries"]:
        if (record.get("status") != "OWNER_APPROVAL_REPORTED_PENDING_SOURCE_EVIDENCE"
                or record.get("submission_review", {}).get("exact_submitted_URL_and_approval_pair_independently_verified") is not False
                or record.get("intake_provenance", {}).get("canonical_approval_admitted") is not False
                or record.get("authority") is not False):
            raise ValueError("Additional source lead must not be promoted")
        sources.append((record, "ADDITIONAL_OWNER_APPROVAL_RECONCILIATION_PENDING", False))
    recovery = json_read(TRIPO_RECOVERY)
    aggregate = recovery.get("historical_aggregate_reconciliation", {})
    if (recovery.get("schema") != "cfa3.donor-l1-historical-tripo-unity-dcc-pose-recovery.v1"
            or recovery.get("status") != "CANDIDATE_STAGED_NOT_CANONICAL_PUBLISHED"
            or recovery.get("archived_registry_blob_sha") != EXPECTED[REGISTRY.name]
            or recovery.get("original_submitted_url_occurrences") != 48
            or recovery.get("unique_submitted_urls") != 46
            or recovery.get("pending_unmatched_identities") != 30
            or recovery.get("matched_preexisting_identities") != 6
            or len(recovery.get("entries", [])) != 30
            or len(recovery.get("url_provenance", [])) != 48
            or aggregate.get("status") != "NON_ADMITTED_RECONCILIATION_REFERENCE_ONLY"
            or aggregate.get("not_a_new_donor") is not True
            or aggregate.get("no_canonical_merge") is not True
            or len(aggregate.get("preserved_archive_identities", [])) != 3
            or recovery.get("original_L1_B") is not None
            or recovery.get("all_owner_approvals_exhaustively_verified") is not False
            or recovery.get("publication_gate") != "BLOCKED"
            or recovery.get("runtime_admission") is not False):
        raise ValueError("Historical Tripo recovery must preserve bounded identity evidence without publication")
    for record in recovery["entries"]:
        if (record.get("status") != "OWNER_APPROVAL_REPORTED_PENDING_SOURCE_EVIDENCE"
                or record.get("submission_review", {}).get("exact_submitted_URL_and_approval_pair_independently_verified") is not False
                or record.get("intake_provenance", {}).get("canonical_approval_admitted") is not False
                or record.get("authority") is not False
                or record.get("runtime_admission") is not False):
            raise ValueError("Historical Tripo candidate must remain blocked")
        sources.append((record, "HISTORICAL_TRIPO_OWNER_APPROVAL_PENDING", False))
    ids, keys = set(), set()
    for record, _, _ in sources:
        ident = record["donor_id"]
        key = record["source"]["normalized_key"]
        if not ident or not key or ident in ids or key in keys:
            raise ValueError(f"Conflicting source identity: {ident}: {key}")
        ids.add(ident)
        keys.add(key)
    return sources

def register_historical_urls(db, sources):
    """Index exact submitted URLs with source and alias provenance.

    Preserve the documented Ascend supersession without deleting the legacy identity.
    This is historical evidence, not completeness certification.
    """
    data = UNION.read_bytes()
    if sha_blob(data) != "d22dce8bfe3d9697a1121033ff7b387d051a638a":
        raise ValueError("Historical owner-source union blob mismatch")
    union = json.loads(data)
    coverage = union["source_coverage"]
    if len(coverage) != 445:
        raise ValueError("Unexpected bounded historical union")
    by_id = {entry["donor_id"]: entry for entry, _, _ in sources}
    supersession = union["superseded_resolution"]
    archived = 0
    for record in coverage:
        sid = record["resolved_donor_id"]
        entry = by_id.get(sid)
        if not entry:
            raise ValueError("Historical approval source missing: " + sid)
        if entry["source"]["normalized_key"] != record["normalized_key"]:
            allowed = (sid == supersession["replacement_donor_id"] and
                       record["donor_id"] == supersession["historical_donor_id"] and
                       record["normalized_key"] == "github:ascend/triton-ascend")
            if not allowed:
                raise ValueError("Unresolved source alias identity: " + sid)
        for original in record["original_locators"]:
            if not original:
                raise ValueError("Empty historical source URL")
            db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (original, sid))
            for source_set in record["source_sets"]:
                db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                           (sid, original, source_set, "2026-10-05-owner-source-union"))
            archived += 1
    db.execute("INSERT INTO metadata VALUES(?,?)",
               ("bounded_union_link_records", str(len(coverage))))
    db.execute("INSERT INTO metadata VALUES(?,?)",
               ("bounded_union_original_url_records", str(archived)))
    db.execute("INSERT INTO metadata VALUES(?,?)",
               ("bounded_union_distinct_donor_ids", str(len({e["resolved_donor_id"] for e in coverage}))))
    return archived


def register_tripo_historical_urls(db, sources):
    """Preserve every original occurrence, including repeated URLs, without new admission."""
    manifest = json_read(TRIPO_RECOVERY)
    by_id = {entry["donor_id"]: entry for entry, _, _ in sources}
    seen = set()
    for record in manifest["url_provenance"]:
        i, url, sid = record["occurrence_index"], record["original_url"], record["source_id"]
        # Parentless historical user submissions are L1 roots; never reset children.
        if record.get("parent_id") is not None or record.get("global_level", 1) != 1:
            raise ValueError("Historical Tripo input must be a parentless L1 root")
        if not isinstance(i, int) or isinstance(i, bool) or i < 1 or i > 48 or i in seen:
            raise ValueError("Historical Tripo occurrence index missing, duplicated or invalid")
        seen.add(i)
        source = by_id.get(sid)
        if source is None:
            raise ValueError("Historical Tripo unresolved source: " + sid)
        src = source["source"]
        if record["normalized_key"] != src["normalized_key"]:
            raise ValueError("Historical Tripo source identity and canonical key conflict: " + url)
        if url not in ({src["locator"]} | set(src.get("discovery_urls", []))):
            raise ValueError("Historical Tripo URL not grounded by source metadata: " + url)
        existing = {x[0] for x in db.execute("SELECT source_id FROM aliases WHERE alias=?", (url,))}
        if existing - {sid}:
            raise ValueError("Historical Tripo URL alias resolves to multiple canonical IDs: " + url)
        db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (url, sid))
        db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                   (sid, url, "HISTORICAL_TRIPO_UNITY_DCC_POSE_20261004",
                    "historical-branch-ce8b8a88-submitted-links"))
        db.execute("INSERT INTO historical_link_occurrences VALUES(?,?,?,?,?,?,?,?,?)",
                   ("HISTORICAL_TRIPO_UNITY_DCC_POSE_20261004", i, sid, url,
                    record["normalized_key"], record["identity_resolution"],
                    "historical-head-ce8b8a888a8c762393a4fa4c80e5a1c08a64dbed",
                    None, 1))
    if seen != set(range(1, 49)):
        raise ValueError("Historical Tripo occurrence coverage incomplete")
    if len({row["original_url"] for row in manifest["url_provenance"]}) != 46:
        raise ValueError("Historical Tripo distinct raw URL count mismatch")
    for preserved in manifest["historical_aggregate_reconciliation"]["preserved_archive_identities"]:
        rows = [x for x in manifest["url_provenance"] if x["original_url"] == preserved["original_url"]]
        if (len(rows) != 1 or rows[0]["source_id"] != preserved["archived_donor_id"]
                or rows[0]["normalized_key"] != preserved["archived_normalized_key"]
                or rows[0]["identity_resolution"] !=
                   "EXISTING_ARCHIVED_EXACT_URL_PRESERVE_DISTINCT_QUERY_VIEW"):
            raise ValueError("Historical Tripo topic query-view identity not preserved")
    return len(seen)


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
      CREATE TABLE source_provenance(
        source_id TEXT NOT NULL REFERENCES sources(source_id),
        original_url TEXT NOT NULL, source_set TEXT NOT NULL,
        historical_evidence TEXT NOT NULL,
        PRIMARY KEY(source_id,original_url,source_set,historical_evidence));
      CREATE INDEX provenance_url_lookup ON source_provenance(original_url);
      CREATE TABLE historical_link_occurrences(
        source_group TEXT NOT NULL, occurrence_index INTEGER NOT NULL,
        source_id TEXT NOT NULL REFERENCES sources(source_id),
        original_url TEXT NOT NULL, normalized_key TEXT NOT NULL,
        identity_resolution TEXT NOT NULL, evidence_ref TEXT NOT NULL,
        parent_id TEXT CHECK(parent_id IS NULL),
        global_level INTEGER NOT NULL CHECK(global_level=1),
        PRIMARY KEY(source_group,occurrence_index));
      CREATE INDEX historical_link_url_lookup ON historical_link_occurrences(original_url);
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
    register_historical_urls(db, sources)
    register_tripo_historical_urls(db, sources)
    db.executemany("INSERT INTO metadata VALUES(?,?)",(
        ("schema","cfa3.donor-l1-index.v1"),
        ("run_id",run_id),
        ("input_link_occurrences_B","UNVERIFIED"),
        ("expansion_raw_limit","UNVERIFIED"),
        ("known_unique_source_identities",str(len(sources))),
        ("supplemental_owner_source_candidates","23"),
        ("additional_owner_source_leads","4"),
        ("total_pending_owner_source_candidates","57"),
        ("historical_tripo_new_pending_sources","30"),
        ("historical_tripo_original_occurrences","48"),
        ("historical_tripo_distinct_urls","46"),
        ("all_owner_submissions_verified","FALSE"),
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
        classified_count = db.execute("SELECT count(DISTINCT source_id) FROM classes").fetchone()[0]
        if classified_count > expected:
            raise ValueError("Class index inconsistent")
        union = json_read(UNION)
        expected_urls = {url: record["resolved_donor_id"]
                         for record in union["source_coverage"]
                         for url in record["original_locators"]}
        if len(expected_urls) != 445:
            raise ValueError("Original owner URL count is not 445")
        distinct_urls = db.execute(
            "SELECT count(DISTINCT original_url) FROM source_provenance "
            "WHERE historical_evidence='2026-10-05-owner-source-union'").fetchone()[0]
        distinct_ids = db.execute(
            "SELECT count(DISTINCT source_id) FROM source_provenance "
            "WHERE historical_evidence='2026-10-05-owner-source-union'").fetchone()[0]
        if distinct_urls != len(expected_urls) or distinct_ids != len(set(expected_urls.values())):
            raise ValueError("Historical URL provenance coverage mismatch")
        for url, identity in expected_urls.items():
            actual_ids = {item[0] for item in db.execute(
                "SELECT source_id FROM source_provenance WHERE original_url=?", (url,))}
            if identity not in actual_ids:
                raise ValueError("Missing historical provenance mapping: " + url)
        for sid, locator, key, content, digest in db.execute(
                "SELECT source_id,locator,normalized_key,original_record,original_digest FROM sources"):
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
                raise ValueError("Source record digest mismatch")
            for alias in (locator, key):
                row = db.execute("SELECT source_id FROM aliases WHERE alias=? AND source_id=?",
                                 (alias,sid)).fetchone()
                if row is None:
                    raise ValueError("Source lookup failure")
        for source_file in (SUPPLEMENT, ADDITIONAL_LEADS):
            for entry in json_read(source_file)["entries"]:
                donor_id, url = entry["donor_id"], entry["source"]["locator"]
                row = db.execute("SELECT current_status,locator FROM sources WHERE source_id=?", (donor_id,)).fetchone()
                if row != ("BLOCKED", url):
                    raise ValueError("Unreconciled owner source missing or wrongly admitted: " + donor_id)
        recovery = json_read(TRIPO_RECOVERY)
        actual = list(db.execute(
            "SELECT occurrence_index,source_id,original_url,normalized_key,identity_resolution,parent_id,global_level "
            "FROM historical_link_occurrences WHERE source_group=? ORDER BY occurrence_index",
            ("HISTORICAL_TRIPO_UNITY_DCC_POSE_20261004",)))
        expected_occurrences = [
            (x["occurrence_index"], x["source_id"], x["original_url"],
             x["normalized_key"], x["identity_resolution"], None, 1)
            for x in recovery["url_provenance"]
        ]
        if len(actual) != 48 or actual != expected_occurrences:
            raise ValueError("Historical Tripo exact occurrence read-back mismatch")
        if len({row[2] for row in actual}) != 46:
            raise ValueError("Historical Tripo duplicate URL occurrence count lost")
        for occurrence_index, sid, url, key, resolution, parent_id, global_level in actual:
            if not db.execute("SELECT 1 FROM aliases WHERE alias=? AND source_id=?",
                              (url, sid)).fetchone():
                raise ValueError("Historical Tripo URL alias read-back missing")
        for item in recovery["entries"]:
            sid = item["donor_id"]
            row = db.execute("SELECT current_status,normalized_key FROM sources WHERE source_id=?",
                             (sid,)).fetchone()
            if row != ("BLOCKED", item["source"]["normalized_key"]):
                raise ValueError("Historical Tripo source missing or improperly admitted")
        old_aggregate_id = recovery["historical_aggregate_reconciliation"]["historical_proposed_donor_id"]
        if db.execute("SELECT 1 FROM sources WHERE source_id=?", (old_aggregate_id,)).fetchone():
            raise ValueError("Non-canonical historical Tripo aggregate was improperly admitted")
        url_locator_rows = db.execute(
            "SELECT count(*) FROM sources WHERE locator LIKE 'http://%' OR locator LIKE 'https://%'"
        ).fetchone()[0]
        non_url_locator_rows = total - url_locator_rows
        # These are stored canonical locator fields, NOT original user link occurrences.
        # Neither staged source-record totals nor stored locator fields freeze B.
    return {"rows":total,"locator_index":"PASS","historical_url_provenance":"BOUNDED_445_PASS",
            "observed_http_source_locators":url_locator_rows,
            "observed_non_http_source_locators":non_url_locator_rows,
            "original_L1_link_record_count_B_verified":False,
            "supplemental_unreconciled_owner_sources":23,
            "additional_unreconciled_owner_sources":4,
            "historical_tripo_pending_sources":30,
            "historical_tripo_url_occurrences":48,
            "historical_tripo_provenance":"BOUNDED_48_PASS",
            "historical_unique_source_ids":distinct_ids,
            "hint_classified":classified_count,
            "class_index":"PARTIAL_UNVERIFIED","record_integrity":"PASS"}

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
        return {"state":"STAGED_NOT_PUBLISHED","run_id":run_id,"B":None,
                "raw_link_limit":None,
                "index_evidence":evidence,
                "reason":"UNVERIFIED_FROZEN_L1_B_AND_ALL_OWNER_APPROVED_SUBMISSIONS"}
    finally:
        provisional.unlink(missing_ok=True)

def lookup(path, term, by):
    column = {"id":"source_id","key":"normalized_key","url":"locator"}[by] if by in ("id","key","url") else None
    with sqlite3.connect(path) as db:
        if by in ("alias", "url"):
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
