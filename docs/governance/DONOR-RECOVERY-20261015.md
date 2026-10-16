# Donor recovery: source-file 001

Task: `CFA3-DONOR-DATABASE-RESTORATION-20261015`.
Owner authorization: the 2026-10-15 Work request to restore the donor database
in the new repository through a donor branch and PR, preserve provenance, admit
no new donors, respect 996147 bytes per changed donor data file, and process L1
before L2 without L3–L5.

Inspected main: `ac312804beb418eb6c1293c2c109313217d4b004`.
Branch: `donor/database-restoration-20261015`.
Only the lookup implementation, its regression tests, a read-only source-file
audit and this task's evidence are changed. Completion of this repair means
authenticated lookup on every source-file 001 lookup path, verified preserved
readback, and a reviewed PR with the required bootstrap/qt68-linux checks.
Global donor recovery remains blocked on the evidence listed below.

## Proven defect and repair

On the inspected main, changing a CANDIDATE to ACCEPTED_REFERENCE and
CANONICAL_REFERENCE_REGISTERED in an isolated copy of source-file 001 still
returned the modified record through ID and direct URL lookup. The catalog's
Git blob digest was only enforced on the supplementary alias path. This was a
lookup integrity defect; no existing catalog corruption was found.

Published lookup now verifies the existing catalog blob
`7de979fd2d975ff99573f41e4a0035a57925bb52` before parsing or returning a hit or
miss. Batch readers can explicitly reuse an authenticated immutable snapshot;
individual lookups without a handle authenticate the current files. The batch
handle cannot be forged through constructor bypass or modified through returned
records. It represents the verified snapshot, not subsequent filesystem changes.
The authenticated bytes are the bytes parsed. Regression coverage includes
unauthorized approval promotion, replacement of an ID with unchanged index
length, corruption in another record, and detached return values.

No original donor record, approval, alias, lifecycle decision or provenance was
rewritten. No additional donor was approved. The five preexisting oversized
files remain byte-for-byte unchanged; editing them later requires lossless
splitting under the existing size policy.

## Bounded readback result

Run `python3 scripts/check_donor_source_file01_recovery.py` from the repository.
The checked-in JSON report records the input SHA-256 digests and actual file
sizes. The script exits unsuccessfully on missing or inconsistent readbacks;
input authentication errors also fail the command.
Both historical observation batch paths and their respective 15/10 record
counts are mandatory. Their full bytes must also match independently pinned
historical SHA-256 digests. Missing, renamed, unexpected, truncated or altered
batches fail the audit instead of silently reducing or changing its evidence.
All 1919 IDs and 2012 URLs are tested through the batch API without file reads
after authentication, preserving the same readback result without repeatedly
loading the catalog and archive.

| Measurement | Result |
| --- | ---: |
| Separate canonical registry records | 81 |
| Source-file 001 historical records read back by ID | 1919 |
| Published exact URLs read back, including 15 supplementary aliases | 2012 |
| Source-file 001 queue records | 1919 |
| Direct / collection / unclassified / non-network queue groups | 1136 / 546 / 80 / 157 |
| Historical metadata observations | 25 |
| Metadata returned / not found at the historical check | 24 / 1 |
| MISSING within the tested source-file 001 coverage | 0 |
| UNRESOLVED_CONFLICT within that coverage | 0 |
| Donor records changed / new approvals | 0 / 0 |

The Ascend/triton-ascend URL intentionally returns the historical SUPERSEDED
identity in the immutable publication, while the current transfer/lifecycle
route selects its recorded successor. Both related identities and the
HISTORICAL_OWNER_BASELINE authority are preserved. This is not an unresolved
identity conflict.

The 25 observations are metadata evidence from 2026-10-12, not 25 fully processed
L1 sources or fresh upstream verification. The historical NOT_FOUND_AT_CHECK
for `https://github.com/6174/recut` does not prove deletion, justify removing a
donor, or count as missing database content. The queue's zero fully verified
sources is not replaced by the metadata-observation count.

## Donor branches and historical evidence

The source-file 001/002 publications, 15-alias repair, queue, and both observation
batches are already in main. The PR545 preservation and recovered-source-file
branches retain commits outside main's ancestry, but their PRs #16 and #15 were
merged and their relevant content is present; no blind re-merge is needed.
PR545 still exposes 17 non-admitted proposals and three unapplied rekey proposals.
Those proposals are not new owner-approved donors or automatically resolved aliases.

`cfa3/donor-update-old-l1-l2-20261010` at
`e6c9c64294e6afa4e8b983f6f1bb0366e09296a6` retains a separate URL export:
249 source files, 1985 URLs, labelled 1932 L1 and 53 L2. Its own definition makes
L2 an occurrence in historical repository documents, not external L2 traversal
or a verified level publication. It remains a historical source, not a basis
for asserting L2 completion or admitting donors.

Open PRs #8 and #65 were checked for file overlap; neither touches these files.
No legacy-repository write was made.

## Remaining blockers and boundaries

- The original frozen L1 input-record count B is still null. The 1919-entry
  historical registry and the recovered 445 URL coverage are not automatically B.
- The lifecycle index explicitly remains incomplete, although its 1981 known
  records, 3979 stored locator routes and authenticated input projection validate.
- Exhaustive coverage of all historical owner submissions/conversations is not
  proven. Global MISSING and UNRESOLVED_CONFLICT are therefore UNPROVEN, not zero.
- Historical PR545 approval and rekey adjudication remains unresolved; proposals
  remain searchable without admission.
- No L1 PUBLISHED_AND_VERIFIED_PASS exists. L2 is not started by this repair,
  and L3–L5 are outside the requested scope.

The earlier ChatGPT reference returned only content-reference placeholders for
assistant messages and no attachments. Its unseen audit text is not evidence.
The task uses the current repository and the owner's explicit request instead.

Reference CI proves repository checks only. It does not prove physical Current
Host, rights review, global L1 completion, or runtime admission. PR review and
merge are separate from the bounded readback result recorded here.
