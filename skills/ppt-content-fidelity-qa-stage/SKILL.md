---
name: ppt-content-fidelity-qa-stage
description: "Verify source fidelity before deck generation in a manuscript-to-PPT workflow. Use after confirmed production brief, fact ledger, defense narrative, storyboard, speaker notes/rehearsal, defense Q&A/backup plan, asset/layout plan, and any required academic figure prompt exist, and before image generation that depends on the final plan, PPTX generation, or render QA. This stage checks whether slide claims, notes, Q&A answers, backup slides, visual decisions, and generated-visual prompts are grounded in the confirmed fact ledger and must stop for human confirmation or repair routing."
---

# PPT Content Fidelity QA Stage

## Role

Use this stage as the final source-fidelity gate before deck build. It verifies whether the planned deck is true to the confirmed materials.

This is not render QA and not copyediting. It should catch unsupported claims, missing sources, unsafe wording, over-claimed visuals, and Q&A answers that cannot be defended.

Do not proceed unless these confirmed artifacts exist:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`
- `align/ppt_defense_narrative_v*.md`
- `align/PPT_storyboard_v*.md`
- `align/ppt_speaker_notes_rehearsal_v*.md`
- `align/ppt_defense_qa_backup_v*.md`
- `align/PPT_asset_audit_v*.md` or equivalent confirmed asset/layout artifact
- `align/ppt_layout_plan_v*.json`

If `align/visual_enrichment_plan_v*.md` marks `requires_academic_figure_prompt: true`, also require a confirmed `align/academic_figure_prompt_v*.md`.

## Required Output

Write or update:

- `align/ppt_content_fidelity_qa_v*.md`

Include this metadata:

```yaml
stage: content_fidelity_qa
stage_status: draft | confirmed | blocked
requires_confirmed:
  - ppt_production_brief
  - fact_ledger
  - defense_narrative
  - storyboard
  - speaker_notes_rehearsal
  - defense_qa_backup
  - asset_layout_plan
  - academic_figure_prompt_when_required
allowed_next_stage: ppt-deck-build
confirmed_by: <user/date or empty>
```

Use `stage_status: draft` when the review is complete but needs user acceptance. Use `stage_status: blocked` when unsupported content must be repaired before deck build. Only the user may cause `stage_status: confirmed`.

## Fidelity Checks

Check these surfaces against the confirmed fact ledger and material inventory:

- defense thesis and action-title spine;
- each storyboard slide action title and core point;
- every evidence-bearing speaker note;
- rehearsal evidence repair items when present;
- Q&A answers and backup-slide claims;
- visual asset decisions, especially generated or redrawn academic visuals;
- template design rules when they affect citation, source display, readability, or exhibit interpretation;
- academic figure prompt text and source anchors when present;
- limitations, baselines, datasets, metrics, method claims, and contribution wording.

For each issue, record:

- issue ID;
- artifact and slide/question/asset anchor;
- claim or visual decision under review;
- required source fact ID or missing source;
- severity: `blocker | major | minor`;
- owner stage to repair;
- recommended repair: remove, soften wording, cite, move to backup, regenerate prompt, or ask user.

## Pass Criteria

The artifact may be marked draft-pass-ready only when:

- every action title has a source-backed or user-confirmed basis;
- every result, metric, dataset, baseline, and limitation is grounded;
- generated visuals are not labeled as evidence unless source-derived and explicitly approved;
- Q&A answers do not promise unsupported experiments or claims;
- backup slides map to real expected questions;
- assertion-evidence policy from the production brief is satisfied or explicitly relaxed by user decision, including exhibit type, exhibit claim, so-what annotation, and citation need where required;
- rehearsal evidence, when present, has no unresolved blocker that would change claims or timing-critical slide order;
- all blocker and major issues have a repair route.

## Guardrails

- Do not fix upstream artifacts directly in this stage.
- Do not create new facts, claims, visuals, prompts, slides, or Q&A answers.
- Do not generate images, generate PPTX, or run render QA.
- Do not self-confirm the QA artifact.
- If fidelity is poor, set `stage_status: blocked` and route each issue to the responsible earlier stage.

## Stop Rule

After writing the content fidelity QA artifact, stop and ask the user to confirm, accept specific risks, or route repairs.

When the user confirms, update only `align/ppt_content_fidelity_qa_v*.md` to `stage_status: confirmed`, record `confirmed_by`, then stop again. The next user turn must explicitly invoke or allow `ppt-deck-build`.
