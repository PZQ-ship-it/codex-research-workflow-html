#!/usr/bin/env python3
"""Search for academic papers using the OpenReview API."""

import os
import argparse
import re
import sys
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from _http_runtime import configure_external_session, create_session, request

# Load credentials from .env BEFORE any os.environ.get below, so OPENREVIEW_USER/PASS are
# present even when this script is invoked directly via bash (no shell-sourced .env).
try:
    from _env import load_env_once
    load_env_once()
except Exception:
    pass


OPENREVIEW_DEFAULT_VENUES = [
    "ICLR.cc/2023/Conference",
    "ICLR.cc/2024/Conference",
    "ICLR.cc/2025/Conference",
    "ICLR.cc/2026/Conference",
    "NeurIPS.cc/2023/Conference",
    "NeurIPS.cc/2024/Conference",
    "NeurIPS.cc/2025/Conference",
    "NeurIPS.cc/2026/Conference",
    "ICML.cc/2023/Conference",
    "ICML.cc/2024/Conference",
    "ICML.cc/2025/Conference",
    "ICML.cc/2026/Conference",
]


def _openreview_clients():
    """Create OpenReview API clients (v2 and v1)."""
    try:
        import openreview
    except ImportError as e:
        raise RuntimeError("openreview not installed. pip install openreview-py") from e
    # Instantiate anonymously so the SDK cannot perform an unbounded login before
    # we have configured its internally-created requests Sessions.  The SDK also
    # consults OPENREVIEW_USERNAME/PASSWORD on its own, so suppress those aliases
    # during construction; this connector's established public names remain
    # OPENREVIEW_USER/PASS.
    sdk_env = {
        name: os.environ.pop(name)
        for name in ("OPENREVIEW_USERNAME", "OPENREVIEW_PASSWORD")
        if name in os.environ
    }
    try:
        v2 = openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net")
        v1 = openreview.Client(baseurl="https://api.openreview.net")
    finally:
        os.environ.update(sdk_env)

    configure_external_session(v2.session, "openreview")
    configure_external_session(v1.session, "openreview")

    # Keep both the connector's documented names and the SDK aliases working.
    # The aliases were captured above only to defer their implicit login until
    # after the Sessions had the bounded runtime policy installed.
    username = os.environ.get("OPENREVIEW_USER") or sdk_env.get(
        "OPENREVIEW_USERNAME", ""
    )
    password = os.environ.get("OPENREVIEW_PASS") or sdk_env.get(
        "OPENREVIEW_PASSWORD", ""
    )
    if username or password:
        try:
            v2.login_user(username=username, password=password)
            v1.login_user(username=username, password=password)
        except Exception:
            # Do not expose SDK exception payloads, usernames, or login headers.
            raise RuntimeError('OpenReview authentication failed; verify the account locally. Public literature search does not require login (PAPER_SEARCH_OPENREVIEW_AUTH=public).') from None
    else:
        raise RuntimeError('OpenReview authenticated mode requires locally configured credentials; use public mode for public papers')
    return v2, v1


def _or_field(content: dict, key: str, default=""):
    """Extract field from OpenReview content (handles v1 flat and v2 wrapped formats)."""
    v = content.get(key, default)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def _or_note_to_paper(note, venue: str) -> Optional[dict]:
    """Convert an OpenReview note to a standardized paper dict."""
    content = getattr(note, "content", {}) or {}
    title = (_or_field(content, "title", "") or "").strip()
    abstract = (_or_field(content, "abstract", "") or "").strip()
    authors = _or_field(content, "authors", []) or []
    if isinstance(authors, str):
        authors = [authors]

    cdate = getattr(note, "pdate", None) or getattr(note, "cdate", None)
    if not cdate:
        return None
    try:
        pub = datetime.utcfromtimestamp(int(cdate) / 1000)
    except Exception:
        return None

    note_id = getattr(note, "id", "") or ""
    venue_match = re.search(r'/(\d{4})/', venue)
    return {
        "title": title,
        "authors": list(authors),
        "year": int(venue_match.group(1)) if venue_match else pub.year,
        "abstract": abstract,
        "url": f"https://openreview.net/forum?id={note_id}" if note_id else "",
        "venue": venue,
        "citation_count": 0,
        "publication_date": pub.strftime("%Y-%m-%d") if getattr(note, 'pdate', None) else '',
        "submission_date": datetime.utcfromtimestamp(int(getattr(note, 'cdate', None) or cdate)/1000).strftime('%Y-%m-%d'),
        "source": "openreview",
        "doi": None,
        "arxiv_id": None,
    }


