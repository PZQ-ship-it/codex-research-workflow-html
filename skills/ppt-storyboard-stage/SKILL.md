---
name: ppt-storyboard-stage
description: Create, review, or freeze a slide-by-slide storyboard for a manuscript-to-PPT workflow. Use only after confirmed production brief and confirmed fact ledger exist, and before asset/layout planning or PPTX generation.
---

# PPT Storyboard Stage

## Role

Use this stage to design the slide narrative. It is a mandatory stop gate.

Do not proceed unless these confirmed artifacts exist:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`

Use native agent `ppt_storyboard` when available. The leader must inspect the result before asking the user to confirm it.

## Required Output

Write or update:

- `align/PPT_storyboard_v*.md`

Include:

```yaml
stage: storyboard
stage_status: draft | confirmed
requires_confirmed:
  - ppt_production_brief
  - fact_ledger
allowed_next_stage: ppt-asset-layout-plan
confirmed_by: <user/date or empty>
```

Use `stage_status: draft` until the user explicitly confirms the storyboard.

## Storyboard Requirements

Each slide must include:

- slide number and title
- one core point
- source facts or claim IDs
- recommended visual form
- asset needs
- speaking points
- estimated time
- QA risk
- backup/merge/split notes when relevant

Avoid mechanical chapter compression. Optimize for a talkable audience-specific narrative.

## Stop Rule

After writing a draft storyboard, stop and ask the user to review, reorder, merge, split, or confirm. Do not plan assets or generate PPTX in the same turn.

When the user confirms, update only the storyboard status to `stage_status: confirmed`, record `confirmed_by`, then stop again.

