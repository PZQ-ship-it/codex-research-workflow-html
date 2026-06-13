# Advisor Profile Schema

Use this schema when creating or updating persisted advisor profile files.

## `profile.md`

Recommended sections:

```markdown
# <Advisor Name> Profile

Last updated: YYYY-MM-DD
Profile status: draft | active | stale | needs review
Relationship: advisor | PI | committee member | collaborator | evaluator | other
Evidence coverage: low | medium | high

## Snapshot

Short working model in 3-6 bullets.

## Research Taste

- Preferred problem types:
- What counts as an interesting contribution:
- What they tend to distrust:
- Evidence:

## Standards And Evaluation

- Method/experiment standards:
- Writing standards:
- Presentation standards:
- Reproducibility or rigor expectations:

## Feedback Style

- Typical criticism form:
- Typical approval form:
- How direct or indirect:
- What makes feedback stronger or weaker:

## Communication And Workflow

- Meeting style:
- Email/chat style:
- Timing and deadline behavior:
- Preferred preparation format:

## Decision Patterns

- How they decide:
- Risk tolerance:
- What information changes their mind:
- Known tradeoffs:

## User-Specific Relationship Context

- What they already know about the user:
- Repeated advice to the user:
- Trust-building signals:
- Friction points:

## Red Lines And Sensitive Areas

- Topics or behaviors to avoid:
- Known misunderstandings:
- Confidence:

## Open Questions

- What needs more evidence:
```

## `preferences.md`

Use for actionable preferences:

```markdown
# <Advisor Name> Preferences

## Drafts And Writing
- Likes:
- Dislikes:
- Common edits:
- Before sending, check:

## Research Design
- Likes:
- Dislikes:
- Baseline/ablation expectations:
- Evidence threshold:

## Meetings
- Bring:
- Avoid:
- Good questions:
- Bad patterns:

## Emails And Messages
- Subject style:
- Length:
- Tone:
- Follow-up cadence:
```

## `interaction-log.md`

Use summarized interaction records, not raw chat dumps by default:

```markdown
# Interaction Log

## YYYY-MM-DD - <interaction type>

- Context:
- User goal:
- Advisor response:
- Action items:
- Profile signals:
- Evidence ids:
```

## `evidence.jsonl`

One JSON object per evidence unit:

```json
{"id":"ev-YYYYMMDD-001","date":"YYYY-MM-DD","source_type":"meeting_note|email|chat|paper_comment|user_recollection|public_source","sensitivity":"low|medium|high","evidence_level":"A|B|C|D","topic":["writing","experiment"],"summary":"Short paraphrase","excerpt":"Optional short excerpt if safe","interpretation":"What this may indicate","confidence":"low|medium|high","profile_targets":["Writing And Presentation","Feedback Style"],"added_at":"YYYY-MM-DD"}
```

Avoid long verbatim private excerpts. If exact wording matters, keep it short and only with user approval.

## `update-log.md`

Record profile changes:

```markdown
# Update Log

## YYYY-MM-DD

- Material processed:
- Files changed:
- Added:
- Revised:
- Downgraded or removed:
- Conflicts noted:
- User confirmation:
```

## Confidence Rules

- Use `high` only for repeated direct evidence or explicit advisor statements.
- Use `medium` for one direct signal supported by surrounding context.
- Use `low` for user recollection, inference, or ambiguous tone.
- If evidence conflicts, keep both and mark the profile dimension as mixed.
