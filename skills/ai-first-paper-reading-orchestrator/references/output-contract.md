# Output Contract

Use this reference when the user asks for files or a complete run artifact.

## Minimal File Set

```text
manifest.yaml
source-search-log.md
ai-use-log.md
human-learning-lane.md
group/group-brief.md
group/professor-coverage-matrix.md
group/professor-fit-draft.md
learning/learning-plan.md
learning/teachback-check.md
direction/direction-card.md
direction/survey-matrix.md
direction/node-paper-graph.md
direction/benchmark-code-dataset-table.md
direction/fit-decision-memo.md
papers/<paper-slug>/source-lock.md
papers/<paper-slug>/reading-note.md
trace.md
```

## Human Gate Status Values

- `confirmed`
- `pending-human-fit`
- `pending-teachback`
- `pending-risk-approval`
- `not-applicable`

## AI Recommendation Fields

Use these names instead of final human-owned fields:

- `AI Direction Recon`
- `AI recommended taxonomy axis`
- `AI node rationale`
- `AI triage recommendation`
- `AI recommended decision`
- `Pending Human Questions`

Use these names for human-owned fields:

- `Human Preference Gate`
- `Human attention decision`
- `Human confirmed decision`
- `Human override reason`

## Prompt Skeleton

```text
Use $ai-first-paper-reading-orchestrator.

Seed:
<direction / professor / paper / rough goal>

Goal:
<what the run should help decide>

Constraints:
- public/open sources only unless I approve otherwise
- no large downloads/GPU/API/authenticated browsing
- mark subjective fields as pending-human-fit

Output:
- source-search-log
- contact-group context when applicable
- direction-card v0
- survey taxonomy
- node-paper map
- first-paper triage recommendation
- human-learning-lane drill
- learning-support routing
- pending human gates
```
