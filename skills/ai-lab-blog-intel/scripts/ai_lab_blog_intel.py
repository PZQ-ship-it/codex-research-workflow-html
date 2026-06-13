#!/usr/bin/env python3
"""Helpers for AI lab/company blog routing, capture, and normalization."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "0.1"
USER_AGENT = "Codex ai-lab-blog-intel/0.1 (+https://github.com/openai/codex)"

SCHEMA_SUMMARY = {
    "raw/": "Untouched feed JSON transforms, sitemap captures, fetched HTML snippets, article text, and logs.",
    "normalized/posts.jsonl": "Normalized blog posts, research notes, announcements, feed entries, sitemap URLs, and index links.",
    "normalized/links.jsonl": "Linked papers, DOI/arXiv URLs, GitHub repos, model cards, datasets, benchmark pages, docs, and product links.",
    "normalized/sources.jsonl": "Source metadata, feeds, indexes, sitemaps, access status, and credential policy.",
    "sources.csv": "Source review table with URL, source type, priority, status, and auth requirement.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}

DEFAULT_SOURCES: Dict[str, Dict[str, Any]] = {
    "openai": {
        "name": "OpenAI",
        "feeds": ["https://openai.com/news/rss.xml"],
        "indexes": ["https://openai.com/news/"],
        "channels": ["news", "research"],
    },
    "google-research": {
        "name": "Google Research",
        "feeds": ["https://research.google/blog/rss/"],
        "indexes": ["https://research.google/blog/"],
        "channels": ["research"],
    },
    "deepmind": {
        "name": "Google DeepMind",
        "feeds": ["https://deepmind.google/blog/rss.xml"],
        "indexes": ["https://deepmind.google/blog/"],
        "channels": ["research", "blog"],
    },
    "google-ai": {
        "name": "Google AI",
        "feeds": ["https://blog.google/technology/ai/rss/"],
        "indexes": ["https://blog.google/technology/ai/"],
        "channels": ["ai", "blog"],
    },
    "microsoft-research": {
        "name": "Microsoft Research",
        "feeds": ["https://www.microsoft.com/en-us/research/feed/"],
        "indexes": ["https://www.microsoft.com/en-us/research/blog/"],
        "channels": ["research", "blog"],
    },
    "nvidia-research": {
        "name": "NVIDIA Research",
        "feeds": ["https://blogs.nvidia.com/blog/tag/nvidia-research/feed/"],
        "indexes": ["https://blogs.nvidia.com/blog/tag/nvidia-research/"],
        "channels": ["research", "blog"],
    },
    "nvidia-developer": {
        "name": "NVIDIA Developer Blog",
        "feeds": ["https://developer.nvidia.com/blog/feed"],
        "indexes": ["https://developer.nvidia.com/blog/"],
        "channels": ["developer", "engineering"],
    },
    "apple-ml": {
        "name": "Apple Machine Learning Research",
        "feeds": ["https://machinelearning.apple.com/rss.xml"],
        "indexes": ["https://machinelearning.apple.com/research"],
        "channels": ["research"],
    },
    "allen-ai": {
        "name": "Allen AI",
        "feeds": ["https://allenai.org/rss.xml"],
        "indexes": ["https://allenai.org/research", "https://allenai.org/blog"],
        "channels": ["research", "blog"],
    },
    "bair": {
        "name": "Berkeley BAIR",
        "feeds": ["https://bair.berkeley.edu/blog/feed.xml"],
        "indexes": ["https://bair.berkeley.edu/blog/"],
        "channels": ["blog"],
    },
    "mit-machine-learning": {
        "name": "MIT News Machine Learning",
        "feeds": ["https://news.mit.edu/rss/topic/machine-learning"],
        "indexes": ["https://news.mit.edu/topic/machine-learning"],
        "channels": ["news", "machine-learning"],
    },
    "cmu-ml": {
        "name": "CMU ML Blog",
        "feeds": ["https://blog.ml.cmu.edu/feed"],
        "indexes": ["https://blog.ml.cmu.edu/"],
        "channels": ["blog"],
    },
    "anthropic": {
        "name": "Anthropic",
        "feeds": [],
        "indexes": ["https://www.anthropic.com/news", "https://www.anthropic.com/research"],
        "sitemaps": ["https://www.anthropic.com/sitemap.xml"],
        "channels": ["news", "research"],
    },
    "anthropic-news": {
        "name": "Anthropic News",
        "feeds": [],
        "indexes": ["https://www.anthropic.com/news"],
        "sitemaps": ["https://www.anthropic.com/sitemap.xml"],
        "channels": ["news"],
    },
    "anthropic-research": {
        "name": "Anthropic Research",
        "feeds": [],
        "indexes": ["https://www.anthropic.com/research"],
        "sitemaps": ["https://www.anthropic.com/sitemap.xml"],
        "channels": ["research"],
    },
    "meta-ai": {
        "name": "Meta AI",
        "feeds": [],
        "indexes": ["https://ai.meta.com/blog/"],
        "sitemaps": ["https://ai.meta.com/sitemap.xml"],
        "channels": ["blog", "research"],
    },
    "stanford-hai": {
        "name": "Stanford HAI",
        "feeds": [],
        "indexes": ["https://hai.stanford.edu/news"],
        "channels": ["news"],
    },
    "stanford-sail": {
        "name": "Stanford AI Lab Blog",
        "feeds": [],
        "indexes": ["http://ai.stanford.edu/blog/"],
        "channels": ["blog"],
    },
}

ORG_ALIASES = {
    "google-deepmind": "deepmind",
    "gdm": "deepmind",
    "google": "google-research",
    "msr": "microsoft-research",
    "microsoft": "microsoft-research",
    "nvidia": "nvidia-research",
    "apple": "apple-ml",
    "apple-machine-learning": "apple-ml",
    "ai2": "allen-ai",
    "allenai": "allen-ai",
    "berkeley-bair": "bair",
    "mit": "mit-machine-learning",
    "cmu": "cmu-ml",
    "meta": "meta-ai",
    "anthropic-research": "anthropic-research",
    "anthropic-news": "anthropic-news",
}

NEED_ALIASES = {
    "post": "posts",
    "posts": "posts",
    "article": "posts",
    "articles": "posts",
    "feed": "feeds",
    "feeds": "feeds",
    "rss": "feeds",
    "atom": "feeds",
    "sitemap": "sitemap",
    "sitemaps": "sitemap",
    "index": "index",
    "html": "index",
    "links": "links",
    "artifacts": "links",
    "paper": "links",
    "papers": "links",
    "model": "links",
    "models": "links",
    "benchmark": "links",
    "benchmarks": "links",
    "report": "report",
    "summary": "report",
    "anysearch": "anysearch",
    "search": "anysearch",
    "apify": "apify",
}


class FetchError(RuntimeError):
    """Raised for HTTP fetch failures with context."""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower().replace("_", "-")).strip("-")


def canonical_org(value: str) -> str:
    key = slugify(value)
    return ORG_ALIASES.get(key, key)


def split_csv(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip().lower().replace("_", "-")
            if part:
                out.append(NEED_ALIASES.get(part, part))
    return out


def orgs_from_args(values: Optional[Sequence[str]]) -> List[str]:
    orgs = [canonical_org(value) for value in values or []]
    return orgs or ["openai", "anthropic", "google-research", "deepmind", "meta-ai"]


def text_from_html(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<script\b[^>]*>.*?</script\s*>", "", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style\s*>", "", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def absolute_url(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, html.unescape(href.strip()))


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def first_child_text(node: ET.Element, names: Sequence[str]) -> str:
    nameset = {name.lower() for name in names}
    for child in list(node):
        if strip_ns(child.tag).lower() in nameset:
            return html.unescape("".join(child.itertext()).strip())
    return ""


def first_child_attr(node: ET.Element, names: Sequence[str], attr: str) -> str:
    nameset = {name.lower() for name in names}
    for child in list(node):
        if strip_ns(child.tag).lower() in nameset:
            value = child.attrib.get(attr, "")
            if value:
                return html.unescape(value)
    return ""


def http_get_bytes(url: str, timeout: int = 25, accept: str = "*/*") -> Tuple[bytes, Dict[str, str], str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return body, headers, resp.geturl()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise FetchError(f"fetch failed for {url}: {exc}") from exc


def parse_xml_bytes(raw: bytes) -> ET.Element:
    try:
        return ET.fromstring(raw)
    except ET.ParseError:
        text = raw.decode("utf-8", errors="replace")
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
        text = text.replace("\ufffd", "")
        text = re.sub(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9]+;)", "&amp;", text)
        return ET.fromstring(text.encode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def topic_labels(text: str, url: str = "") -> List[str]:
    blob = f"{text} {url}".lower()
    labels: List[str] = []
    patterns = {
        "model-release": r"\b(model|gpt|claude|gemini|llama|mistral|olm[o]?|foundation model)\b",
        "alignment": r"\b(alignment|rlhf|constitutional|interpretability|mechanistic)\b",
        "safety": r"\b(safety|security|risk|red team|policy|evals?)\b",
        "agent-tools": r"\b(agent|tool use|computer use|browser|coding agent|workflow)\b",
        "benchmark": r"\b(benchmark|eval|leaderboard|swe-bench|gaia|mmlu|arena)\b",
        "systems": r"\b(system|infrastructure|training|serving|inference|scaling|cluster)\b",
        "productization": r"\b(product|api|developer|deployment|enterprise|release|launch)\b",
        "open-source": r"\b(open source|open-source|open weights|github|hugging face)\b",
        "multimodal": r"\b(multimodal|vision|image|video|audio|speech)\b",
        "robotics": r"\b(robot|robotics|embodied|autonomous)\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, blob):
            labels.append(label)
    return labels


def infer_org_from_url(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    path = urllib.parse.urlparse(url).path.lower()
    mapping = [
        ("openai.com", "openai"),
        ("anthropic.com", "anthropic"),
        ("deepmind.google", "deepmind"),
        ("research.google", "google-research"),
        ("blog.google", "google-ai"),
        ("ai.meta.com", "meta-ai"),
        ("microsoft.com", "microsoft-research"),
        ("developer.nvidia.com", "nvidia-developer"),
        ("blogs.nvidia.com", "nvidia-research"),
        ("machinelearning.apple.com", "apple-ml"),
        ("allenai.org", "allen-ai"),
        ("bair.berkeley.edu", "bair"),
        ("news.mit.edu", "mit-machine-learning"),
        ("blog.ml.cmu.edu", "cmu-ml"),
        ("hai.stanford.edu", "stanford-hai"),
        ("ai.stanford.edu", "stanford-sail"),
    ]
    for marker, org in mapping:
        if marker in host:
            return org
    if "/anthropic" in path:
        return "anthropic"
    return "unknown"


def infer_channel(url: str, default: str = "") -> str:
    path = urllib.parse.urlparse(url).path.lower()
    for channel in ["research", "news", "blog", "engineering", "developer", "models", "publications"]:
        if f"/{channel}" in path:
            return channel
    return default or "blog"


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": parsed.path or "/",
        "org": infer_org_from_url(url),
        "source_kind": "unknown",
        "recommended_needs": [],
        "recommended_routes": [],
        "auth_required": False,
    }
    if re.search(r"\.(rss|xml|atom)$", path) or "feed" in path:
        result.update(
            {
                "source_kind": "feed-or-sitemap",
                "recommended_needs": ["feeds", "posts", "report"],
                "recommended_routes": ["fetch-feeds if RSS/Atom", "fetch-sitemap if sitemap XML"],
            }
        )
    elif "sitemap" in path:
        result.update(
            {
                "source_kind": "sitemap",
                "recommended_needs": ["sitemap", "posts", "links", "report"],
                "recommended_routes": ["fetch-sitemap"],
            }
        )
    elif any(marker in path for marker in ["/blog", "/news", "/research", "/publications"]):
        result.update(
            {
                "source_kind": "blog-index-or-article",
                "channel": infer_channel(url),
                "recommended_needs": ["index", "posts", "links", "report"],
                "recommended_routes": ["fetch-index", "fetch-article when full links are needed"],
            }
        )
    else:
        result.update(
            {
                "source_kind": "web-page",
                "recommended_needs": ["index", "report"],
                "recommended_routes": ["inspect page manually, then fetch-index or fetch-article"],
            }
        )
    return result


def route_for_needs(needs: List[str], orgs: List[str], scale: str) -> List[Dict[str, Any]]:
    needset = set(needs or ["posts", "links", "report"])
    routes: List[Dict[str, Any]] = []
    feed_orgs = [org for org in orgs if DEFAULT_SOURCES.get(org, {}).get("feeds")]
    index_orgs = [org for org in orgs if DEFAULT_SOURCES.get(org, {}).get("indexes")]
    sitemap_orgs = [org for org in orgs if DEFAULT_SOURCES.get(org, {}).get("sitemaps")]

    if "feeds" in needset or "posts" in needset:
        routes.append(
            {
                "lane": "first-party-feeds",
                "priority": "primary",
                "orgs": feed_orgs,
                "why": "RSS/Atom is the lowest-friction first-party route when available.",
                "suggested_calls": ["fetch-feeds --org <org> --output raw/feeds.json"],
                "credentials": "none",
            }
        )

    if "sitemap" in needset or any(org in {"anthropic", "meta-ai"} for org in orgs):
        routes.append(
            {
                "lane": "first-party-sitemaps",
                "priority": "primary",
                "orgs": sitemap_orgs,
                "why": "Sitemaps help discover official URLs when RSS is absent or stale.",
                "suggested_calls": ["fetch-sitemap --url <sitemap.xml> --include /research/ --include /news/"],
                "credentials": "none",
            }
        )

    if "index" in needset or "posts" in needset:
        routes.append(
            {
                "lane": "public-html-index",
                "priority": "primary-or-fallback",
                "orgs": index_orgs,
                "why": "HTML indexes cover sources without feeds such as Anthropic and Meta AI.",
                "suggested_calls": ["fetch-index --org anthropic --org meta-ai --max-pages 2"],
                "credentials": "none",
            }
        )

    if "links" in needset:
        routes.append(
            {
                "lane": "article-link-extraction",
                "priority": "primary",
                "orgs": orgs,
                "why": "Article pages reveal linked papers, repos, model cards, docs, and benchmarks.",
                "suggested_calls": ["fetch-article --url <post-url> --output raw/articles.json"],
                "credentials": "none",
            }
        )

    if "anysearch" in needset:
        routes.append(
            {
                "lane": "anysearch-discovery",
                "priority": "secondary",
                "orgs": orgs,
                "why": "AnySearch is useful for live source discovery and freshness checks, not canonical evidence.",
                "suggested_calls": ["anysearch_cli.py batch_search --query \"<org> research blog RSS sitemap\""],
                "credentials": "optional ANYSEARCH_API_KEY",
            }
        )

    if "apify" in needset:
        routes.append(
            {
                "lane": "managed-crawler",
                "priority": "secondary-fallback",
                "orgs": orgs,
                "why": "Managed crawlers can help when site structure changes, but may cost money.",
                "suggested_calls": ["assist_ai_lab_blog_auth.ps1 -Provider apify before use"],
                "credentials": "optional APIFY_TOKEN",
            }
        )

    if "report" in needset:
        routes.append(
            {
                "lane": "normalize-and-summarize",
                "priority": "required",
                "orgs": orgs,
                "why": "Merge captured rows into auditable JSONL before synthesis.",
                "suggested_calls": ["normalize --input raw.json --source feed|sitemap|index|article --output-dir normalized"],
                "credentials": "none",
            }
        )

    if scale in {"large", "bulk"}:
        for route in routes:
            route.setdefault("cautions", []).append("Run smoke captures first, then throttle and checkpoint bulk crawls.")
    return routes


def plan(args: argparse.Namespace) -> Dict[str, Any]:
    orgs = orgs_from_args(args.org)
    needs = split_csv(args.needs) or ["posts", "links", "report"]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "target": args.target,
        "orgs": orgs,
        "needs": needs,
        "scale": args.scale,
        "routes": route_for_needs(needs, orgs, args.scale),
        "credential_policy": {
            "default": "No private credentials required for first-party RSS, sitemap, and public HTML baseline.",
            "private_env": "%USERPROFILE%\\.codex\\skills\\ai-lab-blog-intel\\.env",
            "setup_helper": "scripts\\assist_ai_lab_blog_auth.ps1",
            "external_api_onboarding": "Use $external-api-onboarding for AnySearch, Apify, GitHub, or Hugging Face credentials.",
        },
        "output_contract": SCHEMA_SUMMARY,
    }


def source_row(
    org: str,
    source_type: str,
    url: str,
    priority: str,
    status: str,
    auth_required: bool = False,
    note: str = "",
) -> Dict[str, Any]:
    return {
        "row_id": stable_id("source", org, source_type, url),
        "schema_version": SCHEMA_VERSION,
        "org": org or infer_org_from_url(url),
        "source_type": source_type,
        "source_url": url,
        "priority": priority,
        "status": status,
        "auth_required": auth_required,
        "note": note,
        "fetched_at": now_iso(),
    }


def parse_feed(url: str, org: str, max_entries: int) -> Dict[str, Any]:
    raw, headers, final_url = http_get_bytes(
        url,
        accept="application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    )
    content_type = headers.get("content-type", "")
    root = parse_xml_bytes(raw)
    root_name = strip_ns(root.tag).lower()
    feed_title = ""
    entries: List[Dict[str, Any]] = []

    if root_name == "rss" or root.find("channel") is not None:
        channel = root.find("channel") or root
        feed_title = first_child_text(channel, ["title"])
        for item in channel.findall("item")[:max_entries]:
            link = first_child_text(item, ["link"])
            guid = first_child_text(item, ["guid"]) or link
            summary = text_from_html(first_child_text(item, ["description", "summary", "content"]))
            title = text_from_html(first_child_text(item, ["title"]))
            entries.append(
                {
                    "id": guid,
                    "org": org or infer_org_from_url(link or final_url),
                    "channel": infer_channel(link or final_url, "rss"),
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published_at": first_child_text(item, ["pubDate", "published", "updated", "date"]),
                    "authors": [first_child_text(item, ["author", "creator"])] if first_child_text(item, ["author", "creator"]) else [],
                    "categories": [text_from_html("".join(child.itertext())) for child in item if strip_ns(child.tag).lower() == "category"],
                    "feed_url": url,
                    "feed_title": feed_title,
                    "topic_labels": topic_labels(f"{title} {summary}", link),
                }
            )
    else:
        feed_title = first_child_text(root, ["title"])
        nodes = [node for node in root.iter() if strip_ns(node.tag).lower() == "entry"]
        for entry in nodes[:max_entries]:
            link = first_child_attr(entry, ["link"], "href") or first_child_text(entry, ["link"])
            title = text_from_html(first_child_text(entry, ["title"]))
            summary = text_from_html(first_child_text(entry, ["summary", "content"]))
            entry_id = first_child_text(entry, ["id"]) or link
            entries.append(
                {
                    "id": entry_id,
                    "org": org or infer_org_from_url(link or final_url),
                    "channel": infer_channel(link or final_url, "rss"),
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published_at": first_child_text(entry, ["published", "updated"]),
                    "authors": [first_child_text(author, ["name"]) for author in entry if strip_ns(author.tag).lower() == "author" and first_child_text(author, ["name"])],
                    "categories": [child.attrib.get("term", "") for child in entry if strip_ns(child.tag).lower() == "category" and child.attrib.get("term")],
                    "feed_url": url,
                    "feed_title": feed_title,
                    "topic_labels": topic_labels(f"{title} {summary}", link),
                }
            )

    return {
        "org": org or infer_org_from_url(final_url),
        "feed_url": url,
        "final_url": final_url,
        "content_type": content_type,
        "feed_title": feed_title,
        "entry_count": len(entries),
        "entries": entries,
        "raw_bytes": len(raw),
        "status": "ok" if entries else "empty",
    }


def fetch_feeds(args: argparse.Namespace) -> Dict[str, Any]:
    orgs = orgs_from_args(args.org)
    feed_specs: List[Tuple[str, str]] = []
    for org in orgs:
        for feed in DEFAULT_SOURCES.get(org, {}).get("feeds", []):
            feed_specs.append((org, feed))
    for feed in args.feed or []:
        feed_specs.append((infer_org_from_url(feed), feed))

    feeds: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for org, feed_url in feed_specs:
        try:
            feeds.append(parse_feed(feed_url, org, args.max_entries))
        except Exception as exc:  # noqa: BLE001 - structured CLI error output
            errors.append({"org": org, "feed_url": feed_url, "error": str(exc)})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "feed",
        "fetched_at": now_iso(),
        "feeds": feeds,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


def parse_sitemap_xml(raw: bytes, sitemap_url: str, includes: Sequence[str], excludes: Sequence[str], limit: int) -> Dict[str, Any]:
    root = parse_xml_bytes(raw)
    root_name = strip_ns(root.tag).lower()
    urls: List[Dict[str, Any]] = []
    child_sitemaps: List[str] = []

    if root_name == "sitemapindex":
        for node in root:
            if strip_ns(node.tag).lower() != "sitemap":
                continue
            loc = first_child_text(node, ["loc"])
            if loc:
                child_sitemaps.append(loc)
    else:
        for node in root:
            if strip_ns(node.tag).lower() != "url":
                continue
            loc = first_child_text(node, ["loc"])
            if not loc:
                continue
            if includes and not any(part in loc for part in includes):
                continue
            if excludes and any(part in loc for part in excludes):
                continue
            urls.append(
                {
                    "url": loc,
                    "org": infer_org_from_url(loc),
                    "channel": infer_channel(loc),
                    "lastmod": first_child_text(node, ["lastmod"]),
                    "changefreq": first_child_text(node, ["changefreq"]),
                    "priority": first_child_text(node, ["priority"]),
                    "sitemap_url": sitemap_url,
                    "topic_labels": topic_labels(loc, loc),
                }
            )
            if len(urls) >= limit:
                break

    return {"sitemap_url": sitemap_url, "urls": urls, "child_sitemaps": child_sitemaps, "url_count": len(urls)}


def fetch_sitemap(args: argparse.Namespace) -> Dict[str, Any]:
    sitemap_urls = list(args.url or [])
    for org in orgs_from_args(args.org):
        sitemap_urls.extend(DEFAULT_SOURCES.get(org, {}).get("sitemaps", []))
    seen = set()
    unique_urls = []
    for url in sitemap_urls:
        if url not in seen:
            unique_urls.append(url)
            seen.add(url)

    sitemaps: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    queue = list(unique_urls)
    while queue and len(sitemaps) < args.max_sitemaps:
        sitemap_url = queue.pop(0)
        try:
            raw, _headers, final_url = http_get_bytes(sitemap_url, accept="application/xml, text/xml, */*")
            parsed = parse_sitemap_xml(raw, final_url, args.include or [], args.exclude or [], args.limit)
            sitemaps.append(parsed)
            if args.follow_index:
                for child in parsed.get("child_sitemaps", []):
                    if child not in seen:
                        queue.append(child)
                        seen.add(child)
        except Exception as exc:  # noqa: BLE001
            errors.append({"sitemap_url": sitemap_url, "error": str(exc)})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "sitemap",
        "fetched_at": now_iso(),
        "sitemaps": sitemaps,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


LINK_RE = re.compile(r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a\s*>", re.I | re.S)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.I | re.S)
TIME_RE = re.compile(r"<time\b[^>]*(?:datetime=[\"']([^\"']+)[\"'])?[^>]*>(.*?)</time\s*>", re.I | re.S)
META_RE = re.compile(r"<meta\b([^>]+)>", re.I)


def meta_content(html_text: str, names: Sequence[str]) -> str:
    targets = {name.lower() for name in names}
    for match in META_RE.finditer(html_text):
        attrs = match.group(1)
        name_match = re.search(r"(?:name|property)=[\"']([^\"']+)[\"']", attrs, flags=re.I)
        content_match = re.search(r"content=[\"']([^\"']*)[\"']", attrs, flags=re.I | re.S)
        if name_match and content_match and name_match.group(1).lower() in targets:
            return html.unescape(content_match.group(1).strip())
    return ""


def page_title(html_text: str) -> str:
    og = meta_content(html_text, ["og:title", "twitter:title"])
    if og:
        return text_from_html(og)
    match = TITLE_RE.search(html_text)
    return text_from_html(match.group(1)) if match else ""


def page_description(html_text: str) -> str:
    return text_from_html(meta_content(html_text, ["description", "og:description", "twitter:description"]))


def extract_links(base_url: str, html_text: str, org: str, max_links: int) -> List[Dict[str, Any]]:
    links: List[Dict[str, Any]] = []
    seen = set()
    base_host = urllib.parse.urlparse(base_url).netloc.lower()
    for href, inner in LINK_RE.findall(html_text):
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        url = absolute_url(base_url, href)
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if url in seen:
            continue
        seen.add(url)
        anchor = text_from_html(inner)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        same_site = host == base_host or host.endswith("." + base_host)
        likely_post = same_site and any(marker in path for marker in ["/blog", "/news", "/research", "/post", "/articles", "/publications"])
        external_artifact = any(marker in host for marker in ["arxiv.org", "doi.org", "github.com", "huggingface.co", "openreview.net"])
        if likely_post or external_artifact:
            links.append(
                {
                    "org": org or infer_org_from_url(url),
                    "url": url,
                    "title": anchor,
                    "channel": infer_channel(url),
                    "link_type": classify_link(url),
                    "source_url": base_url,
                    "topic_labels": topic_labels(f"{anchor} {url}", url),
                }
            )
        if len(links) >= max_links:
            break
    return links


def extract_dates(html_text: str) -> List[str]:
    dates = []
    for datetime_attr, body in TIME_RE.findall(html_text):
        value = datetime_attr or text_from_html(body)
        if value:
            dates.append(value)
    return dates[:10]


def fetch_index(args: argparse.Namespace) -> Dict[str, Any]:
    index_specs: List[Tuple[str, str]] = []
    for org in orgs_from_args(args.org):
        for url in DEFAULT_SOURCES.get(org, {}).get("indexes", []):
            index_specs.append((org, url))
            if args.max_pages > 1 and org == "meta-ai":
                for page in range(1, args.max_pages):
                    index_specs.append((org, f"https://ai.meta.com/blog/?page={page}"))
    for url in args.url or []:
        index_specs.append((infer_org_from_url(url), url))

    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for org, index_url in index_specs:
        try:
            raw, headers, final_url = http_get_bytes(index_url, accept="text/html, */*")
            html_text = raw.decode("utf-8", errors="replace")
            title = page_title(html_text)
            links = extract_links(final_url, html_text, org, args.max_links)
            dates = extract_dates(html_text)
            pages.append(
                {
                    "org": org or infer_org_from_url(final_url),
                    "index_url": index_url,
                    "final_url": final_url,
                    "content_type": headers.get("content-type", ""),
                    "title": title,
                    "description": page_description(html_text),
                    "dates": dates,
                    "links": links,
                    "link_count": len(links),
                    "raw_bytes": len(raw),
                    "status": "ok" if links else "empty",
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"org": org, "index_url": index_url, "error": str(exc)})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "index",
        "fetched_at": now_iso(),
        "pages": pages,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


def classify_link(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "arxiv.org" in host:
        return "arxiv"
    if "doi.org" in host or re.search(r"10\.\d{4,9}/", url):
        return "doi"
    if "github.com" in host:
        return "github"
    if "huggingface.co" in host and "/datasets/" in path:
        return "dataset"
    if "huggingface.co" in host:
        return "model"
    if any(marker in host for marker in ["openreview.net", "aclanthology.org", "proceedings", "pmlr"]):
        return "paper"
    if any(marker in path for marker in ["benchmark", "leaderboard", "eval"]):
        return "benchmark"
    if any(marker in path for marker in ["docs", "documentation", "api"]):
        return "docs"
    if any(marker in path for marker in ["product", "pricing", "platform"]):
        return "product"
    return "other"


def fetch_article(args: argparse.Namespace) -> Dict[str, Any]:
    articles: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for url in args.url:
        try:
            raw, headers, final_url = http_get_bytes(url, accept="text/html, */*")
            html_text = raw.decode("utf-8", errors="replace")
            title = page_title(html_text)
            description = page_description(html_text)
            plain = text_from_html(html_text)
            org = infer_org_from_url(final_url)
            links = extract_links(final_url, html_text, org, args.max_links)
            articles.append(
                {
                    "org": org,
                    "url": url,
                    "final_url": final_url,
                    "content_type": headers.get("content-type", ""),
                    "title": title,
                    "description": description,
                    "published_at": extract_dates(html_text)[0] if extract_dates(html_text) else "",
                    "content": plain[: args.max_chars],
                    "content_hash": stable_id(plain),
                    "links": links,
                    "topic_labels": topic_labels(f"{title} {description} {plain[:2000]}", final_url),
                    "raw_bytes": len(raw),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"url": url, "error": str(exc)})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "article",
        "fetched_at": now_iso(),
        "articles": articles,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


def normalize_feed(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    posts: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for feed in payload.get("feeds", []):
        org = feed.get("org") or infer_org_from_url(feed.get("feed_url", ""))
        status = feed.get("status") or "ok"
        sources.append(source_row(org, "rss-feed", feed.get("feed_url", ""), "primary", status, False, feed.get("feed_title", "")))
        for entry in feed.get("entries", []):
            url = entry.get("url") or entry.get("id") or feed.get("feed_url", "")
            title = text_from_html(entry.get("title") or "")
            row_id = stable_id("post", org, url, entry.get("id"), title)
            posts.append(
                {
                    "row_id": row_id,
                    "schema_version": SCHEMA_VERSION,
                    "org": entry.get("org") or org,
                    "channel": entry.get("channel") or infer_channel(url, "rss"),
                    "source": "feed",
                    "source_kind": "feed-entry",
                    "source_id": entry.get("id") or url,
                    "source_url": url,
                    "title": title,
                    "author": ", ".join(entry.get("authors") or []),
                    "published_at": entry.get("published_at") or "",
                    "summary": text_from_html(entry.get("summary") or "")[:1500],
                    "categories": entry.get("categories") or [],
                    "topic_labels": entry.get("topic_labels") or topic_labels(f"{title} {entry.get('summary', '')}", url),
                    "source_priority": "primary",
                    "feed_url": feed.get("feed_url", ""),
                    "feed_title": feed.get("feed_title", ""),
                    "fetched_at": fetched_at,
                    "raw_ref": entry.get("id") or url,
                }
            )
    for error in payload.get("errors", []):
        sources.append(source_row(error.get("org") or infer_org_from_url(error.get("feed_url", "")), "rss-feed", error.get("feed_url", ""), "primary", "blocked", False, error.get("error", "")))
    return posts, links, sources


def normalize_sitemap(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    posts: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for sitemap in payload.get("sitemaps", []):
        sitemap_url = sitemap.get("sitemap_url", "")
        sources.append(source_row(infer_org_from_url(sitemap_url), "sitemap", sitemap_url, "primary", "ok", False, f"{sitemap.get('url_count', 0)} urls"))
        for item in sitemap.get("urls", []):
            url = item.get("url", "")
            org = item.get("org") or infer_org_from_url(url)
            title = urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).stem.replace("-", " ")).strip()
            posts.append(
                {
                    "row_id": stable_id("sitemap-post", org, url),
                    "schema_version": SCHEMA_VERSION,
                    "org": org,
                    "channel": item.get("channel") or infer_channel(url),
                    "source": "sitemap",
                    "source_kind": "sitemap-url",
                    "source_id": url,
                    "source_url": url,
                    "title": title,
                    "published_at": item.get("lastmod") or "",
                    "summary": "",
                    "categories": [],
                    "topic_labels": item.get("topic_labels") or topic_labels(url, url),
                    "source_priority": "primary",
                    "sitemap_url": sitemap_url,
                    "fetched_at": fetched_at,
                    "raw_ref": url,
                }
            )
    for error in payload.get("errors", []):
        sources.append(source_row(infer_org_from_url(error.get("sitemap_url", "")), "sitemap", error.get("sitemap_url", ""), "primary", "blocked", False, error.get("error", "")))
    return posts, links, sources


def normalize_index(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    posts: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for page in payload.get("pages", []):
        org = page.get("org") or infer_org_from_url(page.get("final_url") or page.get("index_url", ""))
        status = page.get("status") or "ok"
        sources.append(source_row(org, "html-index", page.get("final_url") or page.get("index_url", ""), "primary", status, False, page.get("title", "")))
        for item in page.get("links", []):
            url = item.get("url", "")
            title = text_from_html(item.get("title") or "")
            post_row_id = stable_id("index-post", org, url, title)
            posts.append(
                {
                    "row_id": post_row_id,
                    "schema_version": SCHEMA_VERSION,
                    "org": item.get("org") or org,
                    "channel": item.get("channel") or infer_channel(url),
                    "source": "index",
                    "source_kind": "index-link",
                    "source_id": url,
                    "source_url": url,
                    "title": title or urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).stem.replace("-", " ")).strip(),
                    "published_at": "",
                    "summary": "",
                    "categories": [],
                    "topic_labels": item.get("topic_labels") or topic_labels(f"{title} {url}", url),
                    "source_priority": "primary",
                    "index_url": page.get("final_url") or page.get("index_url", ""),
                    "fetched_at": fetched_at,
                    "raw_ref": url,
                }
            )
            if item.get("link_type") and item.get("link_type") != "other":
                links.append(link_row(post_row_id, item.get("org") or org, item, fetched_at))
    for error in payload.get("errors", []):
        sources.append(source_row(error.get("org") or infer_org_from_url(error.get("index_url", "")), "html-index", error.get("index_url", ""), "primary", "blocked", False, error.get("error", "")))
    return posts, links, sources


def link_row(post_row_id: str, org: str, item: Dict[str, Any], fetched_at: str) -> Dict[str, Any]:
    url = item.get("url") or item.get("link_url") or ""
    return {
        "row_id": stable_id("link", post_row_id, url),
        "schema_version": SCHEMA_VERSION,
        "post_row_id": post_row_id,
        "org": org or infer_org_from_url(url),
        "link_url": url,
        "link_type": item.get("link_type") or classify_link(url),
        "anchor_text": text_from_html(item.get("title") or item.get("anchor_text") or ""),
        "source_url": item.get("source_url") or "",
        "source_priority": "primary",
        "fetched_at": fetched_at,
    }


def normalize_article(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    posts: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for article in payload.get("articles", []):
        url = article.get("final_url") or article.get("url", "")
        org = article.get("org") or infer_org_from_url(url)
        title = text_from_html(article.get("title") or "")
        post_row_id = stable_id("article", org, url, title)
        sources.append(source_row(org, "article", url, "primary", "ok", False, title))
        posts.append(
            {
                "row_id": post_row_id,
                "schema_version": SCHEMA_VERSION,
                "org": org,
                "channel": infer_channel(url),
                "source": "article",
                "source_kind": "article-page",
                "source_id": url,
                "source_url": url,
                "title": title,
                "published_at": article.get("published_at") or "",
                "summary": text_from_html(article.get("description") or article.get("content") or "")[:1500],
                "categories": [],
                "topic_labels": article.get("topic_labels") or topic_labels(f"{title} {article.get('content', '')}", url),
                "source_priority": "primary",
                "content_hash": article.get("content_hash") or "",
                "fetched_at": fetched_at,
                "raw_ref": url,
            }
        )
        for link in article.get("links", []):
            link = dict(link)
            link["source_url"] = url
            links.append(link_row(post_row_id, org, link, fetched_at))
    for error in payload.get("errors", []):
        sources.append(source_row(infer_org_from_url(error.get("url", "")), "article", error.get("url", ""), "primary", "blocked", False, error.get("error", "")))
    return posts, links, sources


def normalize_generic(payload: Any, source: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    records = payload if isinstance(payload, list) else payload.get("records", []) if isinstance(payload, dict) else []
    posts: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") if isinstance(payload, dict) else now_iso()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        url = record.get("url") or record.get("source_url") or record.get("link") or ""
        org = record.get("org") or infer_org_from_url(url)
        title = text_from_html(record.get("title") or record.get("name") or "")
        posts.append(
            {
                "row_id": stable_id(source, index, org, url, title),
                "schema_version": SCHEMA_VERSION,
                "org": org,
                "channel": record.get("channel") or infer_channel(url),
                "source": source,
                "source_kind": record.get("type") or "item",
                "source_id": record.get("id") or url or str(index),
                "source_url": url,
                "title": title,
                "published_at": record.get("published_at") or record.get("date") or "",
                "summary": text_from_html(record.get("summary") or record.get("description") or "")[:1500],
                "categories": record.get("categories") or record.get("tags") or [],
                "topic_labels": record.get("topic_labels") or topic_labels(f"{title} {record.get('summary', '')}", url),
                "source_priority": "secondary" if source in {"anysearch", "apify"} else "fallback",
                "fetched_at": fetched_at,
                "raw_ref": record.get("id") or str(index),
            }
        )
    return posts, links, sources


def normalize(args: argparse.Namespace) -> Dict[str, Any]:
    input_path = Path(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    source = args.source.lower()
    if source == "feed":
        posts, links, sources = normalize_feed(payload)
    elif source == "sitemap":
        posts, links, sources = normalize_sitemap(payload)
    elif source == "index":
        posts, links, sources = normalize_index(payload)
    elif source == "article":
        posts, links, sources = normalize_article(payload)
    else:
        posts, links, sources = normalize_generic(payload, source)

    output_dir = Path(args.output_dir)
    counts = {
        "posts": write_jsonl(output_dir / "posts.jsonl", posts),
        "links": write_jsonl(output_dir / "links.jsonl", links),
        "sources": write_jsonl(output_dir / "sources.jsonl", sources),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "command": "normalize",
        "input": str(input_path),
        "source": source,
        "output_dir": str(output_dir),
        "counts": counts,
    }
    write_json(output_dir / "manifest.normalize.json", manifest)
    return manifest


def scaffold(args: argparse.Namespace) -> Dict[str, Any]:
    out = Path(args.output_dir)
    for rel in ["raw", "normalized", "reports"]:
        (out / rel).mkdir(parents=True, exist_ok=True)
    plan_doc = plan(args)
    write_json(out / "manifest.json", plan_doc)
    rows = []
    for route in plan_doc.get("routes", []):
        rows.append(
            {
                "org": ",".join(route.get("orgs") or []),
                "source_type": "planned-route",
                "source_url": "",
                "priority": route.get("priority", ""),
                "status": "planned",
                "auth_required": route.get("credentials", "") not in {"", "none"},
                "note": route.get("why", ""),
            }
        )
    with (out / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["org", "source_type", "source_url", "priority", "status", "auth_required", "note"])
        writer.writeheader()
        writer.writerows(rows)
    (out / "reports" / "summary.md").write_text(
        f"# AI Lab Blog Summary\n\nTarget: {args.target}\n\nFill this from normalized row IDs.\n",
        encoding="utf-8",
    )
    return {
        "output_dir": str(out),
        "created": ["raw/", "normalized/", "reports/", "manifest.json", "sources.csv", "reports/summary.md"],
    }


def print_result(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI lab/company blog intelligence helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="Print a source route plan")
    p.add_argument("--target", required=True)
    p.add_argument("--org", action="append", help="Organization keys, repeatable or comma-like by shell")
    p.add_argument("--needs", action="append", help="Comma-separated needs: posts,feeds,sitemap,index,links,anysearch,apify,report")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("inspect-url", help="Classify a URL and recommend routes")
    p.add_argument("url")

    sub.add_parser("schema", help="Print normalized output schema summary")

    p = sub.add_parser("scaffold", help="Create a run directory")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--org", action="append")
    p.add_argument("--needs", action="append")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("fetch-feeds", help="Fetch RSS/Atom feeds from default org registry or explicit feed URLs")
    p.add_argument("--org", action="append")
    p.add_argument("--feed", action="append")
    p.add_argument("--max-entries", type=int, default=20)
    p.add_argument("--output")

    p = sub.add_parser("fetch-sitemap", help="Fetch and filter XML sitemaps")
    p.add_argument("--org", action="append")
    p.add_argument("--url", action="append")
    p.add_argument("--include", action="append")
    p.add_argument("--exclude", action="append")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--max-sitemaps", type=int, default=10)
    p.add_argument("--follow-index", action="store_true")
    p.add_argument("--output")

    p = sub.add_parser("fetch-index", help="Fetch public HTML blog indexes and extract likely post links")
    p.add_argument("--org", action="append")
    p.add_argument("--url", action="append")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--max-links", type=int, default=80)
    p.add_argument("--output")

    p = sub.add_parser("fetch-article", help="Fetch public article pages and extract text plus links")
    p.add_argument("--url", action="append", required=True)
    p.add_argument("--max-links", type=int, default=120)
    p.add_argument("--max-chars", type=int, default=20000)
    p.add_argument("--output")

    p = sub.add_parser("normalize", help="Normalize raw capture JSON into JSONL files")
    p.add_argument("--input", required=True)
    p.add_argument("--source", required=True, choices=["feed", "sitemap", "index", "article", "anysearch", "apify", "generic"])
    p.add_argument("--output-dir", required=True)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            print_result(plan(args))
        elif args.command == "inspect-url":
            print_result(inspect_url(args.url))
        elif args.command == "schema":
            print_result({"schema_version": SCHEMA_VERSION, "outputs": SCHEMA_SUMMARY, "default_orgs": sorted(DEFAULT_SOURCES)})
        elif args.command == "scaffold":
            print_result(scaffold(args))
        elif args.command == "fetch-feeds":
            print_result(fetch_feeds(args))
        elif args.command == "fetch-sitemap":
            print_result(fetch_sitemap(args))
        elif args.command == "fetch-index":
            print_result(fetch_index(args))
        elif args.command == "fetch-article":
            print_result(fetch_article(args))
        elif args.command == "normalize":
            print_result(normalize(args))
        else:
            raise SystemExit(f"unknown command {args.command}")
        return 0
    except FetchError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
