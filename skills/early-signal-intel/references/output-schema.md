# Output Schema

Normalize raw captures before synthesis. Keep the original raw files unchanged and write derived rows into `normalized/`.

## Directory Contract

```text
raw/
normalized/
  items.jsonl
  comments.jsonl
  sources.jsonl
sources.csv
manifest.json
reports/
  summary.md
```

## `items.jsonl`

Use one row per story, post, feed entry, paper-discussion item, search hit, or social item.

Required fields:

- `row_id`: stable hash-like row ID.
- `schema_version`: current schema version.
- `source`: `hn`, `rss`, `alphaxiv`, `bluesky`, `reddit`, `x`, or `generic`.
- `source_kind`: platform-specific kind such as `story`, `comment`, `feed-entry`, `paper`, `post`, or `search-hit`.
- `source_id`: platform identifier when available.
- `source_url`: canonical source URL.
- `discussion_url`: thread/discussion URL when different from `source_url`.
- `title`: concise title or first-line text.
- `author`: public author/account name when available.
- `published_at`: source timestamp or empty string.
- `score`: platform score/points/likes when available; null if not available.
- `comment_count`: visible comment/reply count when available; null if not available.
- `summary`: short local summary or excerpt, not a bulk republication.
- `tags`: source tags/topics when available.
- `source_priority`: `primary`, `secondary`, `anecdotal`, or `fallback`.
- `fetched_at`: UTC capture time.
- `raw_ref`: raw identifier used to trace back to `raw/`.

## `comments.jsonl`

Use one row per comment or reply only when comments are needed. Keep body length bounded.

Required fields:

- `row_id`
- `schema_version`
- `source`
- `source_kind`
- `source_id`
- `source_url`
- `parent_id`
- `author`
- `published_at`
- `body`
- `source_priority`
- `fetched_at`
- `raw_ref`

## `sources.jsonl`

Use one row per API, feed, account, route, or source URL.

Required fields:

- `row_id`
- `schema_version`
- `source`
- `source_type`
- `source_url`
- `priority`
- `status`: `ok`, `planned`, `blocked`, `skipped`, or `fallback`.
- `auth_required`: boolean.
- `note`
- `fetched_at`

## `sources.csv`

For human review, include:

- `source`
- `source_type`
- `source_url`
- `priority`
- `status`
- `auth_required`
- `note`

## `manifest.json`

Record:

- target and needs;
- route plan;
- commands run;
- timestamps;
- scale limits such as `max_results`, `max_comments`, and time window;
- credential policy and private storage path;
- blockers and skipped routes;
- raw and normalized artifact paths.

## Merge Policy

- Merge by `source + source_id` first, then by canonical URL.
- Preserve duplicate community signals across platforms; do not collapse HN comments into Reddit comments.
- If a source row is anecdotal, keep it anecdotal even when many users agree.
- Reports must cite `row_id` and `source_url` for claims about signals.
- For copyrighted user-generated content, quote sparingly and prefer paraphrase.
