#!/usr/bin/env python3
"""Helpers for Chinese AI secondary-media signal routing and normalization."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "0.1"
USER_AGENT = "Codex chinese-ai-signal-crawler/0.1"

SCHEMA_SUMMARY = {
    "raw/": "Untouched AnySearch Markdown/JSON, RSS JSON, public page captures, exported WeChat/Bilibili/MediaCrawler files, and logs.",
    "normalized/items.jsonl": "Media articles, feed entries, search hits, videos, posts, and crawler records.",
    "normalized/comments.jsonl": "Bounded comments and replies when reception analysis is requested.",
    "normalized/sources.jsonl": "Source metadata, routes, access status, auth requirement, and risk notes.",
    "sources.csv": "Human source review table with URL, source type, priority, status, auth requirement, and risk.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}

NEED_ALIASES = {
    "media": "media",
    "media-page": "media",
    "page": "media",
    "rss": "rss",
    "rsshub": "rss",
    "feed": "rss",
    "anysearch": "anysearch",
    "search": "anysearch",
    "wechat": "wechat",
    "weixin": "wechat",
    "wx": "wechat",
    "bilibili": "bilibili",
    "bili": "bilibili",
    "b站": "bilibili",
    "mediacrawler": "mediacrawler",
    "self-media": "mediacrawler",
    "social": "mediacrawler",
    "primary": "primary-check",
    "verify": "primary-check",
    "primary-check": "primary-check",
    "report": "report",
    "summary": "report",
}

CHANNEL_HINTS = {
    "jiqizhixin.com": ("机器之心", "web"),
    "qbitai.com": ("量子位", "web"),
    "paperweekly.site": ("PaperWeekly", "web"),
    "paperweekly.club": ("PaperWeekly", "web"),
    "paperweekly.cn": ("PaperWeekly", "web"),
    "aitechtalk.com": ("AI科技评论", "web"),
    "leiphone.com": ("AI科技评论/雷峰网", "web"),
    "xinzhiyuan.com": ("新智元", "web"),
    "mp.weixin.qq.com": ("微信公众号", "wechat"),
    "bilibili.com": ("Bilibili", "bilibili"),
    "b23.tv": ("Bilibili", "bilibili"),
    "weibo.com": ("微博", "weibo"),
    "zhihu.com": ("知乎", "zhihu"),
    "xiaohongshu.com": ("小红书", "xiaohongshu"),
    "xhslink.com": ("小红书", "xiaohongshu"),
}


class FetchError(RuntimeError):
    """Raised for fetch or command failures with context."""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def split_csv(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            normalized = part.strip().lower().replace("_", "-")
            if normalized:
                out.append(NEED_ALIASES.get(normalized, normalized))
    return out


def text_from_html(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    return text.strip()


def canonical_host(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def channel_for_url(url: str) -> Tuple[str, str]:
    host = canonical_host(url)
    for domain, value in CHANNEL_HINTS.items():
        if host == domain or host.endswith("." + domain):
            return value
    return host or "unknown", "web"


def http_get_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html, application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise FetchError(f"fetch failed for {url}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def source_row(
    source: str,
    url: str,
    source_type: str,
    priority: str,
    status: str,
    auth_required: bool = False,
    risk_note: str = "",
    note: str = "",
) -> Dict[str, Any]:
    return {
        "row_id": stable_id("source", source, url, source_type),
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "source_type": source_type,
        "source_url": url,
        "priority": priority,
        "status": status,
        "auth_required": auth_required,
        "risk_note": risk_note,
        "note": note,
        "fetched_at": now_iso(),
    }


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = canonical_host(url)
    channel, platform = channel_for_url(url)
    path = parsed.path or "/"
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": path,
        "channel": channel,
        "platform": platform,
        "source": "unknown",
        "source_kind": "unknown",
        "recommended_needs": [],
        "recommended_routes": [],
        "auth_required": False,
    }

    if host == "mp.weixin.qq.com":
        result.update(
            {
                "source": "wechat",
                "source_kind": "wechat-article-or-album",
                "recommended_needs": ["wechat", "report"],
                "recommended_routes": ["wespy-plus", "wechat-mcp-or-research-crawler-if-approved"],
                "auth_required": False,
            }
        )
        return result

    if host.endswith("bilibili.com") or host == "b23.tv":
        kind = "bilibili-video" if "/video/" in path or host == "b23.tv" else "bilibili-creator-or-page"
        result.update(
            {
                "source": "bilibili",
                "source_kind": kind,
                "recommended_needs": ["bilibili", "report"],
                "recommended_routes": ["bilibili-crawler-small-run", "comment-scraper-only-if-requested"],
                "auth_required": "comment" in parsed.query.lower(),
            }
        )
        return result

    if platform in {"weibo", "zhihu", "xiaohongshu"}:
        result.update(
            {
                "source": "mediacrawler",
                "source_kind": f"{platform}-page-or-post",
                "recommended_needs": ["mediacrawler", "report"],
                "recommended_routes": ["MediaCrawler small public capture after visible setup"],
                "auth_required": True,
            }
        )
        return result

    if host in CHANNEL_HINTS:
        result.update(
            {
                "source": "media-page",
                "source_kind": "media-site",
                "recommended_needs": ["media", "rss", "anysearch", "report"],
                "recommended_routes": ["fetch-page", "fetch-rss-if-known", "AnySearch site query"],
                "auth_required": False,
            }
        )
        return result

    if "rsshub" in host:
        result.update(
            {
                "source": "rss",
                "source_kind": "rsshub-route",
                "recommended_needs": ["rss", "report"],
                "recommended_routes": ["fetch-rss"],
                "auth_required": False,
            }
        )
        return result

    return result


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_url(target)
    return {
        "url": "",
        "host": "",
        "path": "",
        "channel": "",
        "platform": "",
        "source": "topic",
        "source_kind": "query",
        "recommended_needs": ["media", "anysearch", "rss", "report"],
        "recommended_routes": ["AnySearch discovery", "public media pages", "RSS/RSSHub when known"],
        "auth_required": False,
    }


def route_for_needs(needs: List[str], target_info: Dict[str, Any], scale: str) -> List[Dict[str, Any]]:
    needset = set(needs)
    routes: List[Dict[str, Any]] = []

    if "media" in needset or target_info.get("source") == "media-page":
        routes.append(
            {
                "lane": "public-media-pages",
                "priority": "secondary",
                "why": "Chinese AI media pages are useful for propagation signals and article discovery.",
                "suggested_calls": ["fetch-page --url <media-home-or-article> --max-links 30"],
                "credentials": "none",
                "risk_note": "Secondary source; verify technical claims against primary sources.",
            }
        )

    if "rss" in needset:
        routes.append(
            {
                "lane": "rss-rsshub",
                "priority": "secondary",
                "why": "RSS/RSSHub is the most maintainable route for recurring monitoring.",
                "suggested_calls": ["fetch-rss --feed <feed-or-rsshub-url> --max-entries 20"],
                "credentials": "none",
                "risk_note": "Feed routes can go stale; record failures.",
            }
        )

    if "anysearch" in needset:
        routes.append(
            {
                "lane": "anysearch-discovery",
                "priority": "fallback",
                "why": "AnySearch improves recall across Chinese media and public pages.",
                "suggested_calls": ["fetch-anysearch --query \"<topic> 机器之心 量子位 新智元 PaperWeekly\""],
                "credentials": "optional ANYSEARCH_API_KEY",
                "risk_note": "Search snippets are discovery-only.",
            }
        )

    if "wechat" in needset or target_info.get("source") == "wechat":
        routes.append(
            {
                "lane": "wechat-article-export",
                "priority": "propagation",
                "why": "WeChat articles show Chinese-circle diffusion and commentary.",
                "suggested_calls": ["wespy-plus <mp.weixin.qq.com URL> --output-json"],
                "credentials": "tool-local visible login/cookies only when needed",
                "risk_note": "Copyright and platform controls; summarize sparingly.",
            }
        )

    if "bilibili" in needset or target_info.get("source") == "bilibili":
        routes.append(
            {
                "lane": "bilibili-small-capture",
                "priority": "propagation",
                "why": "Bilibili creator/video metadata and bounded comments show public reception.",
                "suggested_calls": ["bilibili-crawler by UID", "comment scraper only with strict limits"],
                "credentials": "tool-local visible login/cookies for comments when needed",
                "risk_note": "Engagement is not correctness evidence.",
            }
        )

    if "mediacrawler" in needset or target_info.get("source") == "mediacrawler":
        routes.append(
            {
                "lane": "mediacrawler-platform-capture",
                "priority": "propagation",
                "why": "MediaCrawler can collect multi-platform public self-media signals.",
                "suggested_calls": ["MediaCrawler small run after setup"],
                "credentials": "platform login state may be required",
                "risk_note": "Use small scoped runs and obey platform controls.",
            }
        )

    if "primary-check" in needset:
        routes.append(
            {
                "lane": "primary-source-check",
                "priority": "required-for-final-claims",
                "why": "Chinese secondary sources must be checked against paper/release/repo/venue sources.",
                "suggested_calls": ["Use paper/repo/official-release URL search and cite primary source rows."],
                "credentials": "none by default",
                "risk_note": "Do not promote secondary claims to confirmed facts before this check.",
            }
        )

    if "report" in needset:
        routes.append(
            {
                "lane": "normalize-and-summarize",
                "priority": "required",
                "why": "Auditable JSONL rows make secondary-signal claims traceable.",
                "suggested_calls": ["normalize --input raw.json --source media-page|rss|anysearch|wechat|bilibili|mediacrawler"],
                "credentials": "none",
                "risk_note": "",
            }
        )

    if not routes:
        routes.append(
            {
                "lane": "media-anysearch-baseline",
                "priority": "default",
                "why": "No specific need was selected; start with public media and AnySearch discovery.",
                "suggested_calls": ["fetch-page --url <media-page>", "fetch-anysearch --query <target>"],
                "credentials": "none or optional ANYSEARCH_API_KEY",
                "risk_note": "Discovery-only until primary-check.",
            }
        )

    if scale in {"large", "bulk"}:
        for route in routes:
            route.setdefault("cautions", []).append("Run a small smoke capture first, then throttle and checkpoint bulk capture.")
    return routes


def plan(target: str, needs: List[str], scale: str) -> Dict[str, Any]:
    target_info = classify_target(target)
    if not needs:
        needs = list(target_info.get("recommended_needs") or ["media", "anysearch", "rss", "report"])
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "target": target,
        "target_info": target_info,
        "needs": needs,
        "scale": scale,
        "routes": route_for_needs(needs, target_info, scale),
        "credential_policy": {
            "default": "No private credentials required for public media, RSS, and AnySearch anonymous discovery.",
            "private_env": "%USERPROFILE%\\.codex\\skills\\chinese-ai-signal-crawler\\.env",
            "anysearch_env": "%USERPROFILE%\\.codex\\skills\\anysearch\\.env",
            "setup_helper": "scripts\\assist_chinese_ai_signal_auth.ps1",
        },
        "output_contract": SCHEMA_SUMMARY,
    }


def extract_title(page_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", page_text, flags=re.I | re.S)
    return text_from_html(match.group(1)) if match else ""


def extract_links(page_text: str, base_url: str, max_links: int) -> List[Dict[str, Any]]:
    links: List[Dict[str, Any]] = []
    seen = set()
    for match in re.finditer(r"<a\b[^>]*?href\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</a>", page_text, flags=re.I | re.S):
        href = html.unescape(match.group(2)).strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:")):
            continue
        url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))
        if normalized in seen:
            continue
        seen.add(normalized)
        title = text_from_html(match.group(3))[:300]
        channel, platform = channel_for_url(normalized)
        links.append(
            {
                "url": normalized,
                "title": title,
                "channel": channel,
                "platform": platform,
            }
        )
        if len(links) >= max_links:
            break
    return links


def fetch_page(args: argparse.Namespace) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for url in args.url:
        try:
            text = http_get_text(url)
            channel, platform = channel_for_url(url)
            pages.append(
                {
                    "url": url,
                    "channel": channel,
                    "platform": platform,
                    "title": extract_title(text),
                    "links": extract_links(text, url, args.max_links),
                    "raw_chars": len(text),
                }
            )
        except Exception as exc:  # noqa: BLE001 - structured CLI blocker
            errors.append({"url": url, "error": str(exc)})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "media-page",
        "fetched_at": now_iso(),
        "pages": pages,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


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


def parse_feed(url: str, limit: int) -> Dict[str, Any]:
    raw_text = http_get_text(url)
    root = ET.fromstring(raw_text.encode("utf-8"))
    root_name = strip_ns(root.tag).lower()
    feed_title = ""
    entries: List[Dict[str, Any]] = []

    if root_name == "rss" or root.find("channel") is not None:
        channel = root.find("channel") or root
        feed_title = first_child_text(channel, ["title"])
        nodes = channel.findall("item")
        for item in nodes[:limit]:
            link = first_child_text(item, ["link"])
            guid = first_child_text(item, ["guid"]) or link
            channel_name, platform = channel_for_url(link or url)
            entries.append(
                {
                    "id": guid,
                    "title": first_child_text(item, ["title"]),
                    "url": link,
                    "summary": text_from_html(first_child_text(item, ["description", "summary"])),
                    "published_at": first_child_text(item, ["pubDate", "published", "updated"]),
                    "authors": [first_child_text(item, ["author", "creator"])] if first_child_text(item, ["author", "creator"]) else [],
                    "channel": channel_name,
                    "platform": platform,
                    "feed_url": url,
                    "feed_title": feed_title,
                }
            )
    else:
        feed_title = first_child_text(root, ["title"])
        nodes = [node for node in root.iter() if strip_ns(node.tag).lower() == "entry"]
        for entry in nodes[:limit]:
            link = first_child_attr(entry, ["link"], "href") or first_child_text(entry, ["link"])
            entry_id = first_child_text(entry, ["id"]) or link
            channel_name, platform = channel_for_url(link or url)
            entries.append(
                {
                    "id": entry_id,
                    "title": first_child_text(entry, ["title"]),
                    "url": link,
                    "summary": text_from_html(first_child_text(entry, ["summary", "content"])),
                    "published_at": first_child_text(entry, ["published", "updated"]),
                    "authors": [first_child_text(author, ["name"]) for author in entry if strip_ns(author.tag).lower() == "author" and first_child_text(author, ["name"])],
                    "channel": channel_name,
                    "platform": platform,
                    "feed_url": url,
                    "feed_title": feed_title,
                }
            )

    return {"feed_url": url, "feed_title": feed_title, "entry_count": len(entries), "entries": entries, "raw_chars": len(raw_text)}


def fetch_rss(args: argparse.Namespace) -> Dict[str, Any]:
    feeds = []
    errors = []
    for feed_url in args.feed:
        try:
            feeds.append(parse_feed(feed_url, args.max_entries))
        except Exception as exc:  # noqa: BLE001
            errors.append({"feed_url": feed_url, "error": str(exc)})
    payload = {"schema_version": SCHEMA_VERSION, "source": "rss", "fetched_at": now_iso(), "feeds": feeds, "errors": errors}
    if args.output:
        write_json(Path(args.output), payload)
    return payload


def default_anysearch_cli() -> Optional[Path]:
    candidates = [
        Path.home() / ".codex" / "skills" / "anysearch" / "scripts" / "anysearch_cli.py",
        Path(__file__).resolve().parents[2] / "anysearch" / "scripts" / "anysearch_cli.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def parse_anysearch_markdown(markdown: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for line in markdown.splitlines():
        title_match = re.match(r"^###\s+\d+\.\s+(.*)", line)
        url_match = re.match(r"^-\s+\*\*URL\*\*:\s+(.*)", line)
        if title_match:
            if current:
                records.append(current)
            current = {"title": title_match.group(1).strip(), "url": "", "summary": ""}
        elif url_match and current is not None:
            current["url"] = url_match.group(1).strip()
        elif current and line.strip() and not line.startswith(("##", "---")):
            current["summary"] = (current.get("summary", "") + " " + line.strip()).strip()
    if current:
        records.append(current)
    return records


def fetch_anysearch(args: argparse.Namespace) -> Dict[str, Any]:
    cli = Path(args.anysearch_cli) if args.anysearch_cli else default_anysearch_cli()
    if not cli or not cli.exists():
        raise FetchError("AnySearch CLI not found. Install or sync the anysearch skill first.")
    cmd = [
        sys.executable,
        str(cli),
        "search",
        args.query,
        "--max_results",
        str(args.max_results),
    ]
    if args.freshness:
        cmd.extend(["--freshness", args.freshness])
    try:
        proc = subprocess.run(cmd, check=False, text=True, capture_output=True, encoding="utf-8", errors="replace")
    except OSError as exc:
        raise FetchError(f"failed to run AnySearch CLI: {exc}") from exc
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "anysearch",
        "fetched_at": now_iso(),
        "query": args.query,
        "command": " ".join(cmd[:3] + ["<query>", "--max_results", str(args.max_results)]),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "records": parse_anysearch_markdown(proc.stdout),
    }
    if proc.returncode != 0:
        payload["error"] = proc.stderr or proc.stdout
    if args.output:
        path = Path(args.output)
        if path.suffix.lower() in {".md", ".markdown"}:
            write_text(path, proc.stdout)
            write_json(path.with_suffix(path.suffix + ".meta.json"), payload)
        else:
            write_json(path, payload)
    return payload


def item_row(
    source: str,
    source_kind: str,
    source_id: str,
    url: str,
    title: str,
    channel: str,
    platform: str,
    published_at: str = "",
    summary: str = "",
    source_priority: str = "secondary",
    risk_note: str = "",
    raw_ref: str = "",
    engagement_metrics: Optional[Dict[str, Any]] = None,
    needs_primary_source_check: bool = True,
) -> Dict[str, Any]:
    return {
        "row_id": stable_id(source, source_id, url, title),
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "source_kind": source_kind,
        "source_id": source_id or url,
        "source_url": url,
        "title": text_from_html(title)[:500],
        "channel": channel,
        "platform": platform,
        "published_at": published_at or "",
        "summary": text_from_html(summary)[:1200],
        "mentioned_papers": [],
        "mentioned_models": [],
        "mentioned_companies": [],
        "engagement_metrics": engagement_metrics or {},
        "source_priority": source_priority,
        "needs_primary_source_check": needs_primary_source_check,
        "risk_note": risk_note,
        "fetched_at": now_iso(),
        "raw_ref": raw_ref or source_id or url,
    }


def normalize_media_page(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    for page in payload.get("pages", []):
        url = page.get("url", "")
        sources.append(source_row("media-page", url, "public-page", "secondary", "ok", False, "secondary-media", page.get("title", "")))
        for link in page.get("links", []):
            link_url = link.get("url", "")
            channel, platform = channel_for_url(link_url)
            items.append(
                item_row(
                    "media-page",
                    "article-link",
                    link_url,
                    link_url,
                    link.get("title", ""),
                    link.get("channel") or channel,
                    link.get("platform") or platform,
                    source_priority="secondary",
                    risk_note="public page link; article content not verified",
                    raw_ref=url,
                )
            )
    for error in payload.get("errors", []):
        sources.append(source_row("media-page", error.get("url", ""), "public-page", "secondary", "blocked", False, "fetch failed", error.get("error", "")))
    return items, comments, sources


def normalize_rss(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    for feed in payload.get("feeds", []):
        feed_url = feed.get("feed_url", "")
        sources.append(source_row("rss", feed_url, "rss-feed", "secondary", "ok", False, "feed route may be version-sensitive", feed.get("feed_title", "")))
        for entry in feed.get("entries", []):
            url = entry.get("url") or entry.get("id") or feed_url
            channel, platform = channel_for_url(url)
            items.append(
                item_row(
                    "rss",
                    "feed-entry",
                    entry.get("id") or url,
                    url,
                    entry.get("title", ""),
                    entry.get("channel") or channel,
                    entry.get("platform") or platform,
                    entry.get("published_at") or "",
                    entry.get("summary") or "",
                    "secondary",
                    "RSS/feed item; verify technical claims against primary source",
                    feed_url,
                )
            )
    for error in payload.get("errors", []):
        sources.append(source_row("rss", error.get("feed_url", ""), "rss-feed", "secondary", "blocked", False, "feed failed or stale", error.get("error", "")))
    return items, comments, sources


def normalize_anysearch(payload: Any, raw_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if isinstance(payload, str):
        records = parse_anysearch_markdown(payload)
        query = ""
    else:
        records = payload.get("records", []) if isinstance(payload, dict) else []
        query = payload.get("query", "") if isinstance(payload, dict) else ""
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources = [source_row("anysearch", f"query:{query}", "search", "fallback", "ok", False, "discovery-only", str(raw_path))]
    for index, record in enumerate(records):
        url = record.get("url", "")
        channel, platform = channel_for_url(url)
        items.append(
            item_row(
                "anysearch",
                "search-hit",
                record.get("id") or str(index),
                url,
                record.get("title", ""),
                channel,
                platform,
                summary=record.get("summary", ""),
                source_priority="fallback",
                risk_note="AnySearch result; fetch and verify source page before final claim",
                raw_ref=str(raw_path),
            )
        )
    return items, comments, sources


def normalize_generic(payload: Any, source: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    records: List[Any]
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("records") or payload.get("items") or payload.get("data") or []
    else:
        records = []
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        url = record.get("url") or record.get("source_url") or record.get("link") or record.get("permalink") or ""
        channel = record.get("channel") or record.get("account") or record.get("author") or channel_for_url(url)[0]
        platform = record.get("platform") or channel_for_url(url)[1]
        kind = record.get("source_kind") or record.get("type") or ("video" if source == "bilibili" else "item")
        priority = "propagation" if source in {"wechat", "bilibili", "mediacrawler"} else "secondary"
        items.append(
            item_row(
                source,
                kind,
                record.get("id") or record.get("source_id") or str(index),
                url,
                record.get("title") or record.get("name") or record.get("text") or "",
                channel,
                platform,
                record.get("published_at") or record.get("created_at") or record.get("time") or "",
                record.get("summary") or record.get("description") or record.get("text") or "",
                priority,
                record.get("risk_note") or "external crawler output; verify before final claim",
                str(index),
                record.get("engagement_metrics") or {},
                True,
            )
        )
    return items, comments, sources


def read_payload(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return text
    return json.loads(text)


def normalize(args: argparse.Namespace) -> Dict[str, Any]:
    input_path = Path(args.input)
    payload = read_payload(input_path)
    source = args.source.lower()
    if source == "media-page":
        items, comments, sources = normalize_media_page(payload)
    elif source == "rss":
        items, comments, sources = normalize_rss(payload)
    elif source == "anysearch":
        items, comments, sources = normalize_anysearch(payload, input_path)
    else:
        items, comments, sources = normalize_generic(payload, source)

    output_dir = Path(args.output_dir)
    counts = {
        "items": write_jsonl(output_dir / "items.jsonl", items),
        "comments": write_jsonl(output_dir / "comments.jsonl", comments),
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
    needs = split_csv(args.needs)
    plan_doc = plan(args.target, needs, args.scale)
    for rel in ["raw", "normalized", "reports"]:
        (out / rel).mkdir(parents=True, exist_ok=True)
    write_json(out / "manifest.json", plan_doc)
    sources_rows = []
    for route in plan_doc.get("routes", []):
        sources_rows.append(
            {
                "source": route.get("lane", ""),
                "source_type": "planned-route",
                "source_url": "",
                "priority": route.get("priority", ""),
                "status": "planned",
                "auth_required": route.get("credentials", "") not in {"", "none"},
                "risk_note": route.get("risk_note", ""),
                "note": route.get("why", ""),
            }
        )
    with (out / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "source_type", "source_url", "priority", "status", "auth_required", "risk_note", "note"])
        writer.writeheader()
        writer.writerows(sources_rows)
    (out / "reports" / "summary.md").write_text(
        f"# Chinese AI Signal Summary\n\nTarget: {args.target}\n\nFill this from normalized row IDs and primary-source checks.\n",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "created": ["raw/", "normalized/", "reports/", "manifest.json", "sources.csv", "reports/summary.md"]}


def print_result(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chinese AI signal crawler helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="Print a source route plan")
    p.add_argument("--target", required=True)
    p.add_argument("--needs", action="append", help="Comma-separated needs: media,rss,anysearch,wechat,bilibili,mediacrawler,primary-check,report")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("inspect-url", help="Classify a URL and recommend routes")
    p.add_argument("url")

    sub.add_parser("schema", help="Print normalized output schema summary")

    p = sub.add_parser("scaffold", help="Create a run directory")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--needs", action="append")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("fetch-page", help="Fetch public HTML pages and extract candidate links")
    p.add_argument("--url", action="append", required=True)
    p.add_argument("--max-links", type=int, default=30)
    p.add_argument("--output")

    p = sub.add_parser("fetch-rss", help="Fetch RSS/Atom feeds")
    p.add_argument("--feed", action="append", required=True)
    p.add_argument("--max-entries", type=int, default=20)
    p.add_argument("--output")

    p = sub.add_parser("fetch-anysearch", help="Run AnySearch CLI and capture discovery results")
    p.add_argument("--query", required=True)
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--freshness", choices=["day", "week", "month", "year"])
    p.add_argument("--anysearch-cli")
    p.add_argument("--output")

    p = sub.add_parser("normalize", help="Normalize raw capture into JSONL files")
    p.add_argument("--input", required=True)
    p.add_argument("--source", required=True, choices=["media-page", "rss", "anysearch", "wechat", "bilibili", "mediacrawler", "generic"])
    p.add_argument("--output-dir", required=True)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            print_result(plan(args.target, split_csv(args.needs), args.scale))
        elif args.command == "inspect-url":
            print_result(inspect_url(args.url))
        elif args.command == "schema":
            print_result({"schema_version": SCHEMA_VERSION, "outputs": SCHEMA_SUMMARY})
        elif args.command == "scaffold":
            print_result(scaffold(args))
        elif args.command == "fetch-page":
            print_result(fetch_page(args))
        elif args.command == "fetch-rss":
            print_result(fetch_rss(args))
        elif args.command == "fetch-anysearch":
            print_result(fetch_anysearch(args))
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
