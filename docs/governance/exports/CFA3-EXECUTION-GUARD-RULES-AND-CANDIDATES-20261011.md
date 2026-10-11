# CFA3 Execution Guard – szabályok és szabályjelöltek

Forrás: `ubuntuokos/CFA3-CinenemFoundArchitecture3`, commit `11fee820611a8949b6df4b52d4d40a2f236937c4`. Történeti forrás: `ubuntuokos/Final-Architecture-v3.0`, commit `a9c724da62bf49f3353c694990fc51443e634b4a`.

**A jelenlegi 24 DEV/AI-szabály kötelező; a 78 történeti jelölt nincs befogadva.** Ez az export nem módosítja a kötelező ellenőrzéseket, és nem állítja, hogy a teljes történeti szabályleltár kész.

## Jelenlegi kanonikus szabályok (24)

| Azonosító | Kanonikus szabálykód |
|---|---|
| DEV-01 | STOP_ON_BLOCKER |
| DEV-02 | NO_AUTONOMOUS_WORKAROUND |
| DEV-03 | THREAD_SCOPE_LOCK |
| DEV-04 | FRESH_STATE_BEFORE_WRITE |
| DEV-05 | OVERLAP_IS_BLOCKER |
| DEV-06 | NO_AUTOMATIC_WORKFLOW_OR_GATE_START |
| DEV-07 | REPORT_AFTER_EVERY_MUTATION |
| DEV-08 | EXACT_HEAD_BEFORE_MERGE |
| DEV-09 | NO_SILENT_REDESIGN_OR_REPAIR |
| DEV-10 | CURRENT_OWNER_RESTRICTION_WINS |
| DEV-11 | NARROW_SELF_CORRECTION_EXCEPTION |
| DEV-12 | NO_ASSUMPTIONS_EXACT_SCOPE_AND_CANONICAL_DESIGN |
| AI-01 | STOP_ON_BLOCKER |
| AI-02 | NO_INFERRED_BYPASS |
| AI-03 | EXPLICIT_SCOPE_BINDING |
| AI-04 | FRESH_STATE_OVER_CACHE |
| AI-05 | CROSS_AGENT_COLLISION_BLOCK |
| AI-06 | EXPLICIT_SIDE_EFFECT_LEVEL |
| AI-07 | MUTATION_AUDIT |
| AI-08 | EXACT_STATE_AUTHORIZATION |
| AI-09 | UNKNOWN_IS_BLOCKER |
| AI-10 | LATEST_OWNER_CONSTRAINT_WINS |
| AI-11 | NARROW_SELF_CORRECTION_EXCEPTION |
| AI-12 | NO_ASSUMPTIONS_AND_MANDATORY_CFA3_COMPLIANCE |

## Történeti fejlesztési / AI-jelöltek (22)

**DEV-01 — BLOCKER_IS_IMMEDIATE_STOP**

Conflict, changed main, failed gate, uncertain state, overlapping work or unexpected CI causes immediate STOP and report.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/0`

**DEV-02 — NO_AUTONOMOUS_WORKAROUND**

After a blocker, no autonomous rebase, workflow, replacement PR, component change, bypass or alternative route.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/1`

**DEV-03 — THREAD_SCOPE_LOCK**

A conversation may affect only the explicitly scoped task files, PRs and directly authorized dependencies.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/2`

**DEV-04 — FRESH_STATE_BEFORE_WRITE**

Before every GitHub mutation re-check main SHA, target head and relevant open PR state.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/3`

**DEV-05 — OVERLAP_IS_BLOCKER**

Concurrent modification of the same canonical file, gate, workflow or exclusive resource is a blocker unless explicitly owner-overridden for this conversation.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/4`

**DEV-06 — NO_AUTOMATIC_WORKFLOW_OR_GATE_START**

Start a workflow or gate only when required for task closure and only when no equivalent run is already active.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/5`

**DEV-07 — REPORT_AFTER_EVERY_MUTATION**

After each mutation report what changed, current SHA, next step and blocker status.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/6`

**DEV-08 — EXACT_HEAD_BEFORE_MERGE**

Merge requires exact checked head and base/main; any drift blocks merge.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/7`

**DEV-09 — NO_SILENT_REDESIGN_OR_REPAIR**

Unexpected conditions requiring redesign or repair must be reported before changing strategy.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/8`

**DEV-10 — CURRENT_OWNER_RESTRICTION_WINS**

Current explicit owner restrictions override earlier autonomy grants and broader approvals.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/9`

