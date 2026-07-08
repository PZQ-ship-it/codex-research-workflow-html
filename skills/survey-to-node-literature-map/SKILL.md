---
name: survey-to-node-literature-map
description: Convert a survey, tutorial, course note, or literature-review artifact into a compact source-grounded node-paper map and reading path. Use when Codex has a target research direction plus survey/source notes and needs to decide which 1-3 node papers to read next, classify candidate papers as task-def/method-turn/benchmark-dataset/strong-baseline/limitation-reflection, connect choices to professor/contact-group or project context, or create direction/node-paper-graph.md without building a full literature-review pipeline.
---

# Survey To Node Literature Map

Turn a survey into an actionable next-reading map. This skill is intentionally narrow: it selects and explains node papers. It does not perform broad literature search, full PDF digestion, glossary generation, code scouting, reproduction, or final fit judgment.

## Core Contract

Produce a small, evidence-backed map that answers:

- What problem and method structure does this survey imply?
- Which cited or related papers are structural nodes, not just references?
- What should the user read next, in what order, and why?
- Which recommendation is source-stated, Codex-inferred, or still needs checking?

Default output path for file-based runs:

```text
direction/node-paper-graph.md
```

For HKUST(GZ) RA contact-group reading, keep human-facing prose in Chinese by default. Preserve paper titles, method names, datasets, benchmarks, URLs, source IDs, and YAML/JSON keys in English/original form.

## Inputs

Accept any combination of:

- survey HTML, PDF digest, paper notes, or survey URL;
- direction card or topic seed;
- professor/contact-group context;
- existing local candidate papers or manifests;
- constraints such as time budget, open-source-only, or no reproduction.

If no survey-like source exists, first use `paper-review-source-intel` or the parent reading workflow to find one. If a survey PDF is unreadable, use `paper-pdf-to-structured-html` before this skill.

## Workflow

1. Scope the map.
   - Record direction, survey source, local artifact paths, contact group/project context, and non-goals.
   - State whether the map is for first reading, contact material, learning, or reproduction scouting.

2. Extract survey structure.
   - Build a problem tree from the survey's stated taxonomy, section logic, figures/tables, and recurring task definitions.
   - Build a method family tree from method categories, pipelines, system components, or algorithmic families.
   - Mark links as `source-stated`, `Codex-inferred`, or `needs-check`.

3. Recover candidate node papers.
   - Prefer papers named in the survey's taxonomy sections, comparison tables, benchmark tables, historical narrative, or future-challenge sections.
   - Include externally searched recent nodes only when the survey is stale or the task asks for current source refresh.
   - For each candidate, lock at least one canonical source before recommending it.

4. Classify node roles.
   - `task-def`: defines the task/problem setting or benchmark framing.
   - `method-turn`: changes the method family, architecture, optimization, or system design.
   - `benchmark-dataset`: introduces a dataset, metric, leaderboard, or evaluation protocol that later papers depend on.
   - `strong-baseline`: is a comparison anchor, reproducible baseline, or widely used reference point.
   - `limitation-reflection`: exposes failure modes, surveys limitations, or reframes open problems.

5. Rank for next reading.
   - Optimize for the current purpose, not universal citation importance.
   - For RA/contact-group reading, prioritize papers that explain the professor group's direction, support a fit paragraph, or unlock a low-cost first triage.
   - For learning, prioritize prerequisite clarity and high explanatory yield.
   - For reproduction, prioritize code/data/benchmark readiness and small smoke-test feasibility.

6. Write the output.
   - Use `references/output-template.md` when creating `node-paper-graph.md`.
   - Use `references/selection-heuristics.md` for scoring and caveats.
   - Keep the recommendation list small enough to act on.

## Routing

Use other skills only for their own atomic lane:

- `anysearch`: current/public source refresh or discovery.
- `paper-review-source-intel`: canonical paper pages, DOI/arXiv/OpenReview/proceedings, open-access status.
- `paper-pdf-to-structured-html`: convert survey or selected papers into readable HTML.
- `paper-term-glossary-builder`: explain terms that block node selection.
- `professor-direction-mapper`: connect nodes to professor/lab directions.
- `code-model-benchmark-intel`: inspect code, datasets, benchmarks, models, leaderboards.
- `ai-first-paper-reading-orchestrator`: parent workflow when the run also needs source log, direction card, survey matrix, paper triage, learning lane, and human gates.

Do not duplicate those skills' work inside this skill. Link to their outputs.

## Quality Gates

Before calling the map complete, check:

- Each top recommendation has a canonical source or is clearly marked `needs-check`.
- Each top recommendation has a node role and a survey/source anchor.
- The map separates source facts from inference.
- The output recommends 1-3 next papers, not an unranked bibliography.
- Subjective interest, final professor fit, and contact wording remain `pending-human-fit` unless the user explicitly confirmed them.
- Paywalled, private, login-gated, or suspicious sources are not treated as available full text.

## Stop Conditions

Stop and report partial progress when:

- no survey/source artifact is available and search is out of scope;
- the survey is too stale or broad to choose nodes without a current-source refresh;
- candidate papers cannot be source-locked;
- the decision would require private credentials, paywall bypass, large downloads, GPU/API runs, or final human fit.
