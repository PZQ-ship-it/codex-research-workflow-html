---
name: ppt-render-qa-loop
description: Render a generated PPTX through PowerPoint COM or an approved fallback, inspect screenshots, write a QA report, and stop for human acceptance or repair routing. Use only after a confirmed deck build manifest exists.
---

# PPT Render QA Loop

## Role

Use this stage to render-check a generated deck. It is the acceptance gate, not an automatic repair stage.

Do not proceed unless a confirmed `align/ppt_deck_build_manifest_v*.md` exists and points to a generated PPTX. Use native agent `ppt_render_qa` when available.

## Scripts

- `scripts/render_pptx_powerpoint_com.ps1`: open a PPTX with PowerPoint COM and export slide PNGs and optional PDF.

## Required Outputs

Write or update:

- `qa/rendered_pages/*`
- optional `qa/deck_render.pdf`
- optional contact sheet
- `qa/ppt_render_qa_v*.md`

The QA report must include:

```yaml
stage: render_qa
stage_status: pass | fail | needs_human_acceptance
requires_confirmed:
  - deck_build
allowed_next_stage: human_acceptance_or_repair
accepted_by: <user/date or empty>
```

Codex must not mark `accepted_by` unless the user explicitly accepts the rendered deck.

## Blocking Failures

Fail the run for:

- title/subtitle overlap
- clipped text
- unreadable charts, tables, formulas, or figures
- severe crowding
- missing CJK glyphs or wrong font substitution
- blank pages
- content outside slide bounds
- missing images/assets
- obvious template/logo/header/footer misuse

## Stop Rule

After writing QA evidence, stop and ask the user to accept the deck or route defects back to the correct earlier stage. Do not silently repair or generate a replacement PPTX in the same turn.

