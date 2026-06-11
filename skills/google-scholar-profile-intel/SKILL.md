---
name: google-scholar-profile-intel
description: Gather and integrate scholar profile intelligence from open bibliographic sources by default, with Google Scholar scraping only as optional best-effort. Use when Codex needs a no-required-SerpApi/no-required-paid-scraper closure for researcher profiles, OpenAlex author candidates, public citation metrics, topic/institution enrichment, OpenReview public evidence via openreview-py, paper-search-mcp setup/registration, official proceedings/API cross-checks, optional Google Scholar author/publication scraping, Apify actor inputs, normalized JSON/CSV outputs, or an evidence-backed scholar dossier.
---

# Google Scholar Profile Intel

## Overview

Use this skill to turn a scholar name, Google Scholar profile URL, Scholar author ID, or open bibliographic identifier into a structured researcher dossier. The default closure is OpenAlex-based and does not require SerpApi, Apify, Google Scholar scraping, private proxies, or API keys. Direct Google Scholar lanes are optional best-effort because Google Scholar has no official public API and can block automation.

SerpApi is intentionally excluded. Do not ask for SerpApi keys or use SerpApi APIs in this skill.

If the user asks for a complete, dependency-complete, or MCP-enabled setup, read `references/full-setup.md` and actively configure what can be made usable without secrets: isolated `openreview-py`, official `openreview-mcp` as `openreview_knowledge`, `acl-anthology`, `scholarly`, optional `paper-search-mcp`, and `paper_search_mcp` stdio registration. Credentials, Apify spend, proxies, and login-visible OpenReview data require explicit opt-in.

## Decision Tree

1. Identify the target:
   - Google Scholar profile URL or `user=` author ID;
   - author name plus affiliation or domain;
   - existing JSON/CSV profile export that needs enrichment or normalization.
2. Classify the requested depth:
   - `profile`: name, affiliation, interests, homepage, photo, total citations;
   - `indices`: h-index, i10-index, 5-year variants, citation history;
   - `publications`: publication list and citation counts;
   - `coauthors`: coauthor list;
   - `deep-citations`: citation list for each publication;
   - `enrichment`: DOI, venue, topic, institution, ORCID, OpenAlex cross-checks;
   - `openreview`: public submissions, decisions, reviews, forum IDs, and venue evidence;
   - `proceedings`: official accepted-paper/proceedings evidence;
   - `report`: human-readable dossier or comparison table.
3. Run a route plan first unless the user already specifies the source:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py plan `
  --target "https://scholar.google.com/citations?user=AUTHOR_ID&hl=en" `
  --needs profile,indices,publications,enrichment
```

4. Execute only the required lane. Default to `openalex-author`; do not crawl Google Scholar citation pages when the user only needs a usable open-source dossier.

## Full Local Setup

For a complete no-secret local setup with MCP registration:

```powershell
powershell -ExecutionPolicy Bypass -File skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RunNetworkSmoke -RegisterPaperSearchMcp
```

For the full MCP-enabled setup including OpenReview API knowledge tools:

```powershell
powershell -ExecutionPolicy Bypass -File skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RunNetworkSmoke -RegisterPaperSearchMcp -RegisterOpenReviewKnowledgeMcp
```

This installs isolated global-skill runtimes when the skill is installed under `%USERPROFILE%\.codex\skills\google-scholar-profile-intel`. It creates only an empty private `.env` placeholder if registering MCP. After MCP registration, verify with `codex mcp list`; a running Codex session may need restart before new MCP tools appear.

## Source Routing

Use `references/source-routing.md` before choosing a data source.

- `OpenAlex`: default open closure for author disambiguation, ORCID, institutions, topics, works count, cited-by count, and h-index/i10 fields.
- `OpenReview public + openreview-py`: public forum/venue/submission evidence for profile-to-paper/review cross-checks.
- `paper-search-mcp`: optional public-source breadth search after registration; use arXiv/PubMed/bioRxiv/medRxiv helpers first.
- `official proceedings/API`: ACL Anthology, CVF, PMLR, NeurIPS, arXiv, Crossref, Semantic Scholar, OpenAlex, and Unpaywall for publication evidence.
- `scholarly`: optional best-effort lane for single-author Google Scholar profile, selected sections, publications, and coauthors. Use only with `--allow-scholar-scrape`, low request volume, and expected blocking.
- `scholar-scraper`: optional external crawler for batch author IDs when the user explicitly accepts setup and blocking risk.
- `google-scholar-citation-crawler`: optional heavy lane for per-paper citation lists, caching, resume, Excel exports, and long-running runs.
- `Apify Google Scholar Scraper`: managed paid/hosted lane when the user accepts Apify and needs reliability, residential proxies, or larger batches. Generate actor input first; do not spend credits without user approval.

## Common Commands

Plan without network calls:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py plan `
  --target "Geoffrey Hinton University of Toronto" `
  --needs profile,publications,enrichment `
  --max-publications 100
