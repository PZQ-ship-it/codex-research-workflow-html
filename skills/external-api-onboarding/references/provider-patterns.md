# Provider Patterns

Use this file for known setup routes. If a provider is missing or likely to have changed, verify current official docs before editing config.

## AnySearch

- Access type: optional API key; anonymous access works with lower limits.
- Env var: `ANYSEARCH_API_KEY`.
- Preferred storage: `%USERPROFILE%\.codex\skills\anysearch\.env`.
- Console: `https://anysearch.com/console/api-keys`.
- MCP: no MCP server required for the bundled CLI.
- Setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\external-api-onboarding\scripts\set_env_secret.ps1 `
  -EnvFile "$env:USERPROFILE\.codex\skills\anysearch\.env" `
  -Name ANYSEARCH_API_KEY
```

- Smoke test:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py doc
```

Use a small `batch_search` only when the user wants to verify live quota. If the API response offers an auto-registered key, save it only after explicit user approval.

## OpenRouter ICU Image

- Access type: API key for the OpenRouter ICU OpenAI-compatible image API.
- Env var: `OPENROUTER_ICU_API_KEY`.
- Preferred storage: `%USERPROFILE%\.codex\skills\openrouter-icu-image\.env`.
- Existing provider-specific helper: `skills\openrouter-icu-image\scripts\set_openrouter_icu_key.ps1`.
- Generic setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\external-api-onboarding\scripts\set_env_secret.ps1 `
  -EnvFile "$env:USERPROFILE\.codex\skills\openrouter-icu-image\.env" `
  -Name OPENROUTER_ICU_API_KEY
```

- Smoke test: prefer the skill CLI `--dry-run` first. Ask before real image generation because it can cost money.

## Figma Context MCP

- Access type: personal access token for local read/context MCP, plus optional official remote OAuth MCP for writes.
- Env var: `FIGMA_API_KEY`.
- Preferred storage: `%USERPROFILE%\.codex\skills\figma-context-mcp\.env`.
- Existing provider-specific helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\figma-context-mcp\scripts\configure_figma_api_key.ps1
```

- Local context MCP shape:

```powershell
codex mcp add figma_context -- cmd /c npx -y figma-developer-mcp --env "%USERPROFILE%\.codex\skills\figma-context-mcp\.env" --stdio --image-dir generated_assets\figma --format yaml
```

- Optional official write provider:

```powershell
codex mcp add figma_write --url https://mcp.figma.com/mcp
codex mcp login figma_write
```

Keep read/context and write/OAuth providers separate so final summaries can say which one was used.

## OpenAI Developer Docs MCP

- Access type: public MCP docs server; usually no API key needed.
- Setup:

```powershell
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

- Smoke test: list MCP servers with `codex mcp --help` / `/mcp`, or use the MCP in a tiny official-doc lookup if tools are available.

## Skill Eval Optimizer

- Access type: no-key local baseline for skill validation, JSONL trace grading, and eval-pack scaffolding; optional provider setup only when eval cases require live discovery, official docs lookup, repository/HF/Kaggle enrichment, browser automation, or remote MCP tools.
- API key: none required for the base workflow.
- Skill path: `skills\skill-eval-optimizer\`.
- Baseline smoke tests:

```powershell
python skills\skill-eval-optimizer\scripts\skill_eval_harness.py static-check skills\skill-eval-optimizer
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\skill-eval-optimizer
```

- Optional provider routes:
  - AnySearch: use `ANYSEARCH_API_KEY` in `%USERPROFILE%\.codex\skills\anysearch\.env` only when anonymous live discovery is insufficient.
  - OpenAI Developer Docs MCP: use `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp` when current official Codex/OpenAI docs are required.
  - GitHub, Hugging Face, Kaggle: use read-only scoped tokens only when public unauthenticated access cannot satisfy the eval.
  - Browser Use MCP or visible browser helpers: use only for non-secret UI/state checks; the user completes login, MFA, CAPTCHA, and secret reveal steps.
- Smoke test policy: prefer local `doc`, `list`, `whoami`, public read, or dry-run commands. Ask before paid, write-capable, or provider-mutating requests.
- Reporting: include provider name, env var name, private storage path, MCP server name, command shape, and smoke-test result only; never include token values, cookies, auth headers, or browser storage.

## Browser Use MCP

- Access type: local stdio MCP for browser automation.
- Official local command shape:

```powershell
codex mcp add browser_use -- uvx --from "browser-use[cli]" browser-use --mcp
```

- Common env vars:
  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for the Browser Use agent.
  - `BROWSER_USE_HEADLESS=false` when the user needs to see the browser.
- Do not set `BROWSER_USE_DISABLE_SECURITY=true` unless the user explicitly accepts the risk for a controlled local target.
- Smoke test: open a benign page and read non-secret state. Do not use it to extract provider secrets.

## Browser Session Cookie/Storage Providers

Use this pattern for skills like `dianping-explore`, `zhihu-public-intel`, `xhs-explore`, or platform crawlers that require a logged-in browser session rather than an API key or OAuth MCP login.

- Access type: visible user login into a fresh tool-controlled browser session.
- Preferred storage: `%USERPROFILE%\.codex\skills\<skill-name>\.env`, `runtime\cookies.json`, or another skill-private runtime path.
- Default helper behavior:
  - Open the official site in a visible automation browser.
  - Let the user complete login, MFA, CAPTCHA, QR scan, or account verification manually.
  - Save only the cookies/storage state from that helper-created session.
  - Report only path, cookie/state count, and login/status booleans.
- Default prohibitions:
  - Do not ask the user to paste cookies manually when a safe visible helper exists.
  - Do not stop at "cookie missing", run anonymous mode, or switch to search/snippet fallback when a safe visible helper exists and the user has not declined it.
  - Do not read existing Chrome/Edge/browser profiles unless the user explicitly asks and accepts the privacy risk.
  - Do not print cookie values, auth headers, local storage values, or browser-state JSON.
- Fallback gate:
  - Attempt the helper-backed main flow first for requested provider data.
  - Use fallback only when login is declined, the helper fails after a reasonable attempt, the runtime is unavailable, or the user explicitly asks for discovery-only/public cross-checking.
  - If a skill's CLI or instructions prefer fallback before assisted auth, patch the skill as part of onboarding.
- Smoke test: prefer `status`, `check-login`, `cookie_status`, `whoami`, or one small read-only page/API call. Treat a cookie file's existence as insufficient unless a login/status check passes.

## Dianping Explore

- Access type: visible user login into a fresh Playwright Chromium session; saved as `DIANPING_COOKIE` in `%USERPROFILE%\.codex\skills\dianping-explore\.env`.
- Helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\dianping-explore\scripts\assist_dianping_cookie.ps1
```

- Main-flow requirement: `run-crawler` should automatically invoke the helper when `DIANPING_COOKIE` is missing, reload the private `.env`, and continue the small crawler run. Do not report "crawler available but no cookie so no comments were collected" unless visible login was declined, failed, or explicitly disabled.

## Zhihu Public Intel / zhihu-mcp

- Access type: local stdio MCP with user-authorized browser login by default; public AnySearch fallback only when login is declined, two assisted login attempts fail, the MCP runtime remains unavailable, or public-index cross-checking is requested.
- API key: none.
- Preferred private runtime: `%USERPROFILE%\.codex\skills\zhihu-public-intel\runtime\zhihu-mcp`.
- Private auth state: `cookies.json` in the runtime checkout, Playwright cookie format.
- Auth-first setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1
python C:\Users\Administrator\.codex\skills\zhihu-public-intel\scripts\zhihu_public_intel.py check-runtime
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1
```

The helper opens a visible browser. The user completes login, MFA, and CAPTCHA directly in the browser. It stores Zhihu cookies locally and prints only status/path/count, never cookie values. Keep `chrome_cookie_extraction=false` unless the user explicitly approves automatic extraction from an existing browser profile.

If `check_login_status` or `cookie_status` reports `logged_in=false`, `login_verified=false`, missing cookies, stale cookies, or an auth-looking empty exact-name search, run `assist_zhihu_login.ps1` immediately. A present `cookies.json` is not proof of login and should be refreshed through the visible helper before using AnySearch.

- Smoke tests:

```powershell
python C:\Users\Administrator\.codex\skills\zhihu-public-intel\scripts\zhihu_public_intel.py check-runtime
python C:\Users\Administrator\.codex\skills\zhihu-public-intel\scripts\zhihu_public_intel.py auth-guide --target "<关键词>" --needs search,comments
```

After login, use MCP `check_login_status` or `cookie_status`, then `search_content`/detail/comment tools.

- AnySearch fallback:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py batch_search `
  --query "site:zhihu.com <关键词>" `
  --query "site:zhuanlan.zhihu.com <关键词>" `
  --query '"<关键词>" 知乎'
