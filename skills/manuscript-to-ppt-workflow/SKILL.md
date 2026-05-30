---
name: manuscript-to-ppt-workflow
description: "Orchestrate a manuscript, thesis, paper, report, or proposal into a presentation workflow. Use when Codex must coordinate existing skills such as codex-deep-interview, research-fact-source-sync, thesis-figure-pipeline, codex-visual-acceptance, and a small set of native PPT agents for storyboard, PPTX automation, and optional Figma polish."
---

# Manuscript to PPT Workflow

## Role

This skill is the workflow leader, not a giant phase prompt and not a request to spawn an agent for every step.

The main thread owns intent alignment, fact grounding, dependency ordering, integration, and final truth. Use existing skills for those shared capabilities. Delegate only work that has a bounded expert output, a disjoint write scope, and enough stable input to run without blocking the leader.

## Skill-First Orchestration

Use these skills explicitly when their phase is needed:

| Need | Preferred skill | Main-thread responsibility |
|---|---|---|
| Clarify audience, duration, scope, non-goals, acceptance criteria | `codex-deep-interview` | Ask only high-impact questions and write the production brief. |
| Align claims with source files, metrics, figures, terminology, and thesis prose | `research-fact-source-sync` | Build or refresh the fact ledger and mark unsupported claims. |
| Extract or refresh thesis/paper figures from experiment tables | `thesis-figure-pipeline` | Generate or audit reproducible figures before PPTX generation. |
| Check screenshots, exported pages, PDF/PPT renders, or visual artifacts | `codex-visual-acceptance` | Verify readability and layout before calling the deck usable. |
| Create final HTML notes, workflow records, or human-readable manifests | `html-research-notes` | Keep durable handoff evidence concise and navigable. |
| Use Figma for selected page polish | `figma_layout_polish` native agent plus Figma tools | Keep Figma work scoped to selected pages or regions. |

Do not create a native custom agent merely to wrap one of these skills. If a phase is a serial read/write transformation that the leader must inspect immediately, do it in the main thread with the relevant skill.

## Native Agent Policy

Prefer native custom agents from the nearest available agent directory only for bounded expert lanes:

1. Project-local: `.codex/agents/`
2. User-global: `~/.codex/agents/`

Default native agents:

| Phase | Native agent name | Native TOML | Use when |
|---|---|---|---|
| Storyboard | `ppt_storyboard` | `ppt-storyboard.toml` | Production brief and fact ledger are stable enough to plan slides. |
| PPTX automation | `ppt_template_automation` | `ppt-template-automation.toml` | Storyboard and asset decisions are ready for an editable draft. |
| Figma polish | `figma_layout_polish` | `figma-layout-polish.toml` | Visual polish is requested or selected pages need layout repair. |

Deprecated as default native lanes:

- Intent alignment: use `codex-deep-interview` in the main thread.
- Fact extraction: use `research-fact-source-sync` or local source inspection in the main thread.
- Asset audit: do in the main thread while integrating storyboard and available assets, unless the user explicitly asks for a separate read-only audit lane.

If native subagent tools are unavailable, execute the phase locally. If the user explicitly requires agents and a native agent is unavailable, stop and report the missing role instead of silently pretending delegation happened.

## Runtime Defaults

Ask for missing inputs only when they cannot be inferred safely. Required for a full run:

- `source_materials`
- `project_type`
- `target_duration`
- `audience`
- `output_dir`

Recommended:

- `target_page_count`
- `language`
- `template_file`
- `visual_style`
- `asset_dirs`
- `figma_policy`: disabled, optional, required, or fallback-only
- `editability_policy`: prefer_editable, mixed, or allow_whole_page_images
- `validation_policy`
- `intent_sync_policy`: ask-first, infer-and-record, or skip-only-if-brief-provided
- `subagent_policy`: native-when-useful, native-required, local-only, or ask-first

Default to `subagent_policy: native-when-useful`. This means do not spawn native agents for serial critical-path work, even if matching TOML files exist.

## Directory Policy

Project outputs should use:

- `align/`: production brief, fact ledger, storyboard, asset manifest, page plans, Figma frame manifests.
- `generated_assets/`: extracted, redrawn, or generated assets.
- `generated_pptx_test/`: generated PPTX files and rendered screenshots.
- `exp/`: generation scripts, workflow tests, validation records.
- `agent/`: legacy or extended agent specs, only as fallback guidance.

Keep this skill folder limited to orchestration metadata. Do not put project-specific facts, templates, alignment files, or long agent specs inside the skill.

## Workflow

### 0. Setup And Routing

Inspect the source paths, existing `align/`, template files, generated assets, and prior notes. Check `codex features list` only when the run depends on native subagents.

Load `agent/agent_collaboration_standard.md` only when actually delegating to native agents or resolving handoffs across lanes.

### 1. Intent Alignment

Use `codex-deep-interview` principles in the main thread. Produce `align/ppt_production_brief_v*.md` unless the user already supplied a current brief.

The brief should record:

- audience, duration, target slide count, language, and project type
- confirmed decisions, inferred defaults, and open questions
- non-goals and acceptance criteria
- template, asset, Figma, editability, and validation policies
- planned agent lanes, if any

Do not delegate this phase by default. The leader needs this context to route the rest of the workflow.

### 2. Fact Grounding

Use source inspection plus `research-fact-source-sync` when available. Produce or refresh `align/fact_ledger_v*.md` and optional `align/claim_source_map_v*.md`.

The fact ledger is the source of truth for contributions, methods, systems, experiments, limitations, terminology, figures, and QA risks. Bind important claims to source locations whenever possible. Do not invent baselines, metrics, figures, or conclusions.

Do not delegate this phase by default. It is serial, source-sensitive, and directly controls downstream truth.

### 3. Storyboard

Use native agent `ppt_storyboard` when native subagents are available and the storyboard can be written as a bounded lane. Otherwise do it locally.

Required input:

- production brief
- fact ledger or equivalent source-grounded notes

Output:

- `align/PPT_storyboard_v*.md`

Every slide should have one core point, visual strategy, asset needs, speaking points, estimated time, and QA risk.

### 4. Asset Decisions

Make the asset audit in the main thread while integrating the storyboard, fact ledger, local asset directories, template constraints, and figure pipeline outputs.

Output:

- `align/PPT_asset_audit_v*.md`
- optionally `align/PPT_asset_manifest_v*.csv`

Every slide should have a reuse, redraw, generate, omit, or confirm decision. Use `thesis-figure-pipeline` for reproducible academic figures when the assets come from experiment tables or thesis figures.

Only use a separate read-only explorer lane for asset inventory when asset directories are large and the lane has no write scope.

### 5. PPTX Automation

Use native agent `ppt_template_automation` when the storyboard and asset decisions are stable. Otherwise execute locally with the same output contract.

Output:

- `generated_pptx_test/<deck>_v*.pptx`
- generation script or manifest when useful
- rendered PNGs/contact sheet when possible

Validate slide count, aspect ratio, media embedding, template mapping, text readability, and basic open/render behavior.

### 6. Figma Polish

Use native agent `figma_layout_polish` only when visual polish is requested or a small set of target pages needs layout repair. Do not route the whole deck through Figma by default.

Before Figma work:

- follow `figma-use` guidance before `use_figma`
- check Figma MCP status or run `whoami` if unknown
- use CJK-capable fonts for Chinese, defaulting to `Noto Sans SC`
- preserve file key/frame id and rate-limit notes

### 7. Visual QA And Handoff

Use `codex-visual-acceptance` for screenshot/PDF/PPT render checks when practical. The leader must inspect outputs before reporting done.

Before calling the workflow complete, verify:

- production brief exists and records assumptions/open questions
- facts and limitations are consistent across brief, fact ledger, storyboard, and PPTX
- slide count and timing match target
- PPTX opens or renders when a renderer is available
- important pages are readable in screenshots
- Figma limitations, font issues, or rate limits are disclosed
- remaining manual polish items are listed

## Fallback Specs

Legacy Markdown specs may exist under `agent/` and can be used as supplementary guidance, not as the primary routing mechanism:

| Purpose | Spec file |
|---|---|
| Storyboard | `agents_storyboard_agent_spec.md` |
| PPTX automation | `template_automation_agent_spec.md` |
| Figma polish | `figma_layout_polish_agent_spec.md` |
| Historical alignment guidance | `ppt_production_alignment_agent_spec.md` |
| Historical fact extraction guidance | `fact_extraction_agent_spec.md` |
| Historical asset audit guidance | `agents_asset_audit_agent_spec.md` |

Load only the specific spec needed for the current phase. If a spec conflicts with this skill, this skill owns orchestration and the native TOML owns the delegated lane.

## Output Contract

A complete run should leave:

- `align/ppt_production_brief_v*.md`
- `align/fact_ledger_v*.md`
- `align/PPT_storyboard_v*.md`
- `align/PPT_asset_audit_v*.md` and/or CSV manifest
- `generated_pptx_test/*.pptx`
- rendered screenshots/contact sheet when available
- `align/*manifest*.csv` for PPTX/Figma handoff
- `exp/*test*.md` or validation record for non-trivial runs

## Prompt Template

```text
Use $manuscript-to-ppt-workflow.

Runtime configuration:
- source_materials: <path/list>
- project_type: <thesis defense/conference/group meeting/...>
- target_duration: <minutes>
- audience: <audience>
- template_file: <optional>
- asset_dirs: <optional>
- output_dir: <project output dir>
- figma_policy: <disabled|optional|required|fallback-only>
- intent_sync_policy: <ask-first|infer-and-record|skip-only-if-brief-provided>
- subagent_policy: <native-when-useful|native-required|local-only|ask-first>

Task:
Run the manuscript-to-PPT workflow. Use main-thread skill orchestration for intent alignment, fact grounding, asset decisions, integration, and validation. Use native agents only for bounded storyboard, PPTX automation, and optional Figma polish lanes when useful.
```
