# Security Policy

Use this reference before touching credentials, OAuth, provider consoles, browser sessions, or Codex MCP configuration.

## Core Rules

- Never ask the user to paste real secrets into chat.
- Never print, summarize, screenshot, log, or commit API keys, bearer tokens, OAuth tokens, cookies, auth headers, private URLs containing tokens, or browser storage.
- Do not read existing `.env` values unless replacing one specific key requires parsing the file. If parsed, do not display values.
- Prefer private user-level storage over repo-local storage:
  - `%USERPROFILE%\.codex\skills\<skill-name>\.env`
  - user environment variables
  - `%USERPROFILE%\.codex\config.toml` for MCP server definitions
- Treat repo-local `.env`, `cookies.json`, `auth.json`, browser storage state, and token dumps as private and untracked unless the user explicitly says otherwise.
- Use least privilege: narrow scopes, short expiry, read-only access, and provider-specific project keys when available.

## Browser and OAuth Guardrails

Allowed browser assistance:

- Navigate to official provider docs, provider consoles, or official OAuth login pages.
- Automatically open official auth targets when user action is required, including OAuth authorization URLs, login pages, API-key consoles, and token-creation pages.
- Read non-secret page text, field labels, scope names, button labels, and success/error status.
- Help fill non-secret metadata such as key names, app names, local callback URLs, redirect URIs, or descriptions.
- Pause for the user to complete login, MFA, CAPTCHA, consent, key reveal, or key copy.

Forbidden browser assistance:

- Bypassing MFA, CAPTCHA, rate limits, paywalls, SSO controls, or account restrictions.
- Extracting secret values from the page state, network panel, screenshots, clipboard, cookies, local storage, or headers.
- Creating broad admin, billing, production-write, or organization-wide keys when a narrower key is enough.
- Regenerating, deleting, rotating, or disabling credentials without explicit user confirmation.

For OAuth MCP servers, prefer the official client flow:

```powershell
codex mcp add <server-name> --url <official-mcp-url>
codex mcp login <server-name>
```

The user should complete the browser consent flow. When possible, wrap `codex mcp login` with `scripts/assist_oauth_login.ps1` or a provider-specific helper so the emitted official authorization URL is opened automatically. Report only whether login appears complete.

If a provider uses PAT/API-key auth instead of OAuth, open the official token/key creation page in the browser, then use hidden local storage such as `scripts/set_env_secret.ps1` or a user environment variable. Do not ask the user to paste the secret into chat.

## Command and Storage Rules

- Prefer hidden prompts for real API keys. Use `scripts/set_env_secret.ps1` rather than command-line `-Value`.
- Use command-line `-Value` only for dummy dry-runs, tests, or explicit non-interactive automation where the user accepts command-history risk.
- Before writing global config, state the target path and what key/server name will be changed.
- Before installing or running an MCP package with `npx`, `uvx`, `pipx`, or similar, make clear that it will execute provider/package code.
- If a command prints an authorization URL instead of opening a browser, capture/open that URL with an assisted helper when feasible.
- For paid APIs, image generation, write-capable endpoints, or destructive actions, ask before the first real request.

## Reporting

Final summaries may include:

- provider name
- env var name
- storage path
- MCP server name
- command shape with placeholders
- smoke-test result
- blocker and next human action

Final summaries must not include:

- secret values or prefixes/suffixes
- OAuth tokens
- cookies or browser storage
- copied auth headers
- screenshots that reveal keys
- provider account private details unrelated to setup

## External References

- OpenAI Codex Skills: https://developers.openai.com/codex/skills
- OpenAI Codex MCP: https://developers.openai.com/codex/mcp
- Browser Use MCP server: https://docs.browser-use.com/open-source/customize/integrations/mcp-server
- MCP authorization guidance: https://modelcontextprotocol.io/docs/tutorials/security/authorization
