# Output Schema

## `manifest.json`

Required fields:

- `target`: original user target.
- `needs`: requested collection needs.
- `recommended_backend`: selected backend lane.
- `commands`: commands or MCP tools planned/run.
- `created_at`: ISO timestamp.
- `limits`: count, depth, and rate limits.
- `blockers`: login, CAPTCHA, permission, network, or endpoint drift.

## `items.jsonl`

One JSON object per public content item:

- `source_id`: stable local ID.
- `platform`: `zhihu`.
- `type`: `search_result`, `question`, `answer`, `article`, or `user`.
- `url`: canonical public URL.
- `title`: question/article/search-result title.
- `body_text`: extracted text or summary-safe body.
- `author`: object with public `name`, `url`, and optional public headline.
- `question_id`, `answer_id`, `article_id`.
- `topics`: list of public tags/topics.
- `counts`: object for vote, comment, answer, follower, view, or like counts.
- `published_at`, `updated_at`.
- `captured_at`.
- `backend`: backend name.
- `raw_ref`: path under `raw/` when available.

## `comments.jsonl`

One JSON object per comment:

- `source_id`: stable local comment ID.
- `item_source_id`: local source item ID.
- `url`: source answer/article URL.
- `comment_id`.
- `parent_comment_id`: empty for top-level comments.
- `author`: public author object.
- `content_text`.
- `like_count`.
- `created_at`.
- `captured_at`.
- `backend`.
- `raw_ref`.

## `sources.csv`

Review-friendly flattened table:

- `source_id`
- `type`
- `title`
- `url`
- `author`
- `published_at`
- `comment_count`
- `vote_count`
- `backend`
- `raw_ref`

## Merge Policy

- Preserve raw backend output.
- Do not silently merge different URLs unless IDs match.
- Prefer canonical Zhihu IDs over title matching.
- Keep duplicate answers/articles if IDs are missing.
- Store conflicts in `manifest.json` under `merge_warnings`.
