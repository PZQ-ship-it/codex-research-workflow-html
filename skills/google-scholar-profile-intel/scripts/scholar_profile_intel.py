#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "0.1"
SCHOLAR_ID_RE = re.compile(r"(?:user=)([A-Za-z0-9_-]+)")


def extract_scholar_id(target: str) -> Optional[str]:
    match = SCHOLAR_ID_RE.search(target)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{8,}", target.strip()):
        return target.strip()
    return None


def split_csv(value: str) -> List[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def write_json(data: Any, output: Optional[str]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def openalex_url(query: str, per_page: int, mailto: Optional[str]) -> str:
    params = {
        "search": query,
        "per-page": str(per_page),
    }
    if mailto:
        params["mailto"] = mailto
    return "https://api.openalex.org/authors?" + urllib.parse.urlencode(params)


def fetch_json(url: str, timeout: float = 30.0) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "google-scholar-profile-intel/0.1 (+https://openalex.org)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_openalex_author(record: Dict[str, Any]) -> Dict[str, Any]:
    summary = record.get("summary_stats") or {}
    ids = record.get("ids") or {}
    return {
        "source": "openalex",
        "source_id": record.get("id"),
        "display_name": record.get("display_name"),
        "orcid": record.get("orcid") or ids.get("orcid"),
        "works_count": record.get("works_count"),
        "cited_by_count": record.get("cited_by_count"),
        "h_index": summary.get("h_index"),
        "i10_index": summary.get("i10_index"),
        "two_year_mean_citedness": summary.get("2yr_mean_citedness"),
        "last_known_institutions": record.get("last_known_institutions") or [],
        "affiliations": record.get("affiliations") or [],
        "topics": record.get("topics") or [],
        "x_concepts": record.get("x_concepts") or [],
        "raw": record,
    }


def hint_score(record: Dict[str, Any], hint: Optional[str]) -> int:
    if not hint:
        return 0
    needle = hint.lower()
    haystack = json.dumps(record, ensure_ascii=False).lower()
    return 1 if needle in haystack else 0


def command_plan(args: argparse.Namespace) -> None:
    needs = set(split_csv(args.needs))
    scholar_id = extract_scholar_id(args.target)
    has_name_query = scholar_id is None
    commands: List[Dict[str, Any]] = []
    cautions: List[str] = []

    openalex_query = args.target if has_name_query else args.openalex_query or "AUTHOR_NAME_FROM_PROFILE"
    if "profile" in needs or "indices" in needs or "publications" in needs or "enrichment" in needs or args.openalex or has_name_query:
        commands.append(
            {
                "lane": "openalex",
                "why": "Default narrowed closure for open researcher dossiers without Google Scholar scraping, SerpApi, Apify, or required external API keys.",
                "command": (
                    "python skills/google-scholar-profile-intel/scripts/scholar_profile_intel.py "
                    f"openalex-author --query {json.dumps(openalex_query, ensure_ascii=False)} "
                    "--per-page 5 --output output/scholars/openalex_candidates.json"
                ),
                "requires": ["Network access to api.openalex.org"],
                "limits": ["OpenAlex metrics and works may differ from Google Scholar profile counts."],
            }
        )

    if ("deep-citations" in needs or args.deep_citations) and args.allow_external_crawlers:
        commands.append(
            {
                "lane": "google-scholar-citation-crawler",
                "why": "Required for per-paper citing-work lists and resumable long runs.",
                "command": "python scholar_citation.py --author AUTHOR_ID --output-dir output/scholars/AUTHOR_ID",
                "requires": [
                    "External crawler checkout",
                    "Python deps from that project",
                    "Long runtime and anti-block handling",
                ],
            }
        )
        cautions.append("Do not run deep citation crawling for a normal profile summary.")
    elif "deep-citations" in needs or args.deep_citations:
        cautions.append("Deep Google Scholar citation crawling is outside the narrowed default closure; pass --allow-external-crawlers only after user approval.")

    if scholar_id and (needs & {"profile", "indices", "publications", "coauthors"}) and args.allow_scholar_scrape:
        sections = ["basics"]
        if "indices" in needs:
            sections.append("indices")
            sections.append("counts")
        if "publications" in needs:
            sections.append("publications")
        if "coauthors" in needs:
            sections.append("coauthors")
        commands.append(
            {
                "lane": "scholarly",
                "why": "Local single-author Scholar profile fetch with selected sections.",
                "command": (
                    "python skills/google-scholar-profile-intel/scripts/scholar_profile_intel.py "
                    f"scholarly-author --author-id {scholar_id} --sections {','.join(sections)} "
                    f"--max-publications {args.max_publications} --output output/scholars/{scholar_id}_scholarly.json"
                ),
                "requires": ["pip install scholarly in an isolated environment"],
            }
        )
    elif scholar_id and (needs & {"profile", "indices", "publications", "coauthors"}):
        cautions.append("Google Scholar profile scraping via scholarly is optional best-effort and not part of the default closure; pass --allow-scholar-scrape only after accepting CAPTCHA/block risk.")

    if scholar_id and args.batch_ready and args.allow_external_crawlers:
        commands.append(
            {
                "lane": "scholar-scraper",
                "why": "Compact batch export for known Scholar author IDs.",
                "python": (
                    "from scholar_scraper import scholar_scraper\n"
                    f"print(scholar_scraper.start_scraping(['{scholar_id}'], max_threads=2))"
                ),
                "requires": ["pip install scholar-scraper"],
            }
        )
    elif scholar_id and args.batch_ready:
        cautions.append("scholar-scraper is an external crawler and is omitted from the narrowed default closure.")

    if args.allow_apify:
        apify_target = scholar_id or "AUTHOR_ID"
        commands.append(
            {
                "lane": "apify",
                "why": "Managed Scholar extraction when hosted scraping and possible cost are acceptable.",
                "command": (
                    "python skills/google-scholar-profile-intel/scripts/scholar_profile_intel.py "
                    f"apify-input --author-id {apify_target} --limit {args.max_publications} "
                    f"--output output/scholars/{apify_target}_apify_input.json"
                ),
                "requires": ["User approval before running a paid/hosted actor"],
            }
        )

    if not commands:
        commands.append(
            {
                "lane": "manual-disambiguation",
                "why": "The target or requested depth is unclear.",
                "next": "Ask for a Scholar profile URL/author ID, or an author name plus affiliation.",
            }
        )

    cautions.extend(
        [
            "SerpApi is intentionally excluded from this skill.",
            "Default closure is OpenAlex-based; Google Scholar scraping is optional best-effort and can be blocked.",
            "Keep API keys, proxy credentials, cookies, and copied browser headers out of repo files.",
        ]
    )

    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "target": args.target,
            "scholar_id": scholar_id,
            "needs": sorted(needs),
            "recommended_order": commands,
            "cautions": cautions,
        },
        args.output,
    )


