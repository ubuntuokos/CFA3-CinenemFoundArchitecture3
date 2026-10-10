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

## 2026-10-10 — CPU Foundation, plugin isolation and catalog implementation

- Added **cfa3_current_host/foundation_runtime.py**: independently scoped
  Security grants, artifact-rights digest admission, exact CPU Model Router,
  HRB CPU leasing and mandatory Workload Mode arbitration in one composed
  local Foundation runtime. Resources release on expiry and failure; no
  silent model or workload fallback. This is an operational **local reference
  Foundation**, NOT admitted production Security/Evidence authority.
- Added **cfa3_current_host/foundation_pipeline.py**: connects actual Current
  Host POSITIVE/NEGATIVE/ROLLBACK, GUI and handoff obligations to the CPU
  Foundation, with fail-closed prerequisite binding and reference receipts.
- Updated **cfa3_current_host/local_runner.py**: scoped selftests obtain and
  release live local CPU HRB and Workload Mode leases.
- Added **cfa3_current_host/plugin_sandbox.py**: bounded Linux bubblewrap
  subprocess isolation, exact bundle digest and plugin.run permissions. A
  live Foundation session with matching publisher/artifact rights and scope
  is mandatory; no unconfined fallback. Real bubblewrap and vendor/security
  certification are NOT VERIFIED in the current execution environment.
- Added **cfa3_current_host/capability_catalog.py**: enforces **200 distinct
  capability IDs** and exactly 3 minimum proof cases per ID (600 at the
  required target), plus separately required GUI/handoff cases. An empty
  example input lives at examples/current-host-capabilities.json because
  the *real* canonical 200 records are NOT YET RECONCILED. Synthetic 200
  IDs and 600 synthetic receipts never produce physical PASS.
- The user-approved scope is explicitly staged as
  canonical/policies/CFA3-CURRENT-HOST-OWNERSHIP-001.json: certify CFA3
  code and our integration/host interfaces, not vendor drivers, commercial
  software products or community-developed plugin internals.
- Added pyproject.toml installable CLI with catalog-check and optional GUI
  commands.

### Local CPU test evidence — verified exact source bytes

Four GitHub source/test blobs were materialized locally and matched by
git hash-object, then tested with Python 3.13.5:

- foundation_runtime.py: c38d16e6cba0233d251fcad7bf948c45dcbffbed
- test_current_host_foundation_runtime.py: 20d83c1e78709ca627ea76dcfc97321b610f8c06
- capability_catalog.py: 3cf2bbcf370cc592f22d4732a5d5a87b12f6d88e
- test_current_host_capability_catalog.py: 6b33c33710046cf397819cf54104ac47f550d7a8

Result: **29 local tests run, 29 PASS, 0 failures**. This is
**REFERENCE EVIDENCE**, NOT physical Current Host PASS. This result does
not claim that all previous Python/Rust/Qt6/plugin-sandbox tests ran.

### User-facing commands, when this branch is checked out

    python3 -m pip install --no-build-isolation -e .
    python3 -m cfa3_current_host plan --graph examples/current-host-graph.json --changed video-editor
    python3 -m cfa3_current_host catalog-check --catalog examples/current-host-capabilities.json
    python3 -m cfa3_current_host selftest --repo . --output ./current-host-local-candidate.json
    python3 -m cfa3_current_host gui --graph examples/current-host-graph.json --changed video-editor

The last command requires actually installed PySide6/Qt6. It never marks
standalone or parent GUI as PASS without the applicable actual tests.

### Precise remaining acceptance gates

1. Run the whole checked-out branch suite and cargo test --workspace; this
   environment lacks rustc/cargo and Qt6. The actual plugin sandbox run is
   also not yet performed: bubblewrap is absent here.
2. Actual shared Foundation production Security/Rights/HRB/Model Router/
   Workload Mode and Evidence authorities still require independent
   admission/host integration. Local Foundation bootstrap is not a
   substitute for those production trust roots.
3. Reconcile 200 real capability records and the corresponding proof
   obligations. Do not auto-invent identities to satisfy a count.
4. Test real Qt6 parent application handoffs and actual plugin execution
   on a supported Linux host without claiming vendor-product QA.
5. Real physical host evidence and a separate Evidence authority review
   are still required. The current local reference tests cannot certify
   the user's actual hardware.

**Status: IMPLEMENTATION_STAGED, not Current Host FINAL.** The parallel
donor PR #7, RHEL README PR #8 and CrAM branch remain untouched.

### 2026-10-10 local CPU expiry + plugin-lease regression delta

The local CPU Foundation now reclaims expired **idle** CPU/Workload leases
before admitting new work, but never reclaims or force-releases an in-flight
operation. Each operation is bound to one session; duplicate concurrent runs
fail closed and the session TTL is rechecked on completion. The Linux plugin
sandbox wrapper now holds the Foundation CPU/Workload lease through its entire
subprocess operation; an apparent sandbox success after expiry is rejected.