```

Fetch OpenAlex candidates or inspect the exact URL first:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py openalex-author `
  --query "Geoffrey Hinton" `
  --institution-hint "University of Toronto" `
  --per-page 5 `
  --output output\scholars\hinton_openalex.json

python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py openalex-author `
  --query "Geoffrey Hinton" `
  --institution-hint "University of Toronto" `
  --dry-run
```

Generate Apify actor input without running the actor:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py apify-input `
  --author-id JicYPdAAAAAJ `
  --limit 100 `
  --output output\scholars\hinton_apify_input.json
```

Use `scholarly` only after the user accepts best-effort Google Scholar scraping and after preparing an isolated environment if it is not already installed:

```powershell
python -m venv output\scholars\.venv
output\scholars\.venv\Scripts\python -m pip install --upgrade pip
output\scholars\.venv\Scripts\python -m pip install scholarly
output\scholars\.venv\Scripts\python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py scholarly-author `
  --author-id JicYPdAAAAAJ `
  --sections basics,indices,counts,publications,coauthors `
  --max-publications 100 `
  --output output\scholars\hinton_scholarly.json
```

To include this optional lane in a plan, pass `--allow-scholar-scrape`.

Print the normalized output contract:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py schema
```

Check or repair the full local runtime:

```powershell
powershell -ExecutionPolicy Bypass -File skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RegisterPaperSearchMcp
```

## Output Contract

Write raw source captures and normalized artifacts separately:

- `raw_<source>_<author>.json`: unmodified or lightly sanitized source response;
- `author_profile.json`: normalized author object;
- `publications.csv` or `publications.json`: publication rows;
- `coauthors.csv` or `coauthors.json`: coauthor rows when requested;
- `citation_events.json`: per-paper citing works only when `deep-citations` is requested;
- `summary.md`: concise human-facing dossier with provenance and caveats.

Read `references/output-schema.md` before merging multiple sources. Always keep source provenance per field when values disagree.

## Guardrails

- Do not use SerpApi in this workflow.
- Default work must remain useful through OpenAlex/open bibliographic sources without Google Scholar scraping, SerpApi, Apify, private proxies, or API keys.
- Do not run high-volume Google Scholar scraping by default. Google Scholar has no official API and direct scraping is fragile.
- Do not use Google Scholar scraping or paper-search MCP's Google Scholar lane as canonical profile evidence without source-access caveats.
- Do not enable Sci-Hub-like fallbacks, Google Scholar proxy URLs, paid connectors, or private-record credentials as part of the default setup.
- Do not bypass CAPTCHAs automatically or pretend blocks are data absence. Pause and report the blocker.
- Do not download paywalled PDFs or private content. Metadata and public links are enough unless the user provides authorized files.
- Do not overwrite prior raw captures. Add timestamps or write to a new output directory.
- Do not trust a single source for identity when common names are involved. Cross-check affiliation, homepage, ORCID, coauthors, and publication titles.
- Keep API keys, proxy credentials, cookies, and browser headers out of committed files and final summaries.

## Resources

- `scripts/scholar_profile_intel.py`: route planner, OpenAlex fetcher, Apify input generator, optional `scholarly` fetcher, and schema printer.
- `scripts/setup_google_scholar_profile_intel.ps1`: safe setup script for isolated `openreview-py`, `acl-anthology`, `scholarly`, optional `paper-search-mcp`, and MCP registration.
- `references/full-setup.md`: complete setup matrix, optional MCP boundaries, credentials policy, official proceedings/API closure, and smoke tests.
- `references/source-routing.md`: when to call each crawler/API and what to avoid.
- `references/output-schema.md`: normalized JSON fields and source merge policy.
