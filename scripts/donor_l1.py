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
SHGAF_SOURCE = ARCH / "CFA3-DONOR-SHGAF-HALLUCINATION-ASSURANCE-2026-10-06.json"
CAST_SOURCE = ARCH / "FA3-DONOR-CAST-CHROMECAST-ORCHESTRATOR-2026-09-29.json"
MEDIA_SOURCE = ARCH / "FA3-DONOR-MEDIA-INTAKE-2026-09-29.json"
OWNER_RECOVERY = ROOT / "canonical/registries/CFA3-DONOR-L1-HISTORICAL-OWNER-URL-RECOVERY-20261010.json"
PR_OWNER_TRANSFER = ROOT / "canonical/registries/CFA3-DONOR-L1-HISTORICAL-PR-744-745-OWNER-TRANSFER-20261010.json"
# SHA256 over historical GitHub commit ce8b8a888a8c762393a4fa4c80e5a1c08a64dbed:
# ordered 48 original URL occurrences and sorted 36 proposed original donor IDs.
TRIPO_URL_ORDER_SHA256 = "f78ba37406396b871e390f8619eff9c2d7b87d9b4db9e165ef6bff5ac742c433"
TRIPO_ORIGINAL_IDS_SHA256 = "dd1d422a7aa9c43a14eefd8aab91c2d91a49729c073d8fa9ef4bdb44fbe7e5a9"
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


def historical_digest(items):
    """SHA256 of UTF-8 newline-separated historical values, including the final newline."""
    return hashlib.sha256(("\n".join(items) + "\n").encode("utf-8")).hexdigest()

def classify(entry):
    hints = " ".join(str(v) for key in ("donor_modes", "capability_hints", "domain_hints",
                                        "problem_hints", "target_hints", "tags") for v in entry.get(key, []))
    hints = hints.upper()
    out = [label for label, tokens in CLASS_MAP if any(token in hints for token in tokens)]
    # Absence of sufficient evidence must not manufacture an authoritative class.
    return out

def explicit_legacy_donor_marker(entry):
    """Recognize a recorded old-CFA3 owner command, not mere reference suggestions."""
    review = entry.get("submission_review", {})
    marker = str(review.get("reported_owner_marker", "")).strip().casefold()
    return marker in {
        "donornak", "vedd fel donornak", "add a donorlistához",
        "all-links-in-conversation-donornak", "donornak és sdk-ba",
    }


def owner_message_recovery():
    """Immutable historical owner-message L1 evidence; no runtime admission."""
    record = json_read(OWNER_RECOVERY)
    if (record.get("schema") != "cfa3.donor-l1-historical-owner-message-recovery.v1"
            or record.get("status") != "STAGED_NOT_PUBLISHED"
            or record.get("old_repository_read_only") is not True
            or record.get("canonical_level_published") is not False
            or record.get("original_L1_B") is not None
            or record.get("runtime_admission") is not False
            or record.get("novel_identity_count") != 3
            or record.get("existing_identity_override_count") != 1
            or record.get("total_approved_url_occurrences") != 4
            or len(record.get("entries", [])) != 3
            or len(record.get("existing_source_approval_overrides", [])) != 1):
        raise ValueError("Historical L1 owner recovery coverage or admission boundary mismatch")
    expected = {
        "https://github.com/ExistentialAudio/BlackHole": ("CFA3-DONOR-EXISTENTIALAUDIO-BLACKHOLE-001", "github:existentialaudio/blackhole"),
        "https://github.com/ExistentialAudio": ("CFA3-DONOR-EXISTENTIALAUDIO-ORG-001", "github:existentialaudio"),
        "https://github.com/upstash": ("CFA3-DONOR-UPSTASH-ORG-001", "github:upstash"),
    }
    for entry in record["entries"]:
        src = entry["source"]
        if (expected.pop(src["locator"], None) != (entry["donor_id"], src["normalized_key"])
                or entry.get("status") != "OWNER_APPROVED_PENDING_PUBLICATION"
                or entry.get("submission_review", {}).get("reported_owner_marker") not in
                   {"a beszélgetéshez tartozó linkeket donornak", "donor:"}
                or entry.get("runtime_admission") is not False
                or entry.get("intake_provenance", {}).get("canonical_approval_admitted") is not False):
            raise ValueError("Historical owner source identity or marker tampered")
    if expected:
        raise ValueError("Historical approved source lost")
    override = record["existing_source_approval_overrides"][0]
    if (override.get("donor_id") != "FA3-DONOR-OPENCUT-001"
            or override.get("normalized_key") != "github:opencut-app/opencut"
            or override.get("historical_locator") != "https://github.com/OpenCut-app/OpenCut"
            or override.get("original_owner_url") != "https://github.com/opencut-app/opencut"
            or override.get("historical_status") != "CANDIDATE"
            or override.get("new_status") != "OWNER_APPROVED_PENDING_PUBLICATION"
            or override.get("owner_marker") != "donornak és sdk-ba"
            or override.get("old_record_immutable") is not True):
        raise ValueError("Historical OpenCut original status or owner decision changed")
    return record


