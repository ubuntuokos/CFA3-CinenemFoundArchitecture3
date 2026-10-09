# CFA3 donor migration and bounded classification — approved implementation plan V2

- **Plan ID:** `CFA3-DONOR-MIGRATION-AND-CLASSIFICATION-V2-001`
- **Owner approval:** 2026-10-09. Design decision: `canonical/decisions/CFA3-DEC-DONOR-MIGRATION-AND-CLASSIFICATION-V2-20261009.json`.
- **New target:** `ubuntuokos/CFA3-CinenemFoundArchitecture3`
- **Old source repository:** `ubuntuokos/Final-Architecture-v3.0` (read-only extraction; its repair, PR completion or main reconciliation is **not** a migration dependency).
- **Status in GitHub:** OWNER APPROVED / PENDING PR REVIEW AND MERGE. **No donor records have been migrated by this plan commit.**
- **Technical policy:** `canonical/policies/CFA3-DONOR-BOUNDED-CLASSIFICATION-001.json`.
- **Related approved lifecycle:** `CFA3-SOURCE-LIFECYCLE-POLICY-001`.

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
| **L2** | Extracted outbound link occurrences from L1 source references, subject to the raw expansion threshold; known sources reused, unknown references classified. | **L2 PUBLISHED_AND_VERIFIED_PASS** |
| **L3** | Only sources forwarded from L2, with the same guards. | **L3 PUBLISHED_AND_VERIFIED_PASS** |
| **L4** | Only sources forwarded from L3, with the same guards. | **L4 PUBLISHED_AND_VERIFIED_PASS** |
| **L5** | Final permitted level; classify and publish; terminate expansion permanently after L5. | **L5 FINAL PASS** |

Within a level, inspect *only actual relevant sources*; classify every processed source at its correct destination. Parents stay where classified; only references requiring a subsequent stage enter the next queue. The queue is **not an automatic donor registration list**.

**Order in each level:** identify → count potential outbound references for the next level (without processing next-level targets) → raw threshold check → prior-processing/alias check → dedup → relevance/classification → staged registration → indexed, reversible publication → independent read-back verification → level PASS → **only then** start next level.

If there are zero further relevant sources, end with documented `EARLY_EXHAUSTION_PASS` and no fabricated deeper levels. If a level fails any check, **STOP**, retain the last successfully published snapshot, do not start another level and do not silently skip sources.

## 4. EXACT 15% rule — what is counted

Let `B` = the original, frozen number of **L1 input source-link records** before subsequent source deduplication; preserve the audited `B` and source snapshot. Define:

`LIMIT = floor(B * 115 / 100)`.

For each **current processing level**, count the **actual outbound hyperlink occurrences present in its inspected sources** that are being considered for the next level, **before** deduplicating or deciding that a link is already known. Count repeated links, and references to sources already in the donor registry. Do **not** count only net-new donor records or query the size of the active database. Do **not** add counts across L2–L5, and do **not** reset `B` between levels. Exclude non-links (anchors without HTTP(S) destinations, scripts not representing a source URL) deterministically; do not silently filter genuine link occurrences to avoid the limit.

- `B=1000`, raw outgoing count `=1150`: allowed, subject to level PASS.
- `B=1000`, raw outgoing count `=1151`: **STOPPED_EXPANSION_LIMIT**, even if 600 occurrences refer to existing donors.
- The count is bounded **as occurrences are inspected**; stop immediately upon the `LIMIT + 1`th occurrence. Do not complete further extraction, truncate or hide the overage to report PASS.
- A STOP is not an approved complete classification, not a signal to skip sources, not an invitation to increase the starting baseline. Capture an audit report with the exact source, link occurrence and checkpoint that crossed the threshold.
- The last **successfully published and verified** level remains available. The incomplete level remains nonfinal; no subsequent level starts without an explicit owner-approved new decision.

## 5. Mandatory publish-and-read-back gate

`CFA3-DONOR-LEVEL-PUBLISH-GATE-001` applies to **every completed level**, including L1 and L5. A next level cannot begin until the preceding one produces **PUBLISHED_AND_VERIFIED_PASS**.

Publish only the original legitimately approved donor identities as approved. Unapproved discovered children are visible in a **separate classified-source view** with `DISCOVERED_UNREGISTERED` status, never as authorized donor dependencies.

Successful level publication requires:
1. Exhaustive accounted input and classification, resolved identity/dedup conflicts, prior decisions unchanged and all parent/child/root provenance preserved.
2. No raw expansion-limit violation; raw count and fixed baseline present in the audit journal.
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

**E – Deterministic enforcement and tests:** threshold before dedup, STOP on count `LIMIT+1`, known-source skip, correct per-level counts, no L6, no duplicate donor registration, no old decisions rewritten, no publication bypass, atomic rollback, rights-status gating.

**F – L2–L5 level-by-level execution:** each level runs only after verified published prior level. Stop on exhaustion or limit without fabricating complete results.

**G – Independent audit and acceptance:** `MISSING_APPROVED_SOURCES=0`; `UNRESOLVED_IDENTITY_CONFLICTS=0`; `UNJUSTIFIED_DUPLICATES=0`; `UNCLASSIFIED_RELEVANT_SOURCES=0`; `BROKEN_SOURCE_RELATIONS=0`; `UNPUBLISHED_APPROVED_DONORS=0`; `INHERITED_BAD_LEGACY_CONFIGURATIONS=0`; complete level receipt chain; no stopped-expansion claimed as final PASS.

## 8. Negative and boundary test matrix

| Condition | Expected |
| --- | --- |
| `B=1000`, raw `1150` | Within limit |
| `B=1000`, raw `1151` | Immediate `STOPPED_EXPANSION_LIMIT` |
| 1151 occurrences, many known/duplicated | STOP unchanged; no retroactive dedup adjustment |
| L2 1100 occurrences; L3 1140 | Each compared only with frozen `B=1000`; no sum |
| L2 classification succeeds but read-back fails | L3 blocked; previous snapshot retained |
| Same URL in two parent sources | One canonical identity; preserve both parent edges |
| Previously accepted link reappears | Retain prior approved decision; no re-review |
| New upstream version or relocation | Source-lifecycle change review; no silent overwrite |
| Third-party link discovered without donor approval | Classified unregistered candidate, not donor admission |
| Source no longer produces relevant links | Stop branch; document early exhaustion |
| L5 exposes more references | No L6; final level does not spawn further queues |
| Incomplete original approval/source inventory | No donor-baseline FULL PASS |
| Network or CI completes without index read-back | Level publication gate fails |
| Failed L3/limit STOP | Published L1/L2 persist, no L4 auto-run |

## 9. Explicit non-deliverables of this design finalization

- This commit **does not perform** donor migration, crawling, classification or indexing.
- The new CFA3 active source index remains **incomplete** until the actual L1 import and reconciliation, and must not certify unmatched links as new.
- A validated design policy is **not** a successful source crawl or an installed application, Foundation PASS, runtime provider admission or physical Current Host PASS.
- This plan does not authorize new automatic implementation PRs, merges or modification of the old repository.

**Approved design principle:** *Preserve all useful data; build clean canonical identity; process strictly level by level; publish and prove searchability before the next level; stop raw link expansion above 115% of the original L1 input — never attempt to index the entire internet.*
