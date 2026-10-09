# CFA3 — Cinema Fund Architectura 3

**Development target:** Complete Production Platform.

**New CFA3 implementation repository:** `ubuntuokos/CFA3-CinenemFoundArchitecture3`.

> **STATUS: FOUNDATION NOT IMPLEMENTED.** This repository starts with a governance and CI bootstrap only. Neither the 200-capability ledger nor the full Foundation, application catalog, Qt 6 GUI, or physical Current Host has been completed or certified.

## Start here
1. Read [Bootstrap scope](docs/BOOTSTRAP.md) and [governance reconciliation](docs/governance/RECONCILIATION.md).
2. Read [repository instructions](AGENTS.md) and the JSON baseline under `canonical/policies/`.
3. Run `python3 scripts/check_bootstrap.py`, `python3 -m unittest discover -s tests -v`, and `cargo test --workspace`.
4. Complete the full legacy **development-rules** audit and the new CFA3 architecture/capability-source reconciliation **before feature implementation**.

## Non-negotiable boundaries
- The old `ubuntuokos/Final-Architecture-v3.0` repository is a **historical source**. Never bulk-copy its code/config/gates or treat its 175-capability proofs as new CFA3 evidence.
- The new CFA3 targets **200 individually reconciled capabilities**; current ledger is **PENDING**.
- **Qt 6** is required for every GUI app. **Rust-first** for new native components; preserve other languages when rewriting is unjustified.
- Local-first, CPU-only platform baseline. Conditional, recorded CPU fallback cannot yield accelerator or physical host PASS.
- Single explicit task scope; one active implementation PR; review required; STOP on blocker.
- The source ledger and bootstrap CI check **internal consistency only**, not full-governance transfer or production readiness.

Bootstrap proposal status: **candidate pending human review and merge**.