def historical_pr_owner_approvals():
    """Historical owner decisions survive old unmerged PRs without old-repo writes."""
    manifest = json_read(PR_OWNER_TRANSFER)
    if (manifest.get("schema") != "cfa3.donor-l1-historical-pr-owner-approved-transfer.v1"
            or manifest.get("status") != "STAGED_NOT_PUBLISHED"
            or manifest.get("old_repository_read_only") is not True
            or manifest.get("canonical_level_published") is not False
            or manifest.get("original_L1_B") is not None
            or manifest.get("new_identity_count") != 0
            or manifest.get("preexisting_staged_identity_count") != 2
            or manifest.get("owner_approval_status") != "OWNER_APPROVED_PENDING_PUBLICATION"
            or manifest.get("no_second_owner_approval_required") is not True
            or manifest.get("no_code_import") is not True
            or manifest.get("no_sdk_adoption") is not True
            or manifest.get("no_runtime_admission") is not True
            or len(manifest.get("records", [])) != 2):
        raise ValueError("Legacy PR donor approval transfer boundary mismatch")
    expected = {
        744: ("FA3-DONOR-AFFAAN-M-ECC-001", "github:affaan-m/ecc",
              "f294c3eef3875990725b1f7150824bdade6bbbc6"),
        745: ("FA3-DONOR-MOHAMEDELAASSAL-YOUTUBE-VIDEO-GENERATOR-001",
              "github:mohamedelaassal/youtubevideogenerator",
              "71d83d4bec340e08723cd94e8497d4058678be48"),
    }
    seen = set()
    for row in manifest["records"]:
        pr = row["old_pr"]
        if pr not in expected or pr in seen:
            raise ValueError("Unexpected or repeated historical owner-approved PR")
        seen.add(pr)
        ident, key, blob = expected[pr]
        frozen = ARCH / ("PR-" + str(pr) + "-ADDITIONAL-REFERENCE.json")
        actual = json_read(frozen)
        if (sha_blob(frozen.read_bytes()) != blob or row["source_blob"] != blob
                or actual["entry"]["donor_id"] != ident
                or actual["entry"]["source"]["normalized_key"] != key
                or actual["entry"]["source"]["locator"] != row["url"]
                or row["id"] != ident or row["normalized_key"] != key
                or actual["entry"]["status"] != "ACCEPTED_REFERENCE"
                or actual["entry"]["submission_review"].get("owner_donor_command") != "donornak"
                or row["historical_owner_marker"] != "donornak"
                or row["new_staging_status"] != "OWNER_APPROVED_PENDING_PUBLICATION"
                or row["previous_staging_status"] != "BLOCKED"):
            raise ValueError("Historical donor approval or source identity changed")
        aliases = row.get("additional_exact_search_aliases", [])
        if pr == 745 and aliases != ["https://github.com/mohamedelaassal/youtubevideogenerator"]:
            raise ValueError("Original GitHub path alias not preserved")
        if pr == 744 and aliases:
            raise ValueError("Unexpected ECC alias")
    if seen != {744, 745}:
        raise ValueError("Historical approved PRs not fully represented")
    return manifest["records"]


