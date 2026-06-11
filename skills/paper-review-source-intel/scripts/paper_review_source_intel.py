#!/usr/bin/env python3
"""Planning and normalization helpers for paper and peer-review source workflows."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse


SCHEMA_VERSION = "0.1"

VENUE_ALIASES = {
    "acl": "ACL",
    "emnlp": "EMNLP",
    "naacl": "NAACL",
    "coling": "COLING",
    "cvpr": "CVPR",
    "iccv": "ICCV",
    "wacv": "WACV",
    "eccv": "ECCV",
    "iclr": "ICLR",
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "icml": "ICML",
    "aistats": "AISTATS",
    "colt": "COLT",
}

OPENREVIEW_VENUES = {"ICLR", "NeurIPS", "ICML", "COLM", "TMLR", "ARR", "ACL", "EMNLP", "CoRL"}
ACL_VENUES = {"ACL", "EMNLP", "NAACL", "COLING"}
CVF_VENUES = {"CVPR", "ICCV", "WACV", "ECCV"}
PMLR_VENUES = {"ICML", "AISTATS", "COLT"}

SCHEMA_SUMMARY = {
    "raw/": "Untouched API JSON, scraped HTML, PDFs, screenshots, or logs.",
    "normalized/papers.jsonl": "Normalized paper/submission/proceedings rows.",
    "normalized/reviews.jsonl": "Normalized review, meta-review, rebuttal, and decision rows.",
    "normalized/artifacts.jsonl": "Downloaded/generated artifacts such as PDFs, text, BibTeX, screenshots, and reports.",
    "sources.csv": "Source review table with source URL, priority, and status.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def split_csv(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip().lower().replace("_", "-")
            if part:
                out.append(part)
    return out


def normalize_venue(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    stripped = value.strip()
    return VENUE_ALIASES.get(stripped.lower(), stripped)


def content_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def first_present(record: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in record and record.get(key) not in (None, ""):
            return record.get(key)
    content = record.get("content")
    if isinstance(content, dict):
        for key in keys:
            if key in content:
                value = content_value(content.get(key))
                if value not in (None, ""):
                    return value
    return None


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    query = parse_qs(parsed.query)
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": path or "/",
        "source": "unknown",
        "source_kind": "unknown",
        "ids": {},
        "recommended_needs": [],
        "recommended_routes": [],
    }

    if "openreview.net" in host:
        forum_id = query.get("id", [""])[0]
        result.update(
            {
                "source": "openreview",
                "source_kind": "review-platform",
                "ids": {"forum_id": forum_id} if forum_id else {},
                "recommended_needs": ["papers", "reviews", "meta-reviews", "rebuttals", "decisions"],
                "recommended_routes": ["openreview-public-page", "openreview-py"],
            }
        )
        return result

    arxiv_match = re.search(r"/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?|[a-z-]+/[0-9]{7}(?:v\d+)?)", path)
    if "arxiv.org" in host and arxiv_match:
        result.update(
            {
                "source": "arxiv",
                "source_kind": "preprint",
                "ids": {"arxiv_id": arxiv_match.group(1).removesuffix(".pdf")},
                "recommended_needs": ["papers", "pdfs"],
                "recommended_routes": ["arxiv-api"],
            }
        )
        return result

    if "aclanthology.org" in host:
        acl_id = path.strip("/").split("/")[0]
        result.update(
            {
                "source": "acl-anthology",
                "source_kind": "official-proceedings",
                "ids": {"acl_id": acl_id} if acl_id else {},
                "recommended_needs": ["papers", "pdfs", "bibtex"],
                "recommended_routes": ["acl-anthology-python"],
            }
        )
        return result

    if "openaccess.thecvf.com" in host:
        venue_year = path.strip("/").split("/")[0] if path.strip("/") else ""
        result.update(
            {
                "source": "cvf-openaccess",
                "source_kind": "official-proceedings",
                "ids": {"venue_year": venue_year} if venue_year else {},
                "recommended_needs": ["papers", "pdfs", "bibtex"],
                "recommended_routes": ["cvf-static"],
            }
        )
        return result

    if "proceedings.mlr.press" in host:
        volume_match = re.search(r"/v(\d+)", path)
        result.update(
            {
                "source": "pmlr",
                "source_kind": "official-proceedings",
                "ids": {"volume": volume_match.group(1)} if volume_match else {},
                "recommended_needs": ["papers", "pdfs", "bibtex"],
                "recommended_routes": ["pmlr-static"],
            }
        )
        return result

    if "papers.nips.cc" in host or "neurips.cc" in host:
        year_match = re.search(r"(20\d{2}|19\d{2})", path)
        result.update(
            {
                "source": "neurips-proceedings",
                "source_kind": "official-proceedings",
                "ids": {"year": year_match.group(1)} if year_match else {},
                "recommended_needs": ["papers", "pdfs"],
                "recommended_routes": ["neurips-proceedings"],
            }
        )
        return result

    if "doi.org" in host:
        result.update(
            {
                "source": "doi",
                "source_kind": "identifier",
                "ids": {"doi": path.strip("/")},
                "recommended_needs": ["papers", "metadata", "pdfs"],
                "recommended_routes": ["crossref-public", "unpaywall-public"],
            }
        )
        return result

    if "semanticscholar.org" in host:
        result.update(
            {
                "source": "semantic-scholar",
                "source_kind": "metadata-enrichment",
                "ids": {},
                "recommended_needs": ["metadata", "citations", "authors"],
                "recommended_routes": ["semantic-scholar-public-api"],
            }
        )
        return result

    if "openalex.org" in host:
        source_id = path.strip("/")
        result.update(
            {
                "source": "openalex",
                "source_kind": "metadata-enrichment",
                "ids": {"openalex_id": source_id} if source_id else {},
                "recommended_needs": ["metadata", "citations", "authors", "topics"],
                "recommended_routes": ["openalex-api"],
            }
        )
        return result

    return result


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_url(target)
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", target, flags=re.I)
    if doi_match:
        return {
            "url": "",
            "host": "",
            "path": "",
            "source": "doi",
            "source_kind": "identifier",
            "ids": {"doi": doi_match.group(0)},
            "recommended_needs": ["papers", "metadata", "pdfs"],
            "recommended_routes": ["crossref-public", "unpaywall-public"],
        }
    return {
        "url": "",
        "host": "",
        "path": "",
        "source": "topic",
        "source_kind": "query",
        "ids": {"query": target},
        "recommended_needs": ["papers", "metadata", "report"],
        "recommended_routes": ["openalex-public-api", "semantic-scholar-public-api", "crossref-public"],
    }


def route_for_venue(venue: Optional[str], needs: List[str], year: Optional[int]) -> List[Dict[str, Any]]:
    routes: List[Dict[str, Any]] = []
    if not venue:
        return routes

    if venue in OPENREVIEW_VENUES and any(
        need in needs for need in ["reviews", "review", "scores", "meta-reviews", "meta-review", "rebuttals", "decisions", "decision", "venue-stats", "weaknesses"]
    ):
        routes.append(
            {
                "lane": "openreview-public-page",
                "priority": "primary",
                "why": "Default narrowed route for public OpenReview pages and visible notes without requiring an MCP server.",
                "suggested_calls": [
                    "Open the forum/group page and save visible public JSON/HTML under raw/.",
                    "Normalize public note JSON with --source openreview-public-page.",
                ],
                "setup": ["No MCP required; visibility depends on what OpenReview exposes publicly."],
            }
        )
        routes.append(
            {
                "lane": "openreview-py",
                "priority": "optional",
                "why": "Optional local library for custom venue/group queries when public pages are insufficient.",
                "setup": ["python -m venv .venv", ".venv\\Scripts\\python -m pip install openreview-py"],
            }
        )

    if venue in ACL_VENUES:
        routes.append(
            {
                "lane": "acl-anthology",
                "priority": "primary",
                "why": "Official ACL Anthology metadata and PDFs for NLP proceedings.",
                "setup": ["pip install acl-anthology"],
                "source_hint": "Use Anthology.from_repo() or official ACL metadata under data/xml and data/yaml.",
            }
        )

    if venue in CVF_VENUES:
        venue_year = f"{venue}{year}" if year else f"{venue}<YEAR>"
        routes.append(
            {
                "lane": "cvf-openaccess",
                "priority": "primary",
                "why": "Official CVF Open Access accepted-paper pages.",
                "source_hint": f"https://openaccess.thecvf.com/{venue_year}",
            }
        )

    if venue in PMLR_VENUES:
        routes.append(
            {
                "lane": "pmlr",
                "priority": "primary",
                "why": "Official PMLR volume pages for ICML/AISTATS/COLT proceedings.",
                "source_hint": "Resolve the year to its PMLR volume before scraping.",
            }
        )

    if venue == "NeurIPS":
        routes.append(
            {
                "lane": "neurips-proceedings",
                "priority": "primary",
                "why": "Official NeurIPS proceedings for accepted papers and PDFs.",
                "source_hint": "https://papers.nips.cc/",
            }
        )

    return routes


def generic_routes(target_info: Dict[str, Any], needs: List[str], scale: str) -> List[Dict[str, Any]]:
    routes: List[Dict[str, Any]] = []
    source = target_info.get("source")
    recommended = target_info.get("recommended_routes") or []

    if source == "openreview" and not any(route.get("lane") == "openreview-public-page" for route in routes):
        routes.append(
            {
                "lane": "openreview-public-page",
                "priority": "primary",
                "why": "The target is an OpenReview page or forum; capture only public visible fields by default.",
                "suggested_calls": ["Open public forum/group page; save visible note JSON/HTML; normalize visible fields."],
            }
        )

    if any(need in needs for need in ["papers", "metadata", "pdfs", "full-text", "report", "search"]) or source in {"topic", "doi", "arxiv"}:
        routes.append(
            {
                "lane": "public-paper-sources",
                "priority": "primary" if source == "topic" else "secondary",
                "why": "Default narrowed route using public official sources and open metadata without paper-search MCP.",
                "suggested_calls": [
                    "Use arXiv Atom, Crossref public REST, OpenAlex public API, Unpaywall public endpoint, and official proceedings pages.",
                    "Download only open-access PDFs from official or OA URLs.",
                ],
                "setup": ["No required API key or MCP; use polite rate limits and record blockers."],
            }
        )

    if any(need in needs for need in ["citations", "authors", "topics", "enrichment"]):
        routes.append(
            {
                "lane": "openalex-semantic-scholar-public",
                "priority": "secondary",
                "why": "Public citation, author, topic, and identifier enrichment without required credentials.",
                "suggested_calls": ["OpenAlex works/authors API", "Semantic Scholar paper/author API"],
            }
        )

    if scale in {"large", "deep"}:
        routes.append(
            {
                "lane": "scholar-megasearch-pattern",
                "priority": "optional",
                "why": "Optional orchestration pattern for broad fan-out; not part of the narrowed default closure.",
                "note": "Use only after confirming source licenses, local installation requirements, and user approval.",
            }
        )

    if recommended:
        for lane in recommended:
            if not any(route.get("lane") == lane for route in routes):
                priority = "optional" if lane in {"openreview-py", "paper-search-mcp", "openreview-mcp"} else "source-specific"
                routes.append({"lane": lane, "priority": priority, "why": "Suggested by URL/identifier inspection."})

    return routes


def build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    needs = split_csv(args.needs)
    target_info = classify_target(args.target)
    if not needs:
        needs = target_info.get("recommended_needs") or ["papers", "metadata", "report"]
    venue = normalize_venue(args.venue)
    year = args.year
    routes = route_for_venue(venue, needs, year) + generic_routes(target_info, needs, args.scale)

    seen = set()
    deduped = []
    for route in routes:
        lane = route.get("lane")
        if lane in seen:
            continue
        seen.add(lane)
        deduped.append(route)

    if not deduped:
        deduped.append(
            {
                "lane": "manual-source-resolution",
                "priority": "fallback",
                "why": "The target is ambiguous. Resolve exact venue, URL, DOI, arXiv ID, or OpenReview forum first.",
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "target": args.target,
        "target_info": target_info,
        "needs": needs,
        "venue": venue,
        "year": year,
        "scale": args.scale,
        "recommended_routes": deduped,
        "output_contract": SCHEMA_SUMMARY,
        "guardrails": [
            "Default to public official pages/APIs and local normalization; do not require MCP, paid services, or private credentials for the base closure.",
            "Prefer official APIs/proceedings and public OpenReview visibility over general search.",
            "Do not bypass paywalls, CAPTCHAs, private reviews, or login gates.",
            "Keep credentials, cookies, proxies, headers, and .env files local and untracked.",
            "Record source IDs, URLs, fetch timestamps, limits, and blockers in the manifest.",
        ],
    }


def write_json(data: Any, output: Optional[str]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def command_plan(args: argparse.Namespace) -> None:
    write_json(build_plan(args), args.output)


def command_inspect_url(args: argparse.Namespace) -> None:
    write_json(inspect_url(args.url), args.output)


def command_schema(args: argparse.Namespace) -> None:
    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "directory_contract": SCHEMA_SUMMARY,
            "paper_row_required": ["row_type", "row_id", "source", "source_id", "source_url", "fetched_at", "title"],
            "review_row_required": ["row_type", "row_id", "source", "source_id", "source_url", "fetched_at", "openreview_forum"],
            "artifact_row_required": ["row_type", "row_id", "artifact_type", "source", "local_path", "created_at"],
            "dedupe_keys": ["doi", "arxiv_id", "openreview_forum", "acl_id", "normalized_title+venue+year"],
        },
        args.output,
    )


def command_scaffold(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    for rel in ["raw", "normalized", "reports"]:
        (output_dir / rel).mkdir(parents=True, exist_ok=True)
    plan = build_plan(args)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "target": args.target,
        "needs": plan["needs"],
        "venue": plan["venue"],
        "year": plan["year"],
        "created_at": now_iso(),
        "plan": plan,
        "commands": [],
        "limits": {"scale": args.scale},
        "credential_policy": "Keep credentials in local env/.env outside committed artifacts; do not store secrets in this run directory.",
        "blockers": [],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lane", "priority", "status", "source_url", "notes"])
        writer.writeheader()
        for route in plan["recommended_routes"]:
            writer.writerow(
                {
                    "lane": route.get("lane", ""),
                    "priority": route.get("priority", ""),
                    "status": "planned",
                    "source_url": route.get("source_hint", ""),
                    "notes": route.get("why", ""),
                }
            )
    (output_dir / "reports" / "summary.md").write_text(
        "# Paper Review Source Summary\n\n"
        "Status: scaffolded.\n\n"
        "Use normalized row IDs from `normalized/` when writing the final synthesis.\n",
        encoding="utf-8",
    )
    print(str(output_dir))


def load_records(path: Path) -> Iterable[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ["notes", "papers", "items", "results", "data", "submissions", "works"]:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [data]
    return []


def is_review_like(record: Dict[str, Any]) -> bool:
    invitation = str(record.get("invitation") or record.get("type") or "").lower()
    content = record.get("content") if isinstance(record.get("content"), dict) else {}
    haystack = " ".join([invitation] + [str(key).lower() for key in content.keys()])
    return any(token in haystack for token in ["review", "meta_review", "meta-review", "rebuttal", "decision", "rating", "confidence"])


def normalize_paper(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    title = first_present(record, ["title", "paper_title", "name", "display_name"])
    source_id = str(first_present(record, ["id", "forum", "paperId", "paper_id", "doi", "arxiv_id"]) or "")
    source_url = first_present(record, ["url", "html_url", "source_url", "paper_url"]) or ""
    authors = first_present(record, ["authors", "author", "author_names"]) or []
    return {
        "row_type": "paper",
        "row_id": stable_id(source, source_id, title, source_url),
        "source": source,
        "source_priority": "primary" if source in {"openreview", "acl-anthology", "cvf", "pmlr", "neurips-proceedings", "arxiv"} else "secondary",
        "source_id": source_id,
        "source_url": source_url,
        "fetched_at": now_iso(),
        "title": title,
        "authors": authors,
        "abstract": first_present(record, ["abstract"]),
        "venue": first_present(record, ["venue", "conference", "booktitle"]),
        "year": first_present(record, ["year", "publication_year"]),
        "doi": first_present(record, ["doi"]),
        "arxiv_id": first_present(record, ["arxiv_id", "arxivId"]),
        "openreview_forum": first_present(record, ["forum"]),
        "pdf_url": first_present(record, ["pdf_url", "pdf", "pdfUrl"]),
        "status": first_present(record, ["status", "decision"]),
        "citations_count": first_present(record, ["citations_count", "citationCount", "cited_by_count"]),
        "raw_ref": raw_ref,
    }


def normalize_review(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    content = record.get("content") if isinstance(record.get("content"), dict) else {}
    invitation = str(record.get("invitation") or "")
    row_type = "review"
    low = invitation.lower()
    if "meta" in low:
        row_type = "meta_review"
    elif "rebuttal" in low or "response" in low:
        row_type = "rebuttal"
    elif "decision" in low:
        row_type = "decision"
    source_id = str(record.get("id") or record.get("note_id") or stable_id(invitation, record.get("forum")))
    return {
        "row_type": row_type,
        "row_id": stable_id(source, source_id, record.get("forum"), invitation),
        "source": source,
        "source_id": source_id,
        "source_url": f"https://openreview.net/forum?id={record.get('forum')}" if record.get("forum") else "",
        "fetched_at": now_iso(),
        "openreview_forum": record.get("forum"),
        "invitation": invitation,
        "rating": content_value(content.get("rating")),
        "confidence": content_value(content.get("confidence")),
        "recommendation": content_value(content.get("recommendation")),
        "decision": content_value(content.get("decision")),
        "summary": content_value(content.get("summary")),
        "strengths": content_value(content.get("strengths")),
        "weaknesses": content_value(content.get("weaknesses")),
        "questions": content_value(content.get("questions")),
        "limitations": content_value(content.get("limitations")),
        "visibility": "unknown",
        "raw_ref": raw_ref,
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def command_normalize(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    records = list(load_records(input_path))
    papers: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []
    raw_ref = str(input_path)
    for record in records:
        if is_review_like(record):
            reviews.append(normalize_review(record, args.source, raw_ref))
        else:
            papers.append(normalize_paper(record, args.source, raw_ref))
    paper_count = write_jsonl(output_dir / "papers.jsonl", papers)
    review_count = write_jsonl(output_dir / "reviews.jsonl", reviews)
    write_jsonl(output_dir / "artifacts.jsonl", [])
    write_json({"papers": paper_count, "reviews": review_count, "output_dir": str(output_dir)}, args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Plan source routes for a paper/review evidence task.")
    plan.add_argument("--target", required=True)
    plan.add_argument("--needs", action="append", help="Comma-separated needs such as papers,reviews,decisions,pdfs,report.")
    plan.add_argument("--venue")
    plan.add_argument("--year", type=int)
    plan.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="medium")
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    inspect = sub.add_parser("inspect-url", help="Classify a source URL.")
    inspect.add_argument("url")
    inspect.add_argument("--output")
    inspect.set_defaults(func=command_inspect_url)

    schema = sub.add_parser("schema", help="Print the normalized output schema.")
    schema.add_argument("--output")
    schema.set_defaults(func=command_schema)

    scaffold = sub.add_parser("scaffold", help="Create a run directory scaffold.")
    scaffold.add_argument("--output-dir", required=True)
    scaffold.add_argument("--target", required=True)
    scaffold.add_argument("--needs", action="append")
    scaffold.add_argument("--venue")
    scaffold.add_argument("--year", type=int)
    scaffold.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="medium")
    scaffold.set_defaults(func=command_scaffold)

    normalize = sub.add_parser("normalize", help="Normalize a raw JSON/JSONL capture into JSONL artifacts.")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--source", required=True)
    normalize.add_argument("--output-dir", required=True)
    normalize.add_argument("--output")
    normalize.set_defaults(func=command_normalize)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
