---
name: manuscript-to-ppt-workflow
description: "Orchestrate a manuscript, thesis, paper, report, LaTeX project, asset folder, experiment output, or proposal into a PPT-native presentation workflow with a mandatory codex-deep-interview intent/material gate, source-grounded fact ledger, optional OpenRouter ICU Image visual enrichment, bounded storyboard/PPTX agents, python-pptx template generation, and PowerPoint COM screenshot/render QA. Use when Codex must create or revise a real editable PowerPoint deck from flexible research materials without guessing audience, duration, material availability, template role, render policy, or acceptance criteria."
---

# Manuscript to PPT Workflow

## Role

This skill is the workflow leader for PPT-native deck production.

The main thread owns intent alignment, fact grounding, dependency ordering, integration, and final truth. Use existing skills for shared capabilities. Delegate only bounded expert work with a stable input contract and a clear write scope.

Figma is not part of the default workflow. Do not use Figma MCP, Figma context, Figma write tools, or Figma layout agents for this workflow unless the user explicitly starts a separate Figma experiment outside the PPT-native lane.

## Non-Negotiable Gates

For any full deck run, do not proceed past setup until a current production brief exists and critical decisions are confirmed by the user. Use `codex-deep-interview` to obtain that confirmation unless the user already supplied an explicit, current `align/ppt_production_brief_v*.md`.

The leader must stop and ask one concise question at a time when any of these are missing or ambiguous:

- audience and presentation setting
- target duration and slide count range
- material bundle: manuscript PDFs, DOCX/Markdown notes, LaTeX repository, BibTeX, figure folders, tables, experiment outputs, screenshots, prior slides, brand/school assets, and any source directories the user can provide
- source priority: which materials are authoritative when files conflict
- required template file and whether it is binding or only visual inspiration
- output priority: editable PPTX, visual polish, speaker script, or quick rough draft
- language, identity fields, and required cover information
- visual enrichment policy, including whether OpenRouter ICU Image may generate or edit supporting visuals
- `python_pptx_policy`, including whether editable native shapes are required
- `powerpoint_com_qa_policy`, including whether PowerPoint COM render QA is required or best-effort
- acceptance criteria for "done", including visual QA thresholds

Do not infer these for a real full deck. `infer-and-record` is allowed only for narrow exploratory tasks, smoke tests, or when the user explicitly asks for a rough draft with assumptions.

## Skill-First Orchestration

Use these skills explicitly when their phase is needed:

| Need | Preferred skill | Main-thread responsibility |
|---|---|---|
| Clarify audience, duration, scope, non-goals, acceptance criteria | `codex-deep-interview` | Ask only high-impact questions, get user confirmation, and write the production brief before downstream work. |
| Align claims with source files, metrics, figures, terminology, and thesis prose | `research-fact-source-sync` | Build or refresh the fact ledger and mark unsupported claims. |
| Extract or refresh thesis/paper figures from experiment tables | `thesis-figure-pipeline` | Generate or audit reproducible figures before PPTX generation. |
| Generate or edit supporting visuals, conceptual diagrams, cover imagery, or icon-like assets | `openrouter-icu-image` | Use only after the brief and asset decisions approve image generation; preserve source-grounded meaning and record prompts/outputs. |
| Check screenshots, exported pages, PDF/PPT renders, or visual artifacts | `codex-visual-acceptance` | Verify readability and layout before calling the deck usable. |
| Create final HTML notes, workflow records, or human-readable manifests | `html-research-notes` | Keep durable handoff evidence concise and navigable. |

Do not create a native custom agent merely to wrap one of these skills. If a phase is a serial read/write transformation that the leader must inspect immediately, do it in the main thread with the relevant skill.

## Native Agent Policy

Prefer native custom agents from the nearest available agent directory only for bounded expert lanes:

1. Project-local: `.codex/agents/`
2. User-global: `~/.codex/agents/`

Default native agents:

