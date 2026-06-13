# Full Setup

Use this reference when the user asks to complete, repair, or API-enable `conference-workshop-intel`. The safe default is a no-secret local workflow using public official pages, OpenReview public visibility, ai-workshop-tracker, ACL Anthology, CVF Open Access, PMLR, and NeurIPS proceedings.

## Safe Default

Run from the repo or from the installed global skill:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\conference-workshop-intel\scripts\setup_conference_workshop_intel.ps1 -RunNetworkSmoke
```

The script defaults to the user-level global skill directory when it exists:

```text
%USERPROFILE%\.codex\skills\conference-workshop-intel
```

It creates:

- `runtime/conference-workshop/.venv`: isolated Python runtime for public crawling helpers.
- `runtime/source-repos/ai-workshop-tracker`: optional clone when `-CloneWorkshopTracker` is passed.
- `.env`: private placeholder for optional credentials. Do not commit it.

Default Python packages:

- `requests`, `beautifulsoup4`, `lxml`, `PyYAML` for page and structured-data parsing.
- `openreview-py` for OpenReview public API queries.
- `acl-anthology` for official ACL metadata.

Do not commit `runtime/`, `.env`, cookies, browser storage, downloaded PDFs, raw crawl outputs, or credential-bearing logs.

## Source Facts

Primary public routes:

- OpenReview Python client docs: `https://openreview-py.readthedocs.io/`
- OpenReview API docs: `https://docs.openreview.net/getting-started/using-the-api`
- ai-workshop-tracker: `https://github.com/Yeping-Hu/ai-workshop-tracker`
- ACL Anthology metadata package: `https://github.com/acl-org/acl-anthology`
- ACL Anthology development/API notes: `https://aclanthology.org/info/development/`
- CVF Open Access: `https://openaccess.thecvf.com/`
- PMLR: `https://proceedings.mlr.press/`
- NeurIPS proceedings: `https://papers.nips.cc/`

## Optional Credentials

Required credentials: none for the default closure.

Use `$external-api-onboarding` before setting any optional credential. Store values only in private user-level storage or user environment variables. Never paste secrets into chat.

Recommended private path:

```text
%USERPROFILE%\.codex\skills\conference-workshop-intel\.env
```

Optional variables:

- `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`: only for user-authorized OpenReview data visible to that account. Do not use them to bypass private reviews or venue controls.
- `SEMANTIC_SCHOLAR_API_KEY`: optional enrichment and higher rate limits for paper/citation matching.
- `GITHUB_TOKEN`: optional for higher GitHub API limits or authenticated clone/API operations.
- `HF_TOKEN`: optional only when a selected benchmark/workshop dataset is on Hugging Face and public reads are insufficient.
- `PAPER_SEARCH_MCP_UNPAYWALL_EMAIL`, `PAPER_SEARCH_MCP_CORE_API_KEY`, `PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY`: optional if routing through `paper-review-source-intel` or paper-search MCP for enrichment.

Hidden local storage example:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\external-api-onboarding\scripts\set_env_secret.ps1 `
  -EnvFile "$env:USERPROFILE\.codex\skills\conference-workshop-intel\.env" `
  -Name SEMANTIC_SCHOLAR_API_KEY
```

For environment variables used by Codex or MCP servers, the Codex process must actually see the variable. A `.env` file alone is not enough unless the launcher loads it.

## Visible Provider Assistance

Open official provider pages without handling secrets:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\conference-workshop-intel\scripts\assist_conference_workshop_auth.ps1 -Provider openreview,semantic-scholar,github
```

The helper opens only official login/token pages and prints storage command shapes. The user completes login, MFA, CAPTCHA, token creation, and secret copy.

## Optional ai-workshop-tracker Clone

Clone or update the structured workshop tracker:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\conference-workshop-intel\scripts\setup_conference_workshop_intel.ps1 -SkipPythonDeps -CloneWorkshopTracker
```

Destination:

```text
%USERPROFILE%\.codex\skills\conference-workshop-intel\runtime\source-repos\ai-workshop-tracker
```

Use its YAML data and committed OpenReview caches as structured input, but verify official pages before reporting policy, deadlines, or final accepted-paper counts.

## Smoke Tests

Planner:

```powershell
python %USERPROFILE%\.codex\skills\conference-workshop-intel\scripts\conference_workshop_intel.py plan --target "NeurIPS 2025 workshops accepted papers CFP review policy" --venue NeurIPS --year 2025 --needs workshops,accepted-papers,cfp,policy,awards,report
```

URL inspection:

```powershell
python %USERPROFILE%\.codex\skills\conference-workshop-intel\scripts\conference_workshop_intel.py inspect-url "https://openaccess.thecvf.com/ICCV2025"
```

Public source reachability:

```powershell
python %USERPROFILE%\.codex\skills\conference-workshop-intel\scripts\conference_workshop_intel.py public-smoke
```

Python runtime import:

```powershell
%USERPROFILE%\.codex\skills\conference-workshop-intel\runtime\conference-workshop\.venv\Scripts\python.exe -c "import requests, bs4, yaml, openreview; from acl_anthology import Anthology; print('ok')"
```

Dependency integrity:

```powershell
%USERPROFILE%\.codex\skills\conference-workshop-intel\runtime\conference-workshop\.venv\Scripts\python.exe -m pip check
```

If a newly installed skill or configured environment is not visible to an already-running Codex session, restart Codex.
