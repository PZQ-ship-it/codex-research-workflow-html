# Source Routing

## Route Matrix

| Need | Preferred backend | Notes |
|---|---|---|
| Keyword search | `public-browser-lite` | Default narrowed lane. Use public pages/search results, save raw captures, then normalize. |
| Question detail + answer list | `public-browser-lite` | Capture public visible page fields. Login walls, CAPTCHA, or hidden dynamic fields are blockers. |
| Single answer or zhuanlan article detail | `public-browser-lite` | Normalize body, author, counts, publish/edit time, and URL from public visible fields. |
| Comment collection | optional `zhihu-mcp` or `ZhihuApis` | Full comments usually need logged-in/runtime-specific handling; not part of the default closure. |
| User public profile/activity | `public-browser-lite`; optional `zhihu-mcp` | Keep this public and non-invasive. Avoid private-history workflows. |
| Bulk crawl | optional `MediaCrawler` | Use only when the user accepts external crawler setup and strict limits. |
| Personal favorites/history/collection export | Out of scope by default | Use only if the user explicitly changes the requirement. |

## Backend Notes

### public-browser-lite

Default route. It does not require an MCP server, paid API, external crawler checkout, or committed login state.

Useful for:

- Public keyword/topic scouting.
- Public question, answer, article, and lightweight user/profile capture.
- Small smoke runs whose output can be normalized into `items.jsonl` and `sources.csv`.

Typical workflow:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py scaffold `
  --output-dir output\zhihu\agent_discussion `
  --target "大模型 Agent" `
  --needs search,answers,report
```

Then save public raw captures under `raw/` and normalize:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py normalize `
  --input output\zhihu\agent_discussion\raw\public_search.json `
  --source public-browser-lite `
  --output-dir output\zhihu\agent_discussion\normalized
```

Limits:

- Do not bypass CAPTCHA or login walls.
- Hidden comments, private activity, and complete logged-in views are blockers unless the user explicitly approves a local authenticated optional backend.

### zhihu-k-search

Repository: `https://github.com/KunCheng-He/zhihu-k-search`

Useful for:

- Search Zhihu content by keyword.
- Fetch question details and answer lists.
- Fetch single answer details.
- Fetch article details.
- Export JSON or Markdown.

This is an optional convenience CLI when already installed or when the user approves setup. It is not required for the base closure.

Typical setup:

```powershell
cd path\to\zhihu-k-search\scripts
uv sync
uv run playwright install chromium
uv run python main.py login
```

Typical commands:

```powershell
uv run python main.py search "大模型 Agent" -t answer -l 20 -o raw_search.json
uv run python main.py detail "https://www.zhihu.com/question/19550225" -o raw_question.json
uv run python main.py detail "https://zhuanlan.zhihu.com/p/123456" -o raw_article.json
```

### zhihu-mcp

Repository: `https://github.com/alizeeblack-code/zhihu-mcp`

Useful for:

- Agent-facing MCP tools.
- Search, question detail, answer detail, article detail, comments, user profile, public activity.
- Reusable workflows such as `research-on-zhihu`, `analyze-zhihu-question`, `analyze-zhihu-answer`, and `track-zhihu-user`.

This is optional. Use only when the user explicitly wants an MCP toolchain.

Typical setup:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python mcp_server.py --test
```

Keep `cookies.json` local and untracked.

### MediaCrawler

Repository: `https://github.com/NanmiCoder/MediaCrawler`

Useful for:

- Larger public crawling jobs.
- Multi-platform public data collection where Zhihu is one lane among Xiaohongshu, Weibo, Bilibili, Tieba, and others.
- Comment crawling at scale.

This is optional. Use only when scale justifies an external crawler checkout.

Prefer a smoke crawl first, then scale up with strict limits and resumable output.

### ZhihuApis

Repository: `https://github.com/cv-cat/ZhihuApis`

Useful for:

- Full comment collection for answers and zhuanlan articles.
- Nested comments / replies.
- When comment completeness matters more than broad page extraction.

It requires logged-in cookies and computes Zhihu request signatures. Keep cookies in local runtime files only.

## Credentials And Local State

Add or keep these out of git:

```gitignore
skills/zhihu-public-intel/runtime/
skills/zhihu-public-intel/**/cookies.json
skills/zhihu-public-intel/**/auth.json
skills/zhihu-public-intel/**/.env
skills/zhihu-public-intel/**/storage_state.json
```

Do not paste cookie strings, `z_c0`, `d_c0`, or request headers into chat or committed docs.
