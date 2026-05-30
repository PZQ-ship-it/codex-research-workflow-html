---
name: manuscript-to-ppt-workflow
description: "Thin stage orchestrator for manuscript, thesis, paper, report, LaTeX project, asset folder, experiment output, or proposal to editable PPTX. Use to route the user through mandatory human-confirmed stages: production brief, material/fact ledger, storyboard, asset/layout plan, optional academic figure prompt, deck build, and render QA. This skill must stop after every stage artifact and never auto-advance."
---

# Manuscript To PPT Workflow

## Role

Use this skill only as the workflow router. It does not replace the stage skills and must not run the full deck pipeline in one turn.

Every stage is a hard human-alignment gate. After a stage writes a draft artifact, stop and ask the user to review, revise, or confirm. Continue only after the user explicitly confirms/freeze the prior stage artifact.

## Stage Skills

Run stages in this order:

| Stage | Skill | Required confirmed input | Main output |
|---|---|---|---|
| 1 | `ppt-production-brief` | user request and materials known enough to interview | `align/ppt_production_brief_v*.md` |
| 2 | `ppt-material-fact-ledger` | confirmed production brief | `align/material_inventory_v*.md`, `align/fact_ledger_v*.md` |
| 3 | `ppt-storyboard-stage` | confirmed brief and fact ledger | `align/PPT_storyboard_v*.md` |
| 4 | `ppt-asset-layout-plan` | confirmed brief, fact ledger, storyboard | template inventory, asset audit, visual plan, layout plan |
| 5 | `academic-figure-prompt` | confirmed asset/layout plan that requires generated academic visuals | `align/academic_figure_prompt_v*.md` |
| 6 | `ppt-deck-build` | confirmed upstream artifacts, layout plan, and any required figure prompt/assets | editable PPTX draft and build manifest |
| 7 | `ppt-render-qa-loop` | confirmed deck build manifest | rendered screenshots and QA report |

Default stage gate:

```yaml
stage_status: draft | confirmed
```

Codex may write `draft`. Only the user may cause `confirmed`.

## Routing Rules

1. If no confirmed production brief exists, route to `ppt-production-brief`.
2. If the brief is confirmed but no confirmed fact ledger exists, route to `ppt-material-fact-ledger`.
3. If facts are confirmed but no confirmed storyboard exists, route to `ppt-storyboard-stage`.
4. If storyboard is confirmed but no confirmed asset/layout plan exists, route to `ppt-asset-layout-plan`.
5. If the confirmed asset/layout plan says an AI-generated academic visual or image2/gpt-image academic prompt is required, and no confirmed `align/academic_figure_prompt_v*.md` exists, route to `academic-figure-prompt`.
6. If the academic figure prompt is confirmed and the user asks to generate the image asset, route to `openrouter-icu-image`; do not generate images in the same turn that drafts the prompt.
7. If all required prompt/assets are confirmed but no confirmed deck build exists, route to `ppt-deck-build`.
8. If deck build is confirmed but no render QA report exists, route to `ppt-render-qa-loop`.
9. If render QA fails, route defects back to the responsible earlier stage. Do not silently repair in the QA stage.

## Non-Negotiable Stop Rule

Do not execute two stages in one assistant turn. Do not combine production brief, fact extraction, storyboard, asset planning, academic figure prompt drafting, image generation, deck generation, and QA into a single run.

The only allowed same-turn action after writing a stage artifact is to summarize the artifact path, list open decisions, and ask the user to confirm or revise.

Generated academic visuals have two gates: first confirm `academic-figure-prompt`, then run `openrouter-icu-image` only when the user approves image generation. Do not let Codex invent visual content to fill missing research facts.

## Agents

Native custom agents are bounded workers, not stage owners:

- `ppt_storyboard`: used inside `ppt-storyboard-stage`.
- `ppt_template_automation`: used inside `ppt-deck-build`.
- `ppt_render_qa`: used inside `ppt-render-qa-loop`.

Do not create agents for production alignment, fact extraction, or default asset audit. Those are human-review stage outputs.

If native subagent tools are unavailable, stop before the affected stage and report the fallback option. Continue locally only after user confirmation.

## Figma Policy

Figma is not part of the default PPT-native lane. Use `figma-context-mcp` only if the user explicitly starts a separate Figma experiment or provides Figma context as a read-only visual reference. Official Figma writes require explicit `figma_write_policy`.

## Hook Guardrail

This repository may include `.codex/hooks.json` and `.codex/hooks/ppt_stage_gate.ps1` to remind and block common stage-skipping write attempts. Treat hooks as guardrails, not as the only source of truth. The stage skills and user confirmation remain mandatory.

## Prompt Template

```text
Use $manuscript-to-ppt-workflow.

Task:
Route this PPT workflow to the next required stage. Do not execute more than one stage. Stop after writing a draft artifact and ask me to review or confirm before continuing.
```
