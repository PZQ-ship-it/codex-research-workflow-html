# RA Mainline Literature Worker Contract

Use this contract for one ranked direction from `mainline-ranking.md`.

## Mission

For one direction, find and verify:

1. One high-quality field survey or review that helps the user understand the problem space, method families, datasets/metrics, and node papers.
2. One to two representative papers for each mapped teacher in this direction, preferably papers already named in the relevant direction-map file.

Save only lawful open-access or user-authorized PDFs into `D:\hkust-gz-ra-paper-reading`.

## Source Priority

1. Direction-map source files listed in the job JSON.
   - Read the `Direction | Group papers first | Survey search queries | Node-paper targets | Reproduction candidate | Reason` table when present.
   - Prefer `Group papers first` entries for teacher representative papers.
   - Use `Survey search queries` as initial search terms, then refine.
2. Official professor/lab/project pages and official publication lists.
3. Official paper pages and public scholarly sources: arXiv, OpenReview, ACL Anthology, CVF, PMLR, NeurIPS proceedings, ACM DL, IEEE pages, Springer/Nature/Wiley/Taylor pages when metadata is public, DOI pages, Semantic Scholar, OpenAlex, Crossref, Unpaywall.
4. General web search only for discovery. Do not treat snippets as final evidence.

## Selection Criteria

Field survey:

- Prefer recent surveys for fast-moving LLM, RAG, agent, diffusion, and infrastructure directions.
- Prefer formal venue, journal, arXiv with strong author/institution signal, or a widely cited/publicly visible review.
- The survey must help map the field, not merely summarize one method.
- If two surveys compete, choose the one that better exposes problem taxonomy and node papers for the ranked direction.

Teacher representative papers:

- Prefer papers by the mapped teacher/lab in the relevant direction.
- Prefer current-mainline papers over historical foundation papers unless the direction map says the historical paper is the best entry point.
- Prefer papers with open PDFs and code/data links when later reproduction may matter.
- Limit to 1-2 selected papers per teacher/direction. Record overflow candidates in the manifest, not as downloads unless clearly useful.

## Download Policy

Allowed:

- arXiv PDFs.
- Official open-access venue PDFs.
- Author/lab-hosted PDFs.
- Publisher PDFs clearly marked open access.
- User-provided PDFs.

Not allowed:

- Paywall bypasses.
- Sci-Hub-like sites.
- Random PDF mirrors, private cloud links, or forum uploads unless the user explicitly authorizes them.
- Login-gated PDFs requiring cookies, tokens, institutional access, or private credentials.

When in doubt, save metadata only and mark `download_status: "metadata-only"`.

## Required Output Layout

Use the `rank_slug` and paths from the job JSON.

```text
D:\hkust-gz-ra-paper-reading\
  papers\mainline-literature\<rank-slug>\
    surveys\
    teachers\<teacher-slug>\
  sources\mainline-literature\<rank-slug>\
    manifest.json
    summary.md
```

## Manifest Schema

Write `manifest.json` with this shape:

```json
{
  "job": {
    "rank": 1,
    "direction": "...",
    "rank_slug": "rank-01-example"
  },
  "selected": [
    {
      "role": "survey",
      "teacher": null,
      "title": "...",
      "authors": ["..."],
      "year": 2026,
      "venue": "...",
      "doi": "...",
      "arxiv_id": "...",
      "landing_url": "...",
      "pdf_url": "...",
      "local_pdf": "papers/mainline-literature/.../surveys/...",
      "open_access_basis": "arXiv",
      "why_selected": "..."
    }
  ],
  "rejected_or_deferred": [
    {
      "title": "...",
      "reason": "not a survey / no open PDF / weak relevance"
    }
  ],
  "gaps": [
    "No open representative paper found for ..."
  ],
  "sources_checked": [
    "..."
  ]
}
```

Use relative paths from the artifact repo for `local_pdf`.

## Summary Markdown

Write `summary.md` in Chinese or mixed Chinese-English. Include:

- Direction and mapped teachers.
- Selected survey and why it fits.
- Selected representative papers per teacher.
- Rejected/deferred candidates and why.
- Missing downloads or uncertainty.
- Suggested next step: HTML digest, glossary, survey-to-node map, or minimal reproduction scout.

## Stop Conditions

Stop the worker and report partial progress when:

- Search or extraction quota is exhausted.
- The direction label is too broad to choose a survey without human narrowing.
- No lawful open PDF can be found.
- Teacher representative papers cannot be attributed with confidence.
- The job would require private credentials, institutional access, or paywall bypass.
