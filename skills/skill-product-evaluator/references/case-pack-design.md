# Case Pack Design

Use this reference before writing `product_cases.csv`.

## Minimum Pack

Create 8-20 realistic cases:

- 3-5 direct positive cases;
- 2-4 implicit natural-language trigger cases;
- 2-4 negative controls for adjacent skills;
- 1-3 missing-evidence, confirmation, privacy, safety, credential, or cost gates;
- 1-3 benchmark-inspired product-quality cases.

## Required Columns

```csv
id,should_trigger,prompt,expected_behavior,expected_artifacts,benchmark_sources,judge_focus,run_source,notes
```

`run_source` values:

- `existing_final`: reuse artifacts from `artifacts/final/<id>.*`;
- `new_product_run`: run the case into `artifacts/product-final/<id>.*`;
- `manual_artifact`: artifact was supplied or generated outside the normal run pattern;
- `not_run`: planned case only.

## Case Quality

Good cases:

- sound like real user requests;
- include enough facts to judge output quality;
- test the skill's product promise, not only its trigger;
- specify expected behavior, not a hidden exact answer;
- include negative controls for adjacent skills;
- include edge cases that a good product must handle gracefully.

Avoid leaking the expected score or diagnosis into the prompt.

