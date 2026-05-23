---
name: codex-consensus-plan
description: Use when the user wants a decision-complete plan before implementation, especially for code, thesis, experiment, documentation, or workflow changes. Inspired by oh-my-codex ralplan/plan consensus behavior, adapted for native Codex IDE/VS Code without OMX commands.
---

# Codex Consensus Plan

Create an implementation-ready plan after gathering enough facts. The plan should leave no important decisions to the implementer.

This is the native Codex adaptation of OMX `$ralplan` / `$plan --consensus`: keep the planner-architect-critic discipline, RALPLAN-DR decision summary, ADR output, and verification-first handoff; omit OMX `.omx/plans`, `omx question`, and automatic execution handoff.

## Workflow

1. Explore first.
   - Inspect the relevant repo, docs, configs, and existing patterns.
   - Identify which facts are confirmed and which are assumptions.
2. Resolve high-impact ambiguity.
   - Ask only questions that materially change scope, design, risk, or acceptance.
   - If a default is safe, choose it and record it.
3. Plan at behavior level.
   - Prefer grouped implementation changes over file-by-file noise.
   - Name specific files only when needed to prevent ambiguity.
4. Add a compact RALPLAN-DR summary before the final plan.
   - Principles: 3-5 constraints that should guide the decision.
   - Decision drivers: top 3 factors.
   - Viable options: at least 2 when possible, with bounded pros/cons.
   - Rejected alternatives: include invalidation rationale when only one option remains.
5. Include verification.
   - State exact checks, screenshots, builds, tests, link checks, or manual acceptance criteria.
   - For high-risk work, include a short pre-mortem and broader test shape.
6. Mark boundaries.
   - Call out what is intentionally not included.
   - Note compatibility, migration, or restart requirements.
7. Decide the next lane without auto-launching it.
   - Direct execution for small scoped work.
   - `$codex-completion-loop` for implementation-to-evidence.
   - `$codex-native-subagent-team` only when the user explicitly asked for native subagents or parallel delegation.
   - Native goal mode when the task needs durable objective tracking.

## Output Shape

Use a compact plan with these sections:

- Summary
- RALPLAN-DR
- ADR
- Key Changes
- Test Plan
- Assumptions
- Next Lane

When the surrounding mode requires a special plan wrapper, follow that mode's wrapper exactly.

## References

Read `references/plan-rubric.html` for a concise plan quality checklist.
