# CSA – Internal development infrastructure

CSA-PLAN-001 v1.3 governs this tool. It is **not** part of the deliverable
CFA3 application, Rust crates, installer, or release artifacts. The
suggestion database contains potentially sensitive conversation text; **never
commit live records to this public application repository or any of its
branches**. A branch name containing "internal" does not make it private.

## Boundaries

- Development code: scripts/csa.py, with tests/test_csa.py.
- Canonical rules: canonical/policies/CSA-POLICY-001-v1.3.md and companion JSON.
- Data: a separately selected storage location outside the application
  checkout; it must not be shipped with the finished product.
- To call the GitHub store canonical, independently confirm a suitably
  access-controlled remote, branch, commit, file readback and permissions.
- Local CLI PASS is not proof of GitHub archiving, automated ChatGPT history
  access, verified implementation status or conversation-native downloads.
- ChatGPT cannot retrieve deleted conversations unless previously preserved.
- No donor migration or donor database changes are authorized by this tool.

## Minimal offline operations

    python3 scripts/csa.py --root /private/csa-archive init
    python3 scripts/csa.py --root /private/csa-archive add --project CFA3 --title "Példa" --suggestion-file /path/to/text.md --source chat:identifier
    python3 scripts/csa.py --root /private/csa-archive find "Példa"
    python3 scripts/csa.py --root /private/csa-archive verify
    python3 scripts/csa.py --root /private/csa-archive export --project CFA3 --output /path/to/export.zip

The user provides the relevant original suggestion as a file; no automatic
access to other conversations is implied. A native ChatGPT attachment must be
created by the active conversation runtime after materializing the real export.

## Remaining qualification

Full historical ingestion, donor-compatible cross-reference graph with
bounded traversal, authoritative repository implementation-state verification,
canonical GitHub synchronization and user-facing native ChatGPT integration
require independent proof. Do not mark those capabilities IMPLEMENTED until
real tests have passed. The parallel donor workflow is unaffected.