| Phase | Native agent name | Native TOML | Use when |
|---|---|---|---|
| Storyboard | `ppt_storyboard` | `ppt-storyboard.toml` | Production brief and fact ledger are stable enough to plan slides. |
| PPTX automation | `ppt_template_automation` | `ppt-template-automation.toml` | Storyboard, template inventory, layout plan, and asset decisions are ready for an editable draft. |
| Render QA | `ppt_render_qa` | `ppt-render-qa.toml` | A draft PPTX exists and must be rendered through PowerPoint COM for screenshot QA. |

Deprecated as default native lanes:

- Intent alignment: use `codex-deep-interview` in the main thread.
- Fact extraction: use `research-fact-source-sync` or local source inspection in the main thread.
- Asset audit: do in the main thread while integrating storyboard and available assets, unless the user explicitly asks for a separate read-only audit lane.
- Figma layout polish: removed from the default workflow. Do not spawn it for manuscript-to-PPT runs.

For a full deck run, default to native agents for storyboard, PPTX automation, and render QA after the production brief, fact ledger, template inventory, and asset decisions are ready. Do not set `subagent_policy: local-only` for a full deck unless the user explicitly chooses local-only after being told that this disables the agent/QA lane separation.

If native subagent tools are unavailable, stop before storyboard/PPTX automation/render QA and report the unavailable agents plus a local fallback option. Continue locally only after the user confirms the fallback.

## Runtime Defaults

Ask for missing inputs only when they cannot be inferred safely. Required for a full run:

- `material_bundle` or `source_materials`
- `project_type`
- `target_duration`
- `audience`
- `output_dir`

Recommended:

- `target_page_count`
- `language`
- `template_file`
- `material_priority`: source-of-truth order for PDF, LaTeX, figures, tables, existing slides, and notes
- `visual_style`
- `asset_dirs`
- `visual_enrichment_policy`: disabled, ask-first, source-grounded, or freeform-rough
- `image_generation_provider`: openrouter-icu-image, local-only, or none
- `python_pptx_policy`: required, preferred, or fallback-only
- `powerpoint_com_qa_policy`: required, best-effort, or disabled
- `render_fallback_policy`: disabled, libreoffice, aspose, or ask-first
- `editability_policy`: prefer_editable, mixed, or allow_whole_page_images
- `validation_policy`
- `intent_sync_policy`: ask-first, confirmed-brief-required, infer-and-record, or skip-only-if-brief-provided
- `subagent_policy`: native-when-useful, native-required, local-only, or ask-first

Default to:

```yaml
intent_sync_policy: confirmed-brief-required
subagent_policy: native-when-useful
visual_enrichment_policy: ask-first
image_generation_provider: openrouter-icu-image
python_pptx_policy: required
powerpoint_com_qa_policy: required
render_fallback_policy: ask-first
editability_policy: prefer_editable
```

For full deck generation, treat `local-only`, `infer-and-record`, disabled render QA, and whole-page-image output as user-selected escape hatches, not defaults.

## Directory Policy

Project outputs should use:

- `align/`: production brief, fact ledger, storyboard, template inventory, asset manifest, layout plan, page plans.
- `generated_assets/`: extracted, redrawn, or generated assets.
- `generated_assets/openrouter-icu/`: generated or edited visual assets from OpenRouter ICU Image.
- `generated_pptx_test/`: generated PPTX files and draft copies.
- `qa/`: rendered pages, contact sheets, visual QA reports.
- `exp/`: generation scripts, workflow tests, validation records.
- `agent/`: legacy or extended agent specs, only as fallback guidance.

Keep this skill folder limited to orchestration metadata and reusable helper scripts. Do not put project-specific facts, templates, alignment files, or long agent specs inside the skill.

## Workflow

### 0. Setup And Routing

Inspect material paths, existing `align/`, template files, generated assets, prior notes, and available render tools. Check `codex features list` only when the run depends on native subagents.

Load `agent/agent_collaboration_standard.md` only when actually delegating to native agents or resolving handoffs across lanes.

