#!/usr/bin/env python3
"""Planning and normalization helpers for AI conference/workshop intelligence."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse


SCHEMA_VERSION = "0.1"

SCHEMA_SUMMARY = {
    "raw/": "Untouched API JSON, scraped HTML, YAML, CSV exports, screenshots, PDFs, and logs.",
    "normalized/events.jsonl": "Conference/year/event rows.",
    "normalized/workshops.jsonl": "Workshop editions, deadlines, websites, OpenReview venues, topics, and paper-list sources.",
    "normalized/papers.jsonl": "Accepted paper, submission, proceedings, oral/spotlight, and workshop-paper rows.",
    "normalized/policies.jsonl": "CFP, review policy, ethics policy, compute policy, reviewer guidance, and timeline rows.",
    "normalized/awards.jsonl": "Best-paper, honorable mention, oral, spotlight, and other award/program-label rows.",
    "normalized/artifacts.jsonl": "Local files, screenshots, downloaded metadata files, logs, and generated reports.",
    "sources.csv": "Source review table with source URL, priority, and status.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}

VENUE_ALIASES = {
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "icml": "ICML",
    "iclr": "ICLR",
    "colm": "COLM",
    "corl": "CoRL",
    "acl": "ACL",
    "emnlp": "EMNLP",
    "naacl": "NAACL",
    "coling": "COLING",
    "cvpr": "CVPR",
    "iccv": "ICCV",
    "eccv": "ECCV",
    "wacv": "WACV",
    "aaai": "AAAI",
    "ijcai": "IJCAI",
    "kdd": "KDD",
    "www": "WWW",
    "thewebconf": "WWW",
    "sigir": "SIGIR",
    "aistats": "AISTATS",
    "colt": "COLT",
}

OPENREVIEW_VENUES = {"NeurIPS", "ICML", "ICLR", "COLM", "CoRL"}
WORKSHOP_TRACKER_VENUES = {"NeurIPS", "ICML", "ICLR", "CVPR", "COLM", "CoRL", "ICRA", "IROS"}
ACL_VENUES = {"ACL", "EMNLP", "NAACL", "COLING"}
CVF_VENUES = {"CVPR", "ICCV", "ECCV", "WACV"}
PMLR_VENUES = {"ICML", "AISTATS", "COLT"}
OFFICIAL_HINTS = {
    "NeurIPS": ["https://neurips.cc/", "https://papers.nips.cc/"],
    "ICML": ["https://icml.cc/", "https://proceedings.mlr.press/"],
    "ICLR": ["https://iclr.cc/", "https://openreview.net/"],
    "COLM": ["https://colmweb.org/", "https://openreview.net/"],
    "CoRL": ["https://www.corl.org/", "https://openreview.net/"],
    "ACL": ["https://www.aclweb.org/", "https://aclanthology.org/"],
    "EMNLP": ["https://2025.emnlp.org/", "https://aclanthology.org/"],
    "NAACL": ["https://2025.naacl.org/", "https://aclanthology.org/"],
    "COLING": ["https://coling2025.org/", "https://aclanthology.org/"],
    "CVPR": ["https://cvpr.thecvf.com/", "https://openaccess.thecvf.com/"],
    "ICCV": ["https://iccv.thecvf.com/", "https://openaccess.thecvf.com/"],
    "ECCV": ["https://eccv.ecva.net/", "https://openaccess.thecvf.com/"],
    "WACV": ["https://wacv.thecvf.com/", "https://openaccess.thecvf.com/"],
    "AAAI": ["https://aaai.org/conference/aaai/", "https://ojs.aaai.org/"],
    "IJCAI": ["https://ijcai.org/", "https://www.ijcai.org/proceedings/"],
    "KDD": ["https://kdd.org/kdd2025/", "https://dl.acm.org/conference/kdd"],
    "WWW": ["https://www2025.thewebconf.org/", "https://dl.acm.org/conference/www"],
    "SIGIR": ["https://sigir.org/sigir2025/", "https://dl.acm.org/conference/sigir"],
    "AISTATS": ["https://aistats.org/", "https://proceedings.mlr.press/"],
    "COLT": ["https://learningtheory.org/colt2025/", "https://proceedings.mlr.press/"],
}

NEED_ALIASES = {
    "paper": "accepted-papers",
    "papers": "accepted-papers",
    "accepted": "accepted-papers",
    "accepted-paper": "accepted-papers",
    "accepted-papers": "accepted-papers",
    "proceedings": "accepted-papers",
    "workshop": "workshops",
    "workshops": "workshops",
    "deadline": "deadlines",
    "deadlines": "deadlines",
    "cfp": "cfp",
    "call-for-papers": "cfp",
    "policy": "policy",
    "review-policy": "policy",
    "ethics": "policy",
    "review": "reviews",
    "reviews": "reviews",
    "decision": "decisions",
    "decisions": "decisions",
    "award": "awards",
    "awards": "awards",
    "best-paper": "awards",
    "oral": "awards",
    "spotlight": "awards",
    "program": "program",
    "schedule": "program",
    "report": "report",
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
                out.append(NEED_ALIASES.get(part, part))
    return out


def normalize_venue(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    stripped = value.strip()
    return VENUE_ALIASES.get(stripped.lower(), stripped)


def infer_venue_from_target(target: str) -> Optional[str]:
    normalized = target.lower()
    for alias, venue in sorted(VENUE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized):
            return venue
    return None


def content_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def first_present(record: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in record and record.get(key) not in (None, ""):
            return record.get(key)
    for parent_key in ["content", "metadata", "meta", "frontmatter"]:
        parent = record.get(parent_key)
        if isinstance(parent, dict):
            for key in keys:
                if key in parent:
                    value = content_value(parent.get(key))
                    if value not in (None, ""):
                        return value
    return None


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    query = parse_qs(parsed.query)
    path_l = path.lower()
    parts = [part for part in path.strip("/").split("/") if part]
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

    if host == "github.com" and len(parts) >= 2:
        owner, repo = parts[0], parts[1]
        if owner.lower() == "yeping-hu" and repo.lower() == "ai-workshop-tracker":
            result.update(
                {
                    "source": "ai-workshop-tracker",
                    "source_kind": "structured-workshop-tracker",
                    "ids": {"owner": owner, "repo": repo},
                    "recommended_needs": ["workshops", "deadlines", "accepted-papers"],
                    "recommended_routes": ["ai-workshop-tracker"],
                }
            )
            return result
        result.update(
            {
                "source": "github",
                "source_kind": "source-repository",
                "ids": {"owner": owner, "repo": repo},
                "recommended_needs": ["workshops", "accepted-papers", "report"],
                "recommended_routes": ["github-public-repo"],
            }
        )
        return result

    if "openreview.net" in host:
        forum_id = query.get("id", [""])[0]
        group_id = query.get("id", [""])[0] if "/group" in path_l else ""
        result.update(
            {
                "source": "openreview",
                "source_kind": "review-platform",
                "ids": {"forum_id": forum_id, "group_id": group_id} if (forum_id or group_id) else {},
                "recommended_needs": ["accepted-papers", "reviews", "decisions", "workshops"],
                "recommended_routes": ["openreview-public-page", "openreview-py"],
            }
        )
        return result

    if any(domain in host for domain in ["neurips.cc", "icml.cc", "iclr.cc"]):
        venue = "NeurIPS" if "neurips" in host else "ICML" if "icml" in host else "ICLR"
        source_kind = "official-venue-site"
        needs = ["cfp", "policy", "program", "workshops", "awards"]
        routes = ["official-venue-site"]
        if "workshop" in path_l or "/events/workshop" in path_l:
            source_kind = "official-workshop-list"
            needs = ["workshops", "deadlines", "accepted-papers"]
            routes = ["official-workshop-page", "ai-workshop-tracker", "openreview-public-page"]
        elif "callforpapers" in path_l or "call-for-papers" in path_l:
            source_kind = "official-cfp"
            needs = ["cfp", "policy", "deadlines"]
        result.update(
            {
                "source": "official-venue-site",
                "source_kind": source_kind,
                "ids": {"venue": venue, "year": infer_year(path)},
                "recommended_needs": needs,
                "recommended_routes": routes,
            }
        )
        return result

    if "aclanthology.org" in host:
        event = parts[1] if len(parts) >= 2 and parts[0] == "events" else (parts[0] if parts else "")
        result.update(
            {
                "source": "acl-anthology",
                "source_kind": "official-proceedings",
                "ids": {"event_or_paper": event} if event else {},
                "recommended_needs": ["accepted-papers", "program"],
                "recommended_routes": ["acl-anthology"],
            }
        )
        return result

    if "openaccess.thecvf.com" in host:
        venue_year = parts[0] if parts else ""
        result.update(
            {
                "source": "cvf-openaccess",
                "source_kind": "official-proceedings",
                "ids": {"venue_year": venue_year} if venue_year else {},
                "recommended_needs": ["accepted-papers", "program"],
                "recommended_routes": ["cvf-openaccess"],
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
                "recommended_needs": ["accepted-papers", "program"],
                "recommended_routes": ["pmlr"],
            }
        )
        return result

    if "papers.nips.cc" in host:
        result.update(
            {
                "source": "neurips-proceedings",
                "source_kind": "official-proceedings",
                "ids": {"year": infer_year(path)},
                "recommended_needs": ["accepted-papers", "program"],
                "recommended_routes": ["neurips-proceedings"],
            }
        )
        return result

    if any(domain in host for domain in ["aaai.org", "ijcai.org", "kdd.org", "thewebconf.org", "sigir.org", "dl.acm.org"]):
        result.update(
            {
                "source": "official-or-publisher-site",
                "source_kind": "official-proceedings-or-venue-site",
                "ids": {"path": path.strip("/")} if path.strip("/") else {},
                "recommended_needs": ["accepted-papers", "cfp", "policy", "awards", "program"],
                "recommended_routes": ["official-venue-site", "publisher-metadata"],
            }
        )
        return result

    return result


def infer_year(text: str) -> Optional[int]:
    match = re.search(r"(20\d{2}|19\d{2})", text)
    return int(match.group(1)) if match else None


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_url(target)
    return {
        "url": "",
        "host": "",
        "path": "",
        "source": "topic",
        "source_kind": "query",
        "ids": {"query": target},
        "recommended_needs": ["workshops", "accepted-papers", "cfp", "policy", "awards", "report"],
        "recommended_routes": ["official-venue-site", "ai-workshop-tracker", "openreview-public-page"],
    }


def dedupe_routes(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for route in routes:
        key = route.get("lane")
        if key in seen:
            continue
        seen.add(key)
        out.append(route)
    return out


def route_for_venue(venue: Optional[str], needs: List[str], year: Optional[int]) -> List[Dict[str, Any]]:
    needset = set(needs)
    routes: List[Dict[str, Any]] = []
    if not venue:
        return routes

    hints = OFFICIAL_HINTS.get(venue, [])
    if needset & {"cfp", "policy", "awards", "program", "deadlines", "workshops"}:
        routes.append(
            {
                "lane": "official-venue-site",
                "priority": "primary",
                "why": "Canonical source for CFP, review/ethics policy, schedules, awards, oral/spotlight labels, and workshop pages.",
                "source_hint": "; ".join(hints),
            }
        )

    if venue in WORKSHOP_TRACKER_VENUES and needset & {"workshops", "deadlines", "accepted-papers"}:
        routes.append(
            {
                "lane": "ai-workshop-tracker",
                "priority": "primary",
                "why": "Maintained structured workshop tracker with editions, deadlines, topics, OpenReview venue discovery, and accepted-paper caches for many ML workshops.",
                "source_hint": "https://github.com/Yeping-Hu/ai-workshop-tracker",
                "suggested_calls": [
                    "Use data/workshops/*.yml for workshop editions and deadlines.",
                    "Use cache/openreview/*.json for committed OpenReview-hosted accepted-paper lists when available.",
                    "Cross-check official workshop pages before reporting final policy, deadlines, or accepted counts.",
                ],
            }
        )

    if venue in OPENREVIEW_VENUES and needset & {"accepted-papers", "reviews", "decisions", "workshops", "awards"}:
        routes.append(
            {
                "lane": "openreview-public-page",
                "priority": "primary",
                "why": "Public OpenReview pages expose submissions, decisions, reviews, forum IDs, and workshop venue groups when the venue releases them.",
                "source_hint": f"https://openreview.net/group?id={venue}.cc/{year}/Conference" if year and venue != "CoRL" else "https://openreview.net/",
                "setup": ["No credentials for public visibility; record hidden/private fields as blockers."],
            }
        )
        routes.append(
            {
                "lane": "openreview-py",
                "priority": "optional",
                "why": "Use the official Python client for batch venue/group queries and pagination.",
                "setup": ["Install openreview-py in the skill runtime; credentials are optional and user-approved only."],
            }
        )

    if venue in ACL_VENUES and needset & {"accepted-papers", "program", "awards"}:
        routes.append(
            {
                "lane": "acl-anthology",
                "priority": "primary",
                "why": "Official ACL Anthology metadata and pages for NLP proceedings.",
                "source_hint": f"https://aclanthology.org/events/{venue.lower()}-{year}/" if year else "https://aclanthology.org/events/",
            }
        )

    if venue in CVF_VENUES and needset & {"accepted-papers", "program", "awards"}:
        routes.append(
            {
                "lane": "cvf-openaccess",
                "priority": "primary",
                "why": "Official CVF Open Access accepted-paper metadata and PDFs.",
                "source_hint": f"https://openaccess.thecvf.com/{venue}{year}" if year else "https://openaccess.thecvf.com/",
            }
        )

    if venue in PMLR_VENUES and needset & {"accepted-papers", "program"}:
        routes.append(
            {
                "lane": "pmlr",
                "priority": "primary",
                "why": "Official PMLR volume pages for ICML/AISTATS/COLT proceedings.",
                "source_hint": "https://proceedings.mlr.press/",
            }
        )

    if venue == "NeurIPS" and needset & {"accepted-papers", "program", "awards"}:
        routes.append(
            {
                "lane": "neurips-proceedings",
                "priority": "primary",
                "why": "Official NeurIPS proceedings for accepted papers and PDFs.",
                "source_hint": "https://papers.nips.cc/",
            }
        )

    if venue in {"AAAI", "IJCAI", "KDD", "WWW", "SIGIR"} and needset & {"accepted-papers", "program", "awards"}:
        routes.append(
            {
                "lane": "official-proceedings-or-publisher",
                "priority": "primary",
                "why": "Use official proceedings/program pages first; supplement with publisher and open metadata only after canonical URLs are captured.",
                "source_hint": "; ".join(hints),
            }
        )

    if needset & {"accepted-papers", "awards", "program"}:
        routes.append(
            {
                "lane": "open-metadata-enrichment",
                "priority": "secondary",
                "why": "Use OpenAlex, Crossref, Semantic Scholar, DBLP, DOI pages, or arXiv only to enrich official rows with identifiers, citations, and related links.",
            }
        )

    return routes


def generic_routes(target_info: Dict[str, Any], needs: List[str], scale: str) -> List[Dict[str, Any]]:
    routes: List[Dict[str, Any]] = []
    source = target_info.get("source")
    recommended = target_info.get("recommended_routes") or []

    if source == "ai-workshop-tracker":
        routes.append(
            {
                "lane": "ai-workshop-tracker",
                "priority": "primary",
                "why": "Target is the structured workshop tracker repository.",
                "source_hint": target_info.get("url"),
            }
        )
    if source == "openreview":
        routes.append(
            {
                "lane": "openreview-public-page",
                "priority": "primary",
                "why": "Target is an OpenReview page or group; capture public visible note/group fields.",
                "source_hint": target_info.get("url"),
            }
        )
    if source in {"acl-anthology", "cvf-openaccess", "pmlr", "neurips-proceedings"}:
        routes.append(
            {
                "lane": source,
                "priority": "primary",
                "why": "Target is an official proceedings source.",
                "source_hint": target_info.get("url"),
            }
        )
    if source in {"official-venue-site", "official-or-publisher-site"}:
        routes.append(
            {
                "lane": "official-venue-site",
                "priority": "primary",
                "why": "Target is an official venue/publisher page; preserve the page and normalize claims by type.",
                "source_hint": target_info.get("url"),
            }
        )

    for lane in recommended:
        if not any(route.get("lane") == lane for route in routes):
            routes.append({"lane": lane, "priority": "source-specific", "why": "Suggested by URL inspection."})

    if target_info.get("source") == "topic":
        routes.append(
            {
                "lane": "source-discovery",
                "priority": "fallback",
                "why": "Resolve exact venue/year/workshop/program URLs before bulk crawling.",
                "suggested_calls": ["Use AnySearch or official conference navigation to discover canonical pages, then re-run plan with --venue/--year or inspect-url."],
            }
        )
    if scale in {"large", "deep"}:
        routes.append(
            {
                "lane": "tracker-cross-check",
                "priority": "secondary",
                "why": "Use deadline trackers, best-paper lists, Paper Copilot-style pages, and broad crawlers only to broaden coverage and discover canonical URLs.",
            }
        )
    return routes


def build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    needs = split_csv(args.needs)
    target_info = classify_target(args.target)
    if not needs:
        needs = target_info.get("recommended_needs") or ["workshops", "accepted-papers", "cfp", "policy", "report"]
    venue = normalize_venue(args.venue) or infer_venue_from_target(args.target)
    year = args.year or infer_year(args.target)
    routes = []
    routes.extend(route_for_venue(venue, needs, year))
    routes.extend(generic_routes(target_info, needs, args.scale))
    routes = dedupe_routes(routes)
    if not routes:
        routes = [
            {
                "lane": "manual-source-resolution",
                "priority": "fallback",
                "why": "Resolve exact venue, year, workshop, OpenReview group/forum, official page, or proceedings URL before crawling.",
            }
        ]
    return {
        "schema_version": SCHEMA_VERSION,
        "target": args.target,
        "target_info": target_info,
        "needs": needs,
        "venue": venue,
        "year": year,
        "scale": args.scale,
        "recommended_routes": routes,
        "output_contract": SCHEMA_SUMMARY,
        "guardrails": [
            "Default to public official sources and local normalization; no MCP, paid services, private tokens, cookies, or login-gated data are required for the base closure.",
            "Prefer official venue pages, official proceedings, OpenReview public visibility, and maintained structured trackers over search snippets.",
            "Use third-party trackers and broad crawlers only as discovery or fallback until official URLs verify claims.",
            "Do not bypass paywalls, CAPTCHAs, private reviews, login gates, rate limits, robots restrictions, or license controls.",
            "Keep credentials, cookies, proxies, headers, browser storage, and .env files local and untracked.",
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
            "common_required": ["row_type", "row_id", "source", "source_priority", "source_id", "source_url", "fetched_at", "venue", "year", "raw_ref"],
            "event_row_required": ["row_type", "row_id", "source", "source_url", "venue", "year", "event_name"],
            "workshop_row_required": ["row_type", "row_id", "source", "source_url", "venue", "year", "workshop_name"],
            "paper_row_required": ["row_type", "row_id", "source", "source_url", "venue", "year", "title"],
            "policy_row_required": ["row_type", "row_id", "source", "source_url", "venue", "year", "policy_type", "title"],
            "award_row_required": ["row_type", "row_id", "source", "source_url", "venue", "year", "award_type", "title"],
            "dedupe_keys": ["openreview_forum", "doi", "acl_id", "pmlr_id", "cvf_id", "normalized_title+venue+year+track"],
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
        "credential_policy": "Default no-secret public-source closure. Keep optional credentials in private user-level env/.env outside committed artifacts.",
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
        "# Conference Workshop Intel Summary\n\n"
        "Status: scaffolded.\n\n"
        "Use normalized row IDs from `normalized/` when writing the final synthesis.\n",
        encoding="utf-8",
    )
    print(str(output_dir))


def load_records(path: Path) -> Iterable[Dict[str, Any]]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return []
    if suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ["workshops", "papers", "items", "results", "data", "events", "policies", "awards", "submissions"]:
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [data]
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise SystemExit("PyYAML is required to normalize YAML inputs. Run setup_conference_workshop_intel.ps1 or install PyYAML.") from exc
        data = yaml.safe_load(text)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
    raise SystemExit(f"Unsupported input format: {path}")


def infer_kind(record: Dict[str, Any], source: str) -> str:
    haystack = json.dumps(record, ensure_ascii=False).lower() + " " + source.lower()
    if any(token in haystack for token in ["workshop", "deadline", "organizer", "openreview_group"]):
        return "workshops"
    if any(token in haystack for token in ["cfp", "call for papers", "review policy", "ethics", "policy"]):
        return "policies"
    if any(token in haystack for token in ["best paper", "award", "oral", "spotlight", "honorable"]):
        return "awards"
    if any(token in haystack for token in ["paper", "title", "abstract", "authors", "doi", "forum"]):
        return "papers"
    if any(token in haystack for token in ["conference", "venue", "event"]):
        return "events"
    return "papers"


def source_priority(source: str) -> str:
    primary = {"official-venue-site", "openreview", "acl-anthology", "cvf-openaccess", "pmlr", "neurips-proceedings", "ai-workshop-tracker"}
    secondary = {"openalex", "semantic-scholar", "crossref", "dblp", "github"}
    source_l = source.lower()
    if source_l in primary or source_l.startswith("official"):
        return "primary"
    if source_l in secondary:
        return "secondary"
    return "fallback"


def base_row(record: Dict[str, Any], source: str, raw_ref: str, row_type: str, source_id: Any, source_url: Any) -> Dict[str, Any]:
    venue = normalize_venue(str(first_present(record, ["venue", "conference", "conf"]) or "")) or None
    year_raw = first_present(record, ["year", "conference_year", "edition_year"])
    year = int(year_raw) if str(year_raw or "").isdigit() else infer_year(str(record))
    return {
        "row_type": row_type,
        "row_id": stable_id(source, row_type, source_id, source_url, first_present(record, ["title", "name", "workshop_name"])),
        "source": source,
        "source_priority": source_priority(source),
        "source_id": str(source_id or ""),
        "source_url": source_url or "",
        "fetched_at": now_iso(),
        "venue": venue,
        "year": year,
        "raw_ref": raw_ref,
    }


def normalize_event(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    source_url = first_present(record, ["url", "website", "official_site", "source_url"]) or ""
    source_id = first_present(record, ["id", "event_id", "slug", "name"]) or source_url
    row = base_row(record, source, raw_ref, "event", source_id, source_url)
    row.update(
        {
            "event_name": first_present(record, ["event_name", "name", "title"]),
            "track": first_present(record, ["track"]),
            "location": first_present(record, ["location"]),
            "start_date": first_present(record, ["start_date", "start"]),
            "end_date": first_present(record, ["end_date", "end"]),
            "official_site": first_present(record, ["official_site", "website", "url"]),
            "program_url": first_present(record, ["program_url", "program"]),
            "submission_site": first_present(record, ["submission_site", "submission_url", "openreview"]),
            "notes": first_present(record, ["notes", "description"]),
        }
    )
    return row


def normalize_workshop(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    source_url = first_present(record, ["url", "website", "site", "source_url"]) or ""
    source_id = first_present(record, ["id", "slug", "acronym", "name", "title"]) or source_url
    row = base_row(record, source, raw_ref, "workshop", source_id, source_url)
    row.update(
        {
            "workshop_name": first_present(record, ["workshop_name", "name", "title"]),
            "acronym": first_present(record, ["acronym", "short_name"]),
            "track": first_present(record, ["track"]),
            "topics": first_present(record, ["topics", "tags", "topic"]),
            "deadline": first_present(record, ["deadline", "submission_deadline", "abstract_deadline"]),
            "notification_date": first_present(record, ["notification_date", "notification"]),
            "camera_ready_date": first_present(record, ["camera_ready_date", "camera_ready"]),
            "workshop_date": first_present(record, ["workshop_date", "date"]),
            "website": first_present(record, ["website", "url", "site"]),
            "openreview_group": first_present(record, ["openreview_group", "openreview", "venue_id", "group_id"]),
            "paper_list_url": first_present(record, ["paper_list_url", "papers_url", "accepted_papers_url"]),
            "accepted_paper_count": first_present(record, ["accepted_paper_count", "paper_count", "num_papers"]),
            "organizers": first_present(record, ["organizers", "chairs"]),
            "status": first_present(record, ["status"]),
            "notes": first_present(record, ["notes", "description"]),
        }
    )
    return row


def normalize_paper(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    source_url = first_present(record, ["url", "html_url", "source_url", "paper_url"]) or ""
    source_id = first_present(record, ["id", "forum", "paper_id", "paperId", "doi", "acl_id", "pmlr_id", "cvf_id"]) or source_url
    row = base_row(record, source, raw_ref, "paper", source_id, source_url)
    row.update(
        {
            "title": first_present(record, ["title", "paper_title", "name"]),
            "authors": first_present(record, ["authors", "author", "author_names"]),
            "abstract": first_present(record, ["abstract"]),
            "track": first_present(record, ["track"]),
            "workshop": first_present(record, ["workshop", "workshop_name"]),
            "decision": first_present(record, ["decision", "status"]),
            "presentation_type": first_present(record, ["presentation_type", "presentation", "session_type"]),
            "award": first_present(record, ["award"]),
            "doi": first_present(record, ["doi"]),
            "arxiv_id": first_present(record, ["arxiv_id", "arxivId"]),
            "openreview_forum": first_present(record, ["forum", "openreview_forum"]),
            "acl_id": first_present(record, ["acl_id"]),
            "pmlr_id": first_present(record, ["pmlr_id"]),
            "cvf_id": first_present(record, ["cvf_id"]),
            "pdf_url": first_present(record, ["pdf_url", "pdf", "pdfUrl"]),
            "software_url": first_present(record, ["software_url", "code_url", "github"]),
            "citations_count": first_present(record, ["citations_count", "citationCount", "cited_by_count"]),
            "topics": first_present(record, ["topics", "keywords", "tags"]),
        }
    )
    return row


def normalize_policy(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    source_url = first_present(record, ["url", "source_url", "official_url"]) or ""
    source_id = first_present(record, ["id", "slug", "policy_type", "title"]) or source_url
    row = base_row(record, source, raw_ref, "policy", source_id, source_url)
    row.update(
        {
            "policy_type": first_present(record, ["policy_type", "type"]) or "other",
            "title": first_present(record, ["title", "name"]),
            "track": first_present(record, ["track"]),
            "effective_date": first_present(record, ["effective_date", "date"]),
            "deadline": first_present(record, ["deadline"]),
            "summary": first_present(record, ["summary", "description", "text"]),
            "official": first_present(record, ["official"]) if first_present(record, ["official"]) is not None else source_priority(source) == "primary",
            "page_date": first_present(record, ["page_date", "updated_at", "last_modified"]),
            "notes": first_present(record, ["notes"]),
        }
    )
    return row


def normalize_award(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    source_url = first_present(record, ["url", "source_url", "official_url", "paper_url"]) or ""
    source_id = first_present(record, ["id", "award_type", "title", "paper_id"]) or source_url
    row = base_row(record, source, raw_ref, "award", source_id, source_url)
    row.update(
        {
            "award_type": first_present(record, ["award_type", "type", "presentation_type"]) or "other",
            "title": first_present(record, ["title", "paper_title", "name"]),
            "paper_row_id": first_present(record, ["paper_row_id"]),
            "authors": first_present(record, ["authors", "author_names"]),
            "track": first_present(record, ["track"]),
            "session": first_present(record, ["session"]),
            "official": first_present(record, ["official"]) if first_present(record, ["official"]) is not None else source_priority(source) == "primary",
            "notes": first_present(record, ["notes", "description"]),
        }
    )
    return row


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
    buckets: Dict[str, List[Dict[str, Any]]] = {key: [] for key in ["events", "workshops", "papers", "policies", "awards"]}
    records = list(load_records(input_path))
    raw_ref = str(input_path)
    for record in records:
        kind = args.kind or infer_kind(record, args.source)
        if kind == "events":
            buckets["events"].append(normalize_event(record, args.source, raw_ref))
        elif kind == "workshops":
            buckets["workshops"].append(normalize_workshop(record, args.source, raw_ref))
        elif kind == "policies":
            buckets["policies"].append(normalize_policy(record, args.source, raw_ref))
        elif kind == "awards":
            buckets["awards"].append(normalize_award(record, args.source, raw_ref))
        else:
            buckets["papers"].append(normalize_paper(record, args.source, raw_ref))

    counts = {name: write_jsonl(output_dir / f"{name}.jsonl", rows) for name, rows in buckets.items()}
    counts["artifacts"] = write_jsonl(output_dir / "artifacts.jsonl", [])
    counts["output_dir"] = str(output_dir)
    write_json(counts, args.output)


def fetch_status(url: str, timeout: int) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "conference-workshop-intel/0.1"})
    started = now_iso()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(256)
            return {
                "url": url,
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "bytes_sampled": len(body),
                "fetched_at": started,
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": False, "status": exc.code, "error": exc.reason, "fetched_at": started}
    except Exception as exc:  # noqa: BLE001 - CLI should report smoke blockers instead of crashing.
        return {"url": url, "ok": False, "status": None, "error": str(exc), "fetched_at": started}


def command_public_smoke(args: argparse.Namespace) -> None:
    urls = args.url or [
        "https://github.com/Yeping-Hu/ai-workshop-tracker",
        "https://openreview.net/",
        "https://aclanthology.org/",
        "https://openaccess.thecvf.com/",
        "https://proceedings.mlr.press/",
        "https://papers.nips.cc/",
    ]
    rows = [fetch_status(url, args.timeout) for url in urls]
    write_json({"schema_version": SCHEMA_VERSION, "checked": rows, "ok_count": sum(1 for row in rows if row["ok"])}, args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Plan source routes for a conference/workshop intelligence task.")
    plan.add_argument("--target", required=True)
    plan.add_argument("--needs", action="append", help="Comma-separated needs such as workshops,accepted-papers,cfp,policy,awards,report.")
    plan.add_argument("--venue")
    plan.add_argument("--year", type=int)
    plan.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="medium")
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    inspect = sub.add_parser("inspect-url", help="Classify a conference/workshop source URL.")
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

    normalize = sub.add_parser("normalize", help="Normalize a raw JSON/JSONL/CSV/YAML capture into JSONL artifacts.")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--source", required=True)
    normalize.add_argument("--output-dir", required=True)
    normalize.add_argument("--kind", choices=["events", "workshops", "papers", "policies", "awards"])
    normalize.add_argument("--output")
    normalize.set_defaults(func=command_normalize)

    smoke = sub.add_parser("public-smoke", help="Check reachability of public primary source roots.")
    smoke.add_argument("--url", action="append", help="Additional or replacement URL to check. Repeatable.")
    smoke.add_argument("--timeout", type=int, default=12)
    smoke.add_argument("--output")
    smoke.set_defaults(func=command_public_smoke)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
