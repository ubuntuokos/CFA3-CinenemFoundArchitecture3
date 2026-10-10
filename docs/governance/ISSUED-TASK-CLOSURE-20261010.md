# Issued task closure

Owner request: complete the previously issued tasks; do not report incomplete work as complete.

Baseline: new CFA3 main `b33e900ee54d43ee838ba3861584d4563b351452`.
Historical source (read only): `a9c724da62bf49f3353c694990fc51443e634b4a`.

Allowed work: reconcile existing task evidence, repair donor lookup integration and
its tests, preserve historical decisions, document remaining evidence requirements.
No historical repository writes, invented approvals, capability IDs, upstream
versions, physical-host PASS, or global donor-completeness claims.

Acceptance: repository-backed task status; populated lifecycle lookup preserving
known identities, original routes and approvals; positive and negative integration
tests; precise remaining blockers. Broader requested closure remains open until
the original task specification and its required evidence are recovered.

## Execution record

- PRs 1 and 2 were already merged at the baseline; no repeat merge required.
- The 19–26 reference registry already contains 81 IDs and 83 original URLs.
- The staged donor index contains 1981 sources; the lifecycle index was empty.
- The current donor plan requires original submitted-link occurrences to freeze B;
  a unique-source total or stored URL count is not an authorized substitute.
- The Foundation baseline explicitly says the architecture is not implemented;
  an approved list of 200 capability identities is not present in this repository.

This record is not a declaration that the whole project is complete.

## Implemented in this change

- Connected all 1981 staged source identities and 3946 locator routes to the
  default lifecycle gate; original owner approvals and the existing 81 canonical
  reference registrations remain attached to their source identity.
- Added a reproducible offline projection and tests for lossless routing,
  all 81 registered IDs/83 URLs, unknown links, malformed routes, and ambiguous
  normalized variants. No upstream revision, license or runtime authority inferred.
- Replaced the obsolete assertion that the lifecycle index must stay empty with
  a coverage invariant and retained the prohibition on false global completeness.
- Closed production SQLite connections after stage, verify and lookup operations.

## Verified remaining tasks and evidence needed

| Task | Current evidence | Required next result |
| --- | --- | --- |
| Full L1 closure | 1981 staged sources; global completion false | Original submitted-link occurrence ledger, complete prior submission coverage and classifications, then publication/readback receipt |
| PR545 historical proposals | All 17 proposed keys and their corresponding GitHub locator forms absent from the staged/lifecycle lookup | Recover original proposal and effective owner decisions; register only at the evidenced authority level |
| PR545 proposed rekeys | Three original IDs still exist under their original keys; proposed GitHub keys/locators do not resolve | Verify identity/relocation evidence and add reviewed alias relations without deleting original IDs |
| Original L1 denominator | Source-union file reports input names and summary counts only | Recover `Beillesztett markdown.md` and `Beillesztett markdown (2).md`, plus other original inputs; count occurrences without substituting unique donor totals |
| Complete governance reconciliation | 21-source seed ledger, not rule-by-rule completion | Classify the frozen 3159-file tree and review all applicable rules/conflicts before admitting new governance |
| Capability/application/Foundation design | Existing legacy model is 175; new target is 200 without a complete registry | Recover issued specification; enumerate and review actual capability identities and application/layer dossiers |
| Foundation implementation | Only execution-route contract scaffold is present | Implement and verify the approved Foundation contracts; physical-host proof requires an actual scoped run |

The two raw Markdown inputs were not found in either repository's tracked main
tree. The legacy snapshot was independently checked at
`a9c724da62bf49f3353c694990fc51443e634b4a` (3159 tracked files).
The source union reports 266 and 625 raw occurrences and 445 normalized union
entries; none of those numbers is independently established as the entire L1 B.

## Verification

- Bootstrap structural validator: passed.
- Python unittest discovery: 79 passed, including six migration integration tests.
- Rust workspace: 3 passed.
- Projection regeneration check and Git whitespace check: passed.
- Existing test fixtures still emit SQLite ResourceWarnings on Python 3.14;
  production connection lifetimes were repaired, and those warnings are not
  presented as a clean resource audit.

These are reference checks, not complete governance or physical-host acceptance.
