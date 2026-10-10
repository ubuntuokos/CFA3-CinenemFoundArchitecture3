# CFA3 Current Host — Community Plugin Integration

**Implementation ledger • 2026-10-10**

Status: **PARTIALLY IMPLEMENTED / NOT ADMITTED / NO PHYSICAL PASS**.
New repo: ubuntuokos/CFA3-CinenemFoundArchitecture3.
Feature branch: feat/current-host-plugin-fabric-20261010.
Historical repo is READ ONLY. Historical physical PASS cannot be transferred.

## Task start record

**Fő feladat:** Implement the new CFA3 Current Host according to the user-approved three-tier design, including community plugin development, integration and lifecycle.
**Kért eredmény:** Real-edge Foundation → Layer → Global proof planning, delta impacts NONE/SCOPED/FULL, CFA3-owned positive/negative/rollback evidence, community SDK/Testkit/host registry and actual verified integration.
**Engedélyezett kör:** New native Current Host crate and CPU-only reference/testkit modules, manifests, tests, documentation and exact-state GitHub branch changes only.
**Korlátozások:** No main direct write, no donor #7 or documentation #8 or CrAM branch modifications; no authority duplication; CPU-only; no fabricated physical PASS; user-approved vendor/third-party qualification exclusions.
**Befejezési feltétel:** Working runtime-integrated Current Host, physical host proofs and real plugin host isolation/GUI integration; **NOT MET**.

## Scope and manufacturer / commercial software exclusions

The Current Host is responsible for **only CFA3-developed code, CFA3-owned adapters/interfaces and CFA3 plugin-host boundaries**.

- Do not requalify Linux drivers made by hardware manufacturers; refer to the manufacturer's documented distro compatibility and official download source instead. Do not invent physical tests for unavailable hardware.
- Do not perform independent QA of third-party commercial software.
- Do not perform the community developer's product-quality tests for third-party plugins.
- DO prove the CFA3-owned interface to drivers, software or plugins where actually exercised, and enforce the CFA3-owned safety, resource, permission and communication contracts.
- Vendor support declarations are compatibility input, **not** local CFA3 physical PASS or a bypass of security gates.

The user is responsible for selecting third-party software suitable for the environment; CFA3 still prevents its own plug-in host from granting unauthorized system privileges.

## Implemented structure

| Area | Actual implementation | Limit |
| --- | --- | --- |
| Rust native three-level Current Host core | crates/cfa3-current-host/src/lib.rs | No real physical authority, rust test not yet run |
| Rust workspace registration | Cargo.toml, crates/cfa3-current-host/Cargo.toml | Foundation not admitted |
| Python CPU reference planner | cfa3_current_host/core.py | Only structure and obligations; no physical PASS |
| Safe manifest / plugin lifecycle manager | cfa3_current_host/plugin_fabric.py | No plugin execution; external rights/security approval mandatory |
| Community SDK and static host Testkit | cfa3_current_host/developer_sdk.py | Not community plugin product certification |
| CLI | cfa3_current_host/__main__.py | Generates plans and SDK operations, no runtime promotion |
| Real-edge example | examples/current-host-graph.json | 3D → Video → Audio and Video → plugin-host only |
| Tests | tests/test_current_host_core.py, tests/test_current_host_plugins.py, tests/test_current_host_developer_sdk.py, tests/test_current_host_cli.py | Test definitions exist, not yet proven by a run |

### Three-level operation

**Platform Foundation:** test common CFA3-owned runtime and API/safety contracts, not drivers themselves.
**Layer Current Host:** isolate each affected application's CFA3-owned operations, plugin-host bridge, GUI and transfers.
**Global Current Host:** evaluate only *registered* cross-layer handoff boundaries and proofs, never an invented all-to-all dependency graph.

Changes to external drivers, vendor applications or community plugin internals produce **NONE** when no CFA3-owned interface changes. Native app changes yield **SCOPED** plus only actual downstream consumers, while global Security/Evidence/ABI/Workload contracts explicitly yield **FULL**.

Each selected CFA3-owned unit requires POSITIVE, NEGATIVE and ROLLBACK obligations. GUI adds STANDALONE_GUI and, only for an actual parent, PARENT_INTEGRATION_GUI obligations. Cross-layer transfers require handoff verification including revision, origin, processing owner, acceptance and rollback.

### Community plugin development and admission

Community SDK supports manifest schema, target apps, capabilities, permissions, dependencies, version/publisher/license fields, bounded deterministic ZIP packaging, static tests and scaffold generation.

