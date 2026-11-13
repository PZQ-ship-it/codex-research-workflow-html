#!/usr/bin/env python3
"""Search for academic papers using the DBLP API."""

import argparse
import json
import os
import re
import sys
import time

from _http_runtime import create_session, request


class DBLPResponseError(RuntimeError):
    """The REST endpoint returned a non-JSON response, not zero papers."""


def search_papers_by_dblp(query, start_year, end_year, max_results=10):
    if max_results <= 0:
        return []
    backend = os.environ.get('PAPER_SEARCH_DBLP_BACKEND', 'auto').lower()
    if backend not in {'auto', 'rest', 'sparql'}:
        raise ValueError('PAPER_SEARCH_DBLP_BACKEND must be auto, rest or sparql')
    session = create_session('PaperSearch/1.0')
    if backend == 'sparql':
        papers = _search_sparql(query, start_year, end_year, max_results, session)
    else:
        try:
            papers = _search_rest(query, start_year, end_year, max_results, session)
        except DBLPResponseError as exc:
            if backend == 'rest':
                raise
            print(f'[dblp] {exc}; using the official public SPARQL API with title-token matching (not REST ranking). No browser challenge is executed.', file=sys.stderr)
            papers = _search_sparql(query, start_year, end_year, max_results, session)
    for paper in papers:
        abstract = _fetch_abstract_from_doi(paper.get('url', ''), session=session)
        if abstract:
            paper['abstract'] = abstract
        time.sleep(0.5)
    return papers


def _search_rest(
    query: str,
    start_year: int,
    end_year: int,
    max_results: int = 10,
    session=None,
) -> list[dict]:
    """Search for papers on DBLP.

    Args:
        query: Search query string.
        start_year: Filter papers published from this year.
        end_year: Filter papers published up to this year.
        max_results: Maximum number of papers to return.

    Returns:
        List of paper dictionaries.
    """
    url = "https://dblp.org/search/publ/api"
    papers: list[dict] = []
    offset = 0
    limit = min(1000, max_results)  # DBLP max per request is 1000
    session = session or create_session("PaperSearch/1.0")

    while len(papers) < max_results:
        params = {
            "q": query,
            "format": "json",
            "h": limit,
            "f": offset,
        }

        response = request(session, "GET", url, source="dblp", params=params)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        if response.status_code != 200 or 'json' not in content_type:
            challenge = 'anubis' in response.text.lower()
            kind = 'Anubis browser verification' if challenge else 'non-JSON response'
            raise DBLPResponseError(f'REST HTTP {response.status_code}: {kind}')
        try:
            data = response.json()
        except ValueError as exc:
            raise DBLPResponseError('REST returned malformed JSON') from exc
        if not isinstance(data, dict) or not isinstance(data.get('result'), dict):
            raise DBLPResponseError('REST returned an unexpected JSON schema')

        hits = data.get("result", {}).get("hits", {})
        total = int(hits.get("@total", 0))
        hit_list = hits.get("hit", [])

        if not hit_list:
            break

        for hit in hit_list:
            info = hit.get("info", {})
            year = int(info.get("year", 0))

            # Filter by year range
            if year < start_year or year > end_year:
                continue

            # Normalize authors
            authors_info = info.get("authors", {}).get("author", [])
            if isinstance(authors_info, dict):
                authors_info = [authors_info]
            authors = [a.get("text", "") if isinstance(a, dict) else a for a in authors_info]

            papers.append({
                "title": info.get("title", ""),
                "authors": authors,
                "year": year,
                "abstract": "",
                "url": info.get("ee", info.get("url", "")),
                "venue": info.get("venue", ""),
                "citation_count": 0,
                "publication_date": f"{year}-01-01",
                "source": "dblp",
                "doi": info.get("doi"),
                "arxiv_id": None,
                "retrieval_method": "dblp_rest",
            })

        offset += limit

        if offset >= total:
            break

        time.sleep(1)  # Be polite to the API

    return papers[:max_results]


