# CFA3 bootstrap scope and verified readiness

## Exact task
Prepare the **new** repository for governance-first development, without porting old code or claiming that the platform has already been implemented.

## Added now
- Versioned candidate governance, technology and CPU execution constraints in `canonical/policies/`.
- Git-SHA-bound seed list of verified legacy rule sources (not a completed rule-by-rule inventory).
- Read-only bootstrap validator, negative tests and reference CI.
- Minimal dependency-free Rust workspace to validate the new native contract toolchain.
- A clear execution order and stop conditions.

## Status boundaries
- `BOOTSTRAP_STRUCTURAL_PASS` means only that these particular seed files are structurally consistent and the local checks pass.
- `FULL_GOVERNANCE_ADMITTED = false` until a complete sourced rule ledger, conflict reconciliation, owner approvals and executable-enforcement impact review exist.
- `FOUNDATION_VERIFIED = false`; `CAPABILITY_200_VERIFIED = false`; `GUI_PASS = false`; `CURRENT_HOST_PASS = false`.
- The CI reference runner is neither the user's physical host nor hardware qualification evidence.

## Next approved task order (not automatically executable)
1. Recover and reconcile **all** legacy CFA3 development rules, including hidden/indirect gates, scoped agent rules and relevant canonical decisions.
2. Resolve old-vs-new conflicts explicitly (175 → new 200, old Current Host → layer graph, Qt 6, Rust-first, CPU policy).
3. Freeze the new governance contracts with independent tests and explicit review.
4. Complete source/capability/application/layer inventory and S0–S3 Foundation contracts.
5. Only then begin approved CPU-only Foundation bootstrap in subsequent scoped implementation work.

## GitHub owner actions required before merging
- Configure a `main` branch ruleset requiring pull requests and the actual bootstrap check(s) after they appear; do **not** disable existing protections to get a green result.
- Review the draft PR, all policy adaptations, and proof status. Do not interpret the draft's existence as merge authorization.
- Keep one active implementation PR and no direct pushes to main.

## Local reference commands
```bash
python3 scripts/check_bootstrap.py
python3 -m unittest discover -s tests -v
cargo test --workspace
```
These are test commands, not claims they were run on the user's host.
