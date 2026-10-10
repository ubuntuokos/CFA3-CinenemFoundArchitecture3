# CFA3 donor migration and bounded classification — FINAL owner-approved technical plan

- **Plan ID:** `CFA3-DONOR-MIGRATION-AND-CLASSIFICATION-V2-001`
- **Owner approval:** 2026-10-09. Design decision: `canonical/decisions/CFA3-DEC-DONOR-MIGRATION-AND-CLASSIFICATION-V2-20261009.json`.
- **New target:** `ubuntuokos/CFA3-CinenemFoundArchitecture3`
- **Old source repository:** `ubuntuokos/Final-Architecture-v3.0` (read-only extraction; its repair, PR completion or main reconciliation is **not** a migration dependency).
- **Design status:** FINAL OWNER-APPROVED TECHNICAL PLAN. Only the design is final; the actual donor migration, L1 publication, L2–L5 execution and working search index remain PENDING.
- **Repository status:** Owner-approved design in an open Draft PR, not merged into main. No donor records have been transferred by this change.
- **Identifier continuity:** Existing V2-001 ID is retained; later owner clarifications are consolidated here without creating a competing or duplicated plan.
- **Technical policy:** `canonical/policies/CFA3-DONOR-BOUNDED-CLASSIFICATION-001.json`.
- **Related approved lifecycle:** `CFA3-SOURCE-LIFECYCLE-POLICY-001`.

## Végleges műszaki összefoglaló (HU)

**Feladat:** a régi repository összes felhasználó által jóváhagyott donoradatának veszteségmentes átmentése az új CFA3-ba, a régi repo javítása nélkül. A régi hibás konfiguráció, végrehajtási kód, felesleges alkalmazás és duplikáció nem örökölhető. Az eredeti rekordok és döntések megmaradnak, az új adatbázis tisztított.

**Szigorúan egymás után:** L1 besorolás → publikálás és valódi visszakeresési teszt → L2 → L3 → L4 → L5. A következő szint csak az előző bizonyított PUBLISHED_AND_VERIFIED_PASS eredménye után indulhat. A már feldolgozott link korábbi döntését nem írjuk felül.

**Egyetlen globális ötszintű lánc:** csak az eredeti L1-források alkotnak induló gyökeret. L2-ben talált donor 4 szintet (L2–L5), L3-ban 3-at, L4-ben 2-t, L5-ben 1-et (csak L5) érhet el az aktuális szinttel együtt. Egy új donor, új kapcsolat vagy jóváhagyás nem indíthat új öt szintet. L6 tilos.

**Kibontási STOP (tulajdonosi felülírás 2026-10-09):** A befagyasztott eredeti L1 bemeneti linkrekordszám `B`. Az összes nyers URL és kapcsolati evidencia megmarad, de a 15%-os korlát kizárólag a teljes ismert donorindexszel és aliasokkal egyeztetett, **új, egyedi, korábban fel nem dolgozott forrásokra** vonatkozik. `LIMIT=floor(B×1,15)`, szintenként, nem kumulálva. Már feldolgozott donor nem elemzendő újra; 0 új forrásnál az ág kimerült (publikálási ellenőrzés még kötelező). Hiányos index = STOP.

**Szintenkénti érvényesítés:** csak az eredetileg jóváhagyott donor lesz elfogadott donor; a további feltárt technológiák osztályozott, külön státuszú források. A publikált rekordok kanonikus azonosító, eredeti URL, alias, besorolás és szülőkapcsolat szerint visszakereshetők. Következő szint csak sikeres ellenőrzés után.

**Fontos állapothatár:** a végleges terv és a sikeres strukturális CI nem jelenti a donorok tényleges migrációját, hálózati kibontását, licencengedélyét vagy runtime-admissionjét.

---

## Mandate, allowed scope and completion boundary

**Main task:** rescue all historical owner-approved donor/source links into a newly designed, nonduplicating CFA3 donor registry; then perform strictly sequential L1–L5 link inspection, classification, publishing, verified availability and bounded further discovery.

**Requested result:** searchable donor records become usable as *references* after **each completed level**, without waiting for L5; all accepted source provenance and owner decisions preserved, no automatic runtime/admission.

**Permitted scope:** donor source records, source identities and URL aliases, source classifiers, provenance edges, read-only reference search, level queues/checkpoints, publication gate and evidence. Existing CFA3 app/engine/provider architecture may be referenced but not silently recreated or changed.

**Hard restrictions:** no old repository repair; no automatic reintroduction of old bad rules, stale settings, unnecessary applications or modules, old runtime code or fake PASS. No automatic child donor approval. No automatic license, provider, model, SDK, dependency or runtime admission. No sixth level. No uncontrolled network exploration.

