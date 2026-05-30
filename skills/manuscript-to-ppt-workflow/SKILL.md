---
name: manuscript-to-ppt-workflow
description: "Use when the user wants to turn a manuscript, thesis, paper, report, proposal, or long document into a presentation workflow: fact ledger, PPT storyboard, asset audit, template-based PPTX draft, and optional Figma layout polish. Use for portable multi-agent PPT generation and defense/conference presentation preparation."
---

# Manuscript to PPT Workflow

## Overview

This skill orchestrates a portable multi-agent workflow for turning a manuscript into a presentation. It does not replace the specialist agents; it decides which agents are needed, in what order, what files they exchange, and how to verify the final PPTX/visual outputs.

Use it when the user wants an end-to-end or reusable workflow, not just a one-off slide edit.

## Core Pipeline

Default order:

1. Fact extraction
2. Storyboard generation
3. Asset audit
4. Template/PPTX automation
5. Figma layout polish
6. Final validation and handoff

Hard dependencies:

- Storyboard depends on fact ledger unless the source is already structured and short.
- Asset audit depends on storyboard.
- PPTX automation depends on storyboard and asset audit.
- Figma polish depends on a PPTX draft, screenshots, or a page plan.
- Script/QA generation, if requested, should happen after storyboard is mostly frozen and facts are locked.

## Agent Loading

Load only the agent reference needed for the current phase:

- Fact extraction: `references/agents/fact_extraction_agent_spec.md`
- Storyboard: `references/agents/storyboard_agent_spec.md`
- Asset audit: `references/agents/asset_audit_agent_spec.md`
- PPTX automation: `references/agents/template_automation_agent_spec.md`
- Figma polish: `references/agents/figma_layout_polish_agent_spec.md`

Do not load all references by default. Load progressively as the workflow reaches each phase.

## Fact Extraction Necessity

Create a fact ledger by default when:

- The input document is long.
- Multiple downstream agents will work in parallel or across turns.
- The presentation must discuss contributions, method, system, experiments, results, and limitations.
- QA, script, or defense preparation is expected.
- Claims, metrics, figures, or experimental conclusions are risky.

Skip fact extraction only when:

- The user already provides a structured fact ledger.
- The source is short and unambiguous.
- The task is purely visual polish of an existing deck.

Fact extraction is the workflow's source of truth. It prevents storyboard, assets, PPT, script, and QA from using inconsistent contribution claims or experiment conclusions.

## Runtime Inputs

Ask for missing inputs only when they cannot be inferred safely.

Required for full pipeline:

- `source_materials`: manuscript/PDF/LaTeX/Markdown/DOCX/HTML.
- `project_type`: thesis defense, conference talk, group meeting, proposal, product review, etc.
- `target_duration`: e.g. 10, 15, 20 minutes.
- `audience`: committee, domain experts, general audience, investors, internal team.
- `template_file`: optional but recommended for PPTX generation.
- `output_dir`: where generated files go.

Recommended:

- `target_page_count`
- `language`
- `visual_style`
- `asset_dirs`
- `must_include`
- `must_avoid`
- `validation_policy`
- `figma_policy`: disabled, optional, required, or fallback-only

## Directory Policy

For portable projects, use:

- `agent/`: project-level agent definitions or overrides.
- `align/`: task-specific fact ledger, storyboard, asset manifest, page plans, frame manifests.
- `exp/`: workflow tests, generation scripts, validation records.
- `generated_assets/`: extracted or generated assets.
- `generated_pptx_test/`: generated PPTX files and rendered screenshots.
- `skills/`: local skill candidates before global installation.

For an installed portable skill, keep reusable instructions in the skill folder and keep project-specific outputs in the project.

## Global vs Session-Local Agents

Install globally only when the agent is stable, generic, and reusable across projects:

- `manuscript-fact-extraction-agent`
- `storyboard-agent`
- `asset-audit-agent`
- `ppt-template-automation-agent`
- `figma-layout-polish-agent`

Keep session-local or project-local when:

- It includes one project's template, school style, file paths, data schema, or thesis topic.
- It has not been tested across at least two different manuscripts.
- It is a temporary prompt variant for exploration.
- It encodes fragile assumptions from one deck.

This skill itself can be globally installed after validation because it is only an orchestrator. The bundled agent specs are generic references; project-specific overrides should live in the project's `agent/` directory.

## Workflow Details

### 1. Fact Ledger

