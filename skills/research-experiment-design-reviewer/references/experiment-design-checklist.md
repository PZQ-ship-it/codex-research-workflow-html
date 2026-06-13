# Experiment Design Checklist

Use this reference when reviewing empirical experiments, ablation plans, benchmarks, model evaluations, human studies, A/B tests, causal studies, or statistical analysis plans.

## Claim-Evidence Map

For each central claim, require:

- claim wording;
- necessary evidence;
- compared systems or conditions;
- dataset/task/population;
- primary metric;
- minimum success criterion;
- possible falsifying result;
- threat to validity;
- planned analysis or statistical test.

If a claim has no falsifying result, it is probably a narrative claim, not an experiment-ready claim.

## Baselines And Controls

- Strongest known baseline: current SOTA, official baseline, prior paper, production/current system, or accepted benchmark reference.
- Simple baseline: majority, random, heuristic, non-LLM, retrieval-only, prompt-only, no-training, or classical method when relevant.
- Ablated self: proposed method with one component removed or replaced.
- Oracle or upper-bound: human, gold retriever, perfect classifier, or simulated best case when useful.
- Negative control: condition expected not to improve, useful for catching leakage or evaluator bias.

Baselines are unfair when they use weaker data, weaker tuning, stale versions, different preprocessing, different test splits, different inference budgets, or different evaluator scripts without justification.

## Ablation Rules

- Change exactly one factor per ablation unless the interaction is explicitly being tested.
- Keep data split, seed policy, training budget, preprocessing, inference budget, and metric script fixed.
- Name the expected direction before running.
- Include a no-op or negative control when leakage/evaluator bias is plausible.
- Avoid ablations that remove so much functionality that the comparison becomes uninformative.

## Metrics And Statistics

- Define one primary metric before running.
- Separate secondary metrics from guardrail metrics.
- Include confidence intervals, bootstrap, paired tests, randomization tests, or repeated-seed summaries when variance matters.
- Define missing, crashed, timed-out, invalid, or abstained cases before analysis.
- Avoid optimizing on the test set through repeated inspection.
- Report effect size and practical significance, not only p-values or rank changes.

## Benchmark And Evaluation Protocol

- State benchmark version, split, task definition, prompt/template, scoring script, model versions, decoding settings, max tokens, retries, and evaluator model if any.
- Separate simulator, solver, judge, and analyst roles when LLMs are involved.
- Log raw predictions, judge rationales when allowed, metric rows, failure rows, and aggregation scripts.
- Include contamination checks when evaluating pretrained or instruction-tuned models on public benchmarks.
- Define completeness: which rows must finish before aggregate claims are allowed.

## Human Study Or Annotation Protocol

- State participant/annotator criteria, recruitment, consent/IRB needs, task instructions, compensation, quality control, inter-rater agreement, exclusion rules, and privacy controls.
- Predefine sample size or stopping rule.
- Keep raw participant data out of logs unless storage and consent are explicitly approved.
- Separate exploratory qualitative findings from confirmatory statistical claims.

## Review Red Flags

- The design starts with "run everything and see what looks good."
- Baseline choice is weaker than what a reviewer would expect.
- The proposed method receives extra tuning, data, compute, or human filtering.
- Ablations are named but not tied to claims.
- Metrics are chosen after seeing results.
- The plan cannot explain failed or partial runs.
- A single aggregate score hides known hard cases.
- External validity is claimed beyond tested tasks, languages, domains, or populations.

## Useful Output Additions

When reviewing an experiment design, include:

- a claim-evidence table;
- a baseline fairness table;
- a locked experiment matrix;
- a statistics and stopping-rule checklist;
- a reproducibility package checklist.
