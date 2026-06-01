# PPT Page Worker Contract

Use this reference when preparing page jobs or instructing `ppt_page_build`.

## Purpose

The page worker converts exactly one approved slide plan into one editable slide output. It is a narrow builder, not a storyteller, reviewer, source extractor, or deck assembler.

## Required Input

Each worker receives one `page_request.json`.

Required top-level fields:

- `schema`: use `ppt_page_request.v1`
- `run_id`: deck build run identifier
- `slide_id`: stable storyboard slide ID, such as `S07`
- `slide_number`: 1-based output slide number
- `slide_kind`: `main`, `backup`, `separator`, `cover`, or `appendix`
- `action_title`: confirmed action title
- `stage_status`: must be `confirmed`
- `source_indices`: source or fact IDs required by this slide
- `claim_indices`: claim IDs allowed on this slide
- `asset_indices`: asset IDs allowed on this slide
- `layout`: template/layout constraints
- `allowed_inputs`: exact files or directories the worker may read
- `output_dir`: per-slide output directory
- `acceptance`: page-level checklist
- `forbidden`: behavior the worker must avoid

Optional fields:

- `speaker_note_indices`
- `qa_backup_indices`
- `generated_visual_indices`
- `fallback_policy`
- `known_risks`

## Required Output

Write all outputs under the provided per-slide `output_dir`.

Required files:

- `page_result.json`
- `page_validation.json`

At least one editable slide representation:

- `slide_fragment.pptx`
- `slide_instructions.json`

Recommended file:

- `preview.png`, when a renderer is available without advancing to render QA

## Output Status

`page_result.json` must include:

```json
{
  "schema": "ppt_page_result.v1",
  "run_id": "20260601-example",
  "slide_id": "S07",
  "slide_number": 7,
  "status": "done",
  "outputs": {
    "slide_fragment": "pages/slide_007/slide_fragment.pptx",
    "slide_instructions": "pages/slide_007/slide_instructions.json",
    "preview": "pages/slide_007/preview.png"
  },
  "inputs_used": {
    "source_indices": ["F021"],
    "claim_indices": ["C012"],
    "asset_indices": ["A003"]
  },
  "known_defects": [],
  "repair_notes": [],
  "next_owner": "deck_scheduler"
}
```

Allowed statuses:

- `done`
- `needs_repair`
- `blocked`
- `failed`

## Boundaries

The page worker must:

- build exactly one slide
- preserve editable text and objects whenever practical
- use only the provided source, claim, asset, note, and layout indices
- report missing or ambiguous input instead of guessing
- keep generated images marked as generated, not as source evidence
- return page-level evidence even when blocked

The page worker must not:

- change slide count, slide order, or narrative arc
- perform new manuscript extraction
- invent claims, metrics, citations, or visual evidence
- run whole-deck assembly
- run final render QA
- spawn child agents
- overwrite upstream alignment artifacts

## Dispatch Prompt Shape

Use this compact shape when dispatching a page worker:

```text
You are `ppt_page_build`.

Task:
Build exactly one editable slide from:
<path-to-page_request.json>

Rules:
- Read only the allowed inputs listed in the page request.
- Use only the listed source/claim/asset indices.
- Write outputs only under the request's output_dir.
- Return page_result.json, page_validation.json, and either slide_fragment.pptx or slide_instructions.json.
- If anything required is missing, write a blocked page_result.json instead of guessing.
```

