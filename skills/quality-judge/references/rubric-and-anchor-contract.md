# Rubric And Anchor Contract

## Authority Order

1. Freeze `task-contract.json` from the user goal, audience, use case,
   constraints, non-goals, and desired quality outcomes.
2. Draft rubric R0 from the task contract without candidate content.
3. Audit human or retrieved examples for missing dimensions and weak scale
   anchors. Examples may propose changes; they do not become normative by
   themselves.
4. Admit a proposal only when it traces to a task outcome, belongs to the
   quality lane, and is not a deterministic structural check.
5. Freeze rubric R1, update its hashes, then rescore every anchor and candidate.

A retrieved-example-only dimension cannot gate. Put unsupported discoveries in
`generation.example_audit.dimension_proposals` for human review instead.

## Quality Dimension Admission

Every configured dimension must record:

- `origin`: `task_contract`, `human_example`, or `mixed`;
- `lane_owner`: `quality_judge`;
- non-empty `task_trace`;
- `structural_overlap_check: passed`;
- `gating: true`.

The structural lane owns required artifacts, schema compliance, factual and
citation verification, safety, test execution, and reproducibility. The quality
lane owns intent fit, judgment and tradeoffs, coherence, reader effort,
usability, decision value, and finishedness.

Do not show the structural verdict to the quality judge before scoring. A hard
issue noticed by the quality lane goes into `structural_concerns`; it does not
receive a second quality-score penalty.

## Reference Roles

- `calibration_anchor`: teaches or tests the score scale. It never lowers the
  task-derived absolute floor and never creates an outperformance result.
- `challenge_frontier`: a high-quality comparable reference the candidate must
  beat. It must be `retrieved_verified`, use the `high` band, and have band
  provenance other than `self_labeled`.

One high-quality reference may have both roles. Record `quality_band` as
`low`, `boundary`, or `high`, and `band_provenance` as `human`,
`objective_metric`, `independent_judge`, or `self_labeled`.

Self-labeled anchors are diagnostic only. A self-labeled frontier is
ineligible.

## Few-Shot Panel

Prefer 3-5 anchors spanning low, boundary, and high bands. One-shot remains a
valid degraded diagnostic when the frozen config permits it. Validate that
band score ranges are monotonic with the configured minimum separation.

- Incomplete band coverage adds `few_shot_anchor_coverage_incomplete`.
- A non-monotonic panel routes to `needs_human`.
- An anchor-only run may return `anchored_diagnostic`.

## Gate Separation

The candidate must always satisfy the task-derived absolute contract:

```text
candidate overall >= absolute_quality_floor
AND every candidate dimension >= its dimension_floor
```

Only after that check may a challenge frontier add the relative contract:

```text
candidate overall >= frontier reference + margin
AND no critical dimension trails the reference
AND both A/B orders are unanimous
```

A low or boundary anchor can reveal score separation and trigger revision, but
cannot make the relative gate easier.
