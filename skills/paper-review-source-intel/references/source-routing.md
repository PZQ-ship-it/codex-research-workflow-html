# Source Routing

Use the lightest first-source lane that can satisfy the request. The default lane must work without required MCP servers, paid services, private credentials, or login-only review data. Do not start from a general web search when an official public API, proceedings page, or maintained metadata repository exists.

## Priority Matrix

| Need | Primary route | Secondary route | Notes |
|---|---|---|---|
| Public reviews, scores, rebuttals, meta-reviews, decisions | OpenReview public pages / visible public JSON | `openreview-py` custom script | Review visibility varies by venue and stage; missing public fields are blockers, not facts. |
| OpenReview API usage help | `openreview-py` docs/tests | `openreview/openreview-mcp` knowledge server | MCP is optional guidance, not required for the base closure. |
| Multi-source paper corpus | arXiv, Crossref, OpenAlex, Semantic Scholar, Unpaywall, official proceedings | optional `paper-search-mcp` | Use public sources for broad search, dedupe, DOI recovery, and OA PDF resolution first. |
| arXiv preprints | arXiv Atom API | optional arXiv-specific MCP/skill | Respect arXiv rate limits and include `mailto`/polite user agent where possible. |
| ACL/EMNLP/NAACL papers | ACL Anthology Python module / GitHub metadata | Static ACL Anthology pages | Official metadata includes papers, authors, venues, volumes, events, and PDFs. |
| CVPR/ICCV/WACV papers | CVF Open Access pages | CVF crawler fallback | Static official pages usually expose title, authors, abstract, PDF, and BibTeX. |
| ICML/AISTATS/COLT papers | PMLR volume pages / mlresearch GitHub | Static scraper fallback | Resolve the volume page before scraping. |
| NeurIPS accepted papers | NeurIPS proceedings | OpenReview for reviews when hosted there | The proceedings and review venue can be separate evidence lanes. |
| Citation/author/topic enrichment | OpenAlex and Semantic Scholar | Crossref, dblp | Use as enrichment/cross-check, not as the source of venue decisions. |
| Open-access PDF acquisition | Unpaywall public endpoint, arXiv, PMC/Europe PMC, CORE, venue official PDF URLs | optional `paper-search-mcp` | Closed-access papers should be flagged, not bypassed. |

## OpenReview

Use OpenReview when the user asks for:

- public reviews, ratings, confidence, strengths, weaknesses, questions, limitations;
- meta-review or area-chair recommendation;
- author rebuttal / response;
- final decision and decision comment;
- venue stats, acceptance rates, score distributions, or weakness clusters;
- matching submissions to forum IDs.

Default route:

- Capture only public OpenReview page/visible-note data by default.
- Use `openreview-py` only when the user accepts local library setup or the public page shape is insufficient.
- Do not require `openreview-mcp` for the base closure.

Optional tools:

- Third-party `openreview-mcp` from PyPI for MCP tools such as listing venues, searching submissions, getting reviews, meta-reviews, rebuttals, decisions, and venue stats.
- Official `openreview-py` for custom scripts and careful API access.
- Official `openreview/openreview-mcp` for API knowledge, signatures, best practices, and examples when writing `openreview-py` code.

Do not treat missing review fields as rejection evidence. First check whether the venue hid reviews, changed invitations, requires login, or has a different venue group ID.

## Paper Corpus and PDFs

Use public sources first when the user asks for a topic corpus, broad literature scan, DOI recovery, open PDF acquisition, or text extraction. `paper-search-mcp` is an optional convenience layer, not required for the narrowed closure, and is best used as a corpus builder rather than as the sole authority on conference acceptance or review decisions.

Good tasks:

- "Find recent papers on X and download open PDFs."
- "Build a deduplicated corpus from arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed/PMC, CORE, Europe PMC, and Unpaywall."
- "Resolve DOI and OA URLs for this paper list."

For high-breadth workflows, borrow orchestration ideas from `scholar-megasearch`, but keep provenance and source-specific failures in the manifest.

## Official Proceedings

Use venue/proceedings sources for accepted-paper lists:

- ACL Anthology: use its Python module or GitHub metadata for NLP proceedings.
- CVF Open Access: use official pages for CVPR, ICCV, and WACV.
- PMLR: use official volume pages and mlresearch GitHub repositories for ICML, AISTATS, COLT, and workshops.
- NeurIPS proceedings: use `papers.nips.cc` for accepted papers; use OpenReview separately if the year's review process was hosted there.
- arXiv: use official Atom API for preprint metadata and PDFs.

When official proceedings disagree with secondary metadata, keep both values with provenance and prefer official proceedings for venue/year/acceptance status.

## Fallback Crawlers

Use conference-specific crawlers only when:

- the target official source is static and no official API/library is available;
- a small smoke crawl confirms the parser still matches the page shape;
- the crawler does not require private credentials or bypass anti-bot controls.

Record crawler repository, commit/version if installed, input parameters, and source URL in `manifest.json`.

## Synthesis Policy

Separate evidence layers:

- first-source review evidence: OpenReview notes, invitations, forum IDs;
- first-source publication evidence: proceedings pages, official PDFs, official BibTeX;
- enrichment evidence: citations, OpenAlex concepts/topics, Semantic Scholar fields;
- derived analysis: weakness clusters, trend summaries, acceptance-rate summaries.

In reports, label derived analysis clearly and link it back to source row IDs.
