# New CFA3 Foundation constraints (design, not implemented)

- **Architecture:** common platform + separate application layers. Entire application catalog and each layer dossier are designed before layer implementation.
- **Capabilities:** exactly 200 distinct target capability identities after full source reconciliation; not a numeric replacement of the legacy 175 and not yet enumerated.
- **Native code:** Rust-first for new control, registry, lifecycle and safety code; retain technically justified Python/C++/GPU toolchains. No unneeded rewrites.
- **GUI:** Qt 6 mandatory for GUI applications; stand-alone test required; parent-integrated test required **only for a real parent**, otherwise N/A.
- **CPU:** CPU-only platform must work. Development CPU fallback can be approved and traced. No GPU test substitution; GPU-only features can remain unsupported when hardware is missing.
- **Runtime authorities:** Security/Identity, HRB resources, Model Router AI routing, Workload Mode, Evidence, Temporal workflow responsibilities must not be duplicated.
- **Current Host:** Platform Foundation → Layer Unit → Global aggregation; proofs strictly scoped to the actual physical device, app, capability, version and real edge/handoff graph.
- **Handoff:** source provenance and asset ownership remain separate from temporary processing responsibility; explicit accept/decline/rollback and trace.
- **Change handling:** scope lock, one active PR, source/licensing review, immutable historic proof, fail-closed gates, targeted consumer regression only.
- **Status:** `ARCHITECTURE_DESIGN_PENDING`, `FOUNDATION_NOT_BUILT`, `NO_RUNTIME_PASS`.
