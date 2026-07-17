# Gate Contract

Use JSON so deterministic gating has no third-party runtime dependency.

## Commands

```powershell
python scripts\quality_gate.py init --out <run-dir>
python scripts\quality_gate.py reference-mode --run-dir <run-dir>
python scripts\quality_gate.py validate --run-dir <run-dir>
python scripts\quality_gate.py gate --run-dir <run-dir> --out <run-dir>\gate-result.json
```

`reference-mode` runs before reviewers and returns `human_graded`,
`retrieved_provisional`, `retrieve_required`, or
`reference_free_diagnostic`.

## Core Files

`gate-config.json` schema 1.2 freezes absolute and relative policies:

```json
{
  "schema_version": "1.2",
  "absolute_quality_floor": 4.0,
  "dimension_floors": {"intent_fit": 3.5},
  "reference_fallback": {
    "auto_retrieve_when_human_missing": true,
    "min_queries": 2,
    "min_references": 1,
    "max_references": 5,
    "max_snapshot_bytes": 5000000,
    "allowed_mime_types": ["text/plain"],
    "anchor_panel": {
      "preferred_min": 3,
      "preferred_max": 5,
      "required_bands": ["low", "boundary", "high"],
      "min_score_separation": 0.2,
      "allow_one_shot": true
    },
    "provisional_policy": "report_only"
  }
}
```

The existing comparison modes remain `weighted_overall`, `all_dimensions`, and
`hybrid`. `reference_margin`, weights, floors, confidence, calibration, and
dual-review requirements remain versioned policy inputs.

`task-contract.json` is the normative source for the rubric. `rubric.json`
freezes task-specific soft-quality dimensions, their task traces, lane owner,
scale anchors, example audit, and structural-overlap audit. Retrieved mode
stores its run-relative locator and SHA-256 in `reference-set.json`.

`structural-result.json` keeps:

```json
{
  "reviewer": "structural_reviewer",
  "pass": true,
  "critical_failures": [],
  "evidence": [],
  "fixes": []
}
```

`quality-result.json` adds retrieved pairwise evidence:

```json
{
  "reviewer": "quality_judge",
  "scoring_lane": "quality-judge-001",
  "dimension_scores": {},
  "confidence": 0.0,
  "calibration": {"human_anchored": false, "leniency": null, "agreement": {}},
  "evidence": [],
  "reference_comparisons": [
    {
      "reference_id": "ref-001",
      "candidate_first": ["candidate", "candidate", "candidate"],
      "reference_first": ["candidate", "candidate", "candidate"],
      "bias_audit": {
        "verbosity_relation": "similar",
        "format_relation": "none",
        "source_family_overlap": false,
        "judge_family_overlap": "unknown",
        "suspected_confounds": [],
        "unresolved": false
      }
    }
  ],
  "structural_concerns": [],
  "counterexamples": [],
  "revision_actions": []
}
```

Outcomes are `candidate`, `reference`, or `tie`. Arrays must match the frozen
`trials_per_order`. Retrieved reference scores and provenance live in
`reference-set.json`; see `retrieval-reference-contract.md`.

Schema 1.2 intentionally supports exactly one frozen scoring lane. The lane ID
must match `quality-result.json.scoring_lane` and every reference dimension's
`judge_id`. Configure multiple independent lanes only in a future schema that
stores candidate and reference scores per lane.

## Human Compatibility

If a valid `human-reference.json` exists, it takes precedence over retrieved
state. Existing schema `1.0` runs continue to use the original formal gate:

```json
{
  "reference_id": "human-anchor-001",
  "graded_by": "human",
  "grader_count": 2,
  "rubric_version": "1.0",
  "dimension_scores": {},
  "notes": "Independent human scores reconciled before use as a gate."
}
```

## Result Status And Exit Codes

| Status | Meaning | Exit |
|---|---|---:|
| `accepted` | Formal human-calibrated gate passed | 0 |
| `provisional_outperforms_retrieved` | Retrieved frontier passed | 4 |
| `provisional_shortfall` | Absolute floor or stable frontier comparison fell short | 5 |
| `anchored_diagnostic` | Anchors calibrated the scale, but no eligible frontier existed | 6 |
| `needs_human` | Evidence, consistency, or calibration insufficient | 2 |
| `blocked` | Structural or formal human gate failure | 2 |
| invalid input | Schema, hash, or provenance failure | 3 |

`gate-result.json` includes hashes plus `reference_mode`, `reference_tiers`,
`reference_set_hash`, absolute-floor evidence, anchor-panel coverage and
ordering, frontier IDs, `comparison_pass`, `order_consistent`, per-frontier
comparison summaries, and `provisional_reason` when applicable.

Schema 1.1 retrieved runs remain supported with their original all-frontier
contract. New runs initialize as schema 1.2.
