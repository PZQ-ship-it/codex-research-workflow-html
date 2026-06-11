---
name: zhihu-public-intel
description: Route public Zhihu content search, public page capture, normalization, and synthesis. Use when Codex needs a usable no-required-MCP/no-required-API-key Zhihu research closure for public topics, questions, answers, articles, lightweight user/profile evidence, or JSONL/CSV/Markdown reports, with zhihu-k-search, zhihu-mcp, MediaCrawler, and ZhihuApis treated as optional extensions.
---

# Zhihu Public Intel

## Overview

Use this skill for public Zhihu research and evidence collection. The default closure is narrowed to public/local capture: no required external API key, no required MCP server, no paid crawler, and no committed login state. It does not prioritize personal favorites, private collections, or browsing history. Optional external backends may be used only when the user explicitly accepts their setup and access tradeoffs.

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
   - `public-browser-lite`: default narrowed lane for public search, public question/answer/article pages, raw capture, and normalization.
   - `zhihu-k-search`: optional convenience CLI when already installed.
   - `zhihu-mcp`: optional MCP workflow when the user explicitly wants agent tools.
   - `MediaCrawler`: optional larger public bulk crawl.
   - `ZhihuApis`: optional logged-in comment-completeness lane; cookies stay local.
4. Normalize results before synthesis:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py normalize `
  --input output\zhihu\raw_search.json `
  --source public-browser-lite `
  --output-dir output\zhihu\normalized
```

5. Produce reports from normalized artifacts, not from untracked browser state.

## Backend Routing

Read `references/source-routing.md` before selecting a backend.

- Use `public-browser-lite` by default for public pages and lightweight reports. Save public raw HTML/JSON-like captures under `raw/`, then normalize.
- Use `zhihu-k-search` only as an optional convenience CLI when it is already installed or the user approves setup.
- Use `zhihu-mcp` only when the user explicitly wants an ongoing Agent/MCP toolchain.
- Use `MediaCrawler` only when scale matters and the user accepts external crawler setup.
- Use `ZhihuApis` only when comment completeness is the key requirement and the user approves authorized local cookies.

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
- Default work must remain useful without MCP, paid scraping, external API keys, or committed login state.
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
