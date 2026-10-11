# CFA3 Source Lifecycle: mandatory first step for every analyzed link

Owner-approved rule: `CFA3-SOURCE-LIFECYCLE-POLICY-001`. **Development workflow scope: all analyzed external links**, not only donor additions.

## Required order
1. Normalize the incoming URL and **look it up before analysis** against the complete source/decision index, including recorded aliases, moves and historical identifiers.
2. If previously analyzed and no material change is independently verified, **keep the earlier approved decision**. Do not rerun the initial review or override it.
3. If an update, modernization or security-relevant change is verified, prepare an **append-only change assessment**; preserve the prior decision and require the normal task-specific approval before changing the adopted implementation or decision.
4. If relocated, link the newly verified URL to the existing logical source identity; preserve old URLs as aliases and historical provenance. Never create another donor merely for a move.
5. If upstream support ends for a still-needed CFA3 capability, prepare a replacement implementation plan. When rights **permit modification and the intended use/redistribution**, modernize the available code and adapt it to CFA3. Otherwise plan an independent CFA3 implementation **without copying unavailable/restricted code**. Actual work requires explicit owner approval.
6. Do not restore obsolete apps, duplicate shared capabilities or old bad configuration/architectural choices. Keep genuinely different and justified engines/providers.
7. Unknown, incomplete, conflicting or inaccessible source history is **BLOCKER**, not evidence that a link is new. The old CFA3 repository need not be fixed, but its verified source *data* must be preserved before declaring the new source index complete.

## Read-only reference gate
```sh
python3 scripts/source_lifecycle.py "https://github.com/example/project"
python3 scripts/source_lifecycle.py "https://github.com/example/project" --observation /path/to/verified-observation.json
```
Output is a JSON disposition, with exit codes: `0` for a decidable unchanged or truly new source; `2` for hard block; `3` for mandatory verification/change/replacement review.

Until the full source index is reconciled, the repository's empty `canonical/registries/CFA3-SOURCE-LIFECYCLE-INDEX-001.json` deliberately answers unknown URLs with `BLOCKED_INDEX_INCOMPLETE`. **The gate does not fetch websites or attest its own evidence.** A `VERIFIED_BY_AUTHORIZED_REVIEW` observation is an assertion requiring independent corroboration by the authorized reviewer. The CLI neither changes old decisions nor registers donors.

## Example source record (illustrative only; NOT a registered CFA3 donor)
```json
{
  "source_id": "source-example-001",
  "canonical_url": "https://github.com/example/project",
  "aliases": ["https://github.com/old-org/project"],
  "prior_decision": {"decision_id": "DEC-001", "revision": 1, "outcome": "REFERENCE_ONLY"},
  "observed_revision": "commit-sha-or-version",
  "support_status": "SUPPORTED",
  "rights": {"verified": false, "may_modify_and_distribute": false}
}
```

An observation JSON can contain `evidence_ref`, `checked_at`, `verification: "VERIFIED_BY_AUTHORIZED_REVIEW"`, `observed_revision`, `support_status`, `event`, `previous_source_id`, and `rights` when an authorized change assessment exists. Unverified or contradictory claims block.

## Evidence and admission
- Each original source link and authenticated owner command must survive donor migration; no fabricated approvals.
- An observation/review is not donor registration, a usage edge, SDK adoption, runtime admission or Current Host evidence.
- Historical decisions are append-only. A genuinely erroneous old decision is addressed through **explicit owner-authorized correction**, not silent reinterpretation of a re-submitted URL.
- The source lifecycle policy can be structurally checked in CI while the full donor migration remains **PENDING**.
# Current lookup integration

The default lifecycle index is generated offline from the existing staged donor
index, original donor evidence, owner-approval ledger, registered references and
the exact URL routing table. It contains 1981 source identities and preserves all
3946 locator routes, including related historical identities. Regenerate with
`python3 scripts/build_source_lifecycle_index.py`; verify reproducibility with
`python3 scripts/build_source_lifecycle_index.py --check`.

Schema v2 preserves non-HTTP historical locators without manufacturing URLs.
An original URL uses its preserved preferred identity; normalized variants may
resolve only if they have one unambiguous preferred identity. Upstream revisions
and reuse rights remain unknown unless separately verified. Known links now
return prior decision evidence; unknown links remain blocked while global source
coverage is incomplete. Lookup availability does not complete L1 publication.
