# Full Setup

Use this reference when the user asks to complete, repair, or MCP-enable `google-scholar-profile-intel`. The default closure remains open-source and no-secret. MCP registration is allowed for no-secret public-source servers; credentials, paid hosted scraping, proxies, and restricted connectors are opt-in only.

## Safe Default

Run from the repo or from the installed global skill:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RunNetworkSmoke -RegisterPaperSearchMcp -RegisterOpenReviewKnowledgeMcp
```

The script defaults to the user-level global skill directory when it exists:

```text
%USERPROFILE%\.codex\skills\google-scholar-profile-intel
```

It creates isolated runtimes under `runtime/`:

- `openreview-py`: OpenReview public API/custom scripts for author/forum/profile cross-checks.
- `openreview-mcp`: official OpenReview knowledge MCP, installed from `openreview/openreview-mcp` and registered as `openreview_knowledge` when requested.
- `acl-anthology`: official ACL Anthology metadata for NLP proceedings and author-paper corroboration.
- `scholarly`: optional best-effort single-profile Google Scholar fetch, bounded and blocker-aware.
- `paper-search-mcp`: optional stdio MCP for public arXiv/PubMed/bioRxiv/medRxiv breadth search.

Do not commit `runtime/`, `.env`, cookies, browser storage, downloaded PDFs, or raw crawl outputs.

## Source Facts

- Google Scholar has no official public API; direct scraping is optional best-effort and can be blocked.
- OpenAlex is the default open author-disambiguation and enrichment backbone.
- OpenReview's docs describe API 2 as the current API and show installing `openreview-py`.
- `openreview/openreview-mcp` is a knowledge MCP for writing correct `openreview-py` code; it is not required for public profile closure and requires a running HTTP MCP endpoint.
- `paper-search-mcp` can be registered as a no-secret stdio MCP, but treat Google Scholar scraping and download/read tools as non-canonical helpers requiring access checks.
- Official proceedings/API sources such as ACL Anthology, CVF Open Access, PMLR, NeurIPS proceedings, arXiv, Crossref, OpenAlex, Semantic Scholar, and Unpaywall should be preferred for publication evidence.

Primary URLs:

- https://docs.openreview.net/getting-started/using-the-api
- https://docs.openreview.net/getting-started/using-the-api/installing-and-instantiating-the-python-client
- https://github.com/openreview/openreview-mcp
- https://github.com/openags/paper-search-mcp
- https://github.com/acl-org/acl-anthology
- https://docs.openalex.org/

## MCP Registration

### Paper Search MCP

Register the no-secret stdio MCP when the user asks for a full MCP-enabled setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RegisterPaperSearchMcp
```

Then verify:

```powershell
codex mcp list
```

After registration, restart Codex if the current session does not show new MCP tools. Prefer public arXiv/PubMed/bioRxiv/medRxiv tools for breadth. Do not treat Google Scholar scraping as canonical evidence.

### OpenReview Knowledge MCP

Use when Codex needs API signatures, examples, and best practices while writing `openreview-py` scripts. The setup script can install the official repository into a local venv and register stdio MCP without Docker:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RegisterOpenReviewKnowledgeMcp
```

If a long-running HTTP service already exists, register that endpoint instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RegisterOpenReviewKnowledgeMcp -OpenReviewKnowledgeMcpUrl http://localhost:8080/mcp
```

This does not replace public OpenReview capture. It helps write code.

## Optional Credentials

Use `$external-api-onboarding` before setting any of these. Store values only in a private user-level `.env` or user environment variables.

Recommended private path:

```text
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\.env
```

Common optional variables:

- `OPENALEX_MAILTO`: polite OpenAlex contact email; not secret.
- `PAPER_SEARCH_MCP_UNPAYWALL_EMAIL`: enables Unpaywall in paper-search-mcp.
- `PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY`: improves Semantic Scholar rate limits.
- `PAPER_SEARCH_MCP_CORE_API_KEY`: improves CORE reliability.
- `APIFY_TOKEN`: only after the user approves paid/hosted scraping.
- `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`: only for user-authorized login-visible data, never for bypassing private reviews or venue controls.

Never print, summarize, screenshot, commit, or paste secret values.

## Official Proceedings/API Closure

For publication and profile evidence, route through:

- OpenAlex author and works APIs for identity, ORCID, institutions, topics, counts, coauthors, and cited-by counts.
- OpenReview public pages/API and `openreview-py` for public submissions, reviews, decisions, forum IDs, and author-visible venue evidence.
- ACL Anthology Python package or metadata for ACL/EMNLP/NAACL/COLING papers.
- CVF Open Access for CVPR/ICCV/WACV.
- PMLR volume pages for ICML/AISTATS/COLT.
- NeurIPS proceedings for accepted papers.
- arXiv, Crossref, Semantic Scholar, and Unpaywall for DOI/OA PDF/enrichment cross-checks.

## Smoke Tests

Planner:

```powershell
python %USERPROFILE%\.codex\skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py plan --target "Geoffrey Hinton University of Toronto" --needs profile,publications,enrichment,proceedings,openreview
```

OpenAlex dry-run:

```powershell
python %USERPROFILE%\.codex\skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py openalex-author --query "Geoffrey Hinton" --institution-hint "University of Toronto" --dry-run
```

OpenReview public API:

```powershell
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\openreview-py\.venv\Scripts\python.exe -c "import json, openreview; c=openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net'); g=c.get_group('ICLR.cc/2025/Conference'); print(json.dumps({'ok': True, 'group_id': g.id}, ensure_ascii=False))"
```

OpenReview knowledge MCP:

```powershell
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\openreview-mcp\.venv\Scripts\python.exe -m pip check
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\openreview-mcp\.venv\Scripts\python.exe -c "import openreview_mcp; print('ok')"
codex mcp list
```

Paper Search MCP:

```powershell
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\paper-search-mcp\.venv\Scripts\python.exe -m pip check
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\paper-search-mcp\.venv\Scripts\python.exe -c "import paper_search_mcp; print('ok')"
codex mcp list
```
