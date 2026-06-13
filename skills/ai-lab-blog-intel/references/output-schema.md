# Output Schema

Use this contract for substantial runs. Keep raw captures immutable and put all merged evidence in normalized JSONL files.

## Directory Layout

```text
output/ai_lab_blog/<run_name>/
├── raw/
│   ├── feeds.json
│   ├── indexes.json
│   ├── sitemaps.json
│   └── articles.json
├── normalized/
│   ├── posts.jsonl
│   ├── links.jsonl
│   └── sources.jsonl
├── reports/
│   └── summary.md
├── manifest.json
└── sources.csv
```

## `normalized/posts.jsonl`

One row per blog post, research article, announcement, index item, or feed entry.

Required fields:

| Field | Description |
| --- | --- |
| `row_id` | Stable hash for the normalized row. |
| `schema_version` | Script schema version. |
| `org` | Canonical organization key, such as `openai` or `anthropic`. |
| `channel` | Source channel, such as `research`, `news`, `blog`, `engineering`, `rss`, `sitemap`, or `index`. |
| `source` | Capture source type: `feed`, `sitemap`, `index`, `article`, or `generic`. |
| `source_kind` | More specific kind, such as `feed-entry`, `sitemap-url`, or `index-link`. |
| `source_id` | Feed GUID, URL, slug, sitemap loc, or source-specific ID. |
| `source_url` | Canonical URL when known. |
| `title` | Post title. |
| `published_at` | Source-provided date string or ISO timestamp when available. |
| `summary` | Short source-provided or extracted summary. |
| `topic_labels` | Script-derived topical labels. |
| `source_priority` | `primary`, `secondary`, `fallback`, or `blocked`. |
| `fetched_at` | UTC timestamp for the capture. |
| `raw_ref` | Pointer back to raw source ID, URL, or index. |

Optional fields:

- `author`
- `categories`
- `image_url`
- `feed_url`
- `feed_title`
- `sitemap_url`
- `content_hash`
- `language`
- `status`
- `note`

## `normalized/links.jsonl`

One row per extracted link/artifact attached to a post.

Required fields:

| Field | Description |
| --- | --- |
| `row_id` | Stable hash for the link row. |
| `post_row_id` | Parent post row ID when available. |
| `org` | Parent organization key. |
| `link_url` | Absolute URL. |
| `link_type` | `paper`, `arxiv`, `doi`, `github`, `huggingface`, `model`, `dataset`, `benchmark`, `docs`, `product`, or `other`. |
| `anchor_text` | Link label or nearby text when available. |
| `source_url` | Parent article/post URL. |
| `source_priority` | Priority inherited from source or adjusted for fallback. |
| `fetched_at` | UTC timestamp. |

## `normalized/sources.jsonl`

One row per source route, feed, sitemap, index page, or optional provider.

Required fields:

| Field | Description |
| --- | --- |
| `row_id` | Stable hash. |
| `org` | Organization key or `unknown`. |
| `source_type` | `rss-feed`, `sitemap`, `html-index`, `article`, `search`, `api`, or `planned-route`. |
| `source_url` | Source endpoint URL. |
| `priority` | `primary`, `secondary`, `fallback`, or `blocked`. |
| `status` | `ok`, `planned`, `blocked`, `failed`, `not-feed`, or `empty`. |
| `auth_required` | Boolean. |
| `note` | Short status/caveat. |
| `fetched_at` | UTC timestamp. |

## `sources.csv`

Human review table with:

```csv
org,source_type,source_url,priority,status,auth_required,note
```

Use it to audit which endpoints were tried before summarizing.

## `manifest.json`

Include:

- target and run name;
- orgs and needs;
- route plan;
- commands or command shapes;
- credential policy;
- limits such as `max_entries`, `max_pages`, `limit`;
- created_at and fetched_at timestamps;
- blockers and follow-up suggestions.

## Merge Policy

- Deduplicate posts by canonical URL first, then by `org + title + published_at`.
- Preserve all source rows even when a feed fails.
- Prefer `primary` rows over `secondary` and `fallback` rows when titles/URLs conflict.
- Do not overwrite raw captures during normalization.
- If article extraction enriches a feed row, keep the feed row's source priority and add article-only fields rather than replacing the row identity.
