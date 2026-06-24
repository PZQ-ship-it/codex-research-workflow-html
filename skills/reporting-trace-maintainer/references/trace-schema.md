# Reporting Trace Schema

Use this reference when creating or updating durable work traces.

## Purpose

A work trace is a low-polish, high-signal record that lets a future report answer:

- What was the last plan?
- What changed?
- What evidence supports the change?
- What does it mean?
- What should happen next?
- What needs advisor, teammate, or stakeholder input?

## File Placement

Default path:

```text
reports/work-traces/<project>/<YYYY-MM-DD>-<task-id-or-slug>.md
```

Use lowercase slugs. Prefer stable task IDs when available:

```text
reports/work-traces/hkust-gz-ra-academic-fit/2026-06-24-hkust-gz-ra-first-paper-fit-note.md
```

## Required Metadata

```markdown
Updated: YYYY-MM-DD
Project: <project-id>
Task: <task-id or short slug>
Audience Future Use: advisor-update | stakeholder-status | weekly-review | project-briefing | internal
Status: active | paused | completed | blocked
```

Optional metadata:

```markdown
Related Task File: tasks/graph/<task-id>.md
Related Project Index: projects/<project>/INDEX.md
External Artifact Repo: <path or remote, only if already allowed by repo convention>
```

## Section Rules

### Last Plan

Quote or summarize the plan that existed before this execution. If no prior plan existed, write `Not recorded`.

### Work Done

Use concrete actions, not effort narration. Good:

- Ran `python ...` and generated `tasks/graph-view.md`.
- Read `paper-html/red-gnn/red-gnn.html` and extracted three fit concerns.

Weak:

- Worked hard on the project.
- Researched many things.

### Evidence

Prefer a table:

```markdown
| Evidence | Path / Source | What It Supports | Confidence |
|---|---|---|---|
| task graph refresh | `tasks/graph-view.md` | current ready/blocked list | high |
```

Use confidence values:

- `high`: directly verified file, command, user confirmation, or source.
- `medium`: supported by multiple notes but not freshly verified.
- `low`: plausible inference or weak signal.

### Interpretation

Separate:

- `Fact`: directly observed or user-confirmed.
- `Inference`: what Codex thinks it means.
- `Uncertainty`: what remains unverified.

### Decisions / Open Decisions

Record only actual decisions or decision needs. If settled, link to `decisions/` when available. If not settled, phrase the decision question.

### Next Plan

Make each item measurable enough that a later report can say whether it happened.

Good:

- [ ] Check RED-GNN dependency versions and record CUDA / `torch_scatter` risk.

Weak:

- [ ] Keep working on RED-GNN.

### Questions For Next Meeting

Use questions that change next action, scope, or priority:

- Should this direction continue to minimal reproduction or stop at fit judgment?
- Is this evidence enough for an advisor update?

## Privacy Rules

Never record:

- secrets, API keys, tokens, cookies, passwords
- full private chat transcripts
- unredacted personal identifiers not already part of the repo convention
- raw local cache paths unless needed as an execution boundary
- paywalled or restricted full text

When in doubt, write a sanitized summary and link only to an approved artifact location.

## Minimal Trace

For small tasks, use:

```markdown
# Work Trace: <Task Title>

Updated: YYYY-MM-DD
Project: <project-id>
Task: <task-id>
Audience Future Use: internal
Status: completed

## Last Plan

- ...

## Work Done

- ...

## Evidence

| Evidence | Path / Source | What It Supports | Confidence |
|---|---|---|---|

## Next Plan

- [ ] ...
```