**DEV-11 — SELF_CORRECTION_EXCEPTION**

The development AI may autonomously correct only its own clearly mechanical or technical mistake when the correction is deterministic, preserves owner intent, remains inside the active scope and approved architecture/policy, creates no workaround or unnecessary side effect, and does not bypass a blocker, gate, security rule or authority boundary. The AI must notify the owner when the mistake is recognized and correction begins; if partial mutation may have occurred, exact state must be verified first; after correction the AI must report the mistake, correction, state change, current head/SHA or relevant state, and remaining blockers.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/development_rules/10`

**AI-01 — STOP_ON_BLOCKER**

AI execution stops on a blocker and reports it before any further side effect.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/0`

**AI-02 — NO_AUTONOMOUS_BYPASS**

An AI may not infer permission to bypass a blocker from the user's end goal.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/1`

**AI-03 — ACTIVE_SCOPE_BINDING**

AI execution must carry explicit task scope, allowed/forbidden actions and applicable overrides.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/2`

**AI-04 — FRESH_STATE_BEATS_MEMORY**

Live verified state outranks remembered or cached repository, workflow and runtime state.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/3`

**AI-05 — CROSS_AGENT_COLLISION_DETECTION**

Conflicting concurrent work by another agent, task or PR blocks mutating execution.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/4`

**AI-06 — EXPLICIT_SIDE_EFFECT_LEVEL**

READ, ANALYZE, PLAN, WRITE, COMMIT, PUSH, PR, WORKFLOW, GATE, MERGE, RELEASE and EXTERNAL_ACTION permissions do not imply one another.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/5`

**AI-07 — MUTATION_AUDIT**

Every state-changing AI operation requires an attributable audit record.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/6`

**AI-08 — EXACT_STATE_COMMITMENT**

An authorization based on a concrete state expires when that state materially changes.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/7`

**AI-09 — UNCERTAINTY_IS_BLOCKER**

Unknown current state, authority, scope ownership or approval validity fails closed.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/8`

**AI-10 — LATEST_OWNER_CONSTRAINT_PRIORITY**

Current explicit owner restrictions override earlier model autonomy and execution permissions.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/9`

**AI-11 — SELF_CORRECTION_EXCEPTION**

A CFA3 AI/model/agent may autonomously correct only its own clearly mechanical or technical mistake under the same deterministic, scope-preserving, authority-preserving and fail-closed conditions as DEV-11. It must notify before correction, verify exact state first when partial mutation is possible, and report the correction and resulting state. Redesign, alternative technical solutions, new PR/branch, cross-component changes, restriction weakening, review-discovered design or implementation defects, new permissions/side effects, or uncertain corrections remain BLOCKER -> STOP -> REPORT.

Forrás: `canonical/CFA3-DEVELOPMENT-AI-BEHAVIOR-GOVERNANCE-POLICY-001.json#/ai_behavior_rules/10`


## Történeti minőségi szabályjelöltek (29)

**Q-CORE-001 — CORE (HARD_GATE)**

Placeholder prose must not ship.

Mintázat: `(?i)\blorem ipsum\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/0`

**Q-CORE-002 — CORE (HARD_GATE)**

Placeholder copy or metric markers must not ship.

Mintázat: `(?i)\b(?:TODO[_ -]?COPY|PLACEHOLDER[_ -]+(?:COPY|TEXT|METRIC)|DUMMY[_ -]?METRIC)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/1`

**Q-CORE-003 — CORE (HARD_GATE)**

Fabricated metrics or telemetry are forbidden.

Mintázat: `(?i)\b(?:fabricated|invented)[ _-]?(?:telemetry|metric|benchmark|rating)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/2`

**Q-CORE-004 — CORE (PURPOSE_GATE)**

Generic hype or unsupported showcase claims require explicit purpose and evidence.

Mintázat: `(?i)\b(?:next[- ]gen AI 2\.0|10,000% ROI|500,000 founders)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/3`

**Q-UI-001 — UI (PURPOSE_GATE)**

Terminal-like decoration requires an explicit functional purpose.

Mintázat: `(?i)\b(?:fake terminal|terminal decoration)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/4`

**Q-UI-002 — UI (PURPOSE_GATE)**

Bento layout is permitted only when justified by the information architecture.

Mintázat: `(?i)\bbento(?:[- ]grid)?\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/5`

**Q-UI-003 — UI (QUALITY_LOCK)**