**Independent local execution:** Python 3.13.5, 40/40 PASS, 0 failures,
`python3 -m unittest discover -s tests -p 'test_current_host_*.py' -q`
on the isolated CPU Foundation/capability test tree plus the exact sandbox
wrapper and five additional mock-isolation tests. Syntax compilation PASS.
The local `plugin_fabric.py` in this restricted test tree is explicitly a
**test double**, not the full GitHub plugin registry. Hence this is not a
claim of full branch tests or real bubblewrap sandbox execution.

New exact GitHub-readback source hashes, equal to locally executed files:
- Foundation runtime: `80fc6c01195e6d2df05b6fef88f10a020a748773`
- Plugin sandbox wrapper: `ca1953be74a781f93028334d38ff09a030afe627`
- Lease expiry test: `b5dcb4825395701b9425c48f63c09728a0b17f14`
- Plugin lease pin test: `e829e8c6554ea8a1012cbcf37da4e09e4c8e7ff8`

**Unchanged acceptance boundaries:** no physical Current Host PASS, no
full Rust/Qt6 verification, no actual plugin security certification, no
complete canonical 200-capability source reconciliation. All remain PENDING.

### 2026-10-10 — plugin host bounded I/O and concurrent lifecycle regression

The CFA3-owned community plugin sandbox now **never captures arbitrary plugin
stdout/stderr into unbounded host-process memory**. Each output stream goes to
a temporary file. The subprocess receives an RLIMIT_FSIZE of 64 KiB and the
host reads no more than 64 KiB plus one sentinel byte per output stream;
excessive output fails closed. Plugin entrypoint ZIP member size is checked
against its directory metadata BEFORE inflation (1 MiB bound) and once again
after reading, with no unsandboxed fallback.

The Community Plugin Registry serializes all state/activation transitions
under a reentrant per-registry lock, including static inspection, rights
admission, package installation, activation, disablement, quarantine and
removal. Specifically, an in-flight enable may not overwrite an explicitly
applied quarantine. Simultaneous attempts to enable two versions are reduced
to exactly one enabled version (the second is refused). Plugin internals,
commercial applications and vendor drivers remain outside CFA3-owned QA.

**Local Python 3.13.5 reference evidence:** 78 unit tests executed;
78 PASS, 0 failures; syntax compilation PASS. The local test tree contained
the EXACT following GitHub source/test blobs (independent git hash-object
equality confirmed):

- cfa3_current_host/plugin_sandbox.py: 92246bc56621f170d055155c8ad998bc43e61862
- cfa3_current_host/plugin_fabric.py: 1b1a01c50bf0c1cff86cc80b38760b927831dd18
- tests/test_current_host_sandbox_output.py: 9b8973bfda4e4b53c8f2a3035ef2a6f119180a71
- tests/test_current_host_plugin_races.py: 93df04a5e05e646dbdef7fd1ae2f8bb3f9f83083
- tests/test_current_host_plugin_sandbox.py: 816e8c6a41616583e420948765fa5defa50a3173
- tests/test_current_host_plugins.py: db52162851e9394dc6cf8899a0e814ccff8675a4
- cfa3_current_host/foundation_runtime.py: 80fc6c01195e6d2df05b6fef88f10a020a748773
- cfa3_current_host/capability_catalog.py: 3cf2bbcf370cc592f22d4732a5d5a87b12f6d88e

The local test tree additionally included the exact preexisting foundation,
catalog, lease-expiry and sandbox-lease regression files. The command was:

    python3 -m unittest discover -s tests -p 'test_current_host_*.py' -q

These tests validate the selected CPU Foundation, capability and Community
Plugin host functionality and simulated process-isolation boundary tests.
**They are NOT a full branch test run.** The local test tree does not include
the complete GitHub workspace; Rust, GUI, the remaining Python modules and
genuine Linux bubblewrap isolation are still NOT_RUN. Simulated subprocess
tests do not certify plugin isolation on a real host. No physical Current Host
PASS is issued or inferred.

**Known remaining security limit:** a plugin process already running at the
instant of revocation still needs an admitted process-supervisor termination
mechanism. Registry status locking is not a production process-kill service.
The implementation remains STAGED until the full shared runtime, Qt6,
process isolation, 200 real capability identities and physical evidence gates
have been validated.

### 2026-10-10 — canonical test plan and source provenance guards

The physical evidence review boundary and the live Foundation test executor
now **rebuild the Current Host delta plan from the registered real-edge graph**.
Caller-supplied plans cannot omit NEGATIVE, ROLLBACK, actual parent GUI or
actual affected handoff obligations to produce an apparently completed run.
Mismatched NONE/SCOPED/FULL mode, fabricated changed component or forged
plan contents are explicitly blocked. The evidence reviewer now also
rejects extraneous/unknown proof records and proof supplied for genuine NONE
scopes; it still NEVER issues physical Current Host PASS.

