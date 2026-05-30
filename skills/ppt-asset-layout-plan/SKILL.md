---
name: ppt-asset-layout-plan
description: Create, review, or freeze the template inventory, asset decisions, visual enrichment plan, and editable layout plan for a PPT workflow. Use after confirmed brief, fact ledger, and storyboard exist, and before PPTX generation.
---

# PPT Asset Layout Plan

## Role

Use this stage to decide how every confirmed slide will be built. It is a mandatory stop gate before deck generation.

Do not proceed unless confirmed artifacts exist:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`
- `align/PPT_storyboard_v*.md`

Use `openrouter-icu-image` only when the confirmed brief allows visual generation or editing. Do not generate fake evidence, charts, screenshots, scientific images, or result visuals.

## Required Outputs

Write or update:

- `align/template_inventory_v*.md`
- optional `align/template_layout_map_v*.json`
- `align/PPT_asset_audit_v*.md`
- optional `align/PPT_asset_manifest_v*.csv`
- optional `align/visual_enrichment_plan_v*.md`
- `align/ppt_layout_plan_v*.json`

Every Markdown output must include:

```yaml
stage: asset_layout_plan
stage_status: draft | confirmed
requires_confirmed:
  - ppt_production_brief
  - fact_ledger
  - storyboard
allowed_next_stage: ppt-deck-build
confirmed_by: <user/date or empty>
```

Use `stage_status: draft` until the user explicitly confirms asset and layout decisions.

## Planning Requirements

For each slide record:

- template layout choice and reason
- editable content structure
- reuse/redraw/generate/omit/confirm asset decision
- source asset paths and licenses/risks when known
- generated visual role: evidence, source-derived diagram, illustration, or decoration
- editability tradeoffs
- expected QA risks

Template inventory should record slide size, masters, layout names, placeholder geometry, theme fonts/colors, logos, headers, footers, and suitable layouts.

## Stop Rule

After writing draft asset/layout plans, stop and ask the user to review or confirm. Do not generate PPTX in the same turn.

When the user confirms, update only the relevant status blocks to `stage_status: confirmed`, record `confirmed_by`, then stop again.

