---
name: paper-review-source-intel
description: Route first-source academic paper and peer-review intelligence collection, crawling, normalization, and synthesis through public official sources by default. Use when Codex needs a no-required-MCP/no-required-API-key closure for papers, proceedings metadata, public OpenReview visibility, open-access PDFs, citation/author enrichment, or auditable evidence corpora from arXiv, OpenReview public pages, ACL Anthology, CVF, PMLR, NeurIPS proceedings, Semantic Scholar, OpenAlex, Crossref, Unpaywall, or optional paper-search-mcp.
---

# Paper Review Source Intel

## Overview

Use this skill for first-source paper and peer-review evidence collection. The default closure uses public official pages/APIs, proceedings, and open metadata before general web search or unofficial crawlers. It must remain usable without required MCP servers, paid services, private credentials, or login-gated review data.

## Decision Tree

1. Identify the target:
   - topic or keyword paper search;
   - venue/year accepted-paper corpus;
   - OpenReview forum, venue, reviews, meta-review, rebuttal, decision, or score distribution;
   - arXiv ID, DOI, ACL Anthology ID, CVF/PMLR/NeurIPS URL;
   - author/citation enrichment;
   - PDF/full-text acquisition.
2. Run a route plan before installing or crawling:

```powershell
python skills\paper-review-source-intel\scripts\paper_review_source_intel.py plan `
  --target "ICLR 2025 retrieval augmented generation" `
  --venue ICLR `
  --year 2025 `
  --needs papers,reviews,decisions,pdfs,report
```

3. Execute only the required lane:
   - OpenReview reviews/decisions/rebuttals: capture public OpenReview visibility first; use `openreview-py` only as an optional local library.
   - Broad paper corpus and OA PDFs: use public arXiv, Crossref, OpenAlex, Semantic Scholar, Unpaywall, and official proceedings first; `paper-search-mcp` is optional.
   - Official proceedings: use ACL Anthology, CVF Open Access, PMLR, NeurIPS proceedings, or arXiv API directly.
   - Citation/author/topic enrichment: use OpenAlex and Semantic Scholar as secondary metadata backbones.
4. Keep raw captures and normalized outputs separate. Synthesize from normalized artifacts, not from browser state or loose snippets.

## Source Routing

Read `references/source-routing.md` before choosing a backend.

- Use public OpenReview pages/visible notes first for public reviews, scores, meta-reviews, rebuttals, decisions, venue stats, and rejection/weakness-pattern analysis.
- Use official proceedings first for accepted-paper lists: ACL Anthology for ACL/EMNLP/NAACL, CVF for CVPR/ICCV/WACV, PMLR for ICML/AISTATS/COLT, NeurIPS proceedings for NeurIPS accepted papers, and arXiv for preprints.
- Use public arXiv, Crossref, OpenAlex, Semantic Scholar, Unpaywall, and proceedings pages for multi-source literature search, DOI recovery, and open-access PDF resolution by default.
- Use `paper-search-mcp` only as an optional convenience layer after the public-source closure is understood.
- Use Semantic Scholar/OpenAlex for enrichment and cross-checking, not as the only source for official venue decisions.
- Use general crawlers only as a fallback when official pages are static but lack an API.

## Common Commands

Inspect a URL and infer the source lane:

```powershell
python skills\paper-review-source-intel\scripts\paper_review_source_intel.py inspect-url `
  "https://openreview.net/forum?id=abc123"
```

Print the normalized artifact contract:

```powershell
python skills\paper-review-source-intel\scripts\paper_review_source_intel.py schema
```

Generate a run scaffold:

```powershell
python skills\paper-review-source-intel\scripts\paper_review_source_intel.py scaffold `
  --output-dir output\paper_review_sources\iclr2025_rag `
  --target "ICLR 2025 RAG" `
  --venue ICLR `
  --year 2025 `
  --needs papers,reviews,decisions,pdfs,report
```

Normalize a raw JSON/JSONL capture:

```powershell
python skills\paper-review-source-intel\scripts\paper_review_source_intel.py normalize `
  --input output\paper_review_sources\iclr2025_rag\raw\openreview.json `
  --source openreview `
  --output-dir output\paper_review_sources\iclr2025_rag\normalized
```

## Output Contract

Use this directory shape for substantial runs:

- `raw/`: untouched source captures, API JSON, scraped HTML, PDFs, and logs.
- `normalized/papers.jsonl`: normalized paper/submission/proceedings rows.
- `normalized/reviews.jsonl`: normalized review, meta-review, rebuttal, and decision rows.
- `normalized/artifacts.jsonl`: downloaded PDFs, extracted text, BibTeX, screenshots, and other local files.
- `sources.csv`: source review table with URL, source type, source priority, and status.
- `manifest.json`: plan, commands, timestamps, limits, credentials policy, and blockers.
- `summary.md`: human-facing synthesis with links back to normalized source IDs.

Read `references/output-schema.md` before merging multiple sources.

## Guardrails

- Prefer first-party APIs and official proceedings over Google Scholar, search snippets, or aggregator pages.
- Default work must remain useful without MCP, paid services, private credentials, or login-only review data.
- Do not use Google Scholar or SerpApi as the canonical first source for papers or review evidence.
- Do not bypass paywalls, CAPTCHAs, login gates, private reviews, or venue access controls.
- Download only open-access or user-authorized PDFs. Record license/access status when known.
- Keep API keys, OpenReview credentials, cookies, proxy URLs, browser storage state, and `.env` files out of git and final answers.
- Preserve `source_url`, `source_id`, `fetched_at`, and source-specific identifiers for every normalized row.
- Treat review data as visibility-dependent. If a public review, rebuttal, or decision is missing, report the access/visibility state instead of inventing a value.
- Run a small smoke crawl before bulk collection and record rate limits or blocked sources in `manifest.json`.

## Resources

- `scripts/paper_review_source_intel.py`: planner, URL inspector, scaffold generator, schema printer, and lightweight normalizer.
- `references/source-routing.md`: detailed source selection and third-party tool notes.
- `references/output-schema.md`: normalized fields and merge policy.
