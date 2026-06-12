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
