# CFA3-CRAM-ADAPT-001 — CrAM native adaptation

**Approved scope:** three distinct CrAM capabilities; this branch contains only the first structural contract implementation (`CRAM-02`). **Status: STAGED, NOT VERIFIED, NOT ADMITTED.**

## Task record

- **Main task:** implement the owner-approved CFA3-native adaptations of CrAM 2023, CrAM 2025 and CRAM 2026.
- **Requested result:** native Shared AI Model Optimization, Shared RAG Reliability and Shared Continual Learning adapters, with consumer integrations, rollback and applicable real evidence.
- **Allowed scope:** CrAM-specific contracts, tests, provenance and subsequent CrAM adapters only; never modify the historical repository or parallel donor PR.
- **Constraints:** Rust-first contracts, Python upstream adapters where justified, CPU-only platform baseline, no new Model Router/HRB/Security/Workload Mode/Temporal authority, no silent fallback or synthetic physical PASS.
- **Completion:** real implementations, proven permissions and source rights, passing tests, relevant downstream consumers and applicable physical Current Host evidence. This staged contract does not complete that result.

## Three different pinned upstream sources

| CrAM technology | Upstream | Pinned revision | Upstream root license status | CFA3 Shared Fabric |
| --- | --- | --- | --- | --- |
| CrAM / Compression-Aware Minimizer (2023) | https://github.com/IST-DASLab/CrAM | `b89d9ff2b0c7d343736d587dd27f95d86a2df1cf` | Apache-2.0 root license observed | Shared AI Model Optimization |
| CrAM / Credibility-Aware Attention Modification (AAAI 2025) | https://github.com/Aatrox103/CrAM | `b6403d002a7bb445410f277a73907d7a2e3a8bf1` | Root LICENSE not found; rights **UNVERIFIED** | Shared RAG Reliability |
| CRAM / Centroid-Routing and Adaptive MoE (2026) | https://github.com/LAMDA-CL/EMNLP2026-CRAM | `576edf0f0a4c23052f275d6a57d36197d4c067ba` | MIT root license observed | Shared Continual Learning |

Root licenses do not cover all transitive dependencies, datasets or model weights automatically. These pinned records describe the analyzed references; they are **not donor admission or runtime promotion**. Reconcile the source lifecycle index and licensing before any upstream code import.

## CRAM-02: actually staged data-contract implementation

- `crates/cfa3-execution-contracts/src/cram.rs` contains three distinct variants, operation-to-variant binding, exact source-pin checks, structural authority references, a code-origin/rights barrier, CPU-vs-reference-CUDA policy checks, declared fallback checks and outcome/rollback reference shapes.
- The contract is exported from `crates/cfa3-execution-contracts/src/lib.rs`.
- The Rust module includes **12 unit-test definitions** for positive/negative structural cases. They are **NOT RUN**: the local editing environment did not provide `rustc` or `cargo`.
- An opaque authorization reference is *never* proof of permission: actual issuer, actor, operation, scope, decision digest, expiry and live lease must be validated by the already-designated CFA3 authorities before any execution.
- For CrAM 2025, upstream code admission is deliberately blocked at the pinned version even if the caller claims to have rights. A separately written CFA3 contract can be described without importing the upstream source; independent implementation still requires its own rights assessment.
- The pinned upstream CRAM 2026 training environment requires CUDA. It cannot silently become a CPU fallback. No such training implementation exists in this branch.
- The Rust contract is not a second runtime authority, adapter, registry, workflow engine, or proof of real execution.

## Remaining approved execution (NOT DONE)

1. **CRAM-01** complete cross-source lifecycle, code/dependency, dataset and model-rights admission review for actual imports.
2. **CRAM-02** compile, run Rust tests and validate contract integration on an actual Rust toolchain; revise only with proof.
3. **CRAM-03** optimize-model adapter using a rights-qualified PyTorch integration; preserve immutable input artifact, provenance, correctness and rollback.
4. **CRAM-04** independently validated CFA3 RAG reliability/attention adapter; upstream CrAM 2025 code cannot be copied until rights are resolved; clean up all hooks on every outcome.
5. **CRAM-05** isolated optional 2026 continued-learning backend and expert/checkpoint provenance; CUDA-required reference workflow must not compromise CPU-only platform admission.
6. **CRAM-06** integrate actual Shared API consumers and Qt6 GUI where an applicable real parent exists.
7. **CRAM-07** run positive/negative, rollback, compatibility, lease/authority, security/rights and applicable physical Current Host verification, then seek explicit promotion.

**Evidence currently available:** GitHub commit and independent source readback only. Rust test status: `NOT_RUN`. Runtime admission: `NONE`. Physical Current Host PASS: `NONE`. No claim of completed CrAM capability is made here.
