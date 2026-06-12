# Paper Reproduction Result Audit Patterns

Use this reference when comparing noisy ML results, paper tables, generated figures, logs, or partial reproduction evidence.

## Comparison Principles

- Compare only like with like: same dataset version, split, checkpoint, evaluator, metric definition, and preprocessing.
- Normalize before judging: percentages vs fractions, rounded values, macro/micro averages, higher/lower-is-better direction, and table/figure units.
- Record every failed seed, run, or row. Do not hide failures in aggregate summaries.
- Use paper-provided uncertainty when available. If none exists, label any tolerance as inferred.
- Treat smoke/import success as `static_check_only`, not as result reproduction.

## Verdict Pattern

Claim-level verdicts:

- `reproduced`: exact or within stated uncertainty.
- `partially_reproduced`: some comparable metrics match, but not all target conditions are covered.
- `close_outside_tolerance`: near but outside stated or inferred tolerance.
- `not_reproduced`: comparable run contradicts the paper.
- `not_testable`: required artifact or methodological detail is missing.
- `static_check_only`: only repo/import/config checks ran.
- `blocked`: run did not reach comparable results.

Overall verdict must not exceed the weakest important claim needed by the requested scope.

## Statistical Notes

- Multiple seeds are preferred for stochastic training or evaluation.
- If the paper reports confidence intervals, error bars, or standard deviations, preserve the exact interpretation.
- If only one seed is available, say that the audit cannot establish variance.
- For deep RL and similarly high-variance tasks, use especially conservative language unless enough seeds are available.

## Diagnosis Buckets

- Source mismatch.
- Data split/version mismatch.
- Checkpoint mismatch.
- Evaluator or metric mismatch.
- Config or hyperparameter mismatch.
- Random seed variance.
- Hardware/CUDA nondeterminism.
- Dependency drift.
- Missing artifact or license/auth blocker.
- Paper ambiguity.

## Source Notes

- NeurIPS statistical significance and reproducibility guidance: https://neurips.cc/public/guides/PaperChecklist
- How Many Random Seeds? Statistical Power Analysis in Deep RL: https://arxiv.org/abs/1806.08295
- Artifact evaluation tolerance framing: http://jsys.org/artifact_evaluation
- ReproAgent report workflow: https://github.com/hqygtr-prog/repro-agent
- paper-replay verdict pattern from search result: https://github.com/bettyguo/paper-replay
