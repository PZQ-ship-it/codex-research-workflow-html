# Source Routing

Use the lightest official or first-party public source that can answer the question. This skill is for signals and provenance, not authority ranking. Treat all community platforms as context that needs cross-checking against papers, official releases, or project repositories.

## Route Matrix

| Need | Default route | Optional route | Notes |
| --- | --- | --- | --- |
| HN search and engineering spread | Algolia HN Search API | Firebase item API for thread tree | No key required. Good for open-source/product diffusion and engineering feedback. |
| HN thread comments | Firebase `/v0/item/<id>.json` | Algolia search by story title/URL | Traverse comments with depth/count limits. |
| Lab/company blog monitoring | RSS/Atom feed | HTML feed discovery or page extraction | Prefer first-party feeds from OpenAI, Anthropic, Google Research, DeepMind, Meta AI, Microsoft Research, NVIDIA, Apple ML, BAIR, HAI, CSAIL, CMU, etc. |
| arXiv discussion | alphaXiv public pages or `alphaxiv-py` | alphaXiv API key for authenticated/high-quota use | Best for paper-specific comments, resources, overview, and attention signal. |
| Bluesky scholar posts | bounded AT Protocol/Jetstream or appview lookup | app password for account-specific queries | Use seed accounts and short windows; avoid unbounded firehose capture. |
| Reddit ML discussion | official Reddit API via PRAW | manually discovered public pages as snippets only | Anecdotal only. Requires OAuth for robust use. Respect Reddit Data API Terms. |
| X/Twitter scholar signals | official X API | none by default | Paid or quota-limited. Do not use unofficial scrapers unless explicitly approved. |

## Hacker News

Use HN when the user asks whether a paper, repo, model, tool, or idea reached engineering/open-source audiences.

Preferred commands:

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py fetch-hn `
  --query "alphaxiv arxiv discussion" `
  --max-results 20 `
  --output output\early_signal\raw\hn_search.json
```

The CLI defaults to `--tags story`. Algolia treats comma-separated tags as filters that can overconstrain search, so do not use `story,comment` as a broad default.

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py fetch-hn `
  --item-id 41478690 `
  --include-comments `
  --max-comments 40 `
  --output output\early_signal\raw\hn_thread.json
```

Use `max-comments` and optional `delay` for politeness. Do not interpret HN upvotes as academic quality.

## RSS And Lab Blogs

Use RSS for first-party research release monitoring. If a site does not expose a feed, discover it manually or use web search, then capture the source URL and status in `sources.csv`.

Useful feed patterns are version-sensitive, so verify them when a feed fails:

- OpenAI news: `https://openai.com/news/rss.xml`
- Google Research blog: `https://research.google/blog/rss/`
- Google DeepMind: check official site for current feed or use page extraction when no feed is exposed.
- Microsoft Research: check official blog feed or use page extraction.
- BAIR, Stanford HAI, MIT CSAIL, CMU, Allen AI, NVIDIA Research, Apple ML: prefer official feeds or official blog index pages.

## alphaXiv

Use alphaXiv for arXiv-paper discussion:

- comments/questions on top of papers;
- paper-specific resources and mentions;
- overview/status when the user wants a community-facing digest;
- similar-paper recommendations when exploring neighborhood signals.

Preferred implementation is `alphaxiv-py` in an optional isolated runtime. Public reads may work without a key, but authenticated or higher-quota use should be set up through `$external-api-onboarding` and stored in:

`%USERPROFILE%\.codex\skills\early-signal-intel\.env`

Expected env var:

`ALPHAXIV_API_KEY`

## Bluesky

Use Bluesky when the task depends on early scholar announcements or social diffusion:

- seed account timelines;
- keyword/URL mentions over a short time window;
- bounded Jetstream capture for posts only.

Keep captures small and timestamped. If authentication is needed, use app passwords only:

- `BLUESKY_HANDLE`
- `BLUESKY_APP_PASSWORD`

Do not store account passwords. Do not use broad firehose collection unless the user explicitly asks and accepts runtime/storage limits.

## Reddit

Use Reddit only as anecdotal context, never as first-source evidence. Prefer official API/PRAW after OAuth setup:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`

Do not train models on Reddit content captured by this workflow. Do not bulk mirror comments. Summarize and cite URLs.

## X / Twitter

Default posture: official API only, optional, and user-approved. Useful for first-release scholar signals, but often cost/quota constrained.

Expected env var:

`X_BEARER_TOKEN`

Do not install or run unofficial login/GraphQL scrapers unless the user explicitly asks and accepts account, compliance, and maintenance risks.

## Source Priority Labels

- `primary`: first-party API/feed/page for the platform being observed.
- `secondary`: cross-indexed search result, non-official mirror, or enrichment source.
- `anecdotal`: community comments or social posts used only for signal context.
- `fallback`: search snippet or manually discovered page used only when official/public API is unavailable.

Every normalized row should preserve `source_url`, `source_id`, `fetched_at`, and `source_priority`.