Load `references/agents/fact_extraction_agent_spec.md`.

Produce:

- `align/fact_ledger_v*.md`
- optionally `align/claim_source_map_v*.md`

Must include:

- problem facts
- contributions
- method/system modules
- experiments and metrics
- figure/table ledger
- limitations
- terminology
- risk register
- downstream handoff

Validation:

- Every core contribution has evidence.
- Every experiment claim has metric, baseline/comparison, result, and source.
- Risk register exists for defense or high-stakes talks.

### 2. Storyboard

Load `references/agents/storyboard_agent_spec.md`.

Inputs:

- fact ledger
- source materials if needed
- target duration/page count/audience

Produce:

- `align/PPT_storyboard_v*.md`

Each slide should contain:

- title
- core point
- recommended visual form
- asset needs
- speaking points
- estimated time
- QA risk

Validation:

- Total time fits target.
- Each page has one core point.
- Problem, method, system, experiment, and conclusion form a closed loop.

### 3. Asset Audit

Load `references/agents/asset_audit_agent_spec.md`.

Inputs:

- storyboard
- fact ledger
- source figures/assets/template

Produce:

- `align/PPT_asset_audit_v*.md`
- optionally `align/PPT_asset_manifest_v*.csv`

Validation:

- Every slide has a visual strategy.
- Reused assets have paths/sources.
- Redraw assets specify what facts to preserve.
- Low-resolution or high-risk assets are marked.

### 4. PPTX Automation

Load `references/agents/template_automation_agent_spec.md`.

Inputs:

- storyboard
- asset manifest
- template PPTX if available

Produce:

- `generated_pptx_test/<deck>_v*.pptx`
- generation manifest
- rendered PNGs if possible

Validation:

- PPTX opens.
- Slide count matches storyboard.
- Aspect ratio matches template/config.
- Media embeds correctly.
- PowerPoint/LibreOffice export succeeds when available.

### 5. Figma Layout Polish

Load `references/agents/figma_layout_polish_agent_spec.md` only when visual polish is requested or needed.

Inputs:

- PPTX draft
- rendered screenshots
- page plan
- target pages or regions

Modes:

- `partial_asset`: default. Generate local visual assets and keep PPT template title/footer editable.
- `whole_page`: use only when editability is less important.
- `layout_blueprint`: use when Figma export is rate-limited or deterministic local replication is required.

Validation:

- Frame/screenshot or local equivalent exists.
- Text renders correctly, especially CJK fonts.
- Exported/replicated asset is回填 into PPTX if requested.
- PowerPoint render and before/after comparison are generated.

## Figma Policy

Before Figma work:

- Run or reuse `whoami` if plan/seat is unknown.
- Check call budget if the user is on Starter/View.
- Use CJK-capable fonts for Chinese, defaulting to `Noto Sans SC`.
- Minimize read calls; prefer one `use_figma` call returning screenshot when possible.

If rate-limited:

- Stop Figma read/export calls.
- Preserve Figma file key and frame id.
- Use cached screenshot or local layout replication.
- Mark manifest status as `rate_limited`.

## Output Contract

A complete run should leave:

- `align/fact_ledger_v*.md`
- `align/PPT_storyboard_v*.md`
- `align/PPT_asset_audit_v*.md` and/or CSV manifest
- `generated_pptx_test/*.pptx`
- rendered screenshots/contact sheet when available
- `align/*manifest*.csv` for PPTX/Figma handoff
- `exp/*test*.md` or validation record for non-trivial runs

## Final Validation

Before calling the workflow done, verify:

- Facts, contributions, experiment claims, and limitations do not conflict across artifacts.
- Slide count and timing match the target.
- PPTX opens and renders.
- Important pages are readable in screenshots.
- Figma limitations, font issues, or rate limits are disclosed.
- Remaining manual polish items are listed.

## Prompt Template

```text
Use $manuscript-to-ppt-workflow.

Runtime configuration:
- source_materials: <path>
- project_type: <thesis defense/conference/group meeting/...>
- target_duration: <minutes>
- audience: <audience>
- template_file: <optional pptx/beamer/html template>
- asset_dirs: <optional dirs>
- output_dir: <project output dir>
- figma_policy: <disabled|optional|required|fallback-only>

Task:
Run the manuscript-to-PPT workflow. Produce fact ledger, storyboard, asset audit, PPTX draft, and optional Figma polish artifacts. Keep facts grounded in source material and verify PPTX/rendered outputs.
```