**Completion:** fully covered owner-approved source set; L1–L5 (or proven exhaustion) verified and published in order; all acceptance checks pass. A rate STOP is *not* completion.

## 1. Preservation before cleanup

1. Capture the old donor registry, historical input submissions/approval commands, donor–application reference links, source deltas and distinct donor-approved PR-only records from **identified immutable Git commit/blob SHAs**.
2. Store original records and locators losslessly with their origin SHA, path, timestamps where present, explicit owner marker or historical approval evidence, original status and a cryptographic digest. This archive is **not** a second active canonical authority.
3. The old-main registry was observed as **1,919 records** at `a9c724da62bf49f3353c694990fc51443e634b4a`, with 1,919 unique registry source keys in that snapshot. PR #744 and #745 each introduce a distinct proposed accepted-reference record. These numbers are **historical observations, not proof of total user-submitted donor completeness**.
4. Reconcile every historical owner-approved submission. **The new canonical registry may contain more original submitted sources, never fewer**. Explicit prior `donornak` or `add a donorlistához` approval is preserved; ambiguous CANDIDATE entries remain candidate until resolved.
5. Import no old policies as active permissions, no old implementation or CI, and no old 175-capability certification. The new CFA3 200-capability design target remains unproven.

## 2. Canonical identity, classification and registers

Each logical source has **one canonical source ID** and can have multiple original URLs, verified aliases and parent/child references. Do not confuse **source identity**, **donor approval status**, **classification**, **strategic usefulness**, **app usage edge**, **rights/admission** or **runtime deployment**.

Each classification record must retain:
- canonical ID, normalized locator and raw original URLs, aliases and source kind;
- original historical approval evidence and unchanged prior decision reference;
- primary/secondary classes: SDK/API, shared module, engine, plugin/extension, AI model/provider, application reference, research/docs, discovery source, legacy/unsupported;
- L1–L5 discovery level, root ID, source-parent relations and link evidence;
- version/support/license/security observations with verified change/provenance;
- stable status: existing approved reference, analyzed, candidate, superseded, discovered-unregistered or blocked;
- source snapshot + classification revision, checkpoint/batch ID and publication/index version.

A **known link is not re-analyzed**. It may gain a newly observed parent relation without a new donor entity or decision overwrite. Verified upstream changes, relocation or discontinued support use the separate `CFA3-SOURCE-LIFECYCLE-POLICY-001` revision process. A genuinely useful unsupported project needs a replacement plan; modify upstream code only when verified rights permit, otherwise plan an independent native CFA3 substitute. **Previously discarded duplicate apps do not automatically return**.

## 3. Deterministic sequential levels

| Level | Input and permitted work | Closure |
| --- | --- | --- |
| **L1** | Frozen set of original donor source-link records. Preserve archive; identity/dedup; classify; register in appropriate status; identify further link-bearing roots. | **L1 PUBLISHED_AND_VERIFIED_PASS** |
| **L2** | Extract L1 outbound links; preserve raw URLs and provenance edges; resolve known IDs/aliases first; deduplicate and evaluate only truly new identities against the 15% net-new limit. | **L2 PUBLISHED_AND_VERIFIED_PASS** |
| **L3** | Only sources forwarded from L2, with the same guards. | **L3 PUBLISHED_AND_VERIFIED_PASS** |
| **L4** | Only sources forwarded from L3, with the same guards. | **L4 PUBLISHED_AND_VERIFIED_PASS** |
| **L5** | Final permitted level; classify and publish; terminate expansion permanently after L5. | **L5 FINAL PASS** |

## 3.1 Global depth never resets for newly discovered donors

**Owner clarification, 2026-10-09:** The five-level limit is **one global source-discovery chain rooted exclusively in the frozen original L1 inputs**. An additional donor found at L2, L3, L4 or L5 **must not** be treated as a new root with five more expansion levels. Newly approved/classified donors do not reset depth.

| Level of a newly found donor/source | Maximum remaining levels *including the current level* | Permitted absolute levels |
| --- | ---: | --- |
| L1, as an original frozen input | 5 | L1–L5 |
| L2 | 4 | L2–L5 |
| L3 | 3 | L3–L5 |
| L4 | 2 | L4–L5 |
| L5 | 1 | L5 only |

A child reached from a parent at global level `Li` belongs to global level `L(i+1)`, **never** to an invented new `L1`. An L5 source is classified and published as appropriate but **never produces an L6 processing queue**. There are no independent nested five-level discovery runs.

