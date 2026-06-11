# Output Schema

Use this contract when merging Google Scholar, Apify, scholar-scraper, citation crawler, and OpenAlex data.

## Author Profile

```json
{
  "schema_version": "0.1",
  "subject": {
    "name": "",
    "scholar_id": "",
    "scholar_url": "",
    "orcid": "",
    "homepage": "",
    "affiliations": [],
    "interests": [],
    "last_known_institutions": [],
    "topics": []
  },
  "metrics": {
    "cited_by_count": null,
    "h_index": null,
    "i10_index": null,
    "cited_by_5y": null,
    "h_index_5y": null,
    "i10_index_5y": null,
    "works_count": null,
    "citations_per_year": {}
  },
  "publications": [],
  "coauthors": [],
  "citation_events": [],
  "provenance": {
    "sources": [],
    "field_sources": {},
    "fetched_at": "",
    "warnings": []
  }
}
```

## Publication Row

```json
{
  "title": "",
  "authors": [],
  "year": null,
  "venue": "",
  "publication": "",
  "doi": "",
  "openalex_id": "",
  "scholar_citation_id": "",
  "url": "",
  "pdf_url": "",
  "citation_count": null,
  "citations_per_year": {},
  "source": "",
  "source_record": {}
}
```

## Merge Policy

- Prefer Google Scholar for Scholar-visible metrics and publication order.
- Prefer OpenAlex for DOI, ORCID, institutions, topics, and open identifiers.
- Prefer citation crawler output for per-paper citing-work lists.
- Prefer Apify output when it is the only successful Scholar profile capture in a blocked environment.
- When counts conflict, keep both as separate fields or attach source provenance; do not silently average.
- Mark identity as `needs_manual_check` when name, affiliation, homepage, or key publications do not align.

## Minimum Dossier

A useful `summary.md` should include:

- target identity and disambiguation evidence;
- profile metrics with source names and fetch date;
- top publications by citation count and by recency when available;
- research interests or topics;
- coauthor/institution signals if requested;
- source gaps, blocks, and manual-check items.
