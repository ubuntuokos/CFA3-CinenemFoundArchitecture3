#!/usr/bin/env python3
"""Owner-approved net-new unique-source expansion filter (staging only).

This module does not crawl, approve, classify, write to the donor database,
publish a level, or grant SDK/model/provider/runtime admission.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_lifecycle import normalize_url

def evaluate(raw_links, known_aliases, *, frozen_l1_b, level, previous_gate,
             index_complete):
    """Filter ordered {url,parent_id,evidence} links against complete known aliases.

    Identical novel normalized locators count only once. Identity beyond known
    aliases must be separately reconciled before canonical publication.
    """
    if isinstance(frozen_l1_b, bool) or not isinstance(frozen_l1_b, int) or frozen_l1_b < 1:
        raise ValueError("Frozen original L1 link-record count B is required")
    if isinstance(level, bool) or not isinstance(level, int) or not 2 <= level <= 5:
        raise ValueError("Only global L2-L5 can evaluate next-level references")
    if previous_gate != "PUBLISHED_AND_VERIFIED_PASS":
        return {"state":"BLOCKED_PREVIOUS_LEVEL_UNVERIFIED","new_sources":[]}
    if index_complete is not True:
        return {"state":"BLOCKED_INDEX_INCOMPLETE","new_sources":[]}
    if level == 5 and raw_links:
        return {"state":"BLOCKED_L6_FORBIDDEN","new_sources":[]}
    canonical = {}
    for alias, source_id in known_aliases.items():
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("Known source ID missing")
        key = normalize_url(alias)
        if key in canonical and canonical[key] != source_id:
            return {"state":"UNRESOLVED_IDENTITY_CONFLICT","new_sources":[]}
        canonical[key] = source_id
    limit = (frozen_l1_b * 115) // 100
    new_keys = set()
    new_sources = []
    relations = []
    previously_known = 0
    for i, record in enumerate(raw_links):
        if not isinstance(record, dict) or not record.get("parent_id") or not record.get("evidence"):
            raise ValueError("Every link requires parent and evidence")
        original = record["url"]
        normalized = normalize_url(original)
        resolved = canonical.get(normalized)
        relations.append({"parent_id":record["parent_id"],"original_url":original,
                          "normalized_url":normalized,"known_source_id":resolved,
                          "evidence":record["evidence"]})
        if resolved is not None:
            previously_known += 1
            continue
        if normalized in new_keys:
            continue
        new_keys.add(normalized)
        new_sources.append({"normalized_url":normalized,"original_url":original,
                            "global_level":level,"status":"DISCOVERED_UNREGISTERED"})
        if len(new_sources) > limit:
            return {"state":"STOPPED_EXPANSION_LIMIT","B":frozen_l1_b,"limit":limit,
                    "first_exceeding_count":len(new_sources),
                    "raw_examined_at_stop":i+1,"violation_url":original,
                    "new_sources":[],"observed_relations":relations,
                    "previously_published_snapshot_preserved":True}
    return {"state":"EARLY_EXHAUSTION_CANDIDATE" if not new_sources else "STAGED_NOT_PUBLISHED",
            "B":frozen_l1_b,"limit":limit,"raw_link_occurrences":len(relations),
            "known_occurrences":previously_known,"net_new_unique_count":len(new_sources),
            "new_sources":new_sources,"observed_relations":relations,
            "publication_gate":"PENDING"}