- Record a node's global discovery level and every verified parent/root provenance edge. Recording a newly discovered parent, re-encountering a known canonical source, approving a donor or publishing a level **does not reassign the source as a new L1 root or allocate additional five-level depth**.
- Only identities present in the original, frozen L1 input snapshot are legitimate original L1 roots. If such a source is rediscovered deeper in another path, it retains its **original** L1 root provenance; the deeper encounter adds only a verified relation and must not start a second crawl.
- Cycles and repeated references do not increase depth budget. Multiple verified parent paths may be retained, but cannot be used to invent new roots, reset depth or extend beyond L5.
- The next level may begin only after the prior level's `PUBLISHED_AND_VERIFIED_PASS`. The absolute depth of all queued sources and the fixed 15%-limit baseline must survive publication/restart unchanged.

**Noncompliance is a STOP:** any enqueue with global child level above L5, source promotion to a new discovery root, or donor-specific depth reset is prohibited.

Within a level, inspect *only actual relevant sources*; classify every processed source at its correct destination. Parents stay where classified; only references requiring a subsequent stage enter the next queue. The queue is **not an automatic donor registration list**.

**Order in each level:** preserve all raw links and parent references → complete known-source/alias/supersession lookup → retain known-source decisions and edges → deduplicate novel identities → check net-new 15% threshold → classify novel sources only → reversible indexed publication → independent read-back → level PASS → only then start next level.

If there are zero further relevant sources, end with documented `EARLY_EXHAUSTION_PASS` and no fabricated deeper levels. If a level fails any check, **STOP**, retain the last successfully published snapshot, do not start another level and do not silently skip sources.

## 4. EXACT 15% rule — net-new unique-source count (owner revision 2026-10-09)

**This section supersedes the previously approved raw outbound URL occurrence count.** Preserve every URL occurrence and every verified parent/child edge as evidence, but do not apply the quota to occurrences, known identities or within-level duplicates.

- Freeze `B` as the number of original L1 inbound **link records**, immutably identified. Do not infer B from the donor database size or count of unique identities.
- `LIMIT = floor(B * 115 / 100)` for each global level, independently, without restarting the baseline and without summing levels.
- Resolve the encountered URL against the **complete** historical/active identity index and verified aliases (including relocations and supersessions). Known sources retain their previous decisions; log each edge but do not re-analyze them.
- Deduplicate the remaining truly new source identities within the level. Only **net-new unique identities** count toward the limit; discovered URLs remain unapproved candidates without rights/SDK/provider/model/runtime admission.
- If the source index is incomplete, or identity conflict cannot be deterministically resolved, fail closed and do not call the unmatched links new.
- STOP immediately when the count of new unique identities becomes `LIMIT+1`; never truncate the actual source set to force PASS. Keep the previously verified published level intact.
- When zero new sources remain, record an `EARLY_EXHAUSTION_CANDIDATE`; it is not a final PASS until the applicable publication and independent read-back checks pass.
- **Approved examples, B=445 → LIMIT=511:** 650 links with 445 known → 205 new, permitted; 512 links all known → zero new, branch exhausted; 800 links with 151 known → 649 new, STOP at the 512th new identity. Original raw URLs remain preserved in every case.

## 5. Mandatory publish-and-read-back gate

`CFA3-DONOR-LEVEL-PUBLISH-GATE-001` applies to **every completed level**, including L1 and L5. A next level cannot begin until the preceding one produces **PUBLISHED_AND_VERIFIED_PASS**.

Publish only the original legitimately approved donor identities as approved. Unapproved discovered children are visible in a **separate classified-source view** with `DISCOVERED_UNREGISTERED` status, never as authorized donor dependencies.

Successful level publication requires:
1. Exhaustive accounted input and classification, resolved identity/dedup conflicts, prior decisions unchanged and all parent/child/root provenance preserved.
2. No net-new unique-source limit violation; the frozen baseline B, raw URL audit count, known/duplicate count, net-new count and limit must be recorded.
3. Staged data and indexes built under a versioned transaction or snapshot; no partial active indexes.
4. Actual **independent query/read-back** of the published canonical IDs, original/alias locators, classification and relations through the user/developer-accessible search interface.
5. Index and registry revision/digest agreement; no absent accepted donor or misrepresented statuses.
6. Durable `PASS` attestation naming the exact snapshot/level/index version, counts and evidence refs. Mere GitHub CI success or successful HTTP access to upstream is **not** equivalent to actual CFA3 registry publication.
7. If failed, keep the prior published snapshot and mark `BLOCKED_LEVEL_PUBLICATION`; do not begin the next level.

The accepted sources become available for developer reference search **immediately after each level gate passes**; L5 is not required for the earlier levels' usefulness. Using one in application code still requires the separate licensed, secured usage-edge/admission procedures.

