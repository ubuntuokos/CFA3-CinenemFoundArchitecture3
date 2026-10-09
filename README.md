# CFA3 — Cinema Fund Architectura 3

**Development target:** Complete Production Platform.

**New CFA3 implementation repository:** `ubuntuokos/CFA3-CinenemFoundArchitecture3`.

> **STATUS: FOUNDATION NOT IMPLEMENTED.** This repository starts with a governance and CI bootstrap only. Neither the 200-capability ledger nor the full Foundation, application catalog, Qt 6 GUI, or physical Current Host has been completed or certified.

## Planned platform availability

**Linux is the primary CFA3 platform.** Selected CFA3 applications are also planned for **Windows** and **Android**. This does **not** mean that the entire CFA3 platform or every application will be available on all three operating systems.

Cross-platform availability is defined **per application and target OS**: supported functions, UI/interaction model, dependencies, hardware profiles, packaging and platform-specific integration must be designed and verified separately. GUI applications use **Qt 6** on their supported targets; new native components are Rust-first unless their technical stack justifies another language. Windows and Android editions must preserve the applicable local-first, permissions, data-ownership and security requirements.

**Availability is planned, not yet delivered.** A Windows or Android edition will only be labeled supported after actual implementation and target-platform compatibility, installation, standalone GUI (when applicable), and relevant functional/integration testing. Unsupported target-specific capabilities must be disclosed rather than silently assumed to match Linux.

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
