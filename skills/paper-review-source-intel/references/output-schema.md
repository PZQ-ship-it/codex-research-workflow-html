# Output Schema

Keep raw captures immutable and normalize into JSONL rows that preserve source provenance.

## Directory Contract

```text
run_dir/
  manifest.json
  sources.csv
  raw/
  normalized/
    papers.jsonl
    reviews.jsonl
    artifacts.jsonl
  reports/
    summary.md
```

## `manifest.json`

Required fields:

- `schema_version`: schema version used by this skill.
- `target`: user target or query.
- `needs`: requested evidence types.
- `venue`, `year`: normalized when known.
- `created_at`: ISO timestamp.
- `plan`: planner output or route summary.
- `commands`: commands or MCP calls that were run or proposed.
- `limits`: rate limits, max results, crawl depth, and date filters.
- `credential_policy`: note where credentials were expected and confirm none were written to committed files.
- `blockers`: CAPTCHA, login, 403, rate limit, missing API, or source drift.

## `papers.jsonl`

One row per paper, submission, preprint, or proceedings item.

Recommended fields:

- `row_type`: `paper`.
- `row_id`: stable local ID.
- `source`: source name, such as `openreview`, `acl-anthology`, `cvf`, `pmlr`, `neurips-proceedings`, `arxiv`, `acm-dl`, `ieee-csdl`, `ieee-xplore`, `ieee-transactions`, `iacr-tches`, `paper-search-mcp`, `openalex`, or `semantic-scholar`.
- `source_priority`: `primary`, `secondary`, or `fallback`.
- `source_id`: source-native ID.
- `source_url`: source-native page/API URL.
- `fetched_at`: ISO timestamp.
- `title`, `authors`, `abstract`, `venue`, `year`.
- `doi`, `arxiv_id`, `openreview_forum`, `acl_id`.
- `pdf_url`, `html_url`, `bibtex_url`.
- `status`: accepted/rejected/withdrawn/preprint/unknown when known.
- `license`, `access_status`.
- `topics`, `keywords`, `citations_count`.
- `raw_ref`: local path to raw capture if retained.

## `reviews.jsonl`

One row per review-like record.

Recommended fields:

- `row_type`: `review`, `meta_review`, `rebuttal`, or `decision`.
- `row_id`: stable local ID.
- `source`: usually `openreview`.
- `source_id`: note ID or invitation ID.
- `source_url`: forum or note URL.
- `fetched_at`: ISO timestamp.
- `paper_row_id` or `openreview_forum`.
- `invitation`, `venue`, `year`.
- `reviewer_role`: anonymized role when available.
- `rating`, `confidence`, `recommendation`, `decision`.
- `summary`, `strengths`, `weaknesses`, `questions`, `limitations`, `ethics`, `soundness`, `presentation`, `contribution`.
- `visibility`: public/login-required/unknown.
- `raw_ref`: local path to raw capture if retained.

## `artifacts.jsonl`

One row per downloaded or generated artifact.

Recommended fields:

- `row_type`: `artifact`.
- `row_id`: stable local ID.
- `artifact_type`: pdf/text/html/bibtex/screenshot/report.
- `source`, `source_url`, `paper_row_id`.
- `local_path`, `sha256`, `bytes`.
- `license`, `access_status`.
- `created_at`.

## Merge Policy

- Deduplicate papers by DOI first, then arXiv ID, then OpenReview forum ID, then normalized title plus venue/year.
- Preserve all source IDs and source URLs after merging.
- Prefer official proceedings for venue/year/accepted status.
- Prefer OpenReview for review/decision fields.
- Prefer OpenAlex/Semantic Scholar for citation/topic enrichment only when official sources lack those fields.
- Keep conflicting values as source-attributed fields rather than overwriting without explanation.
