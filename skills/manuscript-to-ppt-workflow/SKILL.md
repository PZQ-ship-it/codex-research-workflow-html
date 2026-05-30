---
name: manuscript-to-ppt-workflow
description: "Use when the user wants to turn a manuscript, thesis, paper, report, proposal, or long document into a presentation workflow: intent alignment, production brief, fact ledger, PPT storyboard, asset audit, template-based PPTX draft, and optional Figma layout polish. Use for portable multi-agent PPT generation and defense/conference presentation preparation."
---

# Manuscript to PPT Workflow

## Role

This skill is an orchestration layer. It routes a manuscript-to-presentation job through native custom agents when available, keeps their dependencies ordered, and verifies that durable handoff files are produced.

Do not treat this skill as the detailed prompt for every phase. Use native custom agents for execution, and load the external Markdown agent spec only as fallback or supplementary guidance.

## Native Agents

Prefer Codex native custom agents from the nearest available agent directory:

1. Project-local: `.codex/agents/`
2. User-global: `~/.codex/agents/`

Use these native agent names:

| Phase | Native agent name | Native TOML |
|---|---|---|
| Intent alignment | `ppt_production_alignment` | `ppt-production-alignment.toml` |
| Fact extraction | `manuscript_fact_extraction` | `manuscript-fact-extraction.toml` |
| Storyboard | `ppt_storyboard` | `ppt-storyboard.toml` |
| Asset audit | `ppt_asset_audit` | `ppt-asset-audit.toml` |
| PPTX automation | `ppt_template_automation` | `ppt-template-automation.toml` |
| Figma polish | `figma_layout_polish` | `figma-layout-polish.toml` |

When native subagent tools are available and `subagent_policy` permits it, spawn the relevant custom agent by its native agent name. If the runtime does not expose native subagents or a custom agent is unavailable, execute the phase locally using the fallback Markdown spec.

## Fallback Agent Specs

Find fallback Markdown agent specs outside this skill folder, in the nearest available agent directory:

1. Project-local: `agent/`
2. Repository-local: `<repo>/agent/`
3. User-global: `~/.codex/agent/`

Use these files as supplementary guidance:

| Phase | Legacy Agent ID | Spec file |
|---|---|---|
| Intent alignment | `ppt-production-alignment-agent` | `ppt_production_alignment_agent_spec.md` |
| Fact extraction | `manuscript-fact-extraction-agent` | `fact_extraction_agent_spec.md` |
| Storyboard | `storyboard-agent` | `agents_storyboard_agent_spec.md` |
| Asset audit | `asset-audit-agent` | `agents_asset_audit_agent_spec.md` |
| PPTX automation | `ppt-template-automation-agent` | `template_automation_agent_spec.md` |
| Figma polish | `figma-layout-polish-agent` | `figma_layout_polish_agent_spec.md` |

If neither the native agent nor the fallback spec can be found, report the missing role and continue only when the phase can be safely handled from existing context.

Also load `agent_collaboration_standard.md` when coordinating multiple agents, planning parallel work, or resolving handoffs. Use the workflow skill as the leader and each agent as a bounded lane.

## Native Subagent Rules

- The main thread is always the workflow leader; it owns dependency ordering, integration, verification, and user-facing truth.
- Use native custom agents for full workflow runs when `subagent_policy` is `native-when-available` or `native-required`.
- Use local execution when `subagent_policy` is `local-only`, when native tools are unavailable, or when a phase is on the immediate critical path and delegation would only add latency.
- Spawn dependent phases only after required handoff files exist: production brief -> fact ledger -> storyboard -> asset audit -> PPTX draft -> Figma polish.
- Parallelism is allowed only for independent sidecar work with disjoint write scopes, such as template feasibility while fact extraction runs after a production brief exists.
- If a native custom agent is unavailable, use built-in `explorer` for fact/asset investigation and built-in `worker` for bounded PPTX/Figma edits, or execute locally.
- Every delegated lane must return changed files, assumptions, risks, and integration evidence.
- Do not treat subagent completion as workflow completion; inspect outputs and run the smallest meaningful verification.

## Collaboration Model

The main thread is the workflow leader:

- It owns the critical path, final integration, conflict resolution, and user-facing truth.
- It may delegate to native custom agents or simulate agent lanes locally, but it must inspect their outputs before passing them downstream.
- It must not treat an agent output as complete until the relevant handoff file exists and the smallest meaningful verification has run.

Each agent is a lane:

- It has one bounded responsibility and an explicit write scope.
- It produces durable evidence: files, decisions, assumptions, risks, and next-step handoff.
- It must not modify upstream artifacts unless its spec and the leader allow that exact edit.