def _search_sparql(query, start_year, end_year, max_results, session):
    # This public endpoint is independently documented by DBLP. Do not solve or
    # replay the REST endpoint's Anubis challenge, cookies, or browser identity.
    # REST field/boolean syntax is not silently translated to a different query.
    if not query.strip() or re.search(r'[^\w\s-]', query) or any(t in {'AND', 'OR', 'NOT'} for t in query.split()):
        raise ValueError('DBLP SPARQL title search accepts plain words only; use the REST backend for advanced DBLP syntax')
    terms = list(dict.fromkeys(query.lower().split()))
    filters = ' && '.join(f'CONTAINS(LCASE(STR(?title)), {json.dumps(t, ensure_ascii=False)})' for t in terms)
    sparql = f'''PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?pub ?title ?year ?venue ?doi ?url ?author ?ordinal WHERE {{
 {{ SELECT DISTINCT ?pub ?title ?year WHERE {{
    ?pub dblp:title ?title ; dblp:yearOfPublication ?year .
    FILTER({filters})
    FILTER(STR(?year) >= "{int(start_year)}" && STR(?year) <= "{int(end_year)}")
 }} ORDER BY DESC(?year) ?pub LIMIT {int(max_results)} }}
 OPTIONAL {{ ?pub dblp:publishedIn ?venue }}
 OPTIONAL {{ ?pub dblp:doi ?doi }}
 OPTIONAL {{ ?pub dblp:primaryDocumentPage ?url }}
 OPTIONAL {{ ?pub dblp:hasSignature ?sig .
   ?sig a dblp:AuthorSignature ; dblp:signatureDblpName ?author ; dblp:signatureOrdinal ?ordinal . }}
}} ORDER BY DESC(?year) ?pub ?ordinal'''
    response = request(session, 'GET', 'https://sparql.dblp.org/sparql', source='dblp', params={'query': sparql}, headers={'Accept':'application/sparql-results+json'})
    response.raise_for_status()
    data = response.json()
    rows = data.get('results', {}).get('bindings')
    if not isinstance(rows, list):
        raise DBLPResponseError('SPARQL returned an unexpected JSON schema')
    papers, authors = {}, {}
    for row in rows:
        value = lambda k: row.get(k, {}).get('value', '')
        pub = value('pub')
        if pub not in papers:
            doi = value('doi').replace('https://doi.org/', '') or None
            papers[pub] = {
                'title':value('title'), 'authors':[], 'year':int(value('year')),
                'abstract':'', 'url':value('doi') or value('url') or pub,
                'venue':value('venue'), 'citation_count':0,
                'publication_date':value('year')+'-01-01', 'source':'dblp',
                'doi':doi, 'arxiv_id':None, 'dblp_url':pub,
                'retrieval_method':'dblp_sparql_title_tokens',
            }
            authors[pub] = {}
        if value('author'):
            authors[pub][int(value('ordinal'))] = value('author')
    for pub, paper in papers.items():
        paper['authors'] = [name for _, name in sorted(authors[pub].items())]
    return list(papers.values())


def _fetch_abstract_from_doi(url: str, session=None) -> str:
    """Try to fetch abstract from Crossref using a DOI extracted from the URL."""
    if not url:
        return ""
    # Extract DOI from URL like https://doi.org/10.xxxx/yyyy or direct DOI
    match = re.search(r'(10\.\d{4,9}/[^\s]+)', url)
    if not match:
        return ""
    doi = match.group(1)
    try:
        session = session or create_session("PaperSearch/1.0")
        resp = request(
            session,
            "GET",
            f"https://api.crossref.org/works/{doi}",
            source="dblp",
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("message", {}).get("abstract", "")
            # Strip JATS/XML tags if present
            if abstract:
                abstract = re.sub(r'<[^>]+>', '', abstract).strip()
            return abstract
    except Exception:
        pass
    return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search papers on DBLP")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--start-year", type=int, required=True, help="Start year")
    parser.add_argument("--end-year", type=int, required=True, help="End year")
    parser.add_argument("--max-papers", type=int, default=10, help="Max number of papers (default: 10)")
    args = parser.parse_args()

    papers = search_papers_by_dblp(args.query, args.start_year, args.end_year, args.max_papers)
    print(papers[0] if papers else "No papers found.")

# python search_papers_by_dblp.py --query "data efficiency for model training" --start-year 2024 --end-year 2026 --max-papers 20
