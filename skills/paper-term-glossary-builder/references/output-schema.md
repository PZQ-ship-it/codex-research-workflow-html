# Glossary Output Schema

Use this reference when creating a durable `glossary.md`, `glossary.html`, or `glossary-sources.json`.

## Markdown Structure

```markdown
# Paper Term Glossary: <paper title>

Status: draft | verified | needs-review
Source paper: <path or title>
Generated: <date>
Audience: beginner entering <field>
Recursion depth: <number>

## Reading Orientation

<How to use this glossary and what the paper's terminology landscape looks like.>

## Must-Know Terms

### <Term>

- Plain meaning: <beginner-friendly definition>
- In this paper: <paper-specific role or meaning>
- Why it matters: <what becomes readable once this term is understood>
- First / strongest occurrence: <section/page/heading/caption>
- Prerequisites: <linked or named terms>
- Related / contrast terms: <terms>
- Confidence: paper | external-confirmed | external-disambiguated | uncertain
- Sources: <paper location plus external links if used>

#### Nested prerequisites

- <Nested term>: <short explanation>
  - <Second-level nested term>: <short explanation>

## Helpful Terms

<Same structure, shorter entries allowed.>

## Optional Further Terms

| Term | Short note | Why optional |
|---|---|---|

## Source And Confidence Notes

| Term | Evidence type | Source | Notes |
|---|---|---|---|

## Unresolved / Manual-Check Terms

| Term | Issue | What to check next |
|---|---|---|
```

## Term Categories

Use these categories when helpful:

- `concept`
- `acronym`
- `method`
- `model`
- `architecture`
- `algorithm`
- `metric`
- `dataset`
- `benchmark`
- `robotics-platform`
- `sensor`
- `task`
- `evaluation-protocol`
- `taxonomy-branch`
- `paper-specific-usage`

## Source Labels

- `paper`: supported by the current paper only.
- `external-confirmed`: checked against an external source that agrees with paper usage.
- `external-disambiguated`: external source resolved an ambiguous or overloaded term.
- `uncertain`: evidence is weak, conflicting, or missing.

## JSON Shape

When producing `glossary-sources.json`, use:

```json
{
  "paper": {
    "title": "",
    "source_path": "",
    "workdir": ""
  },
  "settings": {
    "audience": "beginner",
    "max_recursion_depth": 2,
    "external_verification": "as-needed"
  },
  "terms": [
    {
      "term": "",
      "aliases": [],
      "category": "",
      "priority": "must-know",
      "plain_meaning": "",
      "paper_specific_meaning": "",
      "why_it_matters": "",
      "paper_locations": [],
      "nested_prerequisites": [
        {
          "term": "",
          "depth": 1,
          "definition": "",
          "confidence": "paper"
        }
      ],
      "related_terms": [],
      "contrast_terms": [],
      "confidence": "external-confirmed",
      "sources": [
        {
          "type": "paper",
          "locator": "",
          "note": ""
        }
      ],
      "manual_check": false
    }
  ]
}
```