def _query_match(query: str, paper: dict) -> bool:
    """Check if all query tokens appear in the paper's title or abstract."""
    q = (query or "").lower().strip()
    if not q:
        return True
    hay = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    return all(tok in hay for tok in q.split())


def _fetch_venue_notes(v2_client, v1_client, venue: str) -> list:
    """Fetch notes from a venue, trying v2 API first then v1."""
    succeeded = False
    try:
        notes = v2_client.get_all_notes(content={"venueid": venue})
        succeeded = True
        if notes:
            return notes
    except Exception:
        pass
    for inv_suffix in ("/-/Blind_Submission", "/-/Submission"):
        try:
            notes = v1_client.get_all_notes(invitation=f"{venue}{inv_suffix}")
            succeeded = True
            if notes:
                return notes
        except Exception:
            continue
    if not succeeded:
        raise RuntimeError(f'OpenReview venue retrieval failed for {venue}; this is not a zero-hit result')
    return []


def _public_venue_notes(session, query, venue):
    """Page the documented public search API; local matching restores AND semantics.

    The API treats query words broadly. Never assume the first page contains all
    matches. Exact venueid excludes rejected/withdrawn variants of that venue.
    """
    offset, limit = 0, 200
    while True:
        body = {'term':query, 'venueid':venue, 'source':'forum', 'limit':limit, 'offset':offset}
        response = request(session, 'POST', 'https://api2.openreview.net/notes/search', source='openreview', json=body)
        response.raise_for_status()
        data = response.json()
        notes = data.get('notes')
        if not isinstance(notes, list):
            raise RuntimeError('OpenReview search returned an unexpected JSON schema')
        for note in notes:
            actual_venue = _or_field(note.get('content', {}), 'venueid', '')
            if actual_venue and actual_venue != venue:
                continue
            yield SimpleNamespace(**note)
        offset += len(notes)
        count = data.get('count')
        if offset >= 10000:
            print(f'[openreview] Search index limit reached for {venue}; coverage is partial. Narrow the query.', file=sys.stderr)
            break
        if not notes or len(notes) < limit or (isinstance(count, int) and offset >= count):
            break


def search_papers_by_openreview(
    query: str,
    start_year: int,
    end_year: int,
    max_results: int = 10,
    venues: Optional[list[str]] = None,
) -> list[dict]:
    """Search for papers on OpenReview.

    Args:
        query: Search query string.
        start_year: Filter papers published from this year.
        end_year: Filter papers published up to this year.
        max_results: Maximum number of papers to return.
        venues: List of OpenReview venue IDs to search. Defaults to major ML conferences.

    Returns:
        List of paper dictionaries.
    """
    if max_results <= 0:
        return []
    venues = venues or [f'{conf}/{year}/Conference' for year in range(end_year, start_year-1, -1) for conf in ('ICLR.cc', 'NeurIPS.cc', 'ICML.cc')]
    mode = os.environ.get('PAPER_SEARCH_OPENREVIEW_AUTH', 'public').lower()
    if mode not in {'public', 'required'}:
        raise ValueError('PAPER_SEARCH_OPENREVIEW_AUTH must be public or required')
    if mode == 'required':
        v2_client, v1_client = _openreview_clients()
    else:
        session = create_session('PaperSearch/1.0')
        print('[openreview] Using public search without login; account authentication is not tested. Search-index coverage may differ from full venue retrieval.', file=sys.stderr)

    papers: list[dict] = []
    for venue in venues:
        notes = _fetch_venue_notes(v2_client, v1_client, venue) if mode == 'required' else _public_venue_notes(session, query, venue)
        for n in notes:
            paper = _or_note_to_paper(n, venue)
            if paper is None:
                continue
            if not (start_year <= paper["year"] <= end_year):
                continue
            if not _query_match(query, paper):
                continue
            paper['retrieval_method'] = 'openreview_authenticated_venue' if mode == 'required' else 'openreview_public_search'
            papers.append(paper)
            if len(papers) >= max_results:
                return papers
        time.sleep(0.2)

    return papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search papers on OpenReview")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--start-year", type=int, required=True, help="Start year")
    parser.add_argument("--end-year", type=int, required=True, help="End year")
    parser.add_argument("--max-papers", type=int, default=10, help="Max number of papers (default: 10)")
    args = parser.parse_args()

    papers = search_papers_by_openreview(args.query, args.start_year, args.end_year, args.max_papers)
    print(papers[0] if papers else "No papers found.")

# python search_papers_by_openreview.py --query "data efficacy for LM training" --start-year 2024 --end-year 2026 --max-papers 20
