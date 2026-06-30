# Tool Routing For Researcher Field Scout

Use this table after reading the task and before collecting sources. Select the smallest set of lanes that answer the user's decision problem.

## Lane Selection

| Need | Primary Route | Use When | Notes |
|---|---|---|---|
| General current web discovery | `anysearch` | Official pages, direct posts, talks, news, broad discovery | Run AnySearch `doc` first if not already known; use batch search for independent queries. |
| Academic author/profile | `google-scholar-profile-intel` | Need OpenAlex/Scholar-like profile, author disambiguation, citation/profile enrichment | Default to OpenAlex/open bibliographic sources; Google Scholar scraping is optional and fragile. |
| Professor/lab current direction | `professor-direction-mapper` | User asks advisor/RA/professor/lab mainline, branches, historical line | Use as first route for professor/lab direction mapping. |
| Advisor/application fit | `professor-fit-analyzer` | User asks whether a professor is a good fit, outreach, interview, mentoring/lab risk | Broader than direction map; may need user background. |
| Student-led spine | `student-lead-spine-finder` | Need recent recurring student/candidate lead evidence | Prefer delegated subagent when available. |
| Papers/proceedings/reviews | `paper-review-source-intel` | Need paper corpus, open PDFs, OpenReview/ACL/CVF/PMLR/arXiv evidence | Prefer official proceedings and open sources. |
| Code/repo/model/dataset/benchmark | `code-model-benchmark-intel` | GitHub repos, Hugging Face, datasets, evals, leaderboards | Good for builders and open-source researchers. |
| Early discussion signal | `early-signal-intel` | HN, alphaXiv, RSS/lab blogs, Bluesky/Reddit-style signals | Treat as community signal, not fact. |
| Chinese AI media / propagation | `chinese-ai-signal-crawler` | Need Chinese secondary-media diffusion around AI projects/papers | Cross-check primary source. |
| Zhihu | `zhihu-public-intel` | Need Chinese public Q/A discussion or user/article analysis | Follow auth and cookie-safety rules. |
| Xiaohongshu / Dianping | `xhs-explore`, `dianping-explore` | Only for social/local/community discovery relevant to the question | Low-volume, no private data capture. |
| Nowcoder / offer signals | `nowcoder-public-intel`, salary ledger tools | Career/JD/offer side-channel signals | Never treat as salary fact without cross-checking. |
| Report synthesis | `evidence-synthesis-docs` | Collection is done and needs human-facing report/matrix/playbook | Cite source IDs, not loose snippets. |
| Assumption / overclaim QA | `assumption-auditor`, `codex-adversarial-qa` | High-stakes or public report | Check source layers and hidden assumptions. |

## Default Search Fanout

For a single public researcher/builder, start with 4-6 queries:

- `<name> official homepage`
- `<name> GitHub` / `<name> Hugging Face` when code/models matter
- `<name> Google Scholar ORCID OpenAlex Semantic Scholar DBLP`
- `<name> talks blog interview course`
- `<name> recent project paper 2024 2025 2026`
- `<name> lab students collaborators` when academic/lab direction matters

For ambiguous names, add institution, field, or known project.

## Source Priority

1. Self-authored or self-maintained public sources.
2. Official institutional, conference, proceedings, repository, or publication sources.
3. Open bibliographic/database sources.
4. Reputable secondary media/interviews.
5. Community discussion and search snippets.
6. Fallback mirrors when original access is blocked.

## Public Academic Backends To Prefer

These are source backends or identity anchors, not full scouting workflows by themselves:

| Backend | Use | Note |
|---|---|---|
| OpenAlex | https://developers.openalex.org/api-reference/authors | Author disambiguation, works, institutions, topics, citation/profile metadata | Open catalog and API; good default for broad scholarly identity. |
| Semantic Scholar Academic Graph | https://www.semanticscholar.org/product/api | Author/paper search, citation/reference graph, abstracts and paper metadata | Good cross-check and citation-network enrichment. |
| ORCID | https://info.orcid.org/what-is-orcid/services/public-api/ | Persistent researcher ID, affiliations, works, public record data | Strong identity anchor when maintained by the researcher or institution. |
| DBLP | https://dblp.org/faq/How+to+use+the+dblp+search+API | Computer-science author and publication bibliography | Strong CS publication metadata, especially for venues and author pages. |

Use existing local skills that already know these sources before writing new API code.

## Public-Safe Output Rule

Before writing public outputs, scan for:

- local absolute paths,
- secrets or secret-like strings,
- private chats or private browser state,
- paid/gated full text,
- personal sensitive details,
- overlong quotes from copyrighted material.
