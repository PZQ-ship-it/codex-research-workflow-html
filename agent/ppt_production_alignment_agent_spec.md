# Agent Spec: PPT Production Alignment v0.2

Status: historical fallback guidance. The current workflow uses `codex-deep-interview` in the main thread for this phase.

## Purpose

Convert an ambiguous manuscript-to-PPT request into a confirmed production brief before fact grounding, storyboard, PPTX automation, or Figma context work starts.

The alignment phase must prevent Codex from guessing audience, duration, template role, Figma policy, editability requirements, or acceptance criteria.

## Required Brief Fields

```yaml
status: confirmed | rough_assumptions_unconfirmed
project_type:
target_duration:
target_page_count:
audience:
language:
template_file:
template_role: required | visual_reference | none
asset_dirs:
output_dir:
figma_context_policy: disabled | optional | required
figma_write_policy: disabled | official-exempt-only | official-write-explicit
figma_context_provider: glips-framelink
figma_write_provider: figma_write
editability_policy: prefer_editable | mixed | allow_whole_page_images
validation_policy:
deliverables:
acceptance_criteria:
human_confirmation_gates:
```

## Figma Migration Policy

The old single `figma_policy` field is deprecated.

Use:

- `figma_context_policy` for GLips/Framelink read-only design context.
- `figma_write_policy` for any official Figma write exception.
- `figma_context_provider` for open-source Figma context reads.
- `figma_write_provider` for official Figma write or exempt tools.

Default:

```yaml
figma_context_policy: optional
figma_write_policy: disabled
figma_context_provider: glips-framelink
figma_write_provider: figma_write
```

Ask the user before enabling any official Figma path. If the user only supplied a Figma link as reference/template context, keep write disabled. If the task can be handled by official exempt tools such as `generate_figma_design`, use `official-exempt-only`; reserve `official-write-explicit` for broader write-to-canvas operations such as `use_figma`, `create_new_file`, `upload_assets`, or `generate_diagram`.

## Confirmation Points

Record checkpoints when relevant:

- `before_fact_grounding`
- `before_storyboard`
- `before_pptx`
- `before_figma_context`
- `before_final_delivery`

## Downstream Handoff

To storyboard:

- confirmed audience, duration, slide count, language
- fact ledger path or source-grounding status
- template and visual constraints
- acceptance criteria

To PPTX automation:

- storyboard path
- asset decisions
- template file and aspect ratio
- editability policy
- output directory
- validation policy

To Figma context/layout repair:

- `figma_context_policy`
- `figma_write_policy`
- `figma_context_provider`
- `figma_write_provider`
- Figma source URL or node-specific URL
- target pages or selection rules
- local asset/download directory
- export/backfill policy
- CJK font policy

## Stop Rule

If critical fields are missing for a full deck run, stop and ask one concise question at a time. Continue with assumptions only when the user explicitly chooses rough-draft mode, and mark the brief as `rough_assumptions_unconfirmed`.
