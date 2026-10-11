# CFA3 Execution Guard – fail-closed foundation

Status: PARTIAL FOUNDATION; no full-rule admission, no global tool interception.

## In-scope
Only Execution Guard security gates and negative tests. Do not touch donor PR #11, docs PR #8 or the legacy repository.

## Boundary
The registry lists the 24 known DEV/AI rules and all currently present canonical policy files. Historical inventory is incomplete (3159 source files, 21 recorded content reviews). Missing and conflicting rules remain unknown, not zero. Side effects must fail closed.

## Gateway
The scripts/execution_guard.py module requires: independently verified complete policy admission and rule-to-gate coverage; signed exact task and source hashes; source and design validation; scope, expiry, outputs and budget; trusted fresh live main/head, review, CI, overlap and owner-scope evidence; durable nonce and quota consumption before side effects; independent result checks.
The HMAC key, private quota store and all privileged tool credentials must be held by a separate trusted service. It is not safe to expose the key or unchecked adapters to an AI agent. Native ChatGPT tool invocations cannot be intercepted by this module.

## Verification
python3 -m unittest discover -s tests -p test_execution_guard.py -v
python3 scripts/execution_guard.py --status
The status command is expected to exit nonzero while rules are unresolved; do not use it as a positive CI gate. Passing negative-path tests is only structural evidence.

## Before actual execution admission
Complete historical rule reconciliation; prove MISSING=0 and UNRESOLVED_CONFLICT=0; verify each runtime rule gate and accepted GUI design source; provide trusted live adapters, GitHub required status checks, replay/quota/concurrency evidence and true physical Current Host evidence where applicable. No old 175 capability proof or donor evidence is inherited. Main protection remains mandatory.

## Hardening: immutable budget and preflight
The first reserved signed task envelope pins its task scope, source hashes, expiry, result count and budget. Subsequent authorization cannot silently raise the limit. Nonces are unique across task identifiers. Linux quota ledger reservations are serialized, persisted before side effects, and do not refund or automatically retry failures.

A trusted admission callback must independently confirm complete policy reconciliation. Fresh main/head evidence, an independently verified preflight and an audit adapter are required before the executor is called. GUI designs must have an independently verified source. Native ChatGPT tools remain outside this gateway. These unit tests use mocks and are NOT physical/admission evidence.

## Full frozen historical file inventory (not rule admission)
The immutable pinned Git tree at a9c724da62bf49f3353c694990fc51443e634b4a contains 3159 tracked blobs. Every blob path, Git SHA-1 and size is indexed by canonical/registries/CFA3-LEGACY-FROZEN-TREE-001.json; all entries remain potentially rule-bearing and default to UNREVIEWED_RULE_APPLICABILITY. The CI pinned-tree checker compares the complete inventory and all 21 seed ledger entries with GitHub's frozen Git tree; missing, altered, extra or inaccessible files fail closed. This is complete file enumeration **only**: rule-level applicability, owner authority, conflicts, legacy 175-to-new-200 translation and verified runtime gate proofs are still PENDING. No code or data is transferred from the legacy repository.

## Current canonical policy field surface
The independent source-bound inventory canonical/registries/CFA3-CURRENT-POLICY-SURFACE-001.json enumerates 431 JSON leaf fields across all five current canonical policy files, preserving their exact Git blob SHA-1 revisions and declared source admission statuses. The bootstrap workflow compares every source SHA, JSON Pointer and value type with the files checked out for CI. Removing/adding/editing a canonical JSON policy field without updating the inventory fails structurally. This does not automatically authorize any policy status, classify every field as a rule, establish historical completeness or implement its runtime gate. All such semantic dispositions remain PENDING.

## Verified main branch protection requirements
The CFA3-MAIN-PROTECTION repository ruleset (ID 24804719) is active for the default branch. The required GitHub Actions checks are `bootstrap` and `qt68-linux` from integration 15368, with strict checks, protected review threads, no bypass, no force-push and no deletion. The read-only live ruleset verifier runs within the already-required bootstrap job. It fails closed on missing or weakened protections. It does not itself prevent a repository administrator from changing GitHub settings, and the branch protection gate cannot intercept ChatGPT native tools or certify complete CFA3 policy coverage.