Parallelism is allowed only after the required upstream inputs are stable and write scopes are disjoint. Default to sequential execution for the core chain: production brief -> fact ledger -> storyboard -> asset audit -> PPTX automation -> Figma polish.

## Pipeline

Default order:

0. Intent alignment and production brief
1. Fact extraction
2. Storyboard generation
3. Asset audit
4. Template/PPTX automation
5. Figma layout polish, if requested or useful
6. Script and QA, if requested
7. Final validation and handoff

Hard dependencies:

- Fact extraction depends on a production brief unless complete runtime configuration already exists.
- Storyboard depends on production brief and fact ledger.
- Asset audit depends on production brief, storyboard, and fact ledger.
- PPTX automation depends on production brief, storyboard, and asset audit.
- Figma polish depends on production brief plus a PPTX draft, screenshots, page plan, or target regions.
- Script and QA should happen after storyboard is mostly frozen and facts are locked.

## Runtime Defaults

Ask for missing inputs only when they cannot be inferred safely. Prefer the production alignment agent for intent synchronization.

Required for a full run:

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
- `subagent_policy`: native-when-available, native-required, local-only, or ask-first

## Directory Policy

Project outputs should use:

- `align/`: production brief, fact ledger, storyboard, asset manifest, page plans, Figma frame manifests.
- `generated_assets/`: extracted, redrawn, or generated assets.
- `generated_pptx_test/`: generated PPTX files and rendered screenshots.
- `exp/`: generation scripts, workflow tests, validation records.
- `agent/`: project or repository agent specs.

Keep this skill folder limited to orchestration metadata. Do not put project-specific facts, templates, alignment files, or long agent specs inside the skill.

## Phase Rules

### 0. Intent Alignment

Prefer native agent `ppt_production_alignment`. If unavailable, load `ppt_production_alignment_agent_spec.md`.

This phase uses `codex-deep-interview` principles, but it must adapt questions to project context instead of asking a fixed questionnaire.

Produce `align/ppt_production_brief_v*.md` by default. Optionally produce:

- `align/workflow_runtime_config_v*.yaml`
- `align/user_confirmation_points_v*.md`

Do not skip this phase for a full manuscript-to-PPT run unless the user provides a current production brief or explicitly asks for a narrow downstream-only task.

### 1. Fact Extraction

Prefer native agent `manuscript_fact_extraction`. If unavailable, load `fact_extraction_agent_spec.md`.

Produce:

- `align/fact_ledger_v*.md`
- optionally `align/claim_source_map_v*.md`

The fact ledger is the source of truth for contributions, methods, systems, experiments, limitations, terminology, and QA risks.

### 2. Storyboard

Prefer native agent `ppt_storyboard`. If unavailable, load `agents_storyboard_agent_spec.md`.

Produce:

- `align/PPT_storyboard_v*.md`

Each slide should have one core point, a visual strategy, asset needs, speaking points, estimated time, and QA risk.

### 3. Asset Audit

Prefer native agent `ppt_asset_audit`. If unavailable, load `agents_asset_audit_agent_spec.md`.

Produce:

- `align/PPT_asset_audit_v*.md`
- optionally `align/PPT_asset_manifest_v*.csv`

Every slide should have a reuse, redraw, generate, or omit decision.

### 4. PPTX Automation

Prefer native agent `ppt_template_automation`. If unavailable, load `template_automation_agent_spec.md`.

Produce:

- `generated_pptx_test/<deck>_v*.pptx`
- generation manifest or page plan
- rendered PNGs/contact sheet when possible

Validate slide count, aspect ratio, media embedding, and open/render behavior.

### 5. Figma Layout Polish

Prefer native agent `figma_layout_polish` only when visual polish is requested or needed. If unavailable, load `figma_layout_polish_agent_spec.md`.

Before Figma work:

- Use Figma MCP status from context or run `whoami` if unknown.
- Use CJK-capable fonts for Chinese, defaulting to `Noto Sans SC`.
- Minimize read/export calls.
- If rate-limited, preserve file key/frame id and use cached screenshots or local layout replication.

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

## Final Validation

Before calling the workflow done, verify:

- Production brief exists and records assumptions/open questions.
- Facts, contribution claims, experiment conclusions, and limitations are consistent across artifacts.
- Slide count and timing match the target.
- PPTX opens and renders when a renderer is available.
- Important pages are readable in screenshots.
- Figma limitations, font issues, or rate limits are disclosed.
- Remaining manual polish items are listed.

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
- subagent_policy: <native-when-available|native-required|local-only|ask-first>

Task:
Run the manuscript-to-PPT workflow. Prefer native custom agents when available. Start with `ppt_production_alignment`, save `align/ppt_production_brief_v*.md`, then proceed through fact extraction, storyboard, asset audit, PPTX automation, optional Figma polish, and final validation.
```
