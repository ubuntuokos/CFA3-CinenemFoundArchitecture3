# CFA3 donor L1 historical-source preservation receipt (not L1 PASS)

**Date:** 2026-10-09. **Target:** new CFA3 repository; **legacy source read-only:** ubuntuokos/Final-Architecture-v3.0 at a9c724da62bf49f3353c694990fc51443e634b4a.

## Verified source material

- Historical donor registry: `1,919` records, each with a distinct donor ID and normalized source key; status breakdown 825 ACCEPTED_REFERENCE, 963 CANDIDATE, 130 ANALYZED, 1 SUPERSEDED. These **historical** labels are preserved verbatim, not silently adopted as final CFA3 decisions.
- October 5 source-union coverage: `445/445` resolved normalized source keys are present in historical main. Zero missing within **that bounded source union**, not a claim about every conversation.
- The 20 previously missing Oct 7 sources already appear in the 1,919 records. They must **not** be added a second time.
- Two additional distinct historical sources, from unmerged PR #744 and PR #745, have been preserved separately with their exact Git provenance and are **pending** new-repository canonical review. Total observed distinct source keys across the three source snapshots = `1,921`; **not** a final all-user-submissions proof.
- Historical application–donor links are archived **as source data only**; they do not authorize old apps, engines, dependency loads or provider admission.

## Exact archival source identity

- Main donor registry Git blob: `062b7b27aeeaf74819ac315f30c5cbde4ed2c95b`.
- Source-union Git blob: `d22dce8bfe3d9697a1121033ff7b387d051a638a`.
- Historical app–donor links Git blob: `803b9d62062e6aaaeb9fc69301a6202e20279a93`.
- Old submitted-missing-20 PR: #742 commit `5f688d86848daf7c06d59dd6017a4335b3489d08`.
- Separate PR #744 entry source Git blob: `6b7b0f3aa06e81b174c7a12e7f9d24ea089f2679`.
- Separate PR #745 entry source Git blob: `1af261ee4247b8f7293526022111b89bd64cf1ca`.

The original JSON files are stored **verbatim** under `archive/donor-source-migration/2026-10-09/`. They are archival snapshots, **not** the new active donor registry.

## Fail-closed stage status

**STAGED SOURCE ARCHIVE ONLY.** No canonical new L1 classification or publication has been performed, the source lifecycle index remains incomplete, all user-submitted donor links have not yet been independently reconciled, and **no L1 PUBLISHED_AND_VERIFIED_PASS exists**. Therefore L2 is **forbidden**. No network crawl, no use-edge admission, no merge, no Current Host PASS.

The correct next stage is to reconcile full explicit user-authorized source coverage against immutable historical snapshots and then run the new L1 classifier, atomic publication and independent read-back gate.
