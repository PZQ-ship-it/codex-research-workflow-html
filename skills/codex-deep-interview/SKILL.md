---
name: codex-deep-interview
description: Use when a task is ambiguous, underspecified, or likely to branch into multiple valid implementations; clarify intent, constraints, non-goals, and acceptance criteria before planning or editing. Inspired by oh-my-codex deep-interview, adapted for native Codex IDE/VS Code without OMX runtime state.
---

# Codex Deep Interview

Clarify before execution. This skill is for requirements discovery, not implementation.

This is the native Codex adaptation of OMX `$deep-interview`: keep the Socratic pressure, fact-vs-preference split, non-goal gates, and handoff brief; omit OMX `omx question`, `.omx/specs`, mode state, and Stop-hook continuation.

## Workflow

1. Ground yourself in available context first.
   - Read relevant files, configs, docs, issues, or prompts when they are available.
   - Use repo facts to answer discoverable questions instead of asking the user.
2. Separate unknowns into two buckets.
   - Discoverable facts: inspect locally or search official sources when needed.
   - Preference decisions: ask the user only when the answer changes scope, risk, or design.
3. Ask exactly one concise question at a time when clarification is required.
   - Prefer a small set of concrete options if the interface supports it.
   - Explain the tradeoff in one sentence.
   - Prefer questions that expose an example, hidden assumption, tradeoff, non-goal, or decision boundary.
4. Track readiness gates.
   - Do not hand off while `Non-goals`, `Decision boundaries`, or `Acceptance criteria` are still materially unclear.
   - For brownfield work, use evidence-backed confirmation: "I found X in Y. Should this follow that pattern?"
   - If the initial context is too large, ask first for a prompt-safe summary that preserves goal, constraints, non-goals, and references.
5. Produce a short handoff brief when the task is clear.
   - Goal
   - In scope / out of scope
   - Inputs and relevant paths
   - Constraints and risks
   - Acceptance criteria
   - Decision boundaries
   - Recommended next step, such as normal execution, `$codex-consensus-plan`, `$codex-completion-loop`, or `$codex-native-subagent-team` when the user explicitly wants parallel delegation.

## Stop Conditions

- Stop interviewing when the next action is obvious and low-risk.
- Stop and ask when continuing would require guessing the user's preference.
- Do not edit files while operating only as an interview skill.
- Do not create OMX artifacts or rely on `.omx/state`; this skill is session-local unless the user asks for a durable document.

## References

Read `references/interview-pattern.html` when you need example question patterns or a handoff template.
