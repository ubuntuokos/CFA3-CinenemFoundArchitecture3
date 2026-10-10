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

## CRAM-03 CPU optimization prototype — staged and locally exercised

The independent Python implementation `cfa3_cram/optimizer2023.py` provides a **CPU-only** TopkCrAM-style two-pass PyTorch optimizer based on the pinned 2023 algorithm. It uses explicit local sparsity sampling, a closure evaluated with temporarily pruned parameters, restored original parameters before the SGD update, and per-step rollback of parameters and SGD optimizer state on error. The checkpoint includes the source pin, RNG and selected sparsity; incompatible source revisions or optimizer configurations are refused on load. The code contains **no copied upstream source files**.

- Python module: `cfa3_cram/optimizer2023.py` and `cfa3_cram/__init__.py`.
- Negative/positive test file: `tests/test_cram2023_optimizer.py` (**11 tests**).
- **Local verification:** Python 3 with CPU-only PyTorch `2.10.0+cpu`; `python3 -m unittest discover -s tests -v` scoped to the isolated candidate package: **11 run / 11 PASS / 0 failures**. This is local targeted evidence, **not GitHub CI and not physical Current Host acceptance**.
- **Independent GitHub readback:** all three new Python files were fetched from this feature branch. Their Git blob SHA-1s exactly match the separately executed local test files (`git hash-object` comparison), so the tested Python bytes are the staged GitHub bytes.
- **Optional dependency:** the module imports without PyTorch, but constructing the optimizer requires PyTorch; on CI hosts without PyTorch, all eleven CPU tests are **SKIPPED and remain NOT_VERIFIED**, never counted as runtime qualification.
- **Integration barrier:** this is a testable algorithmic adapter, **not runtime admitted**. It does not itself validate CFA3 Security, Model Router, HRB, Workload Mode, project permissions, dataset rights or admission receipts; application-level invocation **must remain disabled** until actual authorities are connected.
- **Rollback scope:** parameter tensors, SGD optimizer state and sampling RNG are restored on step failures. Module buffers, external data iterators, file writes and other side effects inside a caller-provided closure are **not** rolled back. Full-model transactional behavior and immutable artifact registration remain future work.
- **Implementation fidelity:** this CFA3-native TopkCrAM-style implementation currently uses a global quantile threshold over eligible multidimensional parameters and a seeded sparsity choice. Scientific fidelity versus the exact historical reference and additional TopkCrAM/N:M variations remains **UNVERIFIED**; no accuracy/performance claims.
- **Rust build:** `NOT_RUN` because `cargo` and `rustc` are absent from the available local execution environment. The new Python adapter tests do not substitute for Rust checks or actual host evidence.

Remaining blocker for **Rust verification**: access to a Rust toolchain. Remaining blocker for **production promotion**: live CFA3 runtime authorities, rights and dataset qualification, full adapter fidelity, consumer integration and required real-host checks. The parallel donor PR #7 is **not** a blocker for disjoint CrAM-file development.

## CRAM-04/05 CPU-side structural prototypes — tested, NOT runtime-admitted

- `cfa3_cram/reliability2025.py`: independent CFA3-developed CrAM 2025 *input and safety* primitive. Assessed source-ID/provenance digests, strict credibility validation, explicit non-overlapping source token spans, bounded finite additive log-bias proposals and safe temporary PyTorch-style pre-hook lifecycle. **This is not a working, model-qualified attention intervention, an automatic truth assessment or licensed upstream-code adoption.**
- `cfa3_cram/continual2026.py`: independent CPU-only model-internal expert-centroid comparator. Strictly confines comparisons to one externally selected model revision/projection; returns a review-needed outcome instead of creating new experts when no match exists. **This is not adaptive-rank MoE training, model selection, a provider route or checkpoint admission.**
- `tests/test_cram_2025_2026.py`: **15 local unit tests PASSED** (Python 3 and installed CPU PyTorch). These include real CPU PyTorch forward-pre-hook registration, behavior and restoration, plus negative/positive RAG-policy and centroid-ranking tests.
- Independent GitHub readback of all three files: their blob SHAs equal the matching Git object hashes of the locally tested files. Python tests are therefore tied to exact staged source bytes.
- CrAM 2025 upstream root-license verification remains missing; **no upstream 2025 source code was copied**.
- The implementation deliberately does **not** bypass still-unbuilt CFA3 Model Router/HRB/Workload Mode/Security/License authorities. Real runtime calls and app-level admission remain disabled/pending.
- `cargo test --workspace` remains **NOT_RUN** due unavailable local Rust toolchain; no GitHub CI on this branch yet. CPU unit tests are not physical Current Host PASS and do not validate model-level CrAM reproducibility.

