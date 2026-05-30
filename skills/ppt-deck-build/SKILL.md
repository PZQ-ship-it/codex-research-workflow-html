---
name: ppt-deck-build
description: Generate an editable PPTX draft from confirmed PPT workflow artifacts. Use only after confirmed production brief, fact ledger, storyboard, template inventory, asset decisions, layout plan, and any required academic figure prompt/generated visual assets exist; stop before render QA.
---

# PPT Deck Build

## Role

Use this stage to build an editable draft deck. It is a mandatory stop gate before render QA.

Do not proceed unless confirmed artifacts exist:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`
- `align/PPT_storyboard_v*.md`
- `align/PPT_asset_audit_v*.md`
- `align/ppt_layout_plan_v*.json`
- template inventory or equivalent confirmed template policy

If `align/visual_enrichment_plan_v*.md` marks `requires_academic_figure_prompt: true`, also require a confirmed `align/academic_figure_prompt_v*.md` and either approved generated image files or an explicit user decision to build without them.

Use native agent `ppt_template_automation` when available. This stage must not accept the deck as final.

## Scripts

- `scripts/inspect_pptx_template.py`: inspect template PPTX OOXML metadata without modifying the file.

## Required Outputs

Write or update:

- `generated_pptx_test/<deck>_v*.pptx`
- `align/ppt_deck_build_manifest_v*.md`
- optional generation scripts or logs under `exp/`

The build manifest must include:

```yaml
stage: deck_build
stage_status: draft | confirmed
requires_confirmed:
  - ppt_production_brief
  - fact_ledger
  - storyboard
  - asset_layout_plan
  - academic_figure_prompt_when_required
allowed_next_stage: ppt-render-qa-loop
confirmed_by: <user/date or empty>
```

Use `stage_status: draft` until the user explicitly confirms the draft is ready for render QA.

## Build Requirements

Prefer native editable PowerPoint objects: placeholders, text boxes, shapes, tables, charts, and inserted source or approved generated images. Avoid whole-page screenshots unless the confirmed brief accepts that tradeoff.

Record slide count, template mapping, assets used, generated image provenance, known pre-render risks, and the exact PPTX path.

## Stop Rule

After generating the draft PPTX and manifest, stop and ask the user to inspect or confirm readiness for render QA. Do not run PowerPoint COM render QA in the same turn.

When the user confirms, update only the deck build manifest to `stage_status: confirmed`, record `confirmed_by`, then stop again.
