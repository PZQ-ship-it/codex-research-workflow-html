---
name: google-scholar-profile-intel
description: Gather, crawl, and integrate scholar profile intelligence from Google Scholar author pages and open bibliographic sources without SerpApi. Use when Codex needs to collect or update a researcher profile, Google Scholar author publications, h-index/i10/citation summaries, coauthors, per-paper citation lists, OpenAlex enrichment, Apify actor inputs, normalized JSON/CSV outputs, or an evidence-backed scholar dossier.
---

# Google Scholar Profile Intel

## Overview

Use this skill to turn a scholar name, Google Scholar profile URL, or Scholar author ID into a structured researcher dossier. Route each request to the lightest reliable source that satisfies the user's actual need: local Scholar profile fetch, batch author IDs, deep per-paper citation crawling, managed Apify scraping, or OpenAlex enrichment.

SerpApi is intentionally excluded. Do not ask for SerpApi keys or use SerpApi APIs in this skill.

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
   - `report`: human-readable dossier or comparison table.
3. Run a route plan first unless the user already specifies the source:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py plan `
  --target "https://scholar.google.com/citations?user=AUTHOR_ID&hl=en" `
  --needs profile,indices,publications,enrichment
```

4. Execute only the required lane. Do not crawl citation pages when the user only needs profile or publication metadata.

## Source Routing

Use `references/source-routing.md` before choosing a data source.

- `scholarly`: default local fallback for single-author Scholar profile, selected sections, publications, and coauthors. Use low request volume and expect blocking.
- `scholar-scraper`: batch author IDs when the user wants a compact JSON of profile, citation history, coauthors, and publications.
- `google-scholar-citation-crawler`: heavy lane for per-paper citation lists, caching, resume, Excel exports, and long-running runs.
- `Apify Google Scholar Scraper`: managed paid/hosted lane when the user accepts Apify and needs reliability, residential proxies, or larger batches. Generate actor input first; do not spend credits without user approval.
- `OpenAlex`: open enrichment and cross-check lane for author disambiguation, ORCID, institutions, topics, works count, cited-by count, and h-index/i10 fields.

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

Use `scholarly` only after preparing an isolated environment if it is not already installed:

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

Print the normalized output contract:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py schema
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
- Do not run high-volume Google Scholar scraping by default. Google Scholar has no official API and direct scraping is fragile.
- Do not bypass CAPTCHAs automatically or pretend blocks are data absence. Pause and report the blocker.
- Do not download paywalled PDFs or private content. Metadata and public links are enough unless the user provides authorized files.
- Do not overwrite prior raw captures. Add timestamps or write to a new output directory.
- Do not trust a single source for identity when common names are involved. Cross-check affiliation, homepage, ORCID, coauthors, and publication titles.
- Keep API keys, proxy credentials, cookies, and browser headers out of committed files and final summaries.

## Resources

- `scripts/scholar_profile_intel.py`: route planner, OpenAlex fetcher, Apify input generator, optional `scholarly` fetcher, and schema printer.
- `references/source-routing.md`: when to call each crawler/API and what to avoid.
- `references/output-schema.md`: normalized JSON fields and source merge policy.
