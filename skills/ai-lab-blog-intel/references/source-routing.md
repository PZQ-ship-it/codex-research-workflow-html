# Source Routing

Use the lightest first-party public source that can answer the question. This skill observes company/lab publishing behavior; it does not replace paper, code, model, or benchmark source-of-truth checks.

## Route Matrix

| Need | Default route | Optional route | Notes |
| --- | --- | --- | --- |
| Latest official posts | RSS/Atom feed | Blog index HTML | Feed is preferred when available and current. |
| Missing/stale RSS | XML sitemap | HTML index/pagination | Keep include filters narrow, such as `/research/`, `/news/`, `/blog/`. |
| Anthropic research/news | HTML or Next.js data extraction | Apify actor after setup | Current RSS candidates may return 404; prefer public `/news` and `/research`. |
| Meta AI blog | HTML index with pagination | Sitemap/search discovery | Current `ai.meta.com/blog/rss/` returns 404; crawl small page windows. |
| Linked artifacts | Article extraction | AnySearch discovery | Extract public article text only when links/topics are needed. |
| Current source discovery | AnySearch or official docs | General web search | Search snippets are discovery-only, not canonical evidence. |
| Paid managed crawler | None by default | Apify after explicit setup | Mark as `secondary` unless it only reads public first-party pages. |

## Default Source Registry

Verify feeds when a run depends on freshness.

| Org key | Default route | URL |
| --- | --- | --- |
| `openai` | RSS | `https://openai.com/news/rss.xml` |
| `google-research` | RSS | `https://research.google/blog/rss/` |
| `deepmind` | RSS | `https://deepmind.google/blog/rss.xml` |
| `google-ai` | RSS | `https://blog.google/technology/ai/rss/` |
| `microsoft-research` | RSS | `https://www.microsoft.com/en-us/research/feed/` |
| `nvidia-research` | RSS | `https://blogs.nvidia.com/blog/tag/nvidia-research/feed/` |
| `nvidia-developer` | Atom/RSS | `https://developer.nvidia.com/blog/feed` |
| `apple-ml` | RSS | `https://machinelearning.apple.com/rss.xml` |
| `allen-ai` | RSS | `https://allenai.org/rss.xml` |
| `bair` | RSS | `https://bair.berkeley.edu/blog/feed.xml` |
| `mit-machine-learning` | RSS | `https://news.mit.edu/rss/topic/machine-learning` |
| `cmu-ml` | RSS/HTML | `https://blog.ml.cmu.edu/feed` |
| `anthropic-news` | HTML index | `https://www.anthropic.com/news` |
| `anthropic-research` | HTML index | `https://www.anthropic.com/research` |
| `meta-ai` | HTML index | `https://ai.meta.com/blog/` |
| `stanford-hai` | HTML index | `https://hai.stanford.edu/news` |
| `stanford-sail` | HTML index | `http://ai.stanford.edu/blog/` |

## RSS And Atom

Use feeds for stable monitoring and incremental jobs:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-feeds `
  --org openai --org google-research --org deepmind `
  --output output\ai_lab_blog\raw\feeds.json
```

When a feed returns HTML with status 200, treat it as `blocked-or-not-feed` and try sitemap or HTML index. Do not silently normalize HTML as feed content.

## Sitemap

Use sitemaps to discover official URLs when RSS is absent:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-sitemap `
  --url https://www.anthropic.com/sitemap.xml `
  --include "/research/" --include "/news/" `
  --output output\ai_lab_blog\raw\anthropic_sitemap.json
```

Use `--limit` for large sites. Record sitemap URL, include filters, and errors in `sources.csv` or `normalized/sources.jsonl`.

## HTML Index

Use HTML index extraction only for public pages and small windows:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-index `
  --org anthropic --org meta-ai `
  --max-pages 2 `
  --output output\ai_lab_blog\raw\indexes.json
```

The built-in extractor uses simple link/title/date heuristics. If exact structured extraction is needed, create a source-specific parser after saving a raw snapshot and documenting selectors.

## Article Extraction

Use article fetching when the task needs linked papers, repositories, models, benchmarks, or product/docs links. Keep captures concise. The normalizer extracts:

- arXiv links and DOI-like strings;
- GitHub repository URLs;
- Hugging Face model/dataset links;
- benchmark/product/docs links;
- topic labels such as `model-release`, `alignment`, `safety`, `agent-tools`, `benchmark`, `systems`, and `productization`.

## AnySearch

Use AnySearch for live source discovery or freshness cross-checks:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py batch_search `
  --query "Anthropic research blog RSS sitemap" `
  --query "Meta AI blog sitemap RSS" `
  --query "Apple Machine Learning Research RSS"
```

If using an API key, store it through `$external-api-onboarding` in the provider's private `.env`. Do not place keys in this repository.

## Source Priority Labels

- `primary`: first-party RSS/feed/sitemap/page for the observed organization.
- `secondary`: third-party generated feed, managed crawler output, or public search result used for discovery.
- `fallback`: search snippet, cached mirror, or manually discovered page used only when first-party routes are unavailable.
- `blocked`: endpoint failed, requires auth, is not a feed, or changed structure.

Every normalized row should preserve `source_url`, `source_id`, `fetched_at`, `org`, `channel`, and `source_priority`.
