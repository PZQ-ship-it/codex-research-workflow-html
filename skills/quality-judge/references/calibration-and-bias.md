# Calibration And Bias

## Human anchor

- Use 3-5 unambiguous reference cases for the first trusted gate.
- Have two humans score independently when the decision is consequential; keep
  both raw scores and the reconciled reference.
- Record `graded_by`, `grader_count`, rubric version, date, and rationale.
- Recalibrate after a judge model, prompt, rubric, task distribution, or
  generator changes materially.

## Calibration signals

- For ordinal scores, track Spearman correlation against human scores.
- For categorical pass/fail, track Cohen's kappa or an equivalent agreement
  measure.
- Track leniency as `mean(judge_normalized - human_normalized)`. Treat absolute
  leniency above `0.25` across two runs as recalibration-required.
- A single reference cannot establish agreement. It is a provisional anchor,
  not evidence that the judge is calibrated.

## Hostile checks

Run these in `audit` mode:

1. Swap A/B order in pairwise comparisons and compare verdicts.
2. Add irrelevant verbosity while preserving substance.
3. Rewrite the same artifact in a more authoritative style.
4. Compare outputs from the same generator family and an independent family.
5. Repeat identical calls and record score variance.
6. Create a structurally complete but intent-wrong artifact.
7. Create a concise correct artifact to test length bias.

Any material flip must be recorded as a gate risk. Do not hide it by averaging
away the failure. Escalate low-confidence or high-variance cases to a human.
