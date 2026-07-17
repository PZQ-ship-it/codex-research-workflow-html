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

## Retrieved fallback

- Retrieval can supply a comparator and make the quality review actionable; it
  cannot manufacture human calibration.
- Derive gating dimensions from the task contract. Use examples to audit and
  calibrate the rubric, not to impose untraceable style preferences.
- Prefer low/boundary/high few-shot anchors. Verify their score ranges are
  monotonic; do not let low anchors lower the absolute quality floor.
- Keep calibration anchors separate from the high, verified challenge
  frontier. A self-labeled band is diagnostic only.
- Audit the complete candidate pool for selector bias and benchmark shopping.
- Separate selector and judge. Blind the selector to candidate content.
- Require dimension-scoped verification for every critical dimension before a
  retrieved reference may produce a provisional result.
- Freeze query, pool, reference, policy, rubric, judge, and content hashes
  across revisions.
- Treat order flips, ties, unresolved conflicts, and low confidence as
  `needs_human`; do not average them away.
- Use repeated single-artifact calls only for stability. Estimate confidence
  intervals across artifact instances in a pre-registered pilot.

## Hostile checks

Run these in `audit` mode:

1. Swap A/B order in pairwise comparisons and compare verdicts.
2. Add irrelevant verbosity while preserving substance.
3. Rewrite the same artifact in a more authoritative style.
4. Compare outputs from the same generator family and an independent family.
5. Repeat identical calls and record score variance.
6. Create a structurally complete but intent-wrong artifact.
7. Create a concise correct artifact to test length bias.
8. Exclude the highest-ranked eligible search result and verify that the ledger
   exposes the selector manipulation.
9. Add prompt-like instructions to a frozen reference and verify they remain
   inert quoted data.
10. Change a query, snapshot, or reference hash and verify reuse is rejected.
11. Replace a high frontier with a low anchor and verify the absolute gate does
    not become easier.
12. Inject a schema or required-section check into the quality rubric and
    verify the lane-ownership audit rejects it.

Any material flip must be recorded as a gate risk. Do not hide it by averaging
away the failure. Escalate low-confidence or high-variance cases to a human.
