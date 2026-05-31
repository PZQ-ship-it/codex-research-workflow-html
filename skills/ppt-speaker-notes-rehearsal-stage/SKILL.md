---
name: ppt-speaker-notes-rehearsal-stage
description: "Create, review, or freeze speaker notes, per-slide talk tracks, transitions, timing, rehearsal checkpoints, rehearsal evidence, and cut-down guidance for a manuscript-to-PPT workflow. Use after confirmed production brief, fact ledger, defense narrative, and storyboard exist, or when the user provides rehearsal transcript/timing evidence for an existing notes artifact. Use before defense Q&A, backup-slide planning, asset/layout planning, PPTX generation, or render QA. This stage must stop for human confirmation before later stages."
---

# PPT Speaker Notes Rehearsal Stage

## Role

Use this stage to turn the confirmed storyboard into a speakable defense script and rehearsal plan. It is a mandatory stop gate.

Do not proceed unless these confirmed artifacts exist:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`
- `align/ppt_defense_narrative_v*.md`
- `align/PPT_storyboard_v*.md`

Use `codex-deep-interview` if any of these are still unclear:

- speaking language, tone, or formality;
- target duration, per-section timing, or overtime tolerance;
- whether the presenter wants a full script, bullet notes, or cue-card style notes;
- sections the presenter is nervous about;
- advisor or committee preferences for delivery.

Ask only high-impact questions. Do not invent facts, results, claims, or anecdotes.

## Required Output

Write or update:

- `align/ppt_speaker_notes_rehearsal_v*.md`
- optional `align/rehearsal_evidence_v*.md` when the user provides rehearsal transcript, recording-derived notes, timing logs, or self-review notes

Include this metadata:

```yaml
stage: speaker_notes_rehearsal
stage_status: draft | confirmed
requires_confirmed:
  - ppt_production_brief
  - fact_ledger
  - defense_narrative
  - storyboard
allowed_next_stage: ppt-defense-qa-backup-stage
confirmed_by: <user/date or empty>
```

Use `stage_status: draft` until the user explicitly confirms the notes and rehearsal plan. Codex must not self-confirm it.

## Speaker Notes Requirements

For each main slide, include:

- slide number, action title, and linked storyboard item;
- target time and cumulative time checkpoint;
- speaker notes for what to say, sized to the confirmed duration;
- transition in and transition out;
- emphasis cues: what to slow down for, what to skip if time is short, and what wording to avoid;
- source fact or claim IDs for any evidence-bearing statement;
- pronunciation, formula, term, or demo cues when relevant;
- delivery risk and recovery line when the slide is likely to be challenged or misunderstood.

Speaker notes should support delivery. Do not copy the slide text as the note body.

## Rehearsal Requirements

The artifact must include:

- full-talk timing budget with checkpoints;
- first dry-run checklist;
- cut-down plan for shorter timing variants;
- sections to rehearse slowly;
- slides that need user confirmation before being spoken confidently;
- known unresolved delivery risks;
- handoff notes for `ppt-defense-qa-backup-stage`.

## Rehearsal Evidence

When the user provides rehearsal evidence, write or update `align/rehearsal_evidence_v*.md` with:

```yaml
stage: rehearsal_evidence
stage_status: draft | confirmed
requires_confirmed:
  - speaker_notes_rehearsal
allowed_next_stage: ppt-defense-qa-backup-stage | ppt-render-qa-loop
confirmed_by: <user/date or empty>
```

Include observed duration, per-slide timing deltas, unclear transitions, over-explained sections, missing verbal bridges, risky wording, likely audience confusion, and recommended repair owner stage. Do not treat rehearsal evidence as confirmed until the user accepts it.

## Guardrails

- Do not create defense Q&A answers or backup-slide plans in this stage.
- Do not plan assets, generate images, generate PPTX, or run render QA.
- Do not change the confirmed storyboard unless routing back to `ppt-storyboard-stage`.
- Do not make ungrounded claims to improve the speech.
- Mark any weak or unsupported speaking line as an open decision instead of smoothing it over.
- Do not infer rehearsal problems without user-provided rehearsal evidence; keep rehearsal-evidence output optional and user-triggered.

## Stop Rule

After writing a draft speaker notes and rehearsal artifact, stop and ask the user to review, rehearse mentally, revise, or confirm.

When the user confirms, update only `align/ppt_speaker_notes_rehearsal_v*.md` to `stage_status: confirmed`, record `confirmed_by`, then stop again. The next user turn must explicitly invoke or allow `ppt-defense-qa-backup-stage`.
