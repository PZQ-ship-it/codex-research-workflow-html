# Output Schema

Keep raw captures immutable and normalize into JSONL rows with provenance.

## Directory Contract

```text
run_dir/
  manifest.json
  sources.csv
  raw/
  normalized/
    repos.jsonl
    models.jsonl
    benchmarks.jsonl
    artifacts.jsonl
  reports/
    summary.md
```

## `manifest.json`

Required fields:

- `schema_version`: schema version used by this skill.
- `target`: user target or query.
- `needs`: requested evidence types.
- `created_at`: ISO timestamp.
- `plan`: planner output or route summary.
- `commands`: commands or MCP calls that were run or proposed.
- `limits`: max results, date filters, crawl depth, and download policy.
- `credential_policy`: note where credentials were expected and confirm none were written to committed files.
- `blockers`: CAPTCHA, login, 403, rate limit, missing API, stale source, or license restriction.

## `repos.jsonl`

Repository, code, issue, PR, release, or implementation rows.

Recommended fields:

- `row_type`: `repo`, `code_file`, `issue`, `pull_request`, `release`, `workflow`, or `implementation`.
- `row_id`: stable local ID.
- `source`: `github`, `gitlab`, `local-clone`, or source-specific value.
- `source_priority`: `primary`, `secondary`, `archive`, or `fallback`.
- `source_id`, `source_url`, `fetched_at`.
- `owner`, `repo`, `branch`, `commit_sha`, `path`.
- `title`, `description`, `language`, `license`.
- `stars`, `forks`, `open_issues`, `created_at`, `updated_at`, `pushed_at`.
- `paper_id`, `model_id`, `benchmark_id` when linked.
- `raw_ref`: local path to raw capture if retained.

## `models.jsonl`

Model, dataset, Space, model-card, dataset-card, or Hub resource rows.

Recommended fields:

- `row_type`: `model`, `dataset`, `space`, `paper`, `model_card`, or `dataset_card`.
- `row_id`: stable local ID.
- `source`: `huggingface`, `kaggle`, `openml`, `github`, or source-specific value.
- `source_priority`, `source_id`, `source_url`, `fetched_at`.
- `repo_id`, `owner`, `name`, `resource_type`.
- `task`, `library`, `tags`, `license`, `gated`, `private`.
- `downloads`, `likes`, `created_at`, `updated_at`.
- `files`, `card_summary`, `linked_papers`, `linked_datasets`, `linked_spaces`.
- `parameter_count`, `safetensors`, `model_family`.
- `raw_ref`.

## `benchmarks.jsonl`

Benchmark, task, leaderboard, score, run, or evaluation result rows.

Recommended fields:

- `row_type`: `benchmark`, `task`, `leaderboard`, `score`, `run`, or `eval_result`.
- `row_id`: stable local ID.
- `source`: `huggingface-leaderboard`, `kaggle`, `openml`, `livebench`, `arena-snapshot`, `paperswithcode-archive`, etc.
- `source_priority`, `source_id`, `source_url`, `fetched_at`.
- `benchmark_id`, `benchmark_name`, `task_name`, `dataset_id`, `split`, `version`.
- `model_id`, `model_name`, `provider`.
- `metric`, `value`, `rank`, `confidence_interval`.
- `verified`, `verification_status`, `self_reported`, `submission_date`.
- `code_url`, `paper_url`, `model_url`, `notes`.
- `raw_ref`.

## `artifacts.jsonl`

Local files, downloads, logs, and generated reports.

Recommended fields:

- `row_type`: `artifact`.
- `row_id`: stable local ID.
- `artifact_type`: json/csv/parquet/model-card/dataset-card/notebook/log/screenshot/report.
- `source`, `source_url`, `related_row_id`.
- `local_path`, `sha256`, `bytes`.
- `license`, `access_status`.
- `created_at`.

## Merge Policy

- Deduplicate repos by platform plus owner/repo and commit/path where applicable.
- Deduplicate HF resources by `repo_id` and `resource_type`.
- Deduplicate benchmark scores by benchmark/task/split/version/model/metric/source.
- Prefer official source rows over third-party aggregators for scores.
- Preserve all source IDs and source URLs after merging.
- Keep conflicting benchmark values as source-attributed rows rather than overwriting.
- Mark old Papers with Code data as `archive`.