def frozen_sources():
    raw = REGISTRY.read_bytes()
    if sha_blob(raw) != EXPECTED[REGISTRY.name]:
        raise ValueError("Immutable donor archive Git blob mismatch")
    entries = json.loads(raw)["entries"]
    if len(entries) != 1919:
        raise ValueError("Unexpected root source registry size")
    sources = [(e, "OLD_MAIN_ARCHIVE", True) for e in entries]
    approved_prs = {row["old_pr"]: row for row in historical_pr_owner_approvals()}
    for n, file in zip((744, 745), EXTRAS):
        record = json_read(file)
        if (record["pr"] != n or record["state"] !=
                "UNMERGED_HISTORICAL_PR_PRESERVED_NOT_CFA3_CANONICAL_ADMITTED"
                or n not in approved_prs):
            raise ValueError("Unverified historical PR source")
        sources.append((record["entry"], f"HISTORICAL_PR_{n}_OWNER_APPROVED_TRANSFER", False))
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
        origin = ("HISTORICAL_OWNER_APPROVED_TRANSFER" if explicit_legacy_donor_marker(record)
                  else "HISTORICAL_OWNER_APPROVAL_RECONCILIATION_PENDING")
        sources.append((record, origin, False))
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
        origin = ("ADDITIONAL_OWNER_APPROVED_TRANSFER" if explicit_legacy_donor_marker(record)
                  else "ADDITIONAL_OWNER_APPROVAL_RECONCILIATION_PENDING")
        sources.append((record, origin, False))
    recovery = json_read(TRIPO_RECOVERY)
    transfer = recovery.get("legacy_owner_approval_transfer", {})
    if (transfer.get("owner_confirmation_date") != "2026-10-10"
            or transfer.get("historical_owner_marker") != "donornak"
            or transfer.get("historical_delta_blob_sha") != "668910c71dda1e83181a0113a06c8b14433ddbca"
            or transfer.get("new_unmatched_source_count") != 30
            or transfer.get("current_stage_approval_state") != "OWNER_APPROVED_PENDING_PUBLICATION"
            or transfer.get("no_second_donor_approval_required") is not True
            or transfer.get("canonical_level_published") is not False
            or transfer.get("runtime_admission") is not False
            or transfer.get("old_repository_mutations_permitted") is not False):
        raise ValueError("Legacy Tripo owner approval must transfer without premature publication")
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
    # Immutable historic 36-ID set: the collapsed Tripo topic remains an alias/reference,
    # not a replacement for any of the three distinct archived URL identities.
    historical_ids = ([e["donor_id"] for e in recovery["entries"]] +
        [e["legacy_proposed_donor_id"] for e in recovery["existing_identity_matches"]] +
        [aggregate["historical_proposed_donor_id"]])
    if (len(historical_ids) != 36 or len(set(historical_ids)) != 36 or
            recovery.get("historical_original_identity_set_sha256") != TRIPO_ORIGINAL_IDS_SHA256 or
            historical_digest(sorted(historical_ids)) != TRIPO_ORIGINAL_IDS_SHA256):
        raise ValueError("Tripo immutable historical donor identity set mismatch")
    for record in recovery["entries"]:
        if (record.get("status") != "OWNER_APPROVAL_REPORTED_PENDING_SOURCE_EVIDENCE"
                or record.get("submission_review", {}).get("reported_owner_marker") != "donornak"
                or record.get("submission_review", {}).get("exact_submitted_URL_and_approval_pair_independently_verified") is not False
                or record.get("intake_provenance", {}).get("canonical_approval_admitted") is not False
                or record.get("authority") is not False
                or record.get("runtime_admission") is not False):
            raise ValueError("Historical Tripo candidate must remain blocked")
        sources.append((record, "HISTORICAL_TRIPO_OWNER_APPROVED_TRANSFER", False))
    owner = owner_message_recovery()
    existing_opencut = [entry for entry, origin, previous in sources
                        if entry["donor_id"] == "FA3-DONOR-OPENCUT-001"]
    if (len(existing_opencut) != 1 or existing_opencut[0]["status"] != "CANDIDATE"
            or existing_opencut[0]["source"]["normalized_key"] != "github:opencut-app/opencut"):
        raise ValueError("Historical OpenCut identity or status mismatch")
    for entry in owner["entries"]:
        sources.append((entry, "HISTORICAL_OWNER_MESSAGE_APPROVED_TRANSFER", False))
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
    ordered_urls = [record["original_url"] for record in manifest["url_provenance"]]
    if (len(ordered_urls) != 48 or
            manifest.get("historical_digest_encoding") != "SHA256_UTF8_NEWLINE_JOINED_WITH_TRAILING_NEWLINE" or
            manifest.get("historical_url_order_sha256") != TRIPO_URL_ORDER_SHA256 or
            historical_digest(ordered_urls) != TRIPO_URL_ORDER_SHA256):
        raise ValueError("Tripo immutable historical URL sequence mismatch")
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


