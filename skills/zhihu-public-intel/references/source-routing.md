# Source Routing

## Route Matrix

| Need | Preferred backend | Notes |
|---|---|---|
| Keyword search | `zhihu-k-search` or `zhihu-mcp` | `zhihu-k-search` is a simple Playwright CLI; `zhihu-mcp` is better when MCP tools are already configured. |
| Question detail + answer list | `zhihu-k-search` or `zhihu-mcp` | Good first lane for public topic research. |
| Single answer or zhuanlan article detail | `zhihu-k-search` or `zhihu-mcp` | Normalize body, author, counts, publish/edit time, and URL. |
| Comment collection | `zhihu-mcp`; fallback or deep lane `ZhihuApis` | `ZhihuApis` focuses on full answer/article comments and nested replies. |
| User public profile/activity | `zhihu-mcp` | Keep this public and non-invasive. Avoid private-history workflows. |
| Bulk crawl | `MediaCrawler` | Use for larger public crawling and cross-platform consistency. |
| Personal favorites/history/collection export | Out of scope by default | Use only if the user explicitly changes the requirement. |

## Backend Notes

### zhihu-k-search

Repository: `https://github.com/KunCheng-He/zhihu-k-search`

Useful for:

- Search Zhihu content by keyword.
- Fetch question details and answer lists.
- Fetch single answer details.
- Fetch article details.
- Export JSON or Markdown.

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