def command_openalex_author(args: argparse.Namespace) -> None:
    mailto = args.mailto or os.getenv("OPENALEX_MAILTO")
    url = openalex_url(args.query, args.per_page, mailto)
    if args.dry_run:
        write_json({"url": url}, args.output)
        return
    payload = fetch_json(url, timeout=args.timeout)
    results = payload.get("results", [])
    normalized = [normalize_openalex_author(item) for item in results]
    if args.institution_hint:
        normalized.sort(
            key=lambda item: (
                hint_score(item, args.institution_hint),
                item.get("cited_by_count") or 0,
            ),
            reverse=True,
        )
    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "source": "openalex",
            "query": args.query,
            "institution_hint": args.institution_hint,
            "fetched_at_unix": int(time.time()),
            "count": len(normalized),
            "results": normalized,
            "raw_meta": payload.get("meta"),
        },
        args.output,
    )


def command_apify_input(args: argparse.Namespace) -> None:
    if not args.author_id and not args.query:
        raise SystemExit("Provide --author-id for authorProfile mode or --query for search mode.")
    if args.author_id:
        data: Dict[str, Any] = {
            "mode": "authorProfile",
            "authorId": args.author_id,
            "limit": args.limit,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }
    else:
        data = {
            "mode": "search",
            "query": args.query,
            "limit": args.limit,
            "sortBy": args.sort_by,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }
        if args.year_from:
            data["yearFrom"] = args.year_from
        if args.year_to:
            data["yearTo"] = args.year_to
    write_json(data, args.output)


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [plain(v) for v in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def command_scholarly_author(args: argparse.Namespace) -> None:
    try:
        from scholarly import scholarly
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: scholarly. Install it in an isolated environment with "
            "`python -m pip install scholarly`."
        ) from exc

    sections = split_csv(args.sections)
    if args.author_id:
        author = scholarly.search_author_id(args.author_id)
    elif args.name:
        author = next(scholarly.search_author(args.name))
    else:
        raise SystemExit("Provide --author-id or --name.")

    if sections:
        author = scholarly.fill(author, sections=sections)
    else:
        author = scholarly.fill(author)

    data = plain(author)
    if args.max_publications >= 0 and isinstance(data, dict):
        pubs = data.get("publications")
        if isinstance(pubs, list):
            data["publications"] = pubs[: args.max_publications]
            data["publications_truncated_to"] = args.max_publications

    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "source": "scholarly",
            "fetched_at_unix": int(time.time()),
            "result": data,
            "warnings": [
                "Google Scholar may block automated requests. Treat CAPTCHA/403/429 as blockers.",
            ],
        },
        args.output,
    )