```

Use AnySearch only after login is declined, two assisted login attempts fail, the MCP runtime remains unavailable, or as an explicit cross-check, and mark snippets as discovery-only evidence. If the MCP server was newly registered, restart Codex before expecting its tools to appear. Never paste `z_c0`, `d_c0`, cookie strings, request headers, or browser storage into chat.

## Early Signal Intel

- Access type: no-key public baseline for Hacker News and RSS; optional API-key/app-password/OAuth-style setup for alphaXiv, Bluesky, Reddit, and X.
- Preferred storage: `%USERPROFILE%\.codex\skills\early-signal-intel\.env`.
- Baseline setup and smoke:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\early-signal-intel\scripts\setup_early_signal_intel.ps1 -RunNetworkSmoke
```

- Optional provider helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\early-signal-intel\scripts\assist_early_signal_auth.ps1 -Provider alphaxiv
powershell -ExecutionPolicy Bypass -File .\skills\early-signal-intel\scripts\assist_early_signal_auth.ps1 -Provider bluesky
powershell -ExecutionPolicy Bypass -File .\skills\early-signal-intel\scripts\assist_early_signal_auth.ps1 -Provider reddit
powershell -ExecutionPolicy Bypass -File .\skills\early-signal-intel\scripts\assist_early_signal_auth.ps1 -Provider x
```

- Env vars:
  - alphaXiv: `ALPHAXIV_API_KEY` optional.
  - Bluesky: `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` optional; use app passwords only.
  - Reddit: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`; use official API/PRAW and treat content as anecdotal.
  - X: `X_BEARER_TOKEN`; official API only and ask before paid requests.
- Smoke tests:

```powershell
python .\skills\early-signal-intel\scripts\early_signal_intel.py fetch-hn --query "alphaXiv arXiv discussion" --max-results 2
python .\skills\early-signal-intel\scripts\early_signal_intel.py fetch-rss --feed https://openai.com/news/rss.xml --max-entries 2
```

Do not use unofficial X login scrapers or bulk Reddit mirroring by default. Do not train models on captured user-generated content. Store optional secrets through the helper or `set_env_secret.ps1`, never in chat.

## Chinese AI Signal Crawler

- Access type: no-key public baseline for Chinese AI media public pages, RSS/RSSHub, and AnySearch anonymous discovery; optional API key for AnySearch quota; optional visible login/tool-local state for WeChat, Bilibili, and MediaCrawler-style platform captures.
- Preferred storage:
  - `%USERPROFILE%\.codex\skills\chinese-ai-signal-crawler\.env` for skill-specific optional settings.
  - `%USERPROFILE%\.codex\skills\anysearch\.env` for `ANYSEARCH_API_KEY`.
- Baseline setup and smoke:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\chinese-ai-signal-crawler\scripts\setup_chinese_ai_signal_crawler.ps1 -RunNetworkSmoke
```

- Optional provider helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\chinese-ai-signal-crawler\scripts\assist_chinese_ai_signal_auth.ps1 -Provider anysearch
powershell -ExecutionPolicy Bypass -File .\skills\chinese-ai-signal-crawler\scripts\assist_chinese_ai_signal_auth.ps1 -Provider wechat
powershell -ExecutionPolicy Bypass -File .\skills\chinese-ai-signal-crawler\scripts\assist_chinese_ai_signal_auth.ps1 -Provider bilibili
powershell -ExecutionPolicy Bypass -File .\skills\chinese-ai-signal-crawler\scripts\assist_chinese_ai_signal_auth.ps1 -Provider mediacrawler
```

