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
