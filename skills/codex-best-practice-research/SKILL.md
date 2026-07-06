---
name: codex-best-practice-research
description: Use when a task depends on current external best practices, official recommendations, standards, release notes, upstream behavior, version-aware API guidance, migration advice, or source-backed implementation conventions; gather authoritative evidence and produce a cited recommendation without editing files.
---

# Codex Best Practice Research

Gather current source-backed guidance before planning or implementation. This is the native Codex adaptation of OMX `$best-practice-research`: official/upstream evidence first, repo-local constraints second, concise recommendation, then stop.

## Contract

- Read-only by default. Do not edit repo files under this skill.
- Browse when guidance may be version-sensitive, current, legal/security relevant, or otherwise likely to drift.
- Prefer primary sources: official docs, upstream source, standards, release notes, migration guides, maintainer guidance.
- Use third-party posts only as supplemental context.
- State date/version context for every current claim.
- Separate external evidence from repo-local facts and from your recommendation.

## Workflow

1. Classify the question: conceptual best practice, implementation guidance, migration/version guidance, standards/compliance guidance, or mixed local + external guidance.
2. Inspect repo-local facts when local versions, config, or integration constraints affect the answer.
3. Gather the smallest sufficient external evidence set from authoritative sources.
4. Flag stale, conflicting, undocumented, or version-mismatched evidence.
5. Synthesize the recommendation and explain implementation/planning implications.
6. Stop. Hand off to `$codex-consensus-plan` or `$codex-completion-loop` only if the user asks to continue.

## Output Shape

```md
## Best-Practice Research: <question>

### Direct Recommendation
<actionable guidance>

### Evidence Used
- Official/upstream: <source URL> - <what it establishes>
- Supplemental: <source URL> - <why secondary>

### Version / Date Context
<versions, dates, channels, unknowns>

### Repo-Local Context
<facts from local inspection, or "not needed">

### Boundaries / Non-goals
<what this research does not decide>

### Handoff
<planning, implementation, or test implications>
```

## References

Read `references/source-quality-checklist.html` before producing a recommendation.
