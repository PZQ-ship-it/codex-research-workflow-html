# External API Closure For Skill Evals

Most skill evals should run without external credentials. Use external setup only when the skill under test genuinely depends on live provider access, remote MCP tools, browser login, or source discovery.

## Default Closure

1. Classify the provider need.
   - No-auth local: `quick_validate.py`, local scripts, local artifacts.
   - Public remote no-auth: official docs, public RSS/API, public pages.
   - API key: AnySearch, GitHub PAT, Hugging Face token, Kaggle credentials, provider-specific keys.
   - OAuth MCP: remote MCP servers such as OpenAI Developer Docs MCP or similar official providers.
   - Browser-assisted login: provider console, visible auth, or CAPTCHA/MFA.
2. Invoke `$external-api-onboarding` before live setup.
3. Store credentials only in private user-level storage, usually:

```text
%USERPROFILE%\.codex\skills\<provider-skill>\.env
%USERPROFILE%\.codex\config.toml
```

4. Run the smallest read-only smoke test.
5. Record only status, env var names, paths, server names, and command shapes. Never record secret values.

## Common Optional Providers

### AnySearch

Use when skill eval needs live web/source discovery. Anonymous mode is acceptable for low-volume checks.

- Env var: `ANYSEARCH_API_KEY`
- Preferred storage: `%USERPROFILE%\.codex\skills\anysearch\.env`
- Smoke test:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py doc
```

### OpenAI Developer Docs MCP

Use when the skill eval needs current official OpenAI/Codex documentation.

- Usually no API key.
- MCP shape:

```powershell
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

- Smoke test: list MCP servers or perform one tiny official-doc lookup when MCP tools are available.

### GitHub, Hugging Face, Kaggle

Use only when public unauthenticated access is insufficient.

- Prefer read-only, scoped, expiring tokens.
- Ask before organization/admin/write scopes.
- Use `$external-api-onboarding` to open official token pages and store secrets through hidden local prompts.

## Paid Or Write-Capable APIs

Ask before the first real request when a provider can incur cost, mutate remote state, create issues, upload files, generate images, or trigger jobs.

## Reporting Template

```text
External API Closure
- Provider:
- Access type:
- Env var or MCP server name:
- Private storage path:
- Smoke test:
- Status:
- Restart needed:
```
