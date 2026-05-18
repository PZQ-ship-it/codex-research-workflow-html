---
name: paper-pdf-to-structured-html
description: Convert academic research PDFs into structured, highly readable standalone HTML digests with important figures, captions, paper-type detection, and type-specific treatment for survey/review papers, algorithm/method papers, empirical benchmark papers, and system papers. Use when Codex is asked to read, summarize, transform, or build HTML from PDF papers, arXiv PDFs, conference papers, surveys, literature reviews, or research reports, especially when the output should preserve taxonomy diagrams, comparison tables, datasets, metrics, seminal papers, algorithms, experiments, challenges, future directions, or selected branches for deeper second-pass explanation.
---

# Paper PDF To Structured HTML

## Overview

Use this skill to turn a research paper PDF into a navigable HTML reading artifact, not a flat summary. Preserve the paper's structure, extract or render important figures, classify the paper type, and choose a reading template that matches the paper's role.

## Workflow

1. Create a work directory for the paper:
   - `output/paper-html/<paper-slug>/`
   - `assets/` for extracted figures and page renders;
   - `manifest.json` for extraction metadata;
   - `<paper-slug>.html` for the final artifact.
2. Inspect the PDF with `scripts/inspect_paper_pdf.py` when possible:
   - extract title-like metadata, outline, per-page text, candidate captions, references, and embedded images;
   - render figure-heavy pages if embedded image extraction is incomplete.
3. Classify the paper type:
   - survey/review;
   - algorithm/method;
   - empirical/benchmark;
   - system/tool/dataset;
   - mixed or unclear.
4. Read the matching reference before writing:
   - survey/review: `references/survey-reading-workflow.md`;
   - algorithm/method or empirical papers: `references/algorithm-method-workflow.md`;
   - output rules for all types: `references/html-output-rules.md`.
5. Select important visual assets:
   - include taxonomy diagrams, architecture/method overview figures, algorithm flow diagrams, comparison tables, main result plots, dataset/metric tables, and challenge/future-direction diagrams;
   - prefer extracted embedded images when sharp;
   - fall back to page crops or full-page renders when the figure cannot be isolated cleanly;
   - always include the source page and caption/provenance near the image.
6. Generate standalone HTML from `assets/paper-digest-template.html` or the repo's existing HTML note style.
7. Validate the HTML visually with Playwright or browser screenshots when layout quality matters. Check broken images, clipped tables, figure readability, mobile width, and print behavior.

## Type-Specific Output

For survey/review papers, build the HTML around:

- boundary from title and abstract;
- contributions and article structure from the introduction;
- taxonomy tree as the central navigation object;
- branch-by-branch comparison;
- comparison tables, datasets, and evaluation metrics;
- frequently cited foundational papers;
- challenges and future directions;
- optional second-pass branch deep dives requested by the user.

For algorithm/method papers, build the HTML around:

- problem setting and assumptions;
- method overview and architecture;
- core algorithm, objective, or pipeline;
- novelty versus prior work;
- experimental setup, datasets, metrics, baselines, and ablations;
- main results and failure cases;
- reusable implementation notes.

For empirical benchmark, system, or dataset papers, adapt the same structure around tasks, evaluation protocol, system components, dataset construction, limitations, and reproducibility.

## Second-Pass Branch Deepening

When the user has already read the initial HTML and asks about specific branches such as `[branch A, branch B]`, generate a focused follow-up HTML section or companion page:

- restate where each branch sits in the taxonomy;
- explain its core idea, representative methods, strengths, weaknesses, datasets, metrics, and open problems;
- include the relevant figures/tables again if they are needed for understanding;
- link back to the original taxonomy and source pages.

## Guardrails

- Do not invent citations, benchmark numbers, datasets, or figure meanings. Mark uncertain extraction results as `needs manual check`.
- Do not treat OCR/extracted text as layout truth. Render the relevant PDF pages when figures, tables, formulas, or multi-column structure matter.
- Do not include every extracted image. Curate images for reading value and record why each one was included.
- Do not flatten a survey into a generic summary. Preserve the taxonomy and comparison structure.
- Do not flatten an algorithm paper into background prose. Preserve the method pipeline, assumptions, experiments, and ablations.
- Keep the final HTML readable from disk without a build step.

## Resources

- `scripts/inspect_paper_pdf.py`: extract text, candidate captions, references, outlines, and embedded images into a manifest.
- `assets/paper-digest-template.html`: standalone HTML skeleton for the final digest.
- `references/survey-reading-workflow.md`: four-stage survey reading workflow and branch deepening pattern.
- `references/algorithm-method-workflow.md`: method/algorithm/benchmark paper structure.
- `references/html-output-rules.md`: required sections, figure handling, and validation checks.

## Common Commands

```bash
python skills/paper-pdf-to-structured-html/scripts/inspect_paper_pdf.py paper.pdf --out output/paper-html/paper-slug
```

Install missing optional dependencies only when extraction requires them: `pymupdf`, `pdfplumber`, `pypdf`, and Poppler utilities for page rendering.
