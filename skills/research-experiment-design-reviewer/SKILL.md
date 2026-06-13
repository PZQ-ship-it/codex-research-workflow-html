---
name: research-experiment-design-reviewer
description: Use when Codex should critique a research experiment, ML training plan, evaluation protocol, ablation plan, benchmark design, human-study protocol, or statistical analysis plan before results are trusted. Review plans, papers, notebooks, configs, READMEs, experiment manifests, logs, or inferred designs for hypothesis clarity, claim-evidence fit, data splits and leakage, baseline fairness, training setup, ablation isolation, metrics, statistics, compute budget, reproducibility, ethics, and failure modes. If no experiment design exists, use codex-deep-interview to elicit the user's research/training intent, or ask permission to infer a draft design from local code/configs/results and confirm it before reviewing. Use anysearch for external standards, current benchmark norms, official docs, recent baseline expectations, venue checklists, or domain-specific methodological guidance.
---

# Research Experiment Design Reviewer

Critique the design of empirical research before implementation, training, expensive runs, paper claims, or benchmark conclusions depend on it. This skill is for training and experiment design quality, not ordinary software architecture review.

## Review Modes

1. Existing design artifact.
   - Use when the user provides or points to experiment plans, training configs, benchmark specs, RQ plans, paper drafts, notebooks, scripts, manifests, `wandb`/MLflow summaries, protocol docs, or evaluation rubrics.
   - Review the artifact after reading only the local context needed to understand task, data, method, baselines, metrics, and constraints.

2. No design artifact, user has research intent.
   - Use `$codex-deep-interview` to clarify the research or training intent before judging it.
   - Ask one concise question at a time until the claim, task, data, candidate methods, constraints, success criteria, and non-goals are clear enough.
   - Produce a short experiment-design brief, then review that brief.

3. No design artifact, implementation/results exist.
   - Do not silently treat existing code, configs, or results as the intended design.
   - Ask permission before reverse-engineering a design draft from implementation.
   - If approved, inspect local code/configs/docs/logs, summarize the inferred design, mark inferred parts clearly, and ask the user to confirm or correct it before issuing the final review.

## Workflow

1. Locate experiment evidence.
   - Search likely files first: `README*`, `EXPERIMENT*`, `EVAL*`, `BENCHMARK*`, `TRAIN*`, `CONFIG*`, `METHOD*`, `DESIGN*`, `docs/**`, `configs/**`, `experiments/**`, `scripts/**`, `notebooks/**`, `results/**`, `wandb/**`, `mlruns/**`, and paper/proposal drafts.
   - Keep observed facts, inferred intent, and user-stated goals separate.

2. Classify the design.
   - ML training or fine-tuning plan: read `references/training-design-checklist.md`.
   - Empirical experiment, ablation, benchmark, A/B test, user study, or statistical evaluation: read `references/experiment-design-checklist.md`.
   - If external methodological norms matter, read `references/source-routing.md` before using `$anysearch`.

3. Build the design-under-review.
   - Summarize the research question, central claim, task, data, method, baselines, ablations, metrics, statistical plan, resource budget, reproducibility plan, risks, and expected decision from the result.
   - Mark missing or inferred sections explicitly.

4. Route uncertainty and external evidence.
   - Use local files for project-specific facts.
   - Use `$uncertainty-router` when it is unclear whether to inspect, search, test, ask, or assume.
   - Use `$anysearch` when the review depends on current or external facts: official benchmark versions, venue checklists, accepted reporting standards, library defaults, recent baseline expectations, dataset licenses, model/provider limits, or domain-specific statistical guidance.
   - Prefer official docs, venue pages, standards, primary papers, benchmark repos, dataset/model cards, and reproducibility checklists over generic blogs.

5. Review the core dimensions.
   - Claim-evidence fit: Does each intended claim have the smallest strong experiment that could support or falsify it?
   - Data validity: Are data source, split, leakage controls, preprocessing, contamination checks, annotation/QC, and domain shift handled?
   - Baselines and controls: Are comparisons fair, current, reproducible, tuned with comparable budgets, and aligned with the claim?
   - Training/evaluation protocol: Are configs, seeds, hardware, checkpointing, early stopping, evaluator boundaries, and failure handling explicit?
   - Ablations: Does each ablation isolate one factor and preserve all other settings?
   - Metrics and statistics: Are primary, secondary, guardrail metrics and statistical tests defined before running?
   - Feasibility: Is compute, wall time, data access, cost, sample size, and human review effort realistic?
   - Reproducibility: Could another agent or researcher rerun the study and know which results are complete, failed, or excluded?
   - Ethics and safety: Are privacy, consent, license, safety, and misuse concerns handled when relevant?

6. Classify findings.
   - Blocker: The design cannot support its claim, has likely leakage/confounding, uses invalid comparisons, or has unacceptable ethical/legal risk.
   - Major: Important ambiguity, missing baseline/control, weak statistic, underpowered design, unsupported assumption, or costly feasibility risk.
   - Minor: Clarity, documentation, naming, reporting, or polish issue.
   - Observation: Useful strength or context worth preserving.

7. Recommend next action.
   - Prefer concrete design edits, experiment matrix changes, or verification gates over vague advice.
   - If the design is not ready, say what must be decided before running.
   - If it is ready enough, state the conditions for proceeding and the completion checks before trusting results.
   - Route to `$resilient-llm-benchmark` when the next step is a large, resumable LLM evaluation run.
   - Route to `$academic-paper-reviewer` when the user wants review of a finished manuscript rather than pre-run design.
   - Route to `$decision-record-writer` when a reviewed methodological choice should become durable.

## Output Shape

Use this structure unless the user asks otherwise:

- Design under review
- Evidence inspected
- Overall assessment
- Strengths to preserve
- Findings by severity
- External evidence used, if any
- Required design changes
- Minimum experiment matrix or protocol edits
- Open questions
- Proceed / revise / stop recommendation

For each finding, include:

`Severity | Design area | Issue | Why it matters | Evidence | Recommendation`

## Boundaries

- Do not run expensive training, benchmarks, or human-study collection as part of this skill.
- Do not pretend an inferred experiment design is user-approved.
- Do not treat high accuracy or one successful run as valid evidence without checking protocol quality.
- Do not invent baselines, metrics, datasets, sample sizes, paper claims, statistical results, or ethical approvals.
- Do not reduce the review to implementation style; use code/configs/logs only as evidence for the experiment design.
- Do not require external search for ordinary local critique, but search when current external norms affect the verdict.

## Source-Aware Notes

This skill's shape is inspired by public experiment-design skills, ML reproducibility checklists, statistical experiment-design workflows, and venue paper checklists. Use those as review heuristics, not as rigid doctrine.
