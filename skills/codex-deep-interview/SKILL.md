---
name: codex-deep-interview
description: Use when a task is ambiguous, underspecified, or likely to branch into multiple valid implementations; run a native Codex requirements interview that clarifies intent, unknowns, non-goals, decision boundaries, and acceptance criteria before planning or editing.
---

# Codex Deep Interview

Clarify before execution. This skill is a requirements-discovery loop, not an implementation mode.

This is the native Codex adaptation of OMX `$deep-interview` as of upstream `oh-my-codex` main `f947e3a`: keep the Socratic pressure, ambiguity scoring mindset, depth profiles, unknowns pass, readiness gates, and handoff brief; replace OMX commands, `.omx/specs`, mode state, and Stop-hook continuation with normal Codex repo inspection and concise user questions.

## Depth Profiles

Choose the lightest profile that makes the next step safe.

- Quick: fast pre-plan pass for low-risk ambiguity; target no more than 5 rounds.
- Standard: default full requirement interview; target no more than 12 rounds.
- Deep: high-rigor exploration for branching, high-risk, or research/workflow design; target no more than 20 rounds.

The round caps are safeguards, not quotas. Stop early when the gates are satisfied.

## Phase 0: Unknowns Pass

Before asking the user, map the unknowns.

1. Read obvious local context: `AGENTS.md`, README/design docs, task cards, contracts, prior decisions, relevant source files, and user-provided artifacts.
2. Classify each gap:
   - Discoverable fact: inspect files, run safe searches, or check official/live sources when freshness matters.
   - Human preference: ask only if the answer changes scope, risk, UX, policy, or acceptance.
   - Dangerous assumption: state the assumption and either verify it or ask.
3. Check prompt size. If the initial context is too large to use safely, first ask for a concise prompt-safe summary with goal, constraints, non-goals, references, and known decisions.
4. Preserve provenance in your own reasoning: `[from-user]`, `[from-code]`, `[from-doc]`, `[from-research]`, `[assumption]`.

## Ambiguity Dimensions

Use these dimensions to decide the next question. Do not needlessly show a numeric table unless it helps the user.

- Intent: why this matters and what problem is being solved.
- Outcome: what artifact, behavior, decision, or evidence should exist.
- Scope: what is included.
- Non-goals: what must stay out.
- Decision boundaries: what Codex may decide without confirmation.
- Constraints: time, repo conventions, safety, compatibility, dependencies.
- Acceptance criteria: how success will be verified.
- Context clarity: existing codebase/domain facts for brownfield work.

`Non-goals` and `Decision boundaries` are mandatory readiness gates. Do not hand off while either is materially unresolved.

## Question Discipline

- Ask one focused question at a time when clarification is required.
- Prefer structured options when the interface supports them; otherwise ask a concise plain-text question.
- Explain the tradeoff in one sentence.
- Prefer questions that expose an example, hidden assumption, boundary, failure mode, terminology conflict, or expected behavior in a concrete scenario.
- For brownfield work, ask evidence-backed questions: "I found X in Y; should this new work follow that pattern?"
- Do not ask the user questions whose answers are discoverable from the repo or official sources with reasonable effort.

## Closure Audit

Stop ordinary questioning once the active profile is clear enough, then run a closure audit:

- Goal is stated in executable terms.
- In scope and out of scope are explicit.
- Decision boundaries are explicit.
- Acceptance criteria are testable or reviewable.
- Key constraints, paths, source artifacts, and risks are named.
- Residual uncertainty is either low-risk, explicitly accepted, or routed to a later verification step.

## Handoff Brief

When the task is clear, produce a short brief:

- Goal
- In scope / out of scope
- Inputs and relevant paths
- Confirmed facts and assumptions
- Constraints and risks
- Acceptance criteria
- Decision boundaries
- Recommended next lane: normal execution, `$codex-consensus-plan`, `$codex-completion-loop`, `$codex-native-subagent-team` only when the user explicitly wants parallel delegation, or a durable goal/work-trace when the repo requires it.

## Stop Conditions

- Stop interviewing when the next action is obvious and low-risk.
- Stop and ask when continuing would require guessing a meaningful user preference.
- Do not edit files while operating only as an interview skill.
- Do not create OMX artifacts or rely on `.omx/state`; create durable repo notes only when the user or repo workflow asks for them.

## References

Read `references/interview-pattern.html` when you need example question patterns or a handoff template.
