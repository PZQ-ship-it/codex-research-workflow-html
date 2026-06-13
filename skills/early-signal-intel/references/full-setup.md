# Full Setup

Use this file when the user asks to make `early-signal-intel` fully usable, configure optional providers, repair credentials, or run setup smoke tests. Always apply `$external-api-onboarding` security rules before handling secrets.

## Baseline No-Key Setup

The baseline requires only Python standard library and network access:

```powershell
powershell -ExecutionPolicy Bypass -File skills\early-signal-intel\scripts\setup_early_signal_intel.ps1 -RunNetworkSmoke
```

This checks:

- `schema` command;
- HN Algolia no-key search;
- RSS fetch against a small first-party feed.

No `.env` values are required.

## Optional Private Env

Optional secrets belong only in:

```text
%USERPROFILE%\.codex\skills\early-signal-intel\.env
```

Never put real keys in repo-local files, docs, examples, chat, command-line `-Value`, screenshots, or final summaries.

## Optional Python Runtime

For provider SDKs, use an isolated user-level runtime. The helper looks for Python >= 3.10 and can also take an explicit executable:

```powershell
powershell -ExecutionPolicy Bypass -File skills\early-signal-intel\scripts\setup_early_signal_intel.ps1 -InstallOptionalPythonRuntime
```

```powershell
powershell -ExecutionPolicy Bypass -File skills\early-signal-intel\scripts\setup_early_signal_intel.ps1 `
  -InstallOptionalPythonRuntime `
  -PythonExe "C:\ProgramData\Anaconda3\envs\devdefender-lab\python.exe"
```

This installs optional packages into:

```text
%USERPROFILE%\.codex\skills\early-signal-intel\runtime\python\.venv
```

Packages:

- `atproto`
- `praw`
- `feedparser`
- `alphaxiv-py` only when the selected runtime is Python >= 3.12

The core CLI does not require these packages.

## Provider Setup Through External API Onboarding

Use the helper below. It opens official provider pages and delegates secret storage to the `external-api-onboarding` hidden prompt helper.

```powershell
powershell -ExecutionPolicy Bypass -File skills\early-signal-intel\scripts\assist_early_signal_auth.ps1 -Provider alphaxiv
```

Supported providers:

| Provider | Official page opened | Env vars |
| --- | --- | --- |
| `alphaxiv` | `https://alphaxiv.org` | `ALPHAXIV_API_KEY` |
| `reddit` | `https://www.reddit.com/prefs/apps` | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` |
| `bluesky` | `https://bsky.app/settings/app-passwords` | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` |
| `x` | `https://developer.x.com/en/portal/dashboard` | `X_BEARER_TOKEN` |

Use `-DryRun` to validate command shape without opening pages or prompting.

## Smoke Tests

### HN

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py fetch-hn `
  --query "alphaXiv arXiv discussion" `
  --max-results 2
```

### HN Thread

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py fetch-hn `
  --item-id 41478690 `
  --include-comments `
  --max-comments 3
```

### RSS

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py fetch-rss `
  --feed https://openai.com/news/rss.xml `
  --max-entries 2
```

### Normalization

```powershell
python skills\early-signal-intel\scripts\early_signal_intel.py normalize `
  --input output\early_signal\raw\hn_search.json `
  --source hn `
  --output-dir output\early_signal\normalized
```

### alphaXiv

After optional runtime and optional key:

```powershell
%USERPROFILE%\.codex\skills\early-signal-intel\runtime\python\.venv\Scripts\python.exe -m pip show alphaxiv-py
```

Then use the `alphaxiv` CLI according to its current help. Public read commands should be tested before authenticated/write-capable commands.

### Bluesky

After optional runtime:

```powershell
%USERPROFILE%\.codex\skills\early-signal-intel\runtime\python\.venv\Scripts\python.exe -c "import atproto; print('atproto ok')"
```

Use bounded windows or seed-account lookups.

### Reddit

After OAuth env setup:

```powershell
%USERPROFILE%\.codex\skills\early-signal-intel\runtime\python\.venv\Scripts\python.exe -c "import praw; print('praw ok')"
```

Do not run bulk subreddit crawls until a small read-only request succeeds and rate limits are understood.

## Closeout Checklist

- No-key HN/RSS smoke tests pass or blockers are recorded.
- Optional providers store secrets only in the private user-level `.env`.
- No secret values are printed, committed, or summarized.
- Any paid/write-capable provider request is explicitly approved before running.
- The final report lists provider names, env var names, storage path, commands run, smoke-test status, and restart requirements only.
