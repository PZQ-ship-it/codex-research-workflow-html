# Output Schema

Normalize raw captures before synthesis. Keep raw files unchanged and write derived rows into `normalized/`.

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

Use one row per article, feed entry, search hit, video, post, or crawler record.

Required fields:

- `row_id`: stable short hash.
- `schema_version`: current schema version.
- `source`: `media-page`, `rss`, `anysearch`, `wechat`, `bilibili`, `mediacrawler`, or `generic`.
- `source_kind`: `article-link`, `feed-entry`, `search-hit`, `wechat-article`, `video`, `post`, or similar.
- `source_id`: platform identifier when available.
- `source_url`: canonical URL.
- `title`: article/post/video title or first-line text.
- `channel`: media/account/creator/source name when available.
- `platform`: `web`, `rss`, `wechat`, `bilibili`, `weibo`, `zhihu`, `xiaohongshu`, or similar.
- `published_at`: source timestamp or empty string.
- `summary`: short local summary or bounded excerpt.
- `mentioned_papers`: list of paper titles, DOI/arXiv IDs, or empty list.
- `mentioned_models`: list of model names or empty list.
- `mentioned_companies`: list of companies/labs or empty list.
- `engagement_metrics`: object with visible metrics such as views, likes, coins, comments, reposts.
- `source_priority`: `primary`, `secondary`, `propagation`, or `fallback`.
- `needs_primary_source_check`: boolean.
- `risk_note`: caveat such as title exaggeration, search snippet only, login-bound metric, or stale route.
- `fetched_at`: UTC capture time.
- `raw_ref`: raw identifier or file reference.

## `comments.jsonl`

Use one row per bounded comment or reply only when reception analysis is requested.

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
- `engagement_metrics`
- `source_priority`
- `needs_primary_source_check`
- `fetched_at`
- `raw_ref`

Keep `body` bounded. Prefer paraphrase in reports.

## `sources.jsonl`

Use one row per API, feed, public page, account, route, crawler, or source list.

Required fields:

- `row_id`
- `schema_version`
- `source`
- `source_type`
- `source_url`
- `priority`
- `status`: `ok`, `planned`, `blocked`, `skipped`, `fallback`, or `stale`.
- `auth_required`: boolean.
- `risk_note`
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
- `risk_note`
- `note`

## `manifest.json`

Record:

- target and needs;
- route plan;
- commands run;
- timestamps;
- scale limits such as `max_results`, `max_links`, `max_comments`;
- credential policy and private storage paths;
- blockers and skipped routes;
- raw and normalized artifact paths.

## Merge Policy

- Merge by canonical URL first, then by `source + source_id`.
- Preserve duplicate propagation signals across platforms; do not collapse Bilibili comments into WeChat comments.
- Keep source priority conservative. A Chinese article about an official paper remains `secondary` unless the row points to the official source itself.
- Reports must cite `row_id` and `source_url` for claims about Chinese diffusion.
- For copyrighted content and user-generated comments, quote sparingly and prefer paraphrase.
