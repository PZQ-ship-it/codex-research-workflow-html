# Connector recovery

Verified: 2026-11-13. These settings affect this skill only; do not edit global model/auth settings or copy credentials into artifacts.

| Setting | Default | Other modes |
|---|---|---|
| `PAPER_SEARCH_OPENALEX_MODE` | `auto`: semantic, then keyword only for first-page server/network failures | `semantic`: fail explicitly; `keyword`: use keyword search with pagination |
| `PAPER_SEARCH_DBLP_BACKEND` | `auto`: REST, then official SPARQL on non-JSON responses | `rest`: fail on verification pages; `sparql`: direct title-token search |
| `PAPER_SEARCH_OPENREVIEW_AUTH` | `public`: public search, without reading credentials for login | `required`: authenticate and fetch venue notes; failure remains visible |

## OpenAlex

The semantic endpoint may fail while keyword search works. Auto mode retains bounded retries and records the actual `retrieval_method`; it does not rotate keys to evade limits. A 401/403/429 is surfaced. Semantic search currently returns at most 50 results per query. Keyword search paginates separately. Switching methods changes recall and ranking; never claim equivalent result sets.

Official references: [semantic search](https://help.openalex.org/api/semantic-search/), [keyword search](https://help.openalex.org/api/searching/).

## DBLP

REST can return HTTP 202 plus an Anubis HTML verification page. `raise_for_status()` alone does not detect this; parsing it as JSON produces an unhelpful error. The connector recognizes this response and names it in diagnostics.

The alternative is DBLP's officially published, independently accessible [public SPARQL service](https://blog.dblp.org/2024/09/09/introducing-our-public-sparql-query-service/), not a browser challenge solver or proxy. If this API also denies access, surface the failure. Neither backend switches on 429. `dblp_sparql_title_tokens` records the method used. It matches every plain query token in the title and sorts by publication year, unlike REST prefix/metadata search. Advanced DBLP field/Boolean syntax is rejected in SPARQL mode rather than silently reinterpreted. Use several plain queries when broader coverage is needed.

SPARQL years have RDF `gYear` values; compare their lexical year strings. Author signatures are sorted by ordinal to preserve author order. DBLP has no abstracts: DOI records receive best-effort Crossref abstract enrichment, which can remain empty. An empty abstract is not evidence of irrelevance. Citation counts remain connector placeholders, not global citation totals.

## OpenReview

Public literature search uses `POST https://api2.openreview.net/notes/search`, documented in the [OpenAPI definition](https://docs.openreview.net/reference/api-v2/openapi-definition). It filters exact `venueid`, pages broad term matches, then applies local title/abstract token matching. Rejected/withdrawn suffixes are not mislabeled as accepted conference records. Default venues are ICLR, NeurIPS and ICML for each requested year. This is not all of OpenReview, and search-index coverage can differ from authenticated complete venue retrieval. The API's 10,000-result cap is reported if reached; narrow broad queries.

Use the conference year for the paper year; keep submission date separate and do not invent a publication date from submission time. A successful public search says nothing about the configured account's login state.

For an account-specific operation, test login manually at [OpenReview](https://openreview.net/login), using the same account as the local configuration. If the website login fails, resolve activation/password/account status there. If the website works, locally check `OPENREVIEW_USER` / `OPENREVIEW_PASS` (or SDK aliases), restart the shell so stale process variables do not override a changed `.env`, and retry authenticated mode. Never send passwords or verification codes to the agent. MFA requires the official [unattended-script setup](https://docs.openreview.net/getting-started/using-the-api/using-multi-factor-authentication-in-unattended-scripts) when applicable.

## Verification

Run in the installed runtime:

```text
python scripts/selftest_connectors.py
python scripts/selftest_runtime.py
python scripts/selftest_postprocess.py
```

Tests cover transient recovery, no fallback on authentication/rate errors, final-page pagination, Anubis detection, author order, public mode independent of credentials, rejected-paper exclusion, conference year versus submission date, and errors versus genuine empty results. Live checks must additionally confirm actual returned papers. These checks establish connector behavior, not paper relevance or literature-review completeness.