Before reading sources deeply or creating output artifacts, decide whether this is a full deck run or a narrow downstream task. Full deck runs must enter the intent-alignment gate.

### 1. Intent Alignment

Use `codex-deep-interview` in the main thread. Produce `align/ppt_production_brief_v*.md` unless the user already supplied a current brief.

Do not continue to fact grounding, storyboard, asset decisions, template automation, or render QA until the brief records `status: confirmed` or an equivalent explicit confirmation note. If the user declines to answer, offer a rough-draft mode and record `status: rough_assumptions_unconfirmed`; do not present that run as final or production-ready.

The brief should record:

- audience, duration, target slide count, language, and project type
- material bundle inventory and source priority
- confirmed decisions, inferred defaults, and open questions
- non-goals and acceptance criteria
- template, asset, visual enrichment, editability, `python_pptx_policy`, `powerpoint_com_qa_policy`, and fallback render policies
- planned agent lanes, if any
- who confirmed the brief and when, or why the run is explicitly rough/unconfirmed

Do not delegate this phase by default. The leader needs this context to route the rest of the workflow.

### 2. Material Inventory

Build a material inventory before fact grounding. Do not assume the only useful input is a single paper PDF.

Actively check or ask for:

- manuscript PDF, DOCX, Markdown, or plain text
- LaTeX repository or source folder, including `.tex`, `.bib`, `figures/`, `tables/`, and compiled PDF
- image/material folders with original figures, diagrams, screenshots, logos, and icons
- experiment outputs such as CSV, Excel, JSON, logs, plots, notebooks, or result manifests
- previous slides, poster files, HTML notes, or advisor comments
- style assets such as school/company logos, color palettes, fonts, and template PPTX

Produce:

- `align/material_inventory_v*.md`
- optionally `align/material_manifest_v*.csv`

For each item record path, type, authority level, likely use in deck, extraction method, and risk. If sources conflict, follow `material_priority` from the production brief or ask the user.

### 3. Fact Grounding

Use source inspection plus `research-fact-source-sync` when available. Produce or refresh `align/fact_ledger_v*.md` and optional `align/claim_source_map_v*.md`.

The fact ledger is the source of truth for contributions, methods, systems, experiments, limitations, terminology, figures, and QA risks. Bind important claims to source locations whenever possible. Do not invent baselines, metrics, figures, identities, or conclusions.

Do not delegate this phase by default. It is serial, source-sensitive, and directly controls downstream truth.

### 4. Template Inventory

Inspect the PPTX template before storyboard-to-deck automation. Produce `align/template_inventory_v*.md` and, when useful, `align/template_layout_map_v*.json`.

Record:

- slide size and aspect ratio
- slide masters and layout names
- placeholder names, types, and coordinates
- theme fonts and colors
- logos, headers, footers, page numbers, and locked-looking visual conventions
- which layouts fit cover, agenda, section divider, content, figure, comparison, result, conclusion, and backup slides

Use `python-pptx` when available for object-level inspection. For deterministic lightweight inspection, the bundled `scripts/inspect_pptx_template.py` can extract core OOXML metadata without modifying the template.

### 5. Storyboard

Use native agent `ppt_storyboard` when native subagents are available and the storyboard can be written as a bounded lane. For a full deck run, this is the default. Do it locally only for narrow tasks, smoke tests, or user-confirmed local fallback.

Required input:

- confirmed production brief
- fact ledger or equivalent source-grounded notes

Output:

- `align/PPT_storyboard_v*.md`

Every slide should have one core point, visual strategy, asset needs, speaking points, estimated time, and QA risk.

### 6. Asset Decisions, Visual Enrichment, And Layout Plan

Make the asset audit in the main thread while integrating storyboard, fact ledger, material inventory, local asset directories, template constraints, and figure pipeline outputs. This phase must produce leader-approved asset and layout decisions before PPTX automation starts.

Output:

- `align/PPT_asset_audit_v*.md`
- optionally `align/PPT_asset_manifest_v*.csv`
- `align/visual_enrichment_plan_v*.md` when generated/edited visuals are useful
- `align/ppt_layout_plan_v*.json` for PPTX automation

Every slide should have a reuse, redraw, generate, omit, or confirm decision. Every slide should also map to a template layout and a target content structure. Use `thesis-figure-pipeline` for reproducible academic figures when assets come from experiment tables or thesis figures.

Use `openrouter-icu-image` only when the production brief and asset decision approve visual generation or editing. Suitable uses:

- conceptual cover/background images that do not claim factual evidence
- simplified visual metaphors for problem framing
- redrawn explanatory diagrams grounded in fact ledger text
- cleaned or style-matched supporting illustrations
- icon-like visual elements that improve scanability

Not suitable without explicit user approval:

- generating fake experimental results, charts, screenshots, microscopy/medical/scientific evidence, or unverifiable system outputs
- altering source figures in ways that change their scientific meaning
- replacing required editable diagrams with raster-only images when editability is required

For each generated image, record:

- source slide/use case
- grounding facts or references
- prompt summary without secrets
- model/provider
- output file path under `generated_assets/openrouter-icu/`
- whether it is evidence, illustration, or decorative support
- QA risks and required user review

Only use a separate read-only explorer lane for asset inventory when asset directories are large and the lane has no write scope.

### 7. PPTX Automation

Use native agent `ppt_template_automation` when storyboard, template inventory, layout plan, and asset decisions are stable. For a full deck run, this is the default. Execute locally only for narrow tasks, smoke tests, or user-confirmed local fallback.

Default implementation path:

- Use `python-pptx` to create or update an editable `.pptx`.
- Start from the user-provided template when `template_file` is binding.
- Prefer native placeholders, text boxes, shapes, tables, and images over whole-page screenshots.
- Preserve slide size, template masters, logos, header/footer conventions, and theme style when feasible.
- Keep one source-of-truth script or manifest under `exp/` when generation is non-trivial.

Output:

- `generated_pptx_test/<deck>_v*.pptx`
- generation script or manifest when useful
- page-to-storyboard/template mapping

The PPTX automation lane must not mark the draft usable. It hands the draft to render QA.

### 8. PowerPoint COM Render QA

Use native agent `ppt_render_qa` when a draft PPTX exists. This is the default QA lane for Windows runs.

Default implementation path:

- Use PowerPoint COM automation to open the generated deck.
- Export slides to PNG and optionally PDF under `qa/rendered_pages/`.
- Create a contact sheet when practical.
- Produce `qa/ppt_render_qa_v*.md` and/or `exp/ppt_render_qa_v*.md`.

Use the bundled `scripts/render_pptx_powerpoint_com.ps1` when a direct helper is useful. It should fail clearly if PowerPoint is not installed or COM automation is unavailable.

Fallback policy:

- If `powerpoint_com_qa_policy: required` and PowerPoint COM is unavailable, stop and report the blocker.
- Use LibreOffice, Aspose.Slides, or another renderer only when `render_fallback_policy` allows it or the user confirms.
- Do not accept a deck based only on structural inspection when render QA was required.

Blocking visual failures:

- title/subtitle overlap
- clipped text
- unreadable charts, tables, formulas, or figures
- severe crowding
- missing CJK glyphs or wrong font substitution
- blank pages
- content outside slide bounds
- missing images/assets
- obvious template/logo/header/footer misuse

If render QA fails, loop back to PPTX automation for editable layout defects or to the leader for content compression/scope decisions. Do not report the deck as complete after a failed render check.

### 9. Visual Acceptance And Handoff

Use `codex-visual-acceptance` for screenshot/PDF/PPT render checks when practical. The leader must inspect outputs before reporting done.

Before calling the workflow complete, verify:

