# Source Routing

Use the lightest public source that can answer the question. This skill observes Chinese propagation and commercialization signals; it does not turn secondary media into authoritative evidence.

## Route Matrix

| Need | Default route | Optional route | Notes |
| --- | --- | --- | --- |
| Chinese AI media discovery | AnySearch query plus public homepage capture | RSSHub or known RSS feeds | Good for recall. Verify important facts against primary sources. |
| 机器之心 / 量子位 / 新智元 / AI科技评论 | Public site pages and RSS/RSSHub routes when available | AnySearch site queries | Treat headlines and article claims as secondary. |
| PaperWeekly / academic community posts | RSS/RSSHub, known article pages, AnySearch | WeChat article URL export | Useful for Chinese academic-circle attention. |
| WeChat article text | `wespy-plus` single URL or album export | WeChat-specific crawler/MCP after setup | Requires human-controlled login or known public article URL for robust use. |
| WeChat account metrics | Research-specific WeChat crawler after explicit approval | Manual/public article-only capture | Reading/like/comment metrics are fragile and login-bound. |
| Bilibili creator/video signal | Small UID/video metadata crawler | Comment scraper with login and strict limits | Engagement and comments are propagation signals only. |
| Multi-platform self-media | MediaCrawler after setup | Platform-specific CLI wrappers | Keep scale small and record login/proxy/rate-limit blockers. |
| Primary-source verification | Paper, official release, repo, venue, lab/company blog | AnySearch discovery for source URL | Do this before final claims. |

## Public Media Pages

Use `fetch-page` for lightweight public pages when the user needs a quick signal list:

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-page `
  --url https://www.jiqizhixin.com/ `
  --url https://www.qbitai.com/ `
  --max-links 30 `
  --output output\chinese_ai_signal\raw\media_pages.json
```

This parser extracts page title and candidate article links. It is intentionally conservative and should not be treated as full article extraction.

## RSS / RSSHub

Use RSS/Atom when a feed is known or an RSSHub route is available. RSS is best for stable monitoring and low-maintenance automation.

Good source-discovery seeds:

- RSSHub routes and PRs for Chinese AI media.
- `gpt-rss` and AI news aggregator source lists.
- public OPML/source lists maintained by trusted users.

Feed URLs are version-sensitive. If a feed fails, record it as `blocked` or `stale` in `sources.csv` instead of silently inventing a replacement.

## AnySearch

Use AnySearch for discovery:

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-anysearch `
  --query "site:jiqizhixin.com SWE-agent" `
  --max-results 10
```

Suggested query patterns:

- `"论文名" 机器之心 量子位 新智元 PaperWeekly`
- `site:jiqizhixin.com "模型名"`
- `site:qbitai.com "公司名" "模型名"`
- `"论文名" 公众号 AI`
- `"模型名" B站 技术 up`

AnySearch snippets are discovery-only evidence. Save raw results, normalize URLs, then fetch or verify the actual page.

## WeChat

Use WeChat only when the user provides URLs, account names, or has approved login/setup.

Preferred light route:

- `wespy-plus "<mp.weixin.qq.com/s/...>" --output-json`
- `wespy-plus "<album-url>" --album-only`
- `wespy-plus "<album-url>" --max-articles <n>`

Heavier routes such as Fiddler/PC-WeChat crawlers can be useful for research datasets, but they require explicit user approval because they depend on login state, local app versions, and platform controls. Store no cookies or tokens in this repo.

## Bilibili

Use Bilibili for propagation signals:

- creator video list by UID;
- specific video metadata;
- bounded comment samples when the user explicitly needs reception analysis.

Do not use video metrics as evidence of research correctness. Keep comments bounded, summarize instead of quoting heavily, and record login/rate-limit/CAPTCHA blockers.

## MediaCrawler

Use MediaCrawler-style captures when the user wants multi-platform self-media context: B站, 微博, 知乎, 小红书, 贴吧, 抖音, 快手.

Run setup and login in visible user-controlled flows only. Keep captures small and export raw JSON/CSV into `raw/`, then normalize.

## Source Priority Labels

- `primary`: first-party official paper/release/repo/venue/lab/company source.
- `secondary`: Chinese media article, newsletter, RSS item, aggregator result.
- `propagation`: WeChat, Bilibili, social/self-media metrics and comments.
- `fallback`: search snippet, cached source list, or unverified route discovery.

Set `needs_primary_source_check=true` for secondary, propagation, and fallback rows unless the row itself is a primary source.
