# CFA3 repository agent instructions (bootstrap projection)

**This file has no standalone canonical authority.** The canonical new-CFA3 policies under `canonical/policies/` govern admitted rules. A historical `AGENTS.md` is a source to reconcile, not an instruction file to copy unchanged.

## Scope and change discipline
- One explicitly requested task per conversation. Record main task, result, allowed files/actions, constraints, and completion condition before work.
- Never self-expand scope. New ideas are separate proposed tasks, not automatic implementations.
- Only use `ubuntuokos/CFA3-CinenemFoundArchitecture3` for new CFA3 mutations; never write to the legacy repository.
- At most one active implementation PR. No new PR or code implementation without the owner's approval.
- Check exact `main`, target branch/head, checks and overlapping PRs before **every** mutation or merge. Main is not a direct-write workspace.
- **BLOCKER = STOP**: drift, failed gate, conflict, uncertain state, missing authority or overlapping writes. No automatic rebase, bypass, new PR, workaround, rerun or alternative path.
- Notify before long tool/CI chains and security-sensitive operations. After every mutation report target, SHA/state, next step and blockers.
- DEV-11 / AI-11: only your own deterministic mechanical error, inside unchanged scope/policy/authority, may be corrected after notifying; inspect exact state if partial writes might have happened.

## Safety and proof
- Never fake `PASS` or Current Host evidence. Synthetic/reference CI is not physical-host proof. Missing proof is `PENDING`.
- Never weaken security, required tests, resource-lease authorities, evidence or gates just to make CI green.
- No secrets or credentials in repository, logs, or evidence.
- CPU-only must remain valid for the platform; accelerator availability is 0..N, vendor neutral. HRB owns resources, Model Router owns AI model routes, Workload Mode owns operating modes.
- A CPU fallback is allowed in development **only within preauthorized profiles with provenance** and can never make a GPU test or physical Current Host PASS. No silent fallback.
- Never copy legacy code/configs unchanged or unchecked; record source revision, new-CFA3 fitness, risks, licensing, tests and adoption decisions.

## New CFA3 requirements
- 200 distinct capability targets are **not yet reconciled**. Legacy 175 baseline must not be treated as the new count.
- Complete and verify the common Foundation before any application-layer FINAL; design whole application catalog/layer dossiers before implementation.
- Qt 6 mandatory for GUI applications. Standalone GUI PASS and (when real parent exists) actual parent-integration GUI PASS. Do not fabricate parent links.
- Rust-first native development; retain Python/C++/other upstream languages when warranted by evidence.
- Real edge/handoff graph only. Three-level Platform/Layer/Global Current Host. Handoffs preserve source origin, revisions, processing ownership, acceptance and rollback.
- Donor review and usage-edge registration are separate from source discovery, dependency install and runtime admission.

## External-link processing (owner-approved lifecycle rule)
- **Before analyzing any external link** run the source lifecycle lookup and inspect the prior processing history, verified versions, moves, aliases and approval status.
- Reuse the earlier approved decision when unchanged. Updates, moves and discontinued support produce new, append-only review actions, **not silent decision overrides**.
- For unsupported technology supplying a retained capability: propose CFA3 adaptation of reusable, licensed code or an independent CFA3 replacement. Never self-authorize implementation.
- If the imported source index is incomplete, do not label unmatched links new; record `BLOCKED_INDEX_INCOMPLETE`.
- See `canonical/policies/CFA3-SOURCE-LIFECYCLE-POLICY-001.json` and `docs/governance/SOURCE-LIFECYCLE.md`.

## Donor migration and level-by-level expansion (owner-approved design)
- Follow `canonical/policies/CFA3-DONOR-BOUNDED-CLASSIFICATION-001.json` and `docs/governance/DONOR-MIGRATION-AND-CLASSIFICATION-V2-001.md` for the approved *plan*; its implementation and L1–L5 data are still PENDING.
- Process L1 through L5 sequentially. After **each** level, approved donors must be actually published and searchable; the next level is forbidden until a durable `PUBLISHED_AND_VERIFIED_PASS` exists.
- Freeze original L1 incoming link-record count `B`; on each level count raw outbound URL **occurrences before deduplication** and stop immediately if count exceeds `floor(1.15 * B)`. This is *not* the donor DB size and is *not* summed across levels.
- **Global discovery depth never resets:** frozen L1 inputs are the only L1 roots. New sources first found at L2/L3/L4/L5 have only 4/3/2/1 levels remaining (including their current level). New donor approval, re-encounter, newly classified source or publication must not create another five-level crawl; L6 is forbidden.
- Historical decisions, duplicate links and already-processed records are not re-analyzed. Discovered children have **no automatic donor admission**. Stop and retain the last fully published snapshot on blockers; never revive unnecessary legacy applications or configs.

Read `docs/governance/RECONCILIATION.md`: the full legacy rule inventory is **not yet complete**.