## GitHub API protected bypass-list visibility (verified 2026-10-11)
GitHub REST intentionally omits `bypass_actors` unless the API caller has **write access to the Ruleset**. The normal `GITHUB_TOKEN` used by `pull_request` workflows with `contents: read` cannot establish that the bypass list is empty. Therefore the `bootstrap` job runs `scripts/check_execution_guard_ruleset.py --ci-visible`, which fails on any verifiable weakening (required checks, PR review thread resolution, rule scope, force-push prevention, etc.) and rejects bypass actors when a nonempty list is exposed. If bypass actors are hidden, CI explicitly reports `BYPASS_UNVERIFIED`; it MUST NEVER report full Ruleset coverage. The default `--full`/privileged mode rejects missing, null, or nonempty `bypass_actors`, requiring a separate authorized read with sufficient permission. This does NOT grant the GitHub Actions PR workflow any new secret, privileged token, bypass authority or Ruleset modification capability. The gateway live-state adapter must require independent `privileged_bypass_actors_verified` proof before any external effects; this adapter is not deployed, so complete execution is still BLOCKED. A CI-visible PASS alone cannot certify the absence of bypass roles. Reference: https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset

## Per-rule authorization receipt protocol (24 current DEV/AI identities)
Before any trusted operation can proceed, the gateway requires one fresh, separately signed, task-bound and canonical-governance-bound positive receipt for **each** currently known DEV-01..12 and AI-01..12. The receipt validator rejects absent, duplicate, unknown, stale, changed, incorrectly attributed or negative rule evidence. An independent attester signing key must differ from the owner's task authorization key and remain outside agent control. A receipt digest is only a reference to actual evidence; it does not make unimplemented rules automatically PASS. The signed evidence producer, actual rule-by-rule executors, and authoritative runtime proofs do not yet exist, so the Execution Guard continues to deny all operations. Historical 3159-source policy reconciliation and current canonical policy semantics are still PENDING. Synthetic unit test receipts are not authorized runtime evidence.

## 24 canonical rule identities and codes are immutable within the catalog
The Execution Guard checks the exact ID, index, canonical `code` and allowable evidence status of each DEV-01..12 and AI-01..12 record against the current canonical repository governance file. A correct set of rule IDs alone cannot hide a changed rule meaning. Negative tests mutate each code, state and omit every ID, and also alter the canonical side to detect drift. This validates identity mapping, not independent implementation of all rules; admission still requires historical reconciliation and real attestations.

## Rule-proof evidence body verification (fail closed)
All 24 signed rule receipts must now resolve to **actual canonical JSON evidence bytes** in an independently controlled content store. Each receipt's `evidence_sha256` is recomputed from the returned bytes, and the evidence body must identify the same rule, canonical code, task hash, governance hash, main revision, deterministic gate ID, verdict and checked-at time as the signed receipt. Missing/oversized/noncanonical evidence, content substitution and resolver failure block before any privileged adapter is called. The evidence contains an evaluator-implementation fingerprint, but a bare fingerprint does not prove the evaluator was executed: deployed evaluators and source-of-truth attestation still remain PENDING. The reference tests fabricate explicitly marked synthetic evidence for structural verification only. **A caller-controlled evidence resolver is not trusted evidence.**

## Exact source revisions in every signed task authorization
The `check_task` preflight now refuses signed authorizations which omit or mismatch ANY of the currently admitted canonical policy JSON files, the approved branding reference, AGENTS.md, the complete frozen historical tree and canonical policy surface manifests, the Execution Guard module, its evidence and source validators, the bootstrap checker and the required bootstrap CI workflow. Every binding uses the actual file-byte SHA-256 computed at check time. A signed authorization for stale/missing/modified gate code is DENIED; merely copying a 40-character Git revision into a task is not proof that source bytes are unchanged. The trusted signer and tool gateway are not deployed, and this source-bound reference code cannot constrain credentials outside it.

## Historical semantic reconciliation obligations
The pinned 3159-file source tree remains the exhaustive denominator. The non-authoritative register `canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json` tracks file decisions without admitting a single unchecked rule. In three separately read and Git-blob-verified historical source files it records **78 structured rule pointers**: 22 legacy DEV/AI, 29 quality and 27 scope/closure rules. Every candidate status is UNRECONCILED. All 3159 original file dispositions are still pending; prior 175 capability declarations cannot replace the new 200 target. The bootstrap check validates register integrity; the execution preflight fails closed until the complete review and owner-authorized rule mapping are independently established. The existence of source pointers alone is not acceptance or execution enforcement.