def command_schema(args: argparse.Namespace) -> None:
    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "subject": {
                "name": "",
                "scholar_id": "",
                "scholar_url": "",
                "orcid": "",
                "homepage": "",
                "affiliations": [],
                "interests": [],
                "last_known_institutions": [],
                "topics": [],
            },
            "metrics": {
                "cited_by_count": None,
                "h_index": None,
                "i10_index": None,
                "cited_by_5y": None,
                "h_index_5y": None,
                "i10_index_5y": None,
                "works_count": None,
                "citations_per_year": {},
            },
            "publications": [],
            "coauthors": [],
            "citation_events": [],
            "provenance": {
                "sources": [],
                "field_sources": {},
                "fetched_at": "",
                "warnings": [],
            },
        },
        args.output,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scholar profile route planner and helper tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Plan the lightest non-SerpApi route for a scholar task.")
    plan.add_argument("--target", required=True, help="Scholar URL, author ID, or author name query.")
    plan.add_argument(
        "--needs",
        default="profile,indices,publications,enrichment",
        help="Comma-separated needs: profile,indices,publications,coauthors,deep-citations,enrichment,report.",
    )
    plan.add_argument("--max-publications", type=int, default=100)
    plan.add_argument("--deep-citations", action="store_true")
    plan.add_argument("--allow-apify", action="store_true")
    plan.add_argument("--allow-scholar-scrape", action="store_true", help="Include best-effort direct Google Scholar scraping via scholarly.")
    plan.add_argument("--allow-external-crawlers", action="store_true", help="Include external Scholar crawler suggestions.")
    plan.add_argument("--batch-ready", action="store_true", help="Include scholar-scraper batch suggestion.")
    plan.add_argument("--openalex", action="store_true", help="Always include OpenAlex enrichment.")
    plan.add_argument("--openalex-query", help="Author name to use for OpenAlex when target is a Scholar ID.")
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    oa = sub.add_parser("openalex-author", help="Fetch or inspect OpenAlex author search candidates.")
    oa.add_argument("--query", required=True)
    oa.add_argument("--institution-hint", help="Optional affiliation clue used to rank returned candidates.")
    oa.add_argument("--per-page", type=int, default=5)
    oa.add_argument("--mailto", help="Optional polite-pool email. Can also use OPENALEX_MAILTO.")
    oa.add_argument("--timeout", type=float, default=30.0)
    oa.add_argument("--dry-run", action="store_true")
    oa.add_argument("--output")
    oa.set_defaults(func=command_openalex_author)

    apify = sub.add_parser("apify-input", help="Generate Apify actor input without running the actor.")
    apify.add_argument("--author-id")
    apify.add_argument("--query")
    apify.add_argument("--limit", type=int, default=100)
    apify.add_argument("--sort-by", default="relevance", choices=["relevance", "date"])
    apify.add_argument("--year-from", type=int)
    apify.add_argument("--year-to", type=int)
    apify.add_argument("--output")
    apify.set_defaults(func=command_apify_input)

    scholarly_parser = sub.add_parser("scholarly-author", help="Fetch a Scholar author via optional scholarly dependency.")
    scholarly_parser.add_argument("--author-id")
    scholarly_parser.add_argument("--name")
    scholarly_parser.add_argument("--sections", default="basics,indices,counts,publications")
    scholarly_parser.add_argument("--max-publications", type=int, default=100)
    scholarly_parser.add_argument("--output")
    scholarly_parser.set_defaults(func=command_scholarly_author)

    schema = sub.add_parser("schema", help="Print the normalized author profile schema.")
    schema.add_argument("--output")
    schema.set_defaults(func=command_schema)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
