# Full Setup

Use this file when the user asks to make `chinese-ai-signal-crawler` fully usable, configure optional providers, repair credentials, or run smoke tests. Always apply `$external-api-onboarding` security rules before handling secrets, cookies, OAuth, login pages, browser state, or MCP configuration.

## Baseline No-Key Setup

The baseline requires Python and network access only:

```powershell
powershell -ExecutionPolicy Bypass -File skills\chinese-ai-signal-crawler\scripts\setup_chinese_ai_signal_crawler.ps1 -RunNetworkSmoke
```

This checks:

- `schema` command;
- route planning;
- public page capture against a small Chinese AI media page;
- AnySearch CLI `doc` if the AnySearch skill is installed.

No `.env` values are required.

## Private Storage

Optional secrets and provider-specific settings belong only in private user-level paths:

```text
%USERPROFILE%\.codex\skills\chinese-ai-signal-crawler\.env
%USERPROFILE%\.codex\skills\anysearch\.env
```

Never put real keys, cookies, QR login artifacts, browser storage, proxies, account identifiers, or token dumps in repo-local files, docs, examples, chat, command-line `-Value`, screenshots, or final summaries.

## Provider Setup Through External API Onboarding

Use the helper below. It opens official pages or source repositories and delegates secret storage to the `external-api-onboarding` hidden prompt helper when a secret is needed.

```powershell
powershell -ExecutionPolicy Bypass -File skills\chinese-ai-signal-crawler\scripts\assist_chinese_ai_signal_auth.ps1 -Provider anysearch
```

Supported providers:

| Provider | Page opened | Env vars / state |
| --- | --- | --- |
| `anysearch` | `https://anysearch.com/console/api-keys` | `ANYSEARCH_API_KEY` in `%USERPROFILE%\.codex\skills\anysearch\.env` |
| `wechat` | `wespy-plus` and related source/setup pages | no default secret; login/cookies remain tool-local and user-controlled |
| `bilibili` | Bilibili crawler source pages | no default secret; login cookies remain tool-local and user-controlled |
| `mediacrawler` | MediaCrawler source page | no default secret; platform login state remains tool-local and user-controlled |

Use `-DryRun` to validate command shape without opening pages or prompting.

## Optional Tooling

### AnySearch

AnySearch is optional but recommended for discovery and can run anonymously with lower limits:

```powershell
python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py doc
```

Live smoke:

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-anysearch `
  --query "机器之心 量子位 新智元 PaperWeekly AI" `
  --max-results 3
```

If quota is exhausted, configure `ANYSEARCH_API_KEY` through the assisted helper. Do not paste the key into chat.

### WeChat

Use WeChat tools only after user approval and visible login when needed. Preferred light tool:

```powershell
wespy-plus "https://mp.weixin.qq.com/s/xxxxx" --output-json
```

For datasets needing reading/like/comment metrics, use a dedicated research crawler only with explicit approval because it may depend on WeChat PC, Fiddler, local login state, or browser automation.

### Bilibili

Use small captures first:

```powershell
python bilibili-crawler.py
```

For comments, use bounded runs and resume files. Do not run broad comment crawls until a small read-only capture succeeds and blockers are recorded.

### MediaCrawler

Use MediaCrawler for multi-platform self-media capture only after reading its current README and legal disclaimer. Keep tasks small, use visible user login, and export raw JSON/CSV into the run `raw/` directory.

## Smoke Tests

### Schema

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py schema
```

### Plan

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py plan `
  --target "中文AI圈 diffusion" `
  --needs media,anysearch,report
```

### Public Page

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py fetch-page `
  --url https://www.qbitai.com/ `
  --max-links 5
```

### Normalize

```powershell
python skills\chinese-ai-signal-crawler\scripts\chinese_ai_signal_crawler.py normalize `
  --input output\chinese_ai_signal\raw\media_pages.json `
  --source media-page `
  --output-dir output\chinese_ai_signal\normalized
```

## Closeout Checklist

- No-key schema/plan smoke tests pass.
- Optional AnySearch page/CLI route is available or blocker is recorded.
- Optional provider secrets are stored only in private user-level storage.
- No secret values, cookies, auth headers, browser storage, or account-private details are printed, committed, or summarized.
- Final report lists provider names, env var names, storage paths, commands run, smoke-test status, and restart requirements only.