def register_owner_message_urls(db):
    record = owner_message_recovery()
    pairs = [(e["donor_id"], e["source"]["locator"]) for e in record["entries"]]
    pairs.append((record["existing_source_approval_overrides"][0]["donor_id"],
                  record["existing_source_approval_overrides"][0]["original_owner_url"]))
    for sid, url in pairs:
        db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (url,sid))
        db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                   (sid,url,"HISTORICAL_OWNER_MESSAGES_20261007","EXPLICIT_DONOR_COMMAND"))
    return len(pairs)


def register_historical_pr_owner_urls(db):
    """Preserve original mixed-case locator and user-submitted GitHub case alias."""
    for record in historical_pr_owner_approvals():
        for url in [record["url"], *record.get("additional_exact_search_aliases", [])]:
            db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (url, record["id"]))
            db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                       (record["id"],url,"HISTORICAL_OWNER_APPROVED_PR_"+str(record["old_pr"]),
                        "EXPLICIT_DONORNAK_LEGACY_PR_MIGRATION"))


def register_shgaf_original_urls(db):
    """Preserve the exact owner-approved SHGAF source URLs, including topic query views."""
    if sha_blob(SHGAF_SOURCE.read_bytes()) != "3652f591b08acff0de53910a68c03cec84de9971":
        raise ValueError("SHGAF historical source evidence changed")
    delta = json_read(SHGAF_SOURCE)
    if (delta.get("delta_id") != "CFA3-DONOR-SHGAF-HALLUCINATION-ASSURANCE-2026-10-06"
            or delta.get("submitted_url_count") != 20
            or len(delta.get("submitted_urls", [])) != 20
            or delta.get("canonical_identity_count") != 18
            or len(delta.get("canonical_identities", [])) != 18):
        raise ValueError("SHGAF donor source schema or identity count mismatch")
    bindings = {}
    for record in delta["canonical_identities"]:
        sid = record["donor_id"]
        for url in [record["source"], *record.get("submitted_views", [])]:
            if url in bindings and bindings[url] != sid:
                raise ValueError("Conflicting historical SHGAF source URL: " + url)
            bindings[url] = sid
    if set(bindings) != set(delta["submitted_urls"]):
        raise ValueError("Missing or extra historical SHGAF submitted URLs")
    for url, sid in bindings.items():
        if db.execute("SELECT 1 FROM sources WHERE source_id=?", (sid,)).fetchone() is None:
            raise ValueError("SHGAF historical donor identity missing: " + sid)
        db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (url, sid))
        db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                   (sid, url, "HISTORICAL_SHGAF_20261006", "HISTORICAL_SOURCE_DELTA"))
    return len(bindings)