New regression definitions were added in:
- tests/test_current_host_core.py (5 evidence scope / provenance bypass cases).
- tests/test_current_host_foundation_pipeline.py (5 canonical plan bypass cases).

The local test runner no longer reports a trusted checkout revision based
solely on Git HEAD. It also checks a clean Git working tree, including
untracked files. Dirty or unverifiable checkouts are reported as
UNVERIFIED_DIRTY_OR_UNAVAILABLE_CHECKOUT with provenance
NOT_ADMITTED_SOURCE_PROVENANCE. A new regression case for untracked files
was added in tests/test_current_host_runner.py, alongside updates to the
existing clean/failure fixtures.

**Execution status for this update:** independent GitHub mutation and
readback are available; the **new 11 regression definitions are NOT_RUN**.
The earlier 78/78 target-specific CPU tests were re-run from the pre-existing
local partial materialization; that 78-PASS result DOES NOT verify the
changed canonical planner or dirty-checkout runner. The full feature-branch
Python tests, native Rust and Qt6 remain PENDING until the precise complete
branch can be executed. No GitHub CI workflow was dispatched or PR opened.

### 2026-10-10 — actual dirty-source runner test execution

An independent local Python 3.13.5 materialization of the exact GitHub
runner and runner-regression test files was created in the pre-existing
Current Host CPU-only reference test directory. Both file contents
**exactly matched their Git blob identifiers**:

- cfa3_current_host/local_runner.py: d839a5ebefd8e19bc6f5d2724f7681b98cf61812
- tests/test_current_host_runner.py: 8714bf05067b087baea7983f14b7aca590279ddd

The first full targeted run of 83 local tests exposed 3 test-double errors:
the fixture did not accept the default timeout parameter from the test
runner. The fixture was corrected within existing task scope without
changing its test intent or the runner's authority boundaries.

After this correction, the same local collection was rerun:

    python3 -m unittest discover -s tests -p 'test_current_host_*.py' -q

**Result: 83 tests run / 83 PASS / 0 failures**, plus Python syntax
compileall PASS. The corrected runner test's Git blob was independently
read back from GitHub and matched the locally executed source exactly.

**Coverage qualification:** these 83 tests are the existing partial CPU
Foundation/capability/Community Plugin modules plus the source provenance
runner tests. They are **not a complete checkout of the GitHub branch**,
therefore do not include the 10 newer canonical-plan tests. Rust, physical
host, real Qt6 GUI, plugin sandbox containment and 200 real canonical
capability reconciliation remain pending. The result is not physical PASS.

### 2026-10-10 — capability ID, graph and CLI integration

CapabilityCatalog now reconciles its 200 canonical identities against actual
CFA3-owned graph consumers and checks exact component ID, layer, revision,
ownership, missing mappings and duplicate capability consumers. Third-party
drivers and commercial applications remain outside CFA3-owned product QA.

A partial layer/SCOPED mapping cannot report GLOBAL 200 closure even with
a full-size catalog fixture. An external-only graph also cannot claim CFA3
mapping success. Complete global reconciliation requires the actual complete
CFA3 component graph and its 200 approved capability records; no synthetic
source identities were promoted into the canonical new-CFA3 registry.

The CLI command catalog-check now REQUIRES both catalog and actual graph and
calls the graph reconciliation gate rather than checking record count alone:

    python3 -m cfa3_current_host catalog-check \
      --catalog examples/current-host-capabilities.json \
      --graph examples/current-host-graph.json

New tests test_current_host_capability_catalog.py cover correct mappings,
mismatched versions, duplicates, missing catalog members, vendor exclusions,
partial versus global completion and a 200-fixture structural-only case.
GitHub-only test definitions test_current_host_cli.py also verify that no
catalog-check can omit the graph.

**Independently executed local Python proof for exactly matching Git blobs**:
- cfa3_current_host/capability_catalog.py:
  88d6c84a50ad36605258cd7701c4291924e27512
- tests/test_current_host_capability_catalog.py:
  e951be00b8a7d0c9dd90f595fdadf4be36687ea0

A partial materialization of the CPU/Plugin reference modules containing
these two exact files and the previously verified local runner passed
**91/91 unittest cases**, 0 failures, plus Python compileall.
This is a *partial scope* local reference result, NOT the full GitHub branch
suite and NOT a physical Current Host PASS. The new CLI parsing/integration
tests and canonical-plan tests are present in GitHub but remain NOT_RUN in
this local environment. Rust, Qt6, physical runtime and 200 real capabilities
are still pending.