- production brief exists and is confirmed, or the run is explicitly marked rough/unconfirmed
- material inventory exists for non-trivial runs and source priority is clear
- facts and limitations are consistent across brief, fact ledger, storyboard, and PPTX
- generated visuals are labeled as illustration/support unless they are direct source-derived evidence
- slide count and timing match target
- PPTX opens and renders when render QA is required
- important pages are readable in screenshots
- no blocking visual failures remain in accepted screenshots
- remaining manual polish items are listed

## Fallback Specs

Legacy Markdown specs may exist under `agent/` and can be used as supplementary guidance, not as the primary routing mechanism:

| Purpose | Spec file |
|---|---|
| Storyboard | `agents_storyboard_agent_spec.md` |
| PPTX automation | `template_automation_agent_spec.md` |
| PowerPoint COM render QA | `ppt_render_qa_agent_spec.md` |
| Historical alignment guidance | `ppt_production_alignment_agent_spec.md` |
| Historical fact extraction guidance | `fact_extraction_agent_spec.md` |
| Historical asset audit guidance | `agents_asset_audit_agent_spec.md` |

Load only the specific spec needed for the current phase. If a spec conflicts with this skill, this skill owns orchestration and the native TOML owns the delegated lane.

## Output Contract

A complete run should leave:

- `align/ppt_production_brief_v*.md`
- `align/material_inventory_v*.md`
- `align/fact_ledger_v*.md`
- `align/template_inventory_v*.md`
- `align/PPT_storyboard_v*.md`
- `align/PPT_asset_audit_v*.md` and/or CSV manifest
- `align/visual_enrichment_plan_v*.md` when image generation/editing is used
- `align/ppt_layout_plan_v*.json`
- `generated_assets/openrouter-icu/*` when OpenRouter ICU Image is used
- `generated_pptx_test/*.pptx`
- `qa/rendered_pages/*`
- rendered contact sheet when available
- `qa/ppt_render_qa_v*.md` or `exp/*visual_qa*.md`
- `exp/*test*.md` or validation record for non-trivial runs

## Prompt Template

```text
Use $manuscript-to-ppt-workflow.

Runtime configuration:
- material_bundle:
  - source_materials: <path/list>
  - latex_repo: <optional path>
  - asset_dirs: <optional paths>
  - experiment_outputs: <optional paths>
  - prior_slides_or_notes: <optional paths>
- project_type: <thesis defense/conference/group meeting/...>
- target_duration: <minutes>
- audience: <audience>
- template_file: <required for template-bound runs>
- material_priority: <PDF|LaTeX|figures|tables|existing slides|notes order>
- visual_enrichment_policy: <disabled|ask-first|source-grounded|freeform-rough>
- image_generation_provider: <openrouter-icu-image|local-only|none>
- output_dir: <project output dir>
- python_pptx_policy: <required|preferred|fallback-only>
- powerpoint_com_qa_policy: <required|best-effort|disabled>
- render_fallback_policy: <disabled|libreoffice|aspose|ask-first>
- editability_policy: <prefer_editable|mixed|allow_whole_page_images>
- intent_sync_policy: <confirmed-brief-required|ask-first|infer-and-record|skip-only-if-brief-provided>
- subagent_policy: <native-when-useful|native-required|local-only|ask-first>

Task:
Run the PPT-native manuscript-to-PPT workflow. Start with codex-deep-interview and do not proceed past the production brief until critical requirements, material bundle availability, source priority, and visual enrichment policy are confirmed or explicitly marked rough/unconfirmed. Use main-thread skill orchestration for material inventory, fact grounding, template inventory, asset/visual decisions, integration, and validation. Use OpenRouter ICU Image only when the brief and asset plan approve source-grounded visual generation/editing. Use native agents for bounded storyboard, python-pptx PPTX automation, and PowerPoint COM render QA. Do not use Figma in this workflow. Render screenshots and fail the run if visual QA finds overlap, clipping, unreadable charts, severe crowding, missing CJK glyphs, blank pages, missing assets, or content outside slide bounds.
```
