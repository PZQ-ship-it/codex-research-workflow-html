# Source Routing

## Route Matrix

| Need | Preferred backend | Notes |
|---|---|---|
| Keyword search | authenticated `zhihu-mcp` | Default lane. Check runtime, guide visible-browser login if needed, verify login, then use `search_content`. |
| Question detail + answer list | authenticated `zhihu-mcp`; `public-browser-lite` fallback | Prefer MCP after login. Use public capture only for already visible URLs or when auth is declined. |
| Single answer or zhuanlan article detail | authenticated `zhihu-mcp`; `public-browser-lite` fallback | Prefer MCP details after login. Normalize body, author, counts, publish/edit time, and URL. |
| Comment collection | authenticated `zhihu-mcp` or `ZhihuApis` | Full comments usually need logged-in/runtime-specific handling. |
| User public profile/activity | authenticated `zhihu-mcp` | User activity often needs cookies; guide visible login when needed. Avoid private-history workflows. |
| Bulk crawl | optional `MediaCrawler` | Use only when the user accepts external crawler setup and strict limits. |
| Personal favorites/history/collection export | Out of scope by default | Use only if the user explicitly changes the requirement. |

## Backend Notes

### zhihu-mcp-auth

Default route for keyword/topic/person Zhihu research.

Workflow:

```powershell
python skills\zhihu-public-intel\scripts\zhihu_public_intel.py check-runtime
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1
```

Then verify login via the MCP tool `check_login_status` or `cookie_status`, and run `search_content`, `get_question_detail`, `get_answer_detail`, `get_article_detail`, `get_comments`, or `user_profile` as needed.

Rules:

- The user completes login, MFA, and CAPTCHA in the visible browser.
- Do not paste or print cookie values.
- If cookies already exist, still verify login before crawling.
- If auth fails or the user declines login, use AnySearch fallback below and mark it as discovery-only evidence.

### public-browser-lite

Fallback/detail route. It does not require an MCP server, paid API, external crawler checkout, or committed login state.

Useful for:

- Already discovered public question, answer, article, and lightweight user/profile capture.
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

### AnySearch discovery fallback

Use AnySearch only when the user declines zhihu-mcp login, login fails, or a public index cross-check is explicitly useful.

Recommended command shape on this Windows machine:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py batch_search `
  --query "site:zhihu.com <关键词>" `
  --query "site:zhuanlan.zhihu.com <关键词>" `
  --query '"<关键词>" 知乎'
```

Use it for:

- URL and title/snippet discovery.
- Cross-checking whether Zhihu has indexed content before spending login effort.
- Seeding later `get_question_detail`, `get_answer_detail`, or `get_article_detail` attempts.

Limits:

- AnySearch snippets are not full Zhihu captures. Normalize them as `--source anysearch` and say they are discovery evidence.
- Do not claim article/comment/full-answer content was captured unless the Zhihu page or MCP detail tool actually returned it.
- If the user needs full details, comments, or recent activity, escalate to the authenticated `zhihu-mcp` lane below.

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

Preferred repeatable setup for Codex:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1
```

This installs into the user-level global skill runtime, creates an isolated venv, writes a safe default `config.json`, installs Playwright Chromium, and registers the `zhihu_mcp` Codex MCP server.

Manual setup:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python mcp_server.py --test
```

Keep `cookies.json` local and untracked. The bundled setup disables automatic Chrome cookie extraction by default.

For a user-controlled login flow similar to xhs-style browser assistance, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1
```

This opens visible Chromium, waits while the user logs in and handles MFA/CAPTCHA, then writes only Playwright-format Zhihu cookies to the private runtime `cookies.json`. It prints counts/status only, never cookie values. Use `-DryRun` first to show paths without opening the browser.

After login, restart Codex if the MCP server was newly registered and run `check_login_status`/`cookie_status` before collecting content.

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
