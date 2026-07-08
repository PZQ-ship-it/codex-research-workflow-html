---
name: ai-first-paper-reading-orchestrator
description: Run an AI-first paper-reading scout for AI/ML directions, professor contact groups, papers, or research topics. Use when Codex should orchestrate group-aware source recon, survey taxonomy, node-paper mapping, paper triage, learning-assist routing, and pending human gates without hand-writing long prompts.
---

# AI-first Paper Reading Orchestrator

Use this skill to run the AI-owned front half of the paper-reading workflow. The point is to stop asking the human to fill factual direction cards before AI has searched, mapped, and triaged.

## Mode Selection

Choose the lightest mode that fits the seed:

- Single-Seed Mode: use for one direction, professor, paper, or rough research topic.
- Contact-Group Mode: use when a professor contact-group JSON, group id, group title, or several same-batch professors are provided.
- Learning Support Mode: use when the user asks how to learn while reading papers, what to notice in a paper, which skills help with concepts, or Q&A / teach-back support.

Read `references/contact-group-learning-routing.md` when Contact-Group Mode or Learning Support Mode is active.

## Default Contract

AI owns:

- seed normalization and search queries;
- source search log and AI-use log;
- direction-card v0;
- survey / tutorial / course-note scout;
- taxonomy extraction;
- node-paper candidate map;
- first paper triage recommendation;
- group-aware professor coverage matrix when a contact group is provided;
- learning-support routing and micro-drill selection;
- repro-scout questions and risk forecast;
- pending human questions.

Human owns:

- objective priority and subjective fit;
- reading budget;
- high-risk resource approvals;
- quiz / teach-back;
- final `continue / split-and-continue / pause`.

Never fill human subjective fields as if confirmed. Use `pending-human-fit`, `pending-teachback`, or `pending-risk-approval`.

## Required Context

Before running, inspect local context when available:

- `D:\ai-paper-reading-workflow\docs\workflow.md`
- `D:\ai-paper-reading-workflow\docs\execution-guide.md`
- `D:\ai-paper-reading-workflow\templates\`
- contact-group JSON such as `D:\todo\projects\hkust-gz-ra-academic-fit\career-maps\professor-contact-groups-2026-07-08.json`
- project task or run directory in `D:\todo` / `D:\hkust-gz-ra-paper-reading`

If the workflow repo is unavailable, still follow this skill's contract and create equivalent Markdown outputs.

## Workflow

1. Seed Capture
   - Accept a direction, professor, paper, venue, or rough goal.
   - Produce 3-8 search queries and assumptions.
   - Do not ask the human for full taxonomy or task definitions.

2. AI Direction Recon
   - Use `anysearch` or official/public sources when current or external facts matter.
   - Prefer official pages, proceedings, arXiv/DOI/OpenReview, course pages, benchmark/repo pages.
   - Write or draft `source-search-log.md`, `ai-use-log.md`, and `direction-card.md`.

3. Direction Intake Gate
   - Ask only objective-priority, subjective-fit, reading-budget, and risk-boundary questions.
   - If the user is not present, mark these fields pending and continue AI evidence work.

4. Contact-Group Mode
   - Extract group id, title, professors, current mainlines, coverage directions, reading goal, and contact logic.
   - Choose the anchor direction by contact value, market value, and material readiness.
   - Do not read the whole group by default; produce a bounded group-aware run for one anchor direction, one survey/tutorial, and 1-3 node papers.
   - Draft evidence-backed per-professor fit notes, but keep final contact wording and subjective fit as `pending-human-fit`.

5. Survey Taxonomy
   - Find 1-3 survey/tutorial/course-note sources when available.
   - Extract candidate taxonomy axes, open problems, benchmark/data/metric families, terms, and node-paper leads.

6. Node Paper Map
   - Classify candidates as `task-def`, `method-turn`, `benchmark-dataset`, `strong-baseline`, or `limitation-reflection`.
   - Include AI rationale, source/location, confidence, and reading priority.

7. Paper Triage
   - For the first recommended paper, do source-lock and 5-15 minute triage.
   - Output AI recommendation: `continue / skip / hold / need-background`.
   - Human only confirms attention allocation or override.

8. Learning Support Mode / Human Learning Lane
   - While AI scout runs, offer a 5-30 minute guided-learning drill:
     - title/abstract triage;
     - claim-to-evidence;
     - 3-5 minute teach-back;
     - repo README repro intuition.
   - Route concept prerequisites to `paper-term-glossary-builder`, paper Q&A to `guided-learning`, paper digest needs to `paper-pdf-to-structured-html`, source locking to `paper-review-source-intel`, and code / benchmark intuition to `code-model-benchmark-intel`.
   - Record learning status separately from AI evidence.

9. Fit Draft
   - Draft AI recommendation and pending human questions.
   - Do not claim a final direction decision without human confirmation.

## Output Shape

For a normal scout, produce:

- `Run summary`
- `AI evidence packet`
- `Source log`
- `Contact-group context` when applicable
- `Direction card v0`
- `Survey taxonomy`
- `Node paper recommendations`
- `First-paper triage recommendation`
- `Human learning lane`
- `Learning-support routing`
- `Pending human gates`
- `Next 1-3 actions`

When writing files, prefer the templates in `D:\ai-paper-reading-workflow\templates`. For long details, see `references/output-contract.md`.

## Safety

- Do not save secrets, cookies, tokens, API keys, private screenshots, or paywalled full text.
- Do not start large downloads, GPU/API runs, authenticated browsing, contact with external people, or long reproduction without explicit human approval.
- Search snippets are leads, not final evidence; lock canonical sources before making claims.
