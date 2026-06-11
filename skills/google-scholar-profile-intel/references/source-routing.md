# Source Routing

Use the shallowest source that satisfies the task. The default closure is OpenAlex/open-bibliographic and must work without required SerpApi, Apify, private proxies, or Google Scholar scraping. Escalate only when the user asks for more depth or the previous lane cannot answer reliably. For complete dependency/MCP setup, read `full-setup.md`.

## Routes

| Need | Preferred route | Notes |
|---|---|---|
| Author disambiguation and open dossier | `openalex-author` | Default lane. Good for ORCID, institutions, topics, works count, citations, h-index/i10. |
| Profile-to-paper/review cross-check | `openreview-py`, OpenReview public pages | Public submissions, forum IDs, review visibility, decisions, and venue evidence. |
| Broad public paper search | `paper_search_mcp`, arXiv, PubMed, bioRxiv, medRxiv | MCP is a convenience layer after source routing; avoid Google Scholar as canonical evidence. |
| Official publication evidence | ACL Anthology, CVF, PMLR, NeurIPS proceedings, arXiv, Crossref, OpenAlex, Semantic Scholar, Unpaywall | Prefer official proceedings/API over Google Scholar snippets or scraper output. |
| Single scholar profile by Scholar URL or ID | optional `scholarly-author` | Best-effort only after `--allow-scholar-scrape`; keep `publications` bounded. |
| Batch Scholar author IDs | optional `scholar-scraper` | External crawler; use only after explicit approval and low thread count. |
| Per-paper citing-work lists | optional `google-scholar-citation-crawler` | Long-running external lane with cache/resume. Use only for explicitly approved `deep-citations`. |
| Managed Scholar extraction | optional Apify actor input | Generate input first; run actor only after user accepts paid/hosted scraping. |
| Report/dossier | Merge raw captures | Preserve field provenance and conflicts. |

## Default Open Closure

Use `openalex-author` first for a usable researcher dossier:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py openalex-author `
  --query "Author name" `
  --institution-hint "Institution or affiliation clue" `
  --per-page 5 `
  --output output\scholars\openalex_candidates.json
```

OpenAlex is not Google Scholar, so citation counts and publication lists may differ. Treat it as the stable default closure, and label Google Scholar-specific fields as unavailable unless an optional Scholar scrape succeeds.

## OpenReview And Proceedings Closure

Use OpenReview public pages and `openreview-py` when the dossier needs public review/decision evidence, forum IDs, or profile-to-submission corroboration:

```powershell
%USERPROFILE%\.codex\skills\google-scholar-profile-intel\runtime\openreview-py\.venv\Scripts\python.exe -c "import openreview; print('ok')"
```

Use official proceedings/API sources for publication evidence:

- ACL Anthology Python package or metadata for ACL/EMNLP/NAACL/COLING.
- CVF Open Access for CVPR/ICCV/WACV.
- PMLR volume pages for ICML/AISTATS/COLT.
- NeurIPS proceedings for accepted papers.
- arXiv, Crossref, OpenAlex, Semantic Scholar, and Unpaywall for DOI and open-access cross-checks.

When proceedings disagree with Google Scholar, preserve both values with provenance and prefer official proceedings for venue/year/accepted status.

## Paper Search MCP

Register `paper_search_mcp` for MCP-enabled setups:

```powershell
powershell -ExecutionPolicy Bypass -File skills\google-scholar-profile-intel\scripts\setup_google_scholar_profile_intel.ps1 -RegisterPaperSearchMcp
codex mcp list
```

Prefer public arXiv/PubMed/bioRxiv/medRxiv tools for breadth. Treat Google Scholar scraping and download/read tools as non-canonical helpers requiring source-access checks.

## Local Google Scholar Lanes

### scholarly

Use only when the task is small, interactive, and the user accepts best-effort Google Scholar scraping:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py scholarly-author `
  --author-id AUTHOR_ID `
  --sections basics,indices,counts,publications,coauthors `
  --max-publications 100 `
  --output output\scholars\author_scholarly.json
```

Install dependency in an isolated environment if missing:

```powershell
python -m venv output\scholars\.venv
output\scholars\.venv\Scripts\python -m pip install scholarly
```

Risks:

- Google Scholar can block automated requests.
- Some calls, especially citation and publication search, need proxies or delays.
- Treat CAPTCHA, 403, 429, or empty pages as blockers, not as true negative evidence.

To include this lane in planner output, pass `--allow-scholar-scrape`.

### scholar-scraper

Use for compact batch exports from known author IDs only after explicit approval:

```python
from scholar_scraper import scholar_scraper
print(scholar_scraper.start_scraping(["AUTHOR_ID_1", "AUTHOR_ID_2"], max_threads=2))
```

Keep `max_threads` conservative. The package is simple and profile-oriented, but it depends on Google Scholar behavior and may be stale.

### google-scholar-citation-crawler

Use only when the user explicitly needs per-paper citation lists, history, Excel output, or resumable long runs:

```powershell
python scholar_citation.py --author AUTHOR_ID --output-dir output\scholars\AUTHOR_ID
```

Prefer this lane for:

- citation list for every publication;
- resume after interruption;
- year-by-year citation crawling;
- JSON plus Excel deliverables.

Do not trigger this lane for a normal profile summary. It can be slow and noisy.

## Managed And Open Lanes

### Apify

Use when the user accepts hosted scraping and potential cost. Generate actor input first:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py apify-input `
  --author-id AUTHOR_ID `
  --limit 100 `
  --output output\scholars\apify_author_input.json
```

The generated input uses author profile mode and residential proxy configuration. Running the actor requires the user's Apify setup and approval.

### OpenAlex

Use for open enrichment and disambiguation. This is the default route:

```powershell
python skills\google-scholar-profile-intel\scripts\scholar_profile_intel.py openalex-author `
  --query "Author name" `
  --institution-hint "Institution or affiliation clue" `
  --per-page 5 `
  --output output\scholars\openalex_candidates.json
```

OpenAlex is not Google Scholar, so citation counts may differ. Use it to enrich and cross-check, not to overwrite Scholar fields blindly.

Prefer a clean person-name query, then use `--institution-hint`, homepage, ORCID, coauthor overlap, and publication titles for disambiguation. Overly specific full-text searches such as `"Name Institution Department"` can return no candidates even when the author exists.

## Explicit Exclusion

SerpApi Author API is not part of this skill. If a user later requests SerpApi, treat that as a separate explicit change request.