Repeated decorative emoji can indicate generic AI styling.

Mintázat: `(?:✨|🚀|🔥){2,}`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/6`

**Q-UI-004 — UI (HARD_GATE)**

GUI artifacts must not directly execute providers or shell processes.

Mintázat: `(?i)\b(?:ollama\s+run|nvidia-smi|subprocess\.|QProcess\b|Process\s*\{)`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/7`

**Q-COPY-001 — COPY (QUALITY_LOCK)**

Generic hype language should be replaced with concrete claims.

Mintázat: `(?i)\b(?:revolutionary|game[- ]changing|unleash the power|transform your workflow forever)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/8`

**Q-COPY-002 — COPY (PURPOSE_GATE)**

Emoji-led marketing bullets require an explicit content purpose.

Mintázat: `(?m)^\s*[-*]\s*[🚀✨🔥✅💡]`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/9`

**Q-COPY-003 — COPY (PURPOSE_GATE)**

Superlative product claims require explicit justification and evidence.

Mintázat: `(?i)\b(?:best[- ]in[- ]class|world[- ]class)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/10`

**Q-COPY-004 — COPY (HARD_GATE)**

Absolute unsupported claims are forbidden.

Mintázat: `(?i)\b(?:100% accurate|guaranteed results|zero risk)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/11`

**Q-HUMAN-001 — HUMAN (PURPOSE_GATE)**

Disabling keyboard focus on an interactive surface requires explicit justification.

Mintázat: `\bfocusPolicy\s*:\s*Qt\.NoFocus\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/12`

**Q-HUMAN-002 — HUMAN (PURPOSE_GATE)**

Suppressing accessibility exposure requires explicit justification.

Mintázat: `\bAccessible\.ignored\s*:\s*true\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/13`

**Q-HUMAN-003 — HUMAN (QUALITY_LOCK)**

Very low opacity can reduce readability and should be reviewed.

Mintázat: `\bopacity\s*:\s*0\.[0-3]\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/14`

**Q-HUMAN-004 — HUMAN (QUALITY_LOCK)**

Interaction copy should describe the action rather than the gesture.

Mintázat: `(?i)\b(?:click here|tap here)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/15`

**Q-RESP-001 — RESPONSIVE (QUALITY_LOCK)**

Large fixed widths should be reviewed against responsive behavior.

Mintázat: `\bwidth\s*:\s*(?:1[3-9]\d{2}|[2-9]\d{3,})\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/16`

**Q-RESP-002 — RESPONSIVE (QUALITY_LOCK)**

Large fixed heights should be reviewed against responsive behavior.

Mintázat: `\bheight\s*:\s*(?:1[0-9]\d{2}|[2-9]\d{3,})\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/17`

**Q-RESP-003 — RESPONSIVE (HARD_GATE)**

Extreme fixed width constraints are forbidden on general FA3 UI surfaces.

Mintázat: `\b(?:minimumWidth|maximumWidth)\s*:\s*[2-9]\d{3,}\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/18`

**Q-RESP-004 — RESPONSIVE (PURPOSE_GATE)**

Platform-size exclusions require explicit product justification.

Mintázat: `(?i)\b(?:desktop only|not supported on mobile)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/19`

**Q-CODE-001 — CODE (QUALITY_LOCK)**

Decorative comment banners should be removed unless they aid navigation.

Mintázat: `(?m)^\s*(?:#|//)\s*[=\-_*]{8,}\s*$`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/20`

**Q-CODE-002 — CODE (QUALITY_LOCK)**

Generic generation-origin comments add little maintenance value.

Mintázat: `(?im)^\s*(?:#|//)\s*(?:AI[- ]generated|generated by (?:AI|ChatGPT))\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/21`

**Q-CODE-003 — CODE (QUALITY_LOCK)**

Vague maintenance comments should be made actionable or removed.

Mintázat: `(?im)^\s*(?:#|//)\s*(?:TODO|FIXME)\s*:\s*(?:clean up|improve|refactor)\s*$`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/22`

**Q-CODE-004 — CODE (QUALITY_LOCK)**

Fixed sleeps in automation code should be justified by deterministic behavior.

Mintázat: `(?i)\b(?:sleep\(\s*[1-9]\d*\s*\)|time\.sleep\(\s*[1-9]\d*\s*\))\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/23`

**Q-FA3-001 — FA3 (HARD_GATE)**

Fake capability representation is forbidden.

Mintázat: `(?i)\b(?:fake|mock|pretend)[ _-]?capability\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/24`

**Q-FA3-002 — FA3 (HARD_GATE)**

Fake provider or model representation is forbidden.

Mintázat: `(?i)\b(?:fake|placeholder|dummy)[ _-]?(?:provider|model)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/25`

**Q-FA3-003 — FA3 (HARD_GATE)**

User-facing or generated artifacts must not instruct authority bypass.

Mintázat: `(?i)\bbypass\s+(?:UAF|HRB|Model Router|MCP Gateway|Secret Broker)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/26`

**Q-FA3-004 — FA3 (HARD_GATE)**

Silent fallback representation is forbidden.

Mintázat: `(?i)\b(?:silently fallback|silent fallback)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/27`

**Q-FA3-005 — FA3 (HARD_GATE)**

PASS or VERIFIED claims without evidence are forbidden.

Mintázat: `(?i)\b(?:unverified.{0,40}(?:PASS|VERIFIED)|(?:PASS|VERIFIED).{0,40}without evidence)\b`

Forrás: `canonical/quality/FA3-QUALITY-RULE-REGISTRY-001.json#/rules/28`


## Történeti feladatkezelési szabályjelöltek (27)

| Azonosító | Forrásérték |
|---|---|
| `one_task_session_one_explicit_task` | `true` |
| `goal_scope_bound_to_exact_goal_revision_and_digest` | `true` |
| `in_scope_and_out_of_scope_overlap` | `"FORBIDDEN"` |
| `automatic_scope_expansion` | `false` |
| `out_of_scope_work` | `"PERSISTED_HANDOFF_REQUIRES_NEW_TASK_ID_AND_EXPLICIT_USER_START"` |
| `max_same_blocker_attempts` | `3` |
| `fourth_same_blocker_attempt` | `"FORBIDDEN"` |
| `third_same_blocker_failure` | `"FREEZE_AND_REQUIRE_HUMAN_INTERVENTION"` |
| `automatic_retry_after_human_block` | `false` |
| `automatic_replan_after_human_block` | `false` |
| `automatic_alternative_route_after_human_block` | `false` |
| `start_and_resume_require_fresh_task_scope_admission` | `true` |
| `cached_execution_plan_may_not_bypass_newer_control_revision` | `true` |
| `closed_task_execution` | `"FORBIDDEN"` |
| `verified_closure` | `"EVIDENCE_AUTHORITY_RECEIPT_REQUIRED"` |
| `automatic_followup_execution` | `false` |
| `followup_handoff_must_be_persisted_in_task_control` | `true` |
| `user_closure_states` | `["DONE","NEW_TASK_DISCOVERED","HUMAN_INTERVENTION_REQUIRED"]` |
| `all_executable_scope_origins_require_immutable_binding` | `true` |
| `all_executable_scope_origins_require_task_control` | `true` |
| `scope_origin_provenance_preserved_end_to_end` | `true` |
| `active_main_task_identity_immutable` | `true` |
| `main_task_switch_authority` | `"EXPLICIT_OWNER_ONLY"` |
| `new_runtime_rule_is_constraint_not_automatic_main_task` | `true` |
| `parallel_task_or_pr_is_observation_dependency_or_followup_not_automatic_main_task` | `true` |
| `blocker_may_stop_but_not_reassign_main_task` | `true` |
| `owner_main_task_switch_requires_new_or_explicitly_rebound_task_control` | `true` |

## Állapot és kizárási különbség

- A 78 történeti jelölt **nem** része a 24 jelenlegi kanonikus DEV/AI-szabály tényleges egyenkénti bizonyítékellenőrzésének.
- A történeti források hiánytalan egyeztetésének előfeltétele jelenleg továbbra is blokkolja a teljes Execution Guard-elfogadást.
- A 3159 történeti fájl egyenkénti tartalmi minősítése még nincs kész; ezért a 78 jelölt nem minősíthető az összes szabály teljes jegyzékének.

Részletes paraméterek és eredeti források a kísérő JSON-ban.

**Aktuális kizárási döntés (2026-10-11):** a 78 történeti jelölt és az ezekhez kapcsolódó történeti teljességi előfeltételek nem részei a #13-as Execution Guard aktív 24 szabályos ellenőrzésének. A 24 jelenlegi DEV/AI-szabály ellenőrzése változatlanul kötelező. A történeti adatok archiválva, befogadás nélkül maradnak; a teljes CFA3 szabályzat vagy a tényleges futtatás ettől még nem VERIFIED.
