# Source Routing

Use the lightest first-source lane that can satisfy the request. The default lane must work without required MCP servers, paid services, private credentials, or login-only review data. Do not start from a general web search when an official public API, proceedings page, or maintained metadata repository exists. For full setup and optional MCP registration, read `full-setup.md`.

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
| Computer architecture venues | ACM DL, IEEE Computer Society Digital Library, IEEE Xplore, official venue archives | dblp/OpenAlex/Semantic Scholar enrichment | Covers MICRO, ISCA, ASPLOS, and HPCA only when the venue or architecture direction is explicit. |
| FPGA and reconfigurable-computing venues | ACM DL for FPGA; IEEE CSDL/Xplore and official site for FCCM | dblp/OpenAlex/Semantic Scholar enrichment | Covers FPGA and FCCM only when FPGA/HLS/reconfigurable computing is relevant. |
| EDA/CAD and design automation venues | ACM DL, IEEE Xplore/CSDL, official venue archives, IEEE CEDA pages | dblp/OpenAlex/Semantic Scholar enrichment | Covers ICCAD, DAC, DATE, and TCAD only when EDA/CAD/circuit-design automation is relevant. |
| Circuits and solid-state venues | IEEE Xplore, official venue/journal pages, IEEE CEDA/CAS pages | Crossref/OpenAlex/Semantic Scholar enrichment | Covers ISSCC and related TCAD/DATE evidence only when circuits or solid-state systems are relevant. |
| Data-engineering journals | IEEE Computer Society Digital Library / IEEE Xplore journal pages | dblp/OpenAlex/Semantic Scholar enrichment | Covers TKDE only when knowledge/data engineering is relevant. |
| Cryptographic hardware journal/proceedings | IACR TCHES official open-access pages | dblp/Crossref/OpenAlex enrichment | Covers TCHES/CHES journal-conference hybrid evidence when cryptographic hardware or embedded security is relevant. |
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

Default configured runtime:

- `runtime/openreview-py/.venv`: local `openreview-py` client for public API/custom-script use. It can be installed or repaired with `scripts/setup_paper_review_source_intel.ps1`.

Do not treat missing review fields as rejection evidence. First check whether the venue hid reviews, changed invitations, requires login, or has a different venue group ID.

## Paper Corpus and PDFs

Use public sources first when the user asks for a topic corpus, broad literature scan, DOI recovery, open PDF acquisition, or text extraction. `paper-search-mcp` is an optional convenience layer, not required for the narrowed closure, and is best used as a corpus builder rather than as the sole authority on conference acceptance or review decisions. If the user asks for a full MCP-enabled setup, register `paper_search_mcp` and then verify it with `codex mcp list`.

Good tasks:

- "Find recent papers on X and download open PDFs."
- "Build a deduplicated corpus from arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed/PMC, CORE, Europe PMC, and Unpaywall."
- "Resolve DOI and OA URLs for this paper list."

For high-breadth workflows, borrow orchestration ideas from `scholar-megasearch`, but keep provenance and source-specific failures in the manifest.

Do not rely on paper-search MCP by default when the task can close through public APIs and official proceedings. If it is registered, keep Sci-Hub-like fallbacks, Google Scholar proxy URLs, paid connectors, and private-record credentials disabled unless separately authorized. Treat Google Scholar scraping and download/read tools as non-canonical helpers requiring source-access checks.

## Official Proceedings

Use venue/proceedings sources for accepted-paper lists:

- ACL Anthology: use its Python module or GitHub metadata for NLP proceedings.
- CVF Open Access: use official pages for CVPR, ICCV, and WACV.
- PMLR: use official volume pages and mlresearch GitHub repositories for ICML, AISTATS, COLT, and workshops.
- NeurIPS proceedings: use `papers.nips.cc` for accepted papers; use OpenReview separately if the year's review process was hosted there.
- ACM Digital Library: use official conference pages/proceedings for ISCA, ASPLOS, FPGA, DAC, and ACM-side records for joint ACM/IEEE venues.
- IEEE Computer Society Digital Library: use official proceedings series/table-of-contents pages for MICRO, HPCA, FCCM, TKDE, and IEEE Computer Society-hosted records.
- IEEE Xplore: use conference and journal pages for FCCM, ICCAD, DATE, ISSCC, TCAD, TKDE, and IEEE-side records for joint ACM/IEEE venues.
- IACR TCHES: use `https://tches.iacr.org/` for Transactions on Cryptographic Hardware and Embedded Systems accepted articles and open PDFs.
- arXiv: use official Atom API for preprint metadata and PDFs.

When official proceedings disagree with secondary metadata, keep both values with provenance and prefer official proceedings for venue/year/acceptance status.

Default configured runtime:

- `runtime/acl-anthology/.venv`: local ACL Anthology Python package for official NLP proceedings metadata.

## Conditional Venue Expansion

Do not add all venue sources to every broad paper crawl. Use the target direction and venue names to decide whether to include the following source lanes.

| Direction trigger | Venues/journals | Primary official lanes | Source hints |
|---|---|---|---|
| computer architecture, microarchitecture, processor/cache/memory hierarchy, architecture-facing systems | MICRO, ISCA, ASPLOS, HPCA | IEEE CSDL/Xplore, ACM DL, official venue archives | `https://microarch.org/`, `https://dl.acm.org/conference/isca`, `https://www.asplos-conference.org/`, `https://www.hpca-conf.org/` |
| FPGA, HLS, field-programmable, reconfigurable computing | FPGA, FCCM | ACM DL for FPGA; IEEE CSDL/Xplore and official site for FCCM | `https://dl.acm.org/conference/fpga`, `https://www.fccm.org/` |
| EDA, CAD, design automation, placement/routing, logic synthesis, verification, VLSI/IC design | ICCAD, DAC, DATE, TCAD | ACM DL, IEEE Xplore/CSDL, official venue archives, IEEE CEDA pages | `https://iccad.com/`, `https://www.dac.com/`, `https://www.date-conference.com/archive`, `https://ieee-ceda.org/publications/tcad` |
| solid-state circuits, analog/mixed-signal/RF circuits, ADC/PLL/SerDes, SoC/circuit design | ISSCC, TCAD, DATE | IEEE Xplore, ISSCC official site, IEEE CEDA/CAS pages | `https://www.isscc.org/`, `https://ieeexplore.ieee.org/`, `https://ieee-ceda.org/publications/tcad` |
| machine learning, learning theory, representation/RL/foundation models | ICML | PMLR and ICML official site | `https://proceedings.mlr.press/`, `https://icml.cc/` |
| data engineering, knowledge engineering, databases, mining, knowledge graphs, information retrieval | TKDE | IEEE Computer Society Digital Library / IEEE Xplore journal pages | `https://www.computer.org/csdl/journal/tk` |
| cryptographic hardware, embedded security, side-channel/fault attacks, masked implementations | TCHES | IACR TCHES official open-access pages | `https://tches.iacr.org/` |

For a topic-only request, first run `paper_review_source_intel.py plan`. If it emits a `conditional-venue-scouting:*` lane, confirm the matched family is actually part of the user's intent before crawling venue pages. For a named venue or journal, route directly to that venue's official lane and use secondary metadata only for enrichment or gap filling.

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
