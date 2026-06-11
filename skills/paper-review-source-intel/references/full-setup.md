# Full Setup

Use this reference when the user asks to configure the complete `paper-review-source-intel` setup. The safe default is a no-secret local toolchain plus public official sources. Optional MCP servers and credentials are opt-in only.

## Safe Default

Run the setup script from the repo or from the installed global skill:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\paper-review-source-intel\scripts\setup_paper_review_source_intel.ps1 -RunNetworkSmoke
```

The script defaults to the user-level global skill directory when it exists:

```text
%USERPROFILE%\.codex\skills\paper-review-source-intel
```

It creates isolated runtimes under `runtime/`:

- `openreview-py`: official Python client for public OpenReview API access and custom scripts.
- `acl-anthology`: official ACL Anthology metadata package for ACL/EMNLP/NAACL/COLING evidence.

Do not commit `runtime/`, `.env`, cookies, browser storage, downloaded PDFs, or raw crawl outputs.

## Source Facts

- OpenReview's docs describe API 2 as the current API and show installing `openreview-py` with `pip install openreview-py`.
- `openreview/openreview-mcp` is a knowledge MCP for writing correct `openreview-py` code. It is not required for public review capture and does not need an API token.
- `acl-org/acl-anthology` contains metadata for ACL Anthology papers, authors, and venues plus a Python package for accessing the metadata.
- `openags/paper-search-mcp` is a broad paper search/download MCP. Its own docs describe optional API keys, bot-detection limitations, and optional Sci-Hub fallback behavior.

Primary URLs:

- https://docs.openreview.net/getting-started/using-the-api
- https://docs.openreview.net/getting-started/using-the-api/installing-and-instantiating-the-python-client
- https://github.com/openreview/openreview-mcp
- https://github.com/acl-org/acl-anthology
- https://github.com/openags/paper-search-mcp

## Optional MCPs

### OpenReview Knowledge MCP

Use only when Codex needs API signatures, examples, and best practices while writing `openreview-py` scripts.

It is knowledge-only. It is distributed as a Docker-based server, so Docker or an already running HTTP endpoint is required. Register it only after the server is running:

```powershell
codex mcp add openreview_knowledge --url http://localhost:8080/mcp
```

Equivalent script form:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\paper-review-source-intel\scripts\setup_paper_review_source_intel.ps1 -RegisterOpenReviewKnowledgeMcp -OpenReviewKnowledgeMcpUrl http://localhost:8080/mcp
```

This does not replace public OpenReview capture. It helps write code.

### Paper Search MCP

Use only as a convenience layer after the public-source route is understood. Keep source provenance in `manifest.json` and normalized rows.

Install but do not register:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\paper-review-source-intel\scripts\setup_paper_review_source_intel.ps1 -InstallPaperSearchMcp
```

Register only after the user explicitly accepts the optional connector boundary:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\paper-review-source-intel\scripts\setup_paper_review_source_intel.ps1 -RegisterPaperSearchMcp -AllowOptionalRestrictedConnectors
```

Keep these disabled unless explicitly authorized by the user:

- Sci-Hub fallback.
- Google Scholar proxy URLs.
- IEEE/ACM keys, paid connectors, private records, or closed-access downloads.

## Optional Credentials

Use `$external-api-onboarding` before setting any of these. Store values only in a private user-level `.env` or user environment variables.

Recommended private path:

```text
%USERPROFILE%\.codex\skills\paper-review-source-intel\.env
```

Common variables:

- `PAPER_SEARCH_MCP_UNPAYWALL_EMAIL`: enables Unpaywall in paper-search-mcp.
- `PAPER_SEARCH_MCP_CORE_API_KEY`: improves CORE reliability.
- `PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY`: improves Semantic Scholar rate limits.
- `PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN`: only for private Zenodo records when user-authorized.
- `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`: only for user-authorized login-visible data, never for bypassing private reviews or venue controls.

Never print, summarize, screenshot, commit, or paste secret values.

## Smoke Tests

Planner:

```powershell
python %USERPROFILE%\.codex\skills\paper-review-source-intel\scripts\paper_review_source_intel.py plan --target "ICLR 2025 retrieval augmented generation" --venue ICLR --year 2025 --needs papers,reviews,decisions,pdfs,report
```

OpenReview public API:

```powershell
%USERPROFILE%\.codex\skills\paper-review-source-intel\runtime\openreview-py\.venv\Scripts\python.exe -c "import json, openreview; c=openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net'); g=c.get_group('ICLR.cc/2025/Conference'); print(json.dumps({'ok': True, 'group_id': g.id}, ensure_ascii=False))"
```

ACL Anthology import:

```powershell
%USERPROFILE%\.codex\skills\paper-review-source-intel\runtime\acl-anthology\.venv\Scripts\python.exe -c "from acl_anthology import Anthology; print('ok')"
```

Dependency integrity:

```powershell
%USERPROFILE%\.codex\skills\paper-review-source-intel\runtime\openreview-py\.venv\Scripts\python.exe -m pip check
%USERPROFILE%\.codex\skills\paper-review-source-intel\runtime\acl-anthology\.venv\Scripts\python.exe -m pip check
```
