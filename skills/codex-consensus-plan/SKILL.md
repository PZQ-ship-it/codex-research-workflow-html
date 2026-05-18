---
name: codex-consensus-plan
description: Use when the user wants a decision-complete plan before implementation, especially for code, thesis, experiment, documentation, or workflow changes. Inspired by oh-my-codex ralplan/plan consensus behavior, adapted for native Codex IDE/VS Code without OMX commands.
---

# Codex Consensus Plan

Create an implementation-ready plan after gathering enough facts. The plan should leave no important decisions to the implementer.

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
4. Include verification.
   - State exact checks, screenshots, builds, tests, link checks, or manual acceptance criteria.
5. Mark boundaries.
   - Call out what is intentionally not included.
   - Note compatibility, migration, or restart requirements.

## Output Shape

Use a compact plan with these sections:

- Summary
- Key Changes
- Test Plan
- Assumptions

When the surrounding mode requires a special plan wrapper, follow that mode's wrapper exactly.

## References

Read `references/plan-rubric.html` for a concise plan quality checklist.