## 6. Processing states and gates

`L1_INPUT_FROZEN → L1_CLASSIFIED_STAGED → L1_PUBLISHED_AND_VERIFIED_PASS → L2...`

Potential blocking states:
- `BLOCKED_IDENTITY_CONFLICT`
- `BLOCKED_UNVERIFIED_OLD_DECISION`
- `BLOCKED_LEVEL_PUBLICATION`
- `STOPPED_EXPANSION_LIMIT`
- `BLOCKED_UNCLASSIFIED_RELEVANT_SOURCE`
- `BLOCKED_INCOMPLETE_SOURCE_HISTORY`

Neither background retries nor automatic rebase, admission, repair of old repository, threshold override, new PR or unapproved restart are permitted.

## 7. Development phases (implementation separately admitted)

**A – Lossless recovery:** immutable snapshots, source audit ledger, explicit owner approval coverage.

**B – Clean schema and identity:** normalized source registry, aliases, categories, parent edges, old decision references. No active legacy code/config imported.

**C – L1 migration and initial publication:** seed approved/candidate records in their proper statuses; dedup; full Level Publish Gate; searchable, verified L1.

**D – New sequential L2–L5 engine:** *new implementation* using the approved algorithm. Old PR #743 is a historical reference, **not code to copy unchanged**. The historical 16-shard rollout was cancelled; no complete historical crawl graph may be claimed.

**E – Deterministic enforcement and tests:** prior identity lookup and novel dedup before threshold; STOP at net-new unique `LIMIT+1`; known-source skip, correct per-level counts, global L1–L5 depth, no new roots, no L6, no prior decision overwrite, publish/read-back and rights guards.

**F – L2–L5 level-by-level execution:** each level runs only after verified published prior level. Stop on exhaustion or limit without fabricating complete results.

**G – Independent audit and acceptance:** `MISSING_APPROVED_SOURCES=0`; `UNRESOLVED_IDENTITY_CONFLICTS=0`; `UNJUSTIFIED_DUPLICATES=0`; `UNCLASSIFIED_RELEVANT_SOURCES=0`; `BROKEN_SOURCE_RELATIONS=0`; `UNPUBLISHED_APPROVED_DONORS=0`; `INHERITED_BAD_LEGACY_CONFIGURATIONS=0`; complete level receipt chain; no stopped-expansion claimed as final PASS.

## 8. Negative and boundary test matrix

| Condition | Expected |
| --- | --- |
| `B=445`, 650 found, 445 previously known, 205 new | Permitted (limit 511) |
| `B=445`, 800 found, 151 known, 649 new | STOP at 512th new identity |
| `B=445`, 512 found, all known | Zero new; early-exhaustion candidate |
| L2 has 205 novel, L3 has 400 novel, B remains 445 | Each level independently below limit 511 |
| L2 classification succeeds but read-back fails | L3 blocked; previous snapshot retained |
| Same URL in two parent sources | One canonical identity; preserve both parent edges |
| Previously accepted link reappears | Retain prior approved decision; no re-review |
| New upstream version or relocation | Source-lifecycle change review; no silent overwrite |
| Third-party link discovered without donor approval | Classified unregistered candidate, not donor admission |
| Source no longer produces relevant links | Stop branch; document early exhaustion |
| Source discovered at L2 | Four remaining global levels (L2–L5), never five new levels |
| Source discovered at L3 | Three remaining global levels (L3–L5) |
| Source discovered at L4 | Two remaining global levels (L4–L5) |
| Source discovered at L5 | One final global level (L5), no descendants |
| Previously known L1 source discovered again at L4 | Original L1 root unchanged, new parent relation only; no new crawl |
| A newly discovered donor is owner-approved at L3 | Its depth stays L3; no independent five-level restart |
| Cycle or new parent path | Edge recorded; no new root and no global-depth extension |
| L5 exposes more references | No L6; final level does not spawn further queues |
| Incomplete original approval/source inventory | No donor-baseline FULL PASS |
| Network or CI completes without index read-back | Level publication gate fails |
| Failed L3/limit STOP | Published L1/L2 persist, no L4 auto-run |

## 9. Final implementation contract

### 9.1 Deterministic order of execution

The software implementation must obey the following sequence for one frozen migration run:

1. Read-only recovery of every owner-approved historical donor submission and original URL; keep the original JSON/blobs, hashes and provenance immutable.
2. Freeze the L1 input source-link **occurrences** and derive the audit baseline B from that exact immutable input. This initial input is the only source of L1 roots.
3. For the active level, inspect the frozen parent queue; retain previous classifications and decisions for known sources.
4. Extract outbound links; preserve every raw occurrence and verified source edge. Check prior canonical identities, aliases and completed-source index; deduplicate novel identities, then STOP if the **net-new unique** count exceeds `floor(B × 115 / 100)`. Do not publish a truncated or unverified level.
5. Where no STOP occurs, retain all parent-child evidence, classify **only new relevant sources** and preserve earlier decisions. Children enter only the next global queue, never early.
6. Atomically publish the current level's admissible donor references and separate classified-source candidates. Build and activate the source, classification and relation indexes together.
7. Independently query all published items by canonical ID, original URL/alias, classification and parent relation. Issue an immutable level PASS only after actual read-back, version matching and source-coverage checks.
8. Only then begin the next global level. On L5, publish and finish without generating an L6 work queue. If no relevant further link exists earlier, finish with documented early exhaustion.

Every failure freezes progress, leaves the latest verified published level intact, records the blocked stage and requires an explicit new instruction before further action.

### 9.2 Required state and evidence interfaces

| Interface | Minimum evidence |
| --- | --- |
| SourceArchive | Historical raw record/locator, origin commit and blob SHA, user approval or pre-existing status |
| SourceIdentity | Stable canonical ID, normalized source key, URL aliases, last recorded decision |
| DonorRegistry | Approved-reference status, evidence of owner's donor marker, source class, rights/admission state |
| ClassifiedDiscovery | Source URL, global L1–L5 level, class, discovered-unregistered status if not approved |
| ProvenanceEdge | Original L1 root ID, parent and child IDs, observed occurrence and source-evidence reference |
| LevelQueue | One fixed B and immutable run ID, next global level, frozen input references and progress checkpoint |
| LevelReceipt | Original B, raw URL evidence count, previously known count, net-new unique identities, 115% threshold, repeated aliases, relations, STOP status, output version |
| PublishedSnapshot | Atomic registry and index versions, rollback ref, active snapshot digest |
| PublishVerification | Independent read-back by identity, original/alias URL, type and parent relationship; PASS/FAIL receipt |

Do not replace real publication read-back with a successful CLI unit test, HTTP ping or GitHub CI check.

### 9.3 Fixed depth contract

| Discovery level | Remaining levels, including this level | Last allowed level |
| --- | ---: | --- |
| L1 (original root) | 5 | L5 |
| L2 | 4 | L5 |
| L3 | 3 | L5 |
| L4 | 2 | L5 |
| L5 | 1 | L5 |

Re-encountering a prior L1 source deeper creates only a provenance edge, not an additional root. Repeated/cyclic links and multi-parent paths do not confer extra expansion depth. A newly approved donor found at L4 stays at L4; its work cannot restart from L1.

### 9.4 Acceptance criteria for the actual future implementation

The final data-migration proof must show **zero** missing owner-approved original source URLs, unexplained canonical identity collisions, unjustified duplicate donor records, unclassified relevant processed sources, broken verified parent relations, unpublished approved donors, unauthorized legacy configurations or code imports, donor-specific depth restarts and global levels above L5.

Each successfully completed level needs its own search-readback receipt; the next level stays blocked until it exists. B must be reproducible from frozen original inputs; tests cover B=445 and limit=511, 650/445-known → 205 new, 512/512-known → 0 new, 800/151-known → 649 new STOP, repeated known URLs retained as edges without consuming quota, fixed global depth and L5 never starting L6.

If the 15% threshold trips, the previously published levels remain accessible, but the overall run is **STOPPED_EXPANSION_LIMIT**, **never FINAL PASS**. A run may successfully end early only on proven exhaustion of further relevant links and successful publication of its final processed level.

### 9.5 Exact non-deliverables of this plan finalization

No donor import, source-code adoption, network crawl, L1 publication, permission escalation, merge, runtime activation or Current Host PASS is performed by finalizing this document. The existing source index remains incomplete until independently proven otherwise.

---

## 10. Explicit non-deliverables of this design finalization

- This commit **does not perform** donor migration, crawling, classification or indexing.
- The new CFA3 active source index remains **incomplete** until the actual L1 import and reconciliation, and must not certify unmatched links as new.
- A validated design policy is **not** a successful source crawl or an installed application, Foundation PASS, runtime provider admission or physical Current Host PASS.
- This plan does not authorize new automatic implementation PRs, merges or modification of the old repository.

**Approved design principle (2026-10-09 revision):** Preserve useful raw data and canonical identity; process strictly level-by-level; publish and prove searchability before the next level; stop **net-new unique source expansion** above 115% of the frozen original L1 link-record baseline; do not try to index the entire internet.