def register_cast_original_urls(db):
    """Preserve original CAST/Chromecast/Orchestrator filtered topic URLs."""
    if sha_blob(CAST_SOURCE.read_bytes()) != "81d5890e38d70573f6a9a00f77ff14ed467cb59c":
        raise ValueError("CAST historical source evidence changed")
    delta = json_read(CAST_SOURCE)
    if (delta.get("delta_id") != "FA3-DONOR-CAST-CHROMECAST-ORCHESTRATOR-2026-09-29"
            or delta.get("source_count") != 9
            or delta.get("unique_source_key_count") != 8
            or len(delta.get("sources", [])) != 8):
        raise ValueError("CAST donor source schema or identity count mismatch")
    bindings = {}
    for record in delta["sources"]:
        sid = record["donor_id"]
        stored = db.execute(
            "SELECT normalized_key,historical_status,current_status FROM sources "
            "WHERE source_id=?", (sid,)).fetchone()
        if (stored != (record["normalized_source_key"], "CANDIDATE", "CANDIDATE")
                or record["lifecycle_status"] != "CANDIDATE"
                or record["source_code_copy_allowed"] is not False):
            raise ValueError("CAST historical candidate identity or status mismatch: " + sid)
        for url in record["urls"]:
            if url in bindings and bindings[url] != sid:
                raise ValueError("Conflicting CAST historical source URL: " + url)
            bindings[url] = sid
    if len(bindings) != 9:
        raise ValueError("CAST historical source URL coverage mismatch")
    for url, sid in bindings.items():
        db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (url, sid))
        db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                   (sid, url, "HISTORICAL_CAST_CHROMECAST_20260929",
                    "HISTORICAL_SOURCE_DELTA"))
    return len(bindings)



def register_media_intake_original_urls(db):
    """Preserve exact media-intake URLs; reuse existing overlapped DeepFilterNet identity."""
    if sha_blob(MEDIA_SOURCE.read_bytes()) != "8a5c8c2dd2f5429f9d11f2ffd35388bb2b346d17":
        raise ValueError("Media-intake historical source evidence changed")
    delta = json_read(MEDIA_SOURCE)
    if (delta.get("delta_id") != "FA3-DONOR-MEDIA-INTAKE-2026-09-29"
            or delta.get("source_count") != 58
            or len(delta.get("sources", [])) != 58):
        raise ValueError("Media-intake source schema or count mismatch")
    seen_urls, seen_keys = set(), set()
    for record in delta["sources"]:
        original_url = record["url"]
        key = record["normalized_source_key"]
        if original_url in seen_urls or key in seen_keys:
            raise ValueError("Media-intake URL or normalized key repeated")
        seen_urls.add(original_url)
        seen_keys.add(key)
        match = db.execute(
            "SELECT source_id,historical_status,current_status FROM sources "
            "WHERE normalized_key=?", (key,)).fetchone()
        if (match is None or match[1:] != ("CANDIDATE", "CANDIDATE")
                or record["lifecycle_status"] != "CANDIDATE"
                or record["source_copy_allowed"] is not False):
            raise ValueError("Media-intake candidate identity or status mismatch: " + key)
        sid = match[0]
        if key == "github:rikorose/deepfilternet":
            if (sid != "FA3-DONOR-PROD-QUALITY-RIKOROSE-DEEPFILTERNET-001"
                    or record["overlap_pending_pr"] != 528):
                raise ValueError("DeepFilterNet overlap identity or PR lineage mismatch")
        prior = {x[0] for x in db.execute(
            "SELECT source_id FROM aliases WHERE alias=?", (original_url,))}
        if prior and prior != {sid}:
            raise ValueError("Media-intake original URL aliases a different donor: " + original_url)
        db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?)", (original_url, sid))
        db.execute("INSERT OR IGNORE INTO source_provenance VALUES(?,?,?,?)",
                   (sid, original_url, "HISTORICAL_MEDIA_INTAKE_20260929",
                    "HISTORICAL_SOURCE_DELTA"))
    return len(seen_urls)


