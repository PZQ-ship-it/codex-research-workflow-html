# Full Setup

The no-key baseline needs only Python 3.8+ from the standard library. Optional providers are for discovery, managed crawling, or higher-volume jobs and must be configured through `$external-api-onboarding`.

## No-Key Baseline

Run:

```powershell
powershell -ExecutionPolicy Bypass -File skills\ai-lab-blog-intel\scripts\setup_ai_lab_blog_intel.ps1 -RunNetworkSmoke
```

This checks:

- Python can run the helper script.
- `schema` and `plan` commands work.
- A small first-party RSS smoke test can fetch at least one entry.

No API key or login is required.

## Optional Providers

| Provider | Purpose | Env vars | Preferred private storage | Smoke test |
| --- | --- | --- | --- | --- |
| AnySearch | Live discovery and current source verification | `ANYSEARCH_API_KEY` | `%USERPROFILE%\.codex\skills\anysearch\.env` or `%USERPROFILE%\.codex\skills\ai-lab-blog-intel\.env` | `anysearch_cli.py doc`; optional tiny search |
| Apify | Managed crawler fallback for specific public pages | `APIFY_TOKEN` | `%USERPROFILE%\.codex\skills\ai-lab-blog-intel\.env` | list actor metadata or dry-run docs; ask before paid run |
| GitHub | Inspect open-source feed/crawler repos | `GITHUB_TOKEN` optional | user environment or provider-specific private `.env` | read-only API call or unauthenticated page fetch |
| Hugging Face | Enrich linked model/dataset cards | `HF_TOKEN` optional | user environment or provider-specific private `.env` | public model/dataset metadata read |

Do not configure broad organization/admin/write scopes for this skill. Read-only public discovery is enough for normal use.

## Assisted Credential Setup

Use the helper when the user explicitly asks to configure optional providers:

```powershell
powershell -ExecutionPolicy Bypass -File skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider anysearch
powershell -ExecutionPolicy Bypass -File skills\ai-lab-blog-intel\scripts\assist_ai_lab_blog_auth.ps1 -Provider apify
```

The helper follows `$external-api-onboarding` rules:

- opens official provider pages when appropriate;
- writes only to private user-level `.env` files;
- uses hidden prompts for secrets;
- does not print secret values.

## Private `.env` Template

A non-secret template can be kept in the skill directory as `.env.example`:

```dotenv
# Optional only. No key is required for first-party RSS/sitemap/index crawling.
ANYSEARCH_API_KEY=
APIFY_TOKEN=
GITHUB_TOKEN=
HF_TOKEN=
```

The real file should be:

`%USERPROFILE%\.codex\skills\ai-lab-blog-intel\.env`

Never commit the real `.env`.

## Suggested Smoke Tests

No-key script checks:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py schema
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py plan --target "OpenAI and Anthropic model release posts" --org openai --org anthropic
```

Feed smoke:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-feeds `
  --org openai `
  --max-entries 2 `
  --output output\ai_lab_blog\smoke\raw\openai_feed.json
```

Index smoke:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py fetch-index `
  --org anthropic `
  --max-pages 1 `
  --output output\ai_lab_blog\smoke\raw\anthropic_index.json
```

Normalize smoke:

```powershell
python skills\ai-lab-blog-intel\scripts\ai_lab_blog_intel.py normalize `
  --input output\ai_lab_blog\smoke\raw\openai_feed.json `
  --source feed `
  --output-dir output\ai_lab_blog\smoke\normalized
```

## Restart Notes

No Codex restart is needed for script use. If the skill is copied into the global skills folder, an already-running Codex session may need restart before the new skill trigger metadata appears.
