# New CFA3 Foundation constraints (design, not implemented)

- **Architecture:** common platform + separate application layers. Entire application catalog and each layer dossier are designed before layer implementation.
- **Capabilities:** exactly 200 distinct target capability identities after full source reconciliation; not a numeric replacement of the legacy 175 and not yet enumerated.
- **Native code:** Rust-first for new control, registry, lifecycle and safety code; retain technically justified Python/C++/GPU toolchains. No unneeded rewrites.
- **GUI:** Qt 6 mandatory for GUI applications; stand-alone test required; parent-integrated test required **only for a real parent**, otherwise N/A.
- **CPU:** CPU-only platform must work. Development CPU fallback can be approved and traced. No GPU test substitution; GPU-only features can remain unsupported when hardware is missing.
- **Runtime authorities:** Security/Identity, HRB resources, Model Router AI routing, Workload Mode and Evidence must not be duplicated. **Durable workflow engine selection is OPEN** for this new CFA3 target architecture; legacy Temporal designation or runtime evidence is not inherited. One authoritative durable lifecycle owner must be defined before runtime activation.
- **Current Host:** Platform Foundation → Layer Unit → Global aggregation; proofs strictly scoped to the actual physical device, app, capability, version and real edge/handoff graph.
- **Handoff:** source provenance and asset ownership remain separate from temporary processing responsibility; explicit accept/decline/rollback and trace.
- **Change handling:** scope lock, one active PR, source/licensing review, immutable historic proof, fail-closed gates, targeted consumer regression only.
- **Status:** `ARCHITECTURE_DESIGN_PENDING`, `FOUNDATION_NOT_BUILT`, `NO_RUNTIME_PASS`.

## Unified Execution & Fulfillment Fabric (UEFF) — integrated Foundation design

The **UEFF** is the approved target shared-Foundation capability for need assessment, competency/resource/fulfillment planning and durable task orchestration; **CFF is the embedded internal domain, not a separate application or duplicate platform service**. The new CFA3 does not inherit the old repository's Temporal selection, 175-capability baseline, implementation or physical evidence. Future durable-engine choice is open, and no runtime has been admitted by this document.

**Responsibility, reciprocal commitments and warranties are mandatory UEFF design requirements:** customer and contractor preconditions, explicitly assumed obligations, responsibility boundaries, delivery/commissioning/acceptance evidence, statutory versus voluntary warranty conditions, complaint/remedy obligations and post-delivery deadlines. A missing customer power supply may make a refrigerator test `NOT_VERIFIABLE`; an omitted contractor-supplied compressor is an independently assessable incomplete delivery. No automatic legal liability, forfeiture of statutory claims or unapproved scope change is permitted.

Full owner-approved architectural scope and acceptance cases: [UEFF–CFF Foundation plan](UEFF-CFF-FOUNDATION-PLAN.md). This is a **design baseline only**, not completed implementation, admission, CI PASS or Current Host verification.