**Remaining work:** actual model-specific 2025 attention intervention with rights-compliant implementation and quantitative evaluation; 2026 adaptive-rank expert growth and real training/rollback with optional hardware adapters; full application/GUI authority bridge; Rust compilation/CI and physical-host gates. Work on disjoint CrAM files is independent of open parallel donor PR #7.

## CRAM-04/05 additional CPU qualification code (2026-10-10)

### CrAM 2025 — real bounded attention operation

- `cfa3_cram/attention2025.py`: independently written, CPU-only PyTorch **scaled dot-product attention** operation applying token-level additive credibility log-bias. Explicitly requires 4-D `B,H,T,D` float32/float64 CPU tensors, matching Q/K/V shapes, finite inputs, bounded non-positive bias and unambiguous self-attention causal masking. No upstream 2025 code is copied and no model-hook injection is performed.
- `tests/test_attention2025_cpu.py`: **8/8 actual local CPU PyTorch tests PASS**, including changed attention results, causal masking, strict input rejection and repeatability.
- **Limits:** this is a restricted functional attention operator, **not** an automatically approved or model-qualified transformer integration; credibility values and source-to-token mappings must first be approved by existing CFA3 authorities. The upstream CrAM 2025 license is still unverified and no source-code admission occurs.

### CRAM 2026 — bounded adaptive-rank expert training prototype

- `cfa3_cram/training2026.py`: independently written CPU-only low-rank residual expert with explicitly scoped model/projection/expert IDs; rank proposal from a caller-supplied, finite bounded gap; isolated SGD training with a bounded step count, optional reference-delta orthogonality penalty, checkpoint revision checks and rollback of its **own parameters** on failures.
- `tests/test_training2026_cpu.py`: **9/9 local Python/PyTorch CPU tests PASS**, including actual loss reduction on small synthetic data, unchanged previous expert tensors, checkpoint restoration, input validation and overflow rollback.
- **Limits:** this is **not** the upstream multimodal CRAM 2026 training algorithm, dynamic expert admission, a complete continual instruction tuning model, or evidence of no catastrophic forgetting on production datasets. It is a qualified *building block* only. It has no authority to create or activate a production expert, select a model/provider, or publish a checkpoint.

### Concrete local verification and GitHub readback

- Test command `python3 -m unittest discover -s tests -v` run in an isolated directory containing the two above new test modules and their corresponding source modules: **17 tests run, 17 passed, 0 failures**; Python 3.13.5 and PyTorch 2.10.0+cpu.
- Separate `python3 -m compileall -q cfa3_cram tests`: completed without Python syntax error.
- GitHub independent readback verified the precise source bytes of all four new files by equality of `git hash-object` on the locally tested file and GitHub's corresponding blob SHA.
- Feature branch last checked as a **disjoint development branch**; parallel donor PR #7 and documentation PR #8 are untouched. No extra CrAM PR opened and no writes to `main`.
- Rust `cargo test --workspace` and GitHub CI: **NOT_RUN**; `cargo`/`rustc` unavailable in the local test environment and the existing CI triggers on PR or main, neither of which this staging branch uses.
- Runtime rights/security/Model Router/HRB/Workload Mode/Temporal/Qt6 parent-consumer integration and physical Current Host evidence remain **PENDING**. The present tests are not runtime promotion or physical host PASS.