Host lifecycle distinguishes DISCOVERED → INSPECTED → ADMITTED → INSTALLED → ENABLED / DISABLED / QUARANTINED / REMOVED. Re-inspection cannot reset an admitted or enabled plugin to a weaker state. Runtime enablement requires an **external** actual sandbox-runtime validator, with Security, Rights and Identity approval needed at admission. No arbitrary plugin code is imported or executed by the package inspector.

The CFA3-owned host is responsible for safe interfaces and actual consumption edges, not for authoring/QA of external plugin functionality. Qt6 host components, standalone/parent GUI tests and true sandbox launcher remain pending.

## Reference CLI commands

Plan CFA3 video changes:

    python3 -m cfa3_current_host plan --graph examples/current-host-graph.json --changed video-editor

Driver-only change, outside CFA3 verification:

    python3 -m cfa3_current_host plan --graph examples/current-host-graph.json --changed vendor-driver

Community developer SDK starter:

    python3 -m cfa3_current_host plugin-scaffold --target ./my-plugin --id com.example.myplugin --app cfa3.video --publisher "Example Maintainer" --license MIT

Bundle / inspect (no execution):

    python3 -m cfa3_current_host plugin-build --root ./my-plugin --output ./my-plugin.cfa3-plugin
    python3 -m cfa3_current_host plugin-inspect --bundle ./my-plugin.cfa3-plugin --available-app cfa3.video

The static inspection **never claims** producer identity, license verification, actual sandboxing, quality assurance, physical Current Host PASS or runtime admission.

## Evidence and verification status

GitHub commits and independent branch readbacks can prove source files exist. They are not execution evidence.

- Rust compiler / cargo: **unavailable here**, Rust tests NOT_RUN.
- This feature branch does not automatically trigger GitHub Actions (existing workflow triggers on PR or main only); CI: NOT_RUN.
- New host code test definitions exist; actual Python run on exact committed source files is **PENDING**.
- Physical Current Host on the user's actual device: NOT_RUN, NO_PASS.
- Actual CFA3 Foundation authority providers (Security, Rights, HRB, Model Router, Workload Mode, Temporal, Evidence) are still not built/admitted in the new repo.
- This code cannot issue physical PASS: even apparently complete external proofs are reported only as READY_FOR_AUTHORITY_REVIEW.
- Native runtime plugin sandbox / end-user Qt6 GUI: NOT_IMPLEMENTED.
- No fully reconciled 200-capability Current Host contract registry, no production release gate, no main merge.
- Parallel donor PR #7, documentation PR #8 and CrAM development branch remain outside this change.

**The code is a scoped implementation, not a completed Current Host.** Final acceptance requires real runtime authority connections, working sandbox and Qt6 host integration, physical tests of CFA3-owned operations and externally verified evidence on the actual hardware.

## Additional local runner and Qt6 panel

- cfa3_current_host/local_runner.py: bounded local observer for CFA3-owned test modules only. Captures reported Python and Rust reference outcomes and environment metadata; never scans vendor drivers, calls external commercial binaries or issues a physical PASS.
- The observer can be explicitly invoked **on the target user's actual CFA3 checkout**, but its report remains REFERENCE_ONLY_PENDING_EXTERNAL_AUTHORITY until the external Evidence authority validates actual host identity and scoped proofs.
- cfa3_current_host/qt6_dashboard.py: optional PySide6 Qt6 standalone Current Host panel. Four tabs — Foundation, Layer, Global, Community Plugins — with persistent and per-panel mandatory Workload Mode indicator. Shows obligation evidence PENDING; cannot create PASS or pretend an actual parent GUI exists. If Qt6 is unavailable it raises GuiDependencyMissing.
- tests/test_current_host_qt6.py and tests/test_current_host_runner.py add honest missing-toolkit, safe-runner and failure-mode cases. GUI execution and real Qt6 parent-integrated PASS remain **NOT_RUN**.
- CFA3-owned inbound integration is also tested when its *upstream* source remains unchanged, including a vendor → CFA3-owned connector boundary. No third-party component itself is targeted for Current Host proof.
- Run a local, self-contained scoped reference suite, emitting a single immutable JSON report (no redundant archives and no auto-upload):

    python3 -m cfa3_current_host selftest --repo . --output ./current-host-local-candidate.json

The CLI rejects overwriting an existing report, does not change OS drivers, and cannot generate Current Host PASS. If the Rust toolchain is missing, the Rust result is NOT_RUN_MISSING_CARGO.

**Evidence limitation remains:** Current Host no physical authority service is implemented in this branch; the local observer is not a substitute for actual physical attestation. GitHub Actions run on pull_request or main only, and neither event was started for this branch. The source files are in a separate feature branch, not on main.

**Current implementation closure:** Source materialization and independent GitHub readback will be recorded separately; full project closure requires successful runtime and physical proof from the real user environment and the existing central CFA3 authorities.
