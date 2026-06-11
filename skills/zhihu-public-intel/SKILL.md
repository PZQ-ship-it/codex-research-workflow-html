---
name: zhihu-public-intel
description: Route public Zhihu content search, crawling, comment collection, normalization, and synthesis. Use when Codex needs to research public Zhihu topics, search questions/articles/answers/users, crawl public question-answer/article pages, collect comments, choose between zhihu-k-search, zhihu-mcp, MediaCrawler, and ZhihuApis, or integrate public Zhihu captures into JSONL/CSV/Markdown reports without focusing on personal collections or browsing history.
---

# Zhihu Public Intel

## Overview

Use this skill for public Zhihu research and evidence collection. It does not prioritize personal favorites, private collections, or browsing history. It routes the task to the lightest suitable backend, keeps credentials local, and normalizes captured public content into auditable artifacts.

## Decision Tree

1. Identify the target:
   - keyword/topic search;
   - question URL or question ID;
   - answer URL or answer ID;
   - zhuanlan article URL or article ID;
   - comments for an answer/article;
   - user public profile or public recent activity;
   - bulk public crawl.
2. Plan the backend before crawling:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py plan `
  --target "大模型 Agent" `
  --needs search,question,answers,comments,report `
  --scale medium
```

3. Execute only the needed lane:
   - `zhihu-k-search`: lightweight browser workflow for search, question details, answer details, and article details.
   - `zhihu-mcp`: MCP workflow for search, full answers/articles, comments, user profile/activity, and reusable agent tools.
   - `MediaCrawler`: larger public bulk crawl across Zhihu and other social platforms.
   - `ZhihuApis`: focused full comment collection for answer/article comments, including nested replies.
4. Normalize results before synthesis:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py normalize `
  --input output\zhihu\raw_search.json `
  --source zhihu-k-search `
  --output-dir output\zhihu\normalized
```

5. Produce reports from normalized artifacts, not from untracked browser state.

## Backend Routing

Read `references/source-routing.md` before selecting a backend.

- Use `zhihu-k-search` for ad hoc public topic search and page details when a CLI-style skill is enough.
- Use `zhihu-mcp` when the user wants an ongoing Agent toolchain, comments plus content, user public profile/activity, or MCP integration.
- Use `MediaCrawler` when scale matters or the same crawl should later cover Xiaohongshu, Weibo, Bilibili, Tieba, and Zhihu in one framework.
- Use `ZhihuApis` when comment completeness is the key requirement.

## Common Commands

Print backend plan:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py plan `
  --target "https://www.zhihu.com/question/19550225" `
  --needs question,answers,comments,report
```

Extract IDs and classify a URL:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py inspect-url `
  "https://www.zhihu.com/question/19550225/answer/1992353258262504861"
```

Print the normalized artifact contract:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py schema
```

Generate a run scaffold:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py scaffold `
  --output-dir output\zhihu\agent_discussion `
  --target "大模型 Agent" `
  --needs search,answers,comments,report
```

## Output Contract

Keep raw captures and normalized data separate:

- `raw/`: untouched backend outputs, screenshots, or API captures.
- `items.jsonl`: normalized question, answer, article, search result, and user rows.
- `comments.jsonl`: normalized comments and nested replies.
- `sources.csv`: review table with URL, title, type, author, counts, and backend provenance.
- `manifest.json`: backend plan, commands run, timestamps, limits, and blockers.
- `summary.md`: human-facing synthesis with links back to normalized source IDs.

Read `references/output-schema.md` before merging multiple backend outputs.

## Guardrails

- Do not focus on personal favorites, private collections, or browsing history unless the user explicitly asks.
- Keep `cookies.json`, `auth.json`, browser storage state, `.env`, request headers, and token-like values out of git and final answers.
- Use logged-in browser state only when the user has authorized access and the target content is available to that account.
- Do not bypass CAPTCHAs automatically or describe blocks as missing data.
- Rate-limit crawls and prefer small smoke tests before bulk collection.
- Do not republish copyrighted Zhihu content in bulk. Summarize and cite URLs; keep full captures local.
- Respect robots, platform terms, author rights, and legal constraints.

## Resources

- `scripts/zhihu_public_intel.py`: planner, URL inspector, scaffold generator, schema printer, and JSON normalizer.
- `references/source-routing.md`: backend selection and setup notes.
- `references/output-schema.md`: normalized JSONL fields and merge policy.
