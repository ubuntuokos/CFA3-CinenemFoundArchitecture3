# Legacy development rules: controlled reconciliation

Historical source: `ubuntuokos/Final-Architecture-v3.0` at commit `a9c724da62bf49f3353c694990fc51443e634b4a`.
New target: `ubuntuokos/CFA3-CinenemFoundArchitecture3`.

**This is a source inventory seed, not full rule admission.** The 21 Git blob paths and SHAs in `canonical/registries/CFA3-LEGACY-RULE-SOURCE-LEDGER-001.json` were individually discovered. The source tree has 3,159 files; an unreviewed source is **not evidence of absence of a rule**.

## Admission workflow
1. Enumerate every rule-bearing canonical decision/profile/policy/contract, scoped `AGENTS.md`, gate, CI workflow and relevant docs (including indirect constraints).
2. Identify source ID, effective authority/status, implementation vs operational projection, approval/replacement/retirement chronology, SHA and affected scope.
3. Record per-rule: **RETAIN**, **ADAPT**, **SUPERSEDE_WITH_EXPLICIT_APPROVAL**, **NOT_APPLICABLE_WITH_REASON** or **BLOCKED**. Never discard an applicable rule.
4. Preserve all required constraints while adapting new repository names, 200 capabilities, CPU-only baseline, Qt 6, Rust-first and three-level Current Host. A conflict is **BLOCKER**, not permission to choose silently.
5. Create new canonical contracts and corresponding independent positive/negative gates. Old files or tests must not simply be copied; old reference CI/current-host evidence cannot be promoted.
6. Record owner approval, snapshot-bound code review and actual execution proofs. Only then change `full_development_governance_admission`.

## Known preliminary clashes needing explicit reconciliation
- Old `canonical_capability_count: 175` versus **new design target 200**. Do not invent capability IDs or simply change the integer.
- Old Current Host delta contract assumed historic base admission and 175 × 3 evidence. New Platform/Layer/Global proof model has independent rules, actual edges only.
- Old `config/fa3-dev-policy.json` included permissive implicit fallback; new CPU fallback requires preauthorized profile/provenance and must not conceal failed accelerator evidence.
- GUI base was not universally Qt 6; new GUI requirement is mandatory for every GUI app.
- Legacy implementation paths may be Python-centric; new native development is Rust-first, subject to justified language preservation.
- Some legacy policy records are **CANDIDATE/STAGED**, not accepted canonical authority; verify status rather than importing blindly.

## Still required
Complete full source tree classification, rule-by-rule coverage ledger with zero unexplained omissions, current new CFA3 explicit requirements, approved conflict decisions, executable gate plan and physical-test applicability matrix.

**Not allowed at this stage:** copy old source into `src/`, import old CI as-is, claim full governance PASS, import 175 proofs, start application implementation or publish releases.
