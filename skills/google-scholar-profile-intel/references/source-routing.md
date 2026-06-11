# Source Routing

Use the shallowest source that satisfies the task. Escalate only when the user asks for more depth or the previous lane cannot answer reliably.

## Routes

| Need | Preferred route | Notes |
|---|---|---|
| Single scholar profile by Scholar URL or ID | `scholarly-author` | Fill only requested sections. Keep `publications` bounded. |
| Batch Scholar author IDs | `scholar-scraper` | Useful for profile, cites-per-year, coauthors, publications. Keep thread count low. |
| Per-paper citing-work lists | `google-scholar-citation-crawler` | Long-running lane with cache/resume. Use only for `deep-citations`. |
| Managed Scholar extraction | Apify actor input | Generate input first; run actor only after user accepts paid/hosted scraping. |
| Author disambiguation and open cross-check | `openalex-author` | Good for ORCID, institutions, topics, works count, citations, h-index/i10. |
| Report/dossier | Merge raw captures | Preserve field provenance and conflicts. |

## Local Google Scholar Lanes

### scholarly

Use when the task is small and interactive:

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

### scholar-scraper

Use for compact batch exports from known author IDs:

```python
from scholar_scraper import scholar_scraper
print(scholar_scraper.start_scraping(["AUTHOR_ID_1", "AUTHOR_ID_2"], max_threads=2))
```

Keep `max_threads` conservative. The package is simple and profile-oriented, but it depends on Google Scholar behavior and may be stale.

### google-scholar-citation-crawler

Use only when the user needs per-paper citation lists, history, Excel output, or resumable long runs:

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

Use for open enrichment and disambiguation:

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
