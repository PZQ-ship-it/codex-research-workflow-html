# Paper Reproduction Claim Mapping Patterns

Use this reference when the paper has many claims, ambiguous experiment descriptions, or a user asks for a rigorous reproduction plan.

## Patterns Distilled From Current Practice

- NeurIPS checklist guidance treats claims, limitations, experimental reproducibility, open access to code/data, experimental details, statistical significance, compute, licenses, and released assets as separate reporting surfaces. Reflect that separation in the claim ledger.
- Papers with Code code completeness guidance highlights dependencies, training code, evaluation code, pretrained models, and a README table with precise commands. Use these as expected downstream artifact slots.
- ML reproducibility checklists emphasize algorithms/models, assumptions, hyperparameters, seeds, data splits, compute, and uncertainty. Do not hide missing values.
- Reproduction-agent workflows typically start by extracting the main experiment, checking paper-repo consistency, choosing a minimal dataset subset, and then generating a smoke/main experiment plan.

## Claim Types

- `empirical_main`: headline numerical result, SOTA, benchmark, win rate, efficiency, scaling, safety/eval claim.
- `empirical_support`: ablation, robustness, sensitivity, transfer, qualitative examples, case study.
- `method_or_theory`: architecture, algorithm, theorem, proof, complexity, assumption, design claim.
- `artifact`: released dataset, model, code, benchmark, evaluator, demo, checkpoint, or tool.

## Required Fields Per Experiment

- `dataset`: name, config, version, split, preprocessing.
- `metric`: exact name, direction, unit, aggregation, rounding.
- `reported_value`: scalar, interval, table row, or figure reference.
- `baseline`: comparator, implementation source, checkpoint if applicable.
- `hyperparameters`: important settings and search/selection method.
- `seeds_or_repeats`: exact seed list, count, or "not reported".
- `compute`: accelerator, memory, runtime, cloud/local, total budget if reported.
- `entrypoint_hint`: script, notebook, README command, or "not reported".
- `reproduction_priority`: `minimal`, `main`, `ablation`, `full`, or `defer`.

## Minimal Target Heuristic

Prefer targets in this order:

1. Evaluation of an official pretrained model/checkpoint on a small public split.
2. One small dataset/result row backing the headline claim.
3. One ablation that is cheap and diagnostic.
4. One-epoch or tiny-subset training only if evaluation is impossible.
5. Static artifact check when no run is currently possible.

## Source Notes

- NeurIPS Paper Checklist Guidelines: https://neurips.cc/public/guides/PaperChecklist
- Papers with Code releasing research code: https://github.com/paperswithcode/releasing-research-code
- ML Reproducibility Checklist v2.0: https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf
- ReproAgent workflow pattern: https://github.com/hqygtr-prog/repro-agent