- Env vars:
  - AnySearch: `ANYSEARCH_API_KEY` optional; anonymous mode works with lower limits.
  - WeChat/Bilibili/MediaCrawler: no default secret env var; keep cookies, QR login artifacts, browser state, and platform sessions in each external tool's private runtime, not in this repo.
- Smoke tests:

```powershell
python .\skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-page --url https://www.qbitai.com/ --max-links 5
python .\skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-anysearch --query "机器之心 量子位 新智元 PaperWeekly AI" --max-results 2
```

Treat Chinese AI media, WeChat posts, Bilibili videos/comments, and platform captures as secondary or propagation evidence. Cross-check important claims against primary papers, official releases, repositories, or venue/company/lab pages before final synthesis.

## AI Lab Blog Intel

- Access type: no-key public baseline for first-party RSS/Atom, sitemap, and public HTML blog index crawling; optional API keys for AnySearch discovery, Apify managed crawler fallback, GitHub repository enrichment, and Hugging Face model/dataset enrichment.
- Preferred storage:
  - `%USERPROFILE%\.codex\skills\ai-lab-blog-intel\.env` for `APIFY_TOKEN`, optional `GITHUB_TOKEN`, and optional `HF_TOKEN`.
  - `%USERPROFILE%\.codex\skills\anysearch\.env` or the skill-specific `.env` for `ANYSEARCH_API_KEY`; anonymous AnySearch works with lower limits.
- Baseline setup and smoke:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\ai-lab-blog-intel\scripts\setup_ai_lab_blog_intel.ps1 -RunNetworkSmoke
```

- Optional provider helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider anysearch
powershell -ExecutionPolicy Bypass -File .\skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider apify
powershell -ExecutionPolicy Bypass -File .\skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider github
powershell -ExecutionPolicy Bypass -File .\skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider huggingface
```

- Env vars:
  - AnySearch: `ANYSEARCH_API_KEY` optional for higher live-discovery quota.
  - Apify: `APIFY_TOKEN` optional; ask before paid actor runs.
  - GitHub: `GITHUB_TOKEN` optional; use read-only/project-scoped tokens for enrichment.
  - Hugging Face: `HF_TOKEN` optional; public model/dataset pages often work without it.
- Smoke tests:

```powershell
python .\skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-feeds --org openai --max-entries 2
python .\skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-index --org anthropic --max-pages 1 --max-links 5
```

Treat AnySearch snippets and third-party generated feeds as discovery or secondary evidence. Canonical rows should come from first-party feeds, sitemaps, or public organization pages when available.

## OAuth MCP Providers

Use this pattern for Notion-like or other remote MCP providers that support OAuth:

```powershell
codex mcp add <server-name> --url <official-mcp-url>
powershell -ExecutionPolicy Bypass -File .\skills\external-api-onboarding\scripts\assist_oauth_login.ps1 `
  -ServerName <server-name>
```

The helper opens the official authorization URL in the default browser when Codex emits it. The user completes consent in the browser. Store only the MCP config and report login status, not tokens. If the provider has a stronger provider-specific visible-login helper, use that instead.

## GitHub, Hugging Face, Kaggle, and Similar API Keys

Verify official docs before setup because scope names and recommended env vars change.

Common env var candidates:

- GitHub: `GITHUB_TOKEN` or provider-specific token env var.
- Hugging Face: `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN`.
- Kaggle: `KAGGLE_USERNAME` and `KAGGLE_KEY`, often in a provider-specific config file rather than a generic `.env`.

Prefer read-only, project-scoped, expiring credentials. For organization/admin scopes, stop and ask. When a provider uses PAT/API-key auth instead of OAuth, open the official token creation page automatically, but make the user copy the secret into hidden local storage or an environment variable; never into chat.