def build_url_resolution(db):
    """Deterministic exact-URL lookup; never collapse multiple historical IDs.

    Explicit prior-owner URL resolution wins over incidental discovery links.
    Remaining multi-owner locators are a fail-closed conflict, not a guess.
    """
    preferred = {}
    for row in json_read(UNION)["source_coverage"]:
        for url in row["original_locators"]:
            target = (row["resolved_donor_id"], "HISTORICAL_OWNER_BASELINE")
            if url in preferred and preferred[url] != target:
                raise ValueError("Conflicting historical owner URL resolution: " + url)
            preferred[url] = target
    for row in json_read(TRIPO_RECOVERY)["url_provenance"]:
        url = row["original_url"]
        target = (row["source_id"], "HISTORICAL_TRIPO_OWNER_URL")
        if url in preferred and preferred[url][0] != target[0]:
            raise ValueError("Conflicting historical Tripo URL resolution: " + url)
        preferred.setdefault(url, target)
    for source in historical_pr_owner_approvals():
        for url in [source["url"], *source.get("additional_exact_search_aliases", [])]:
            if url in preferred and preferred[url][0] != source["id"]:
                raise ValueError("Owner-approved PR URL resolution conflicts: " + url)
            preferred[url] = (source["id"], "HISTORICAL_PR_OWNER_APPROVAL")
    owner_new = owner_message_recovery()
    approvals = [(e["source"]["locator"],e["donor_id"]) for e in owner_new["entries"]]
    approvals.extend((e["original_owner_url"],e["donor_id"])
                     for e in owner_new["existing_source_approval_overrides"])
    for url,sid in approvals:
        if url in preferred and preferred[url][0] != sid:
            raise ValueError("Owner message vs historical registry URL conflict: " + url)
        preferred[url] = (sid, "HISTORICAL_OWNER_MESSAGE")
    exact_locators = {}
    exact_keys = {}
    for sid, locator, key in db.execute(
            "SELECT source_id,locator,normalized_key FROM sources"):
        exact_locators.setdefault(locator, set()).add(sid)
        exact_keys.setdefault(key, set()).add(sid)
    mapping = {}
    for url, sid in db.execute("SELECT alias,source_id FROM aliases ORDER BY alias,source_id"):
        mapping.setdefault(url, []).append(sid)
    for url, ids in mapping.items():
        if url in preferred:
            primary, reason = preferred[url]
        elif url in exact_locators and len(exact_locators[url]) == 1:
            primary, reason = next(iter(exact_locators[url])), "EXACT_SOURCE_LOCATOR"
        elif url in exact_keys and len(exact_keys[url]) == 1:
            primary, reason = next(iter(exact_keys[url])), "EXACT_NORMALIZED_SOURCE_KEY"
        elif len(ids) == 1:
            primary, reason = ids[0], "SINGLE_DISCOVERY_REFERENCE"
        else:
            raise ValueError("Unresolved multi-source URL; owner mapping required: " + url)
        if primary not in ids:
            raise ValueError("URL resolution target not indexed: " + url)
        db.execute("INSERT INTO url_resolution VALUES(?,?,?,?)",
                   (url,primary,reason,json.dumps(ids,ensure_ascii=False)))
    return len(mapping)


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
      CREATE TABLE url_resolution(
        alias TEXT PRIMARY KEY,
        preferred_source_id TEXT NOT NULL REFERENCES sources(source_id),
        authority TEXT NOT NULL,
        related_source_ids_json TEXT NOT NULL);
      CREATE INDEX url_resolution_preferred_idx ON url_resolution(preferred_source_id);
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
    owner_override = owner_message_recovery()["existing_source_approval_overrides"][0]
    for entry, origin, from_main in sources:
        sid = entry["donor_id"]
        src = entry["source"]
        original = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
        approved_origins = {
            "HISTORICAL_TRIPO_OWNER_APPROVED_TRANSFER",
            "HISTORICAL_OWNER_APPROVED_TRANSFER",
            "ADDITIONAL_OWNER_APPROVED_TRANSFER",
            "HISTORICAL_OWNER_MESSAGE_APPROVED_TRANSFER",
            "HISTORICAL_PR_744_OWNER_APPROVED_TRANSFER",
            "HISTORICAL_PR_745_OWNER_APPROVED_TRANSFER",
        }
        is_override = (from_main and sid == owner_override["donor_id"]
                       and src["normalized_key"] == owner_override["normalized_key"]
                       and entry["status"] == owner_override["historical_status"])
        status = ("OWNER_APPROVED_PENDING_PUBLICATION" if is_override else
                  entry["status"] if from_main else
                  "OWNER_APPROVED_PENDING_PUBLICATION" if origin in approved_origins
                  else "BLOCKED")
        db.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid,src["normalized_key"],src["locator"],entry.get("name",""),entry["status"],
             status,src.get("kind"),origin,1,original,digest,run_id))
        for alias in {src["normalized_key"],src["locator"], *src.get("discovery_urls", [])}:
            db.execute("INSERT INTO aliases VALUES(?,?)",(alias,sid))
        for klass in classify(entry):
            db.execute("INSERT INTO classes VALUES(?,?,?)",(sid,klass,"HINT_BASED_UNVERIFIED"))
    register_historical_urls(db, sources)
    register_tripo_historical_urls(db, sources)
    register_owner_message_urls(db)
    register_historical_pr_owner_urls(db)
    register_shgaf_original_urls(db)
    register_cast_original_urls(db)
    register_media_intake_original_urls(db)
    build_url_resolution(db)
    db.executemany("INSERT INTO metadata VALUES(?,?)",(
        ("schema","cfa3.donor-l1-index.v1"),
        ("run_id",run_id),
        ("input_link_occurrences_B","UNVERIFIED"),
        ("expansion_raw_limit","UNVERIFIED"),
        ("known_unique_source_identities",str(len(sources))),
        ("supplemental_owner_source_candidates","23"),
        ("additional_owner_source_leads","4"),
        ("total_pending_owner_source_candidates","4"),
        ("legacy_owner_approved_pending_publication","59"),
        ("historical_pr_744_745_owner_approved_transfer_sources","2"),
        ("additional_20261007_owner_approved_source_records","3"),
        ("historical_opencut_approval_overrides","1"),
        ("supplement_and_additional_owner_markers_without_primary_pair","23"),
        ("historical_tripo_new_pending_sources","0"),
        ("historical_tripo_owner_approved_transfer_sources","30"),
        ("historical_supplement_owner_approved_transfer_sources","19"),
        ("additional_owner_approved_transfer_sources","4"),
        ("historical_tripo_original_occurrences","48"),
        ("historical_shgaf_submitted_urls","20"),
        ("historical_cast_submitted_url_views","9"),
        ("historical_media_intake_original_urls","58"),
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
                expected_status = ("OWNER_APPROVED_PENDING_PUBLICATION"
                                   if explicit_legacy_donor_marker(entry) else "BLOCKED")
                if row != (expected_status, url):
                    raise ValueError("Historical owner approval transfer or source lookup mismatch: " + donor_id)
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
            if row != ("OWNER_APPROVED_PENDING_PUBLICATION", item["source"]["normalized_key"]):
                raise ValueError("Historical Tripo source missing or improperly admitted")
        old_aggregate_id = recovery["historical_aggregate_reconciliation"]["historical_proposed_donor_id"]
        if db.execute("SELECT 1 FROM sources WHERE source_id=?", (old_aggregate_id,)).fetchone():
            raise ValueError("Non-canonical historical Tripo aggregate was improperly admitted")
        alias_total = db.execute("SELECT count(DISTINCT alias) FROM aliases").fetchone()[0]
        resolved_rows = list(db.execute(
            "SELECT alias,preferred_source_id,related_source_ids_json FROM url_resolution"))
        if len(resolved_rows) != alias_total:
            raise ValueError("URL resolution index coverage incomplete")
        ambiguous = sum(len(json.loads(ids)) > 1 for _,_,ids in resolved_rows)
        if ambiguous != 5:
            raise ValueError("Unexpected number of historical multi-source URL relations")
        for rec in union["source_coverage"]:
            for original in rec["original_locators"]:
                actual = db.execute(
                    "SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                    (original,)).fetchone()
                if actual != (rec["resolved_donor_id"],):
                    raise ValueError("Historical primary URL selection mismatch: " + original)
        for rec in recovery["url_provenance"]:
            actual = db.execute(
                "SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                (rec["original_url"],)).fetchone()
            if actual != (rec["source_id"],):
                raise ValueError("Tripo primary URL selection mismatch")
        for item in historical_pr_owner_approvals():
            sid = item["id"]
            row = db.execute("SELECT current_status FROM sources WHERE source_id=?",
                             (sid,)).fetchone()
            if row != ("OWNER_APPROVED_PENDING_PUBLICATION",):
                raise ValueError("Legacy PR owner donor must be approved: " + sid)
            for url in [item["url"], *item.get("additional_exact_search_aliases", [])]:
                if db.execute("SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                              (url,)).fetchone() != (sid,):
                    raise ValueError("Historical PR URL not directly searchable: " + url)
        owner = owner_message_recovery()
        recovered = [(entry["donor_id"],entry["source"]["locator"]) for entry in owner["entries"]]
        recovered.append((owner["existing_source_approval_overrides"][0]["donor_id"],
                          owner["existing_source_approval_overrides"][0]["original_owner_url"]))
        for sid,url in recovered:
            status = db.execute("SELECT current_status FROM sources WHERE source_id=?", (sid,)).fetchone()
            if status != ("OWNER_APPROVED_PENDING_PUBLICATION",):
                raise ValueError("Missing legacy owner approval transfer: " + sid)
            if not db.execute("SELECT 1 FROM source_provenance WHERE source_id=? AND original_url=?",
                              (sid,url)).fetchone():
                raise ValueError("Historical owner URL provenance missing: " + url)
            primary = db.execute("SELECT preferred_source_id FROM url_resolution WHERE alias=?",
                                 (url,)).fetchone()
            if primary != (sid,):
                raise ValueError("Historical owner URL lookup missing: " + url)
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
            "historical_tripo_pending_sources":0,
            "historical_tripo_owner_approved_transfer_sources":30,
            "historical_supplement_owner_approved_transfer_sources":19,
            "additional_owner_approved_transfer_sources":4,
            "legacy_owner_approved_pending_publication":59,
            "historical_pr_owner_approved_transfer_sources":2,
            "additional_20261007_owner_approved_source_records":3,
            "historical_opencut_approval_overrides":1,
            "legacy_reference_only_pending_sources":4,
            "historical_tripo_url_occurrences":48,
            "historical_tripo_provenance":"BOUNDED_48_PASS",
            "historical_unique_source_ids":distinct_ids,
            "hint_classified":classified_count,
            "class_index":"PARTIAL_UNVERIFIED","record_integrity":"PASS",
            "url_resolution_aliases":alias_total,"ambiguous_urls_with_preserved_relations":ambiguous}

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
        if by == "url":
            query = ("SELECT s.source_id,s.locator,s.current_status FROM sources s "
                     "JOIN url_resolution r ON r.preferred_source_id=s.source_id WHERE r.alias=?")
        elif by == "alias":
            query = ("SELECT s.source_id,s.locator,s.current_status FROM sources s "
                     "JOIN aliases a ON a.source_id=s.source_id WHERE a.alias=? ORDER BY s.source_id")
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
