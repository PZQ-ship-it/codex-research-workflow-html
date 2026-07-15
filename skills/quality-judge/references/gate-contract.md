# Gate Contract

Use JSON so the deterministic gate has no third-party runtime dependency.

## `gate-config.json`

```json
{
  "schema_version": "1.0",
  "rubric_version": "1.0",
  "dimensions": ["intent_fit", "correctness", "completeness", "usability"],
  "weights": {"intent_fit": 0.3, "correctness": 0.3, "completeness": 0.2, "usability": 0.2},
  "scale": {"min": 1, "max": 5},
  "comparison_mode": "hybrid",
  "reference_margin": 0.2,
  "critical_dimensions": ["intent_fit", "correctness"],
  "critical_floor": 3.0,
  "min_confidence": 0.8,
  "require_human_reference": true,
  "require_calibration": true,
  "max_abs_leniency": 0.25,
  "require_quality_evidence": true,
  "require_both_reviewers": true
}
```

`comparison_mode` is one of:

- `weighted_overall`: weighted candidate score must exceed weighted reference
  score plus `reference_margin`;
- `all_dimensions`: every configured dimension must exceed its reference by the
  margin;
- `hybrid`: weighted overall comparison plus every critical dimension floor.

## `human-reference.json`

```json
{
  "reference_id": "human-anchor-001",
  "graded_by": "human",
  "grader_count": 2,
  "rubric_version": "1.0",
  "dimension_scores": {"intent_fit": 4.0, "correctness": 4.5, "completeness": 3.5, "usability": 4.0},
  "notes": "Independent human scores reconciled before use as a gate."
}
```

`graded_by` must be `human` for a blocking gate. `model`, `claude`, or
`synthetic` references may be retained for smoke tests but must cause
`needs_human` when `require_human_reference` is true.

## `structural-result.json`

```json
{
  "reviewer": "structural_reviewer",
  "pass": true,
  "critical_failures": [],
  "evidence": [{"claim": "required artifact exists", "locator": "artifact/index.html"}],
  "fixes": []
}
```

## `quality-result.json`

```json
{
  "reviewer": "quality_judge",
  "dimension_scores": {"intent_fit": 4.5, "correctness": 4.5, "completeness": 4.0, "usability": 4.2},
  "confidence": 0.86,
  "calibration": {"human_anchored": true, "leniency": 0.05, "agreement": {"spearman": 0.82}},
  "evidence": [{"dimension": "intent_fit", "locator": "artifact/summary.md", "claim": "covers the stated decision"}],
  "counterexamples": ["A polished section still omits the requested boundary."],
  "revision_actions": ["Add the missing boundary and re-run the same rubric."]
}
```

## `gate-result.json`

The script emits `status` in `{accepted, blocked, needs_human}`, scores, input
SHA-256 hashes, the comparison basis, and a flat `reasons` list. `accepted` is
valid only when the structural result passes with no critical failures, the
quality result passes every configured check, and required quality evidence is
present.
