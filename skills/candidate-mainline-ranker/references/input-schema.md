# Candidate Mainline Ranker Input Schema

Use JSON for deterministic scoring.

```json
{
  "metadata": {
    "dataset_name": "hkust-gz-ra-candidates",
    "date": "2026-06-24",
    "notes": "Current mainlines only unless stated otherwise."
  },
  "records": [
    {
      "professor": "Yongqi Zhang",
      "pool": "primary",
      "candidate_priority": "P1",
      "source": "projects/hkust-gz-ra-academic-fit/direction-map/zhang-yongqi.md",
      "mainlines": [
        {
          "label": "RAG and LLM agents",
          "raw_label": "RAG / LLM agents / multimodal reasoning",
          "rank": 1,
          "confidence": "medium",
          "evidence_status": "sampled",
          "notes": "Current mainline inferred from recent homepage and papers."
        }
      ]
    }
  ]
}
```

Required fields:

- `records[].professor`
- `records[].pool`
- `records[].mainlines[].label`
- `records[].mainlines[].rank`

Recommended fields:

- `candidate_priority`
- `source`
- `raw_label`
- `confidence`
- `evidence_status`
- `notes`

Allowed values:

- `pool`: `primary`, `extended`, `historical`
- `candidate_priority`: `P1`, `P2`, `P3`, `E1`, `E2`, `E3`, `unknown`
- `confidence`: `high`, `medium`, `low`
- `evidence_status`: `complete`, `sampled`, `weak`, `stale`, `unknown`
