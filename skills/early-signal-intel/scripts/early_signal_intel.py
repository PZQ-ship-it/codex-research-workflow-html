#!/usr/bin/env python3
"""Helpers for early research signal routing, capture, and normalization."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "0.1"
USER_AGENT = "Codex early-signal-intel/0.1 (+https://github.com/openai/codex)"
HN_FIREBASE = "https://hacker-news.firebaseio.com/v0"
HN_ALGOLIA = "https://hn.algolia.com/api/v1"

SCHEMA_SUMMARY = {
    "raw/": "Untouched API JSON, RSS XML/JSON transforms, fetched HTML, and logs.",
    "normalized/items.jsonl": "Stories, posts, feed entries, alphaXiv paper/comment rows, HN search hits, and Bluesky/Reddit items.",
    "normalized/comments.jsonl": "Comments, replies, and thread excerpts with parent/source linkage.",
    "normalized/sources.jsonl": "Source metadata, feeds, accounts, API routes, access status, and credential policy.",
    "sources.csv": "Source review table with URL, source type, priority, status, and auth requirement.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}

NEED_ALIASES = {
    "alpha": "alphaxiv",
    "alphaxiv": "alphaxiv",
    "arxiv-discussion": "alphaxiv",
    "hackernews": "hn",
    "hacker-news": "hn",
    "hn": "hn",
    "rss": "rss",
    "blog": "rss",
    "blogs": "rss",
    "lab-blog": "rss",
    "lab-blogs": "rss",
    "bsky": "bluesky",
    "bluesky": "bluesky",
    "atproto": "bluesky",
    "reddit": "reddit",
    "x": "x",
    "twitter": "x",
    "report": "report",
    "summary": "report",
}


class FetchError(RuntimeError):
    """Raised for HTTP fetch failures with context."""


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


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text_from_html(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def http_get_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return json.loads(body.decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FetchError(f"fetch failed for {url}: {exc}") from exc


def http_get_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise FetchError(f"fetch failed for {url}: {exc}") from exc


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


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    query = urllib.parse.parse_qs(parsed.query)
    parts = [part for part in path.split("/") if part]
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": "/" + path if path else "/",
        "source": "unknown",
        "source_kind": "unknown",
        "ids": {},
        "recommended_needs": [],
        "recommended_routes": [],
        "auth_required": False,
    }

    if host in {"news.ycombinator.com", "www.news.ycombinator.com"}:
        item_id = query.get("id", [""])[0]
        result.update(
            {
                "source": "hn",
                "source_kind": "story" if item_id else "hn-page",
                "ids": {"item_id": item_id} if item_id else {"path": path},
                "recommended_needs": ["hn", "comments", "report"],
                "recommended_routes": ["hn-firebase-api", "hn-algolia-search"],
            }
        )
        return result

    if host.endswith("hn.algolia.com"):
        result.update(
            {
                "source": "hn",
                "source_kind": "search",
                "ids": {"query": query.get("query", [""])[0], "path": path},
                "recommended_needs": ["hn", "report"],
                "recommended_routes": ["hn-algolia-search"],
            }
        )
        return result

    if host.endswith("alphaxiv.org"):
        arxiv_id = ""
        for part in parts:
            if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", part):
                arxiv_id = part
                break
        result.update(
            {
                "source": "alphaxiv",
                "source_kind": "paper" if arxiv_id else "explore",
                "ids": {"arxiv_id": arxiv_id, "path": path},
                "recommended_needs": ["alphaxiv", "comments", "report"],
                "recommended_routes": ["alphaxiv-py", "alphaxiv-public-web"],
                "auth_required": False,
            }
        )
        return result

    if host in {"arxiv.org", "www.arxiv.org"} and parts:
        arxiv_id = parts[-1]
        result.update(
            {
                "source": "arxiv",
                "source_kind": "paper",
                "ids": {"arxiv_id": arxiv_id},
                "recommended_needs": ["alphaxiv", "rss", "report"],
                "recommended_routes": ["alphaxiv-py", "arxiv-public-page"],
            }
        )
        return result

    if "bsky.app" in host or host.endswith("bsky.social"):
        result.update(
            {
                "source": "bluesky",
                "source_kind": "profile-or-post",
                "ids": {"path": path},
                "recommended_needs": ["bluesky", "report"],
                "recommended_routes": ["atproto-public-appview", "jetstream-short-window"],
            }
        )
        return result

    if host.endswith("reddit.com") or host.endswith("old.reddit.com"):
        result.update(
            {
                "source": "reddit",
                "source_kind": "subreddit-or-thread",
                "ids": {"path": path},
                "recommended_needs": ["reddit", "comments", "report"],
                "recommended_routes": ["reddit-official-api-praw"],
                "auth_required": True,
            }
        )
        return result

    if host in {"x.com", "twitter.com", "www.x.com", "www.twitter.com"}:
        result.update(
            {
                "source": "x",
                "source_kind": "profile-or-post",
                "ids": {"path": path},
                "recommended_needs": ["x", "report"],
                "recommended_routes": ["x-official-api-only"],
                "auth_required": True,
            }
        )
        return result

    if any(marker in host for marker in ["openai.com", "anthropic.com", "deepmind.google", "research.google", "ai.meta.com", "microsoft.com", "bair.berkeley.edu", "hai.stanford.edu", "csail.mit.edu"]):
        result.update(
            {
                "source": "rss",
                "source_kind": "research-blog",
                "ids": {"host": host, "path": path},
                "recommended_needs": ["rss", "report"],
                "recommended_routes": ["rss-atom-feed", "html-feed-discovery"],
            }
        )
        return result

    return result


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_url(target)
    arxiv_match = re.search(r"\b\d{4}\.\d{4,5}(v\d+)?\b", target)
    if arxiv_match:
        return {
            "url": "",
            "host": "",
            "path": "",
            "source": "arxiv",
            "source_kind": "paper-id",
            "ids": {"arxiv_id": arxiv_match.group(0), "query": target},
            "recommended_needs": ["alphaxiv", "hn", "rss", "report"],
            "recommended_routes": ["alphaxiv-py", "hn-algolia-search", "rss-atom-feed"],
            "auth_required": False,
        }
    return {
        "url": "",
        "host": "",
        "path": "",
        "source": "topic",
        "source_kind": "query",
        "ids": {"query": target},
        "recommended_needs": ["hn", "rss", "alphaxiv", "report"],
        "recommended_routes": ["hn-algolia-search", "rss-atom-feed", "alphaxiv-py"],
        "auth_required": False,
    }


def route_for_needs(needs: List[str], target_info: Dict[str, Any], scale: str) -> List[Dict[str, Any]]:
    needset = set(needs)
    routes: List[Dict[str, Any]] = []

    if "hn" in needset or target_info.get("source") == "hn":
        routes.append(
            {
                "lane": "hn-public",
                "priority": "primary",
                "why": "HN exposes public Firebase and Algolia APIs with no API key, useful for engineering diffusion and comment-tree signals.",
                "suggested_calls": [
                    "fetch-hn --query <keywords>",
                    "fetch-hn --item-id <id> --include-comments --max-comments 40",
                ],
                "credentials": "none",
            }
        )

    if "rss" in needset or target_info.get("source") == "rss":
        routes.append(
            {
                "lane": "rss-lab-blogs",
                "priority": "primary",
                "why": "RSS/Atom is the lightest first-party route for lab and company research blog monitoring.",
                "suggested_calls": ["fetch-rss --feed <feed-url> --output raw/rss.json"],
                "credentials": "none",
            }
        )

    if "alphaxiv" in needset or target_info.get("source") in {"alphaxiv", "arxiv"}:
        routes.append(
            {
                "lane": "alphaxiv",
                "priority": "primary-for-arxiv-discussion",
                "why": "alphaXiv is the clearest discussion layer for arXiv papers. Use alphaxiv-py when installed; API key is optional for public reads.",
                "suggested_calls": [
                    "python -m pip install alphaxiv-py (optional isolated runtime)",
                    "alphaxiv paper comments list --json",
                    "alphaxiv feed list --json",
                ],
                "credentials": "optional ALPHAXIV_API_KEY",
            }
        )

    if "bluesky" in needset:
        routes.append(
            {
                "lane": "bluesky-atproto",
                "priority": "secondary",
                "why": "AT Protocol and Jetstream are good for time-sensitive scholar/account signals, but broad firehose capture should be bounded.",
                "suggested_calls": [
                    "atproto/Jetstream short-window collection",
                    "seed-account profile/post lookup",
                ],
                "credentials": "optional BLUESKY_HANDLE and BLUESKY_APP_PASSWORD",
            }
        )

    if "reddit" in needset:
        routes.append(
            {
                "lane": "reddit-official-api",
                "priority": "anecdotal",
                "why": "Reddit can expose real practitioner feedback, but it is noisy and subject to API terms, OAuth, and rate limits.",
                "suggested_calls": ["PRAW subreddit search after OAuth setup"],
                "credentials": "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET required for robust use",
            }
        )

    if "x" in needset:
        routes.append(
            {
                "lane": "x-official-api",
                "priority": "optional-costly",
                "why": "X is useful for first-release scholar signals but official API access can cost money; unofficial scrapers are not default.",
                "suggested_calls": ["Official recent search endpoint after explicit user approval"],
                "credentials": "X_BEARER_TOKEN required",
            }
        )

    if "report" in needset:
        routes.append(
            {
                "lane": "normalize-and-summarize",
                "priority": "required",
                "why": "Merge captured rows into auditable JSONL before synthesis.",
                "suggested_calls": ["normalize --input raw.json --source hn|rss|alphaxiv|bluesky|reddit --output-dir normalized"],
                "credentials": "none",
            }
        )

    if not routes:
        routes.append(
            {
                "lane": "hn-rss-baseline",
                "priority": "default",
                "why": "No specific need was selected; start with the no-key HN and RSS closure.",
                "suggested_calls": ["fetch-hn --query <target>", "fetch-rss --feed <known-feed>"],
                "credentials": "none",
            }
        )

    if scale in {"large", "bulk"}:
        for route in routes:
            route.setdefault("cautions", []).append("Run a small smoke capture first, then throttle and checkpoint bulk capture.")

    return routes


def plan(target: str, needs: List[str], scale: str) -> Dict[str, Any]:
    target_info = classify_target(target)
    if not needs:
        needs = list(target_info.get("recommended_needs") or ["hn", "rss", "report"])
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "target": target,
        "target_info": target_info,
        "needs": needs,
        "scale": scale,
        "routes": route_for_needs(needs, target_info, scale),
        "credential_policy": {
            "default": "No private credentials required for HN and RSS baseline.",
            "private_env": "%USERPROFILE%\\.codex\\skills\\early-signal-intel\\.env",
            "setup_helper": "scripts\\assist_early_signal_auth.ps1",
        },
        "output_contract": SCHEMA_SUMMARY,
    }


def fetch_hn_item(item_id: int) -> Dict[str, Any]:
    item = http_get_json(f"{HN_FIREBASE}/item/{item_id}.json")
    if not isinstance(item, dict):
        raise FetchError(f"HN item {item_id} is not an object")
    return item


def walk_hn_comments(item: Dict[str, Any], max_comments: int, delay: float = 0.0) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    queue = list(as_list(item.get("kids")))
    seen = set()
    while queue and len(comments) < max_comments:
        kid = queue.pop(0)
        if kid in seen:
            continue
        seen.add(kid)
        try:
            child = fetch_hn_item(int(kid))
        except FetchError:
            continue
        if child:
            comments.append(child)
            queue.extend(as_list(child.get("kids")))
        if delay:
            time.sleep(delay)
    return comments


def fetch_hn(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": "hn",
        "fetched_at": now_iso(),
        "mode": "",
        "query": args.query,
        "item_id": args.item_id,
        "records": [],
        "comments": [],
        "source_urls": [],
    }
    if args.item_id:
        item = fetch_hn_item(int(args.item_id))
        payload["mode"] = "firebase-item"
        payload["records"] = [item]
        payload["source_urls"] = [f"https://news.ycombinator.com/item?id={args.item_id}"]
        if args.include_comments:
            payload["comments"] = walk_hn_comments(item, args.max_comments, args.delay)
    elif args.query:
        params = {
            "query": args.query,
            "hitsPerPage": str(args.max_results),
            "tags": args.tags,
        }
        url = f"{HN_ALGOLIA}/search?{urllib.parse.urlencode(params)}"
        response = http_get_json(url)
        hits = response.get("hits", []) if isinstance(response, dict) else []
        payload["mode"] = "algolia-search"
        payload["records"] = hits
        payload["source_urls"] = [url]
        payload["meta"] = {k: response.get(k) for k in ["page", "nbHits", "nbPages", "hitsPerPage", "processingTimeMS"] if isinstance(response, dict)}
    else:
        raise SystemExit("fetch-hn requires --query or --item-id")

    if args.output:
        write_json(Path(args.output), payload)
    return payload


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def first_child_text(node: ET.Element, names: Sequence[str]) -> str:
    nameset = {name.lower() for name in names}
    for child in list(node):
        if strip_ns(child.tag).lower() in nameset:
            text = "".join(child.itertext()).strip()
            return html.unescape(text)
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
    raw = http_get_bytes(url)
    root = ET.fromstring(raw)
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
            entries.append(
                {
                    "id": guid,
                    "title": first_child_text(item, ["title"]),
                    "url": link,
                    "summary": text_from_html(first_child_text(item, ["description", "summary"])),
                    "published_at": first_child_text(item, ["pubDate", "published", "updated"]),
                    "authors": [first_child_text(item, ["author", "creator"])] if first_child_text(item, ["author", "creator"]) else [],
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
            entries.append(
                {
                    "id": entry_id,
                    "title": first_child_text(entry, ["title"]),
                    "url": link,
                    "summary": text_from_html(first_child_text(entry, ["summary", "content"])),
                    "published_at": first_child_text(entry, ["published", "updated"]),
                    "authors": [first_child_text(author, ["name"]) for author in entry if strip_ns(author.tag).lower() == "author" and first_child_text(author, ["name"])],
                    "feed_url": url,
                    "feed_title": feed_title,
                }
            )

    return {
        "feed_url": url,
        "feed_title": feed_title,
        "entry_count": len(entries),
        "entries": entries,
        "raw_bytes": len(raw),
    }


def fetch_rss(args: argparse.Namespace) -> Dict[str, Any]:
    feeds = []
    errors = []
    for feed_url in args.feed:
        try:
            feeds.append(parse_feed(feed_url, args.max_entries))
        except Exception as exc:  # noqa: BLE001 - emit structured blocker for CLI users
            errors.append({"feed_url": feed_url, "error": str(exc)})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "rss",
        "fetched_at": now_iso(),
        "feeds": feeds,
        "errors": errors,
    }
    if args.output:
        write_json(Path(args.output), payload)
    return payload


def source_row(source: str, url: str, source_type: str, priority: str, status: str, auth_required: bool = False, note: str = "") -> Dict[str, Any]:
    return {
        "row_id": stable_id("source", source, url, source_type),
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "source_type": source_type,
        "source_url": url,
        "priority": priority,
        "status": status,
        "auth_required": auth_required,
        "note": note,
        "fetched_at": now_iso(),
    }


def normalize_hn(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for url in payload.get("source_urls", []):
        sources.append(source_row("hn", url, "api", "primary", "ok", False, payload.get("mode", "")))

    for record in payload.get("records", []):
        if not isinstance(record, dict):
            continue
        object_id = str(record.get("objectID") or record.get("id") or "")
        item_id = str(record.get("story_id") or record.get("id") or object_id)
        title = record.get("title") or record.get("story_title") or ""
        url = record.get("url") or record.get("story_url") or (f"https://news.ycombinator.com/item?id={item_id}" if item_id else "")
        text = text_from_html(record.get("text") or record.get("comment_text") or "")
        row = {
            "row_id": stable_id("hn-item", item_id or object_id, title, url),
            "schema_version": SCHEMA_VERSION,
            "source": "hn",
            "source_kind": record.get("type") or record.get("_tags", ["story"])[0] if isinstance(record.get("_tags"), list) and record.get("_tags") else "story",
            "source_id": item_id or object_id,
            "source_url": url,
            "discussion_url": f"https://news.ycombinator.com/item?id={item_id}" if item_id else "",
            "title": text_from_html(title),
            "author": record.get("author") or record.get("by") or "",
            "published_at": record.get("created_at") or record.get("time") or "",
            "score": record.get("points") if record.get("points") is not None else record.get("score"),
            "comment_count": record.get("num_comments") if record.get("num_comments") is not None else record.get("descendants"),
            "summary": text[:1000],
            "tags": record.get("_tags", []),
            "source_priority": "primary",
            "fetched_at": fetched_at,
            "raw_ref": item_id or object_id,
        }
        items.append(row)

    for comment in payload.get("comments", []):
        if not isinstance(comment, dict):
            continue
        comment_id = str(comment.get("id") or "")
        comments.append(
            {
                "row_id": stable_id("hn-comment", comment_id),
                "schema_version": SCHEMA_VERSION,
                "source": "hn",
                "source_kind": "comment",
                "source_id": comment_id,
                "source_url": f"https://news.ycombinator.com/item?id={comment_id}" if comment_id else "",
                "parent_id": str(comment.get("parent") or ""),
                "author": comment.get("by") or "",
                "published_at": comment.get("time") or "",
                "body": text_from_html(comment.get("text") or "")[:4000],
                "source_priority": "primary",
                "fetched_at": fetched_at,
                "raw_ref": comment_id,
            }
        )
    return items, comments, sources


def normalize_rss(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") or now_iso()
    for feed in payload.get("feeds", []):
        feed_url = feed.get("feed_url", "")
        sources.append(source_row("rss", feed_url, "rss-feed", "primary", "ok", False, feed.get("feed_title", "")))
        for entry in feed.get("entries", []):
            if not isinstance(entry, dict):
                continue
            url = entry.get("url") or entry.get("id") or feed_url
            items.append(
                {
                    "row_id": stable_id("rss-item", feed_url, entry.get("id"), url, entry.get("title")),
                    "schema_version": SCHEMA_VERSION,
                    "source": "rss",
                    "source_kind": "feed-entry",
                    "source_id": entry.get("id") or url,
                    "source_url": url,
                    "discussion_url": "",
                    "title": text_from_html(entry.get("title") or ""),
                    "author": ", ".join(entry.get("authors") or []),
                    "published_at": entry.get("published_at") or "",
                    "score": None,
                    "comment_count": None,
                    "summary": text_from_html(entry.get("summary") or "")[:1000],
                    "tags": [],
                    "source_priority": "primary",
                    "feed_url": feed_url,
                    "feed_title": feed.get("feed_title", ""),
                    "fetched_at": fetched_at,
                    "raw_ref": entry.get("id") or url,
                }
            )
    for error in payload.get("errors", []):
        if isinstance(error, dict):
            sources.append(source_row("rss", error.get("feed_url", ""), "rss-feed", "primary", "blocked", False, error.get("error", "")))
    return items, comments, sources


def normalize_generic(payload: Any, source: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    records = payload if isinstance(payload, list) else payload.get("records", []) if isinstance(payload, dict) else []
    items: List[Dict[str, Any]] = []
    comments: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    fetched_at = payload.get("fetched_at") if isinstance(payload, dict) else now_iso()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        url = record.get("url") or record.get("source_url") or record.get("permalink") or ""
        title = record.get("title") or record.get("name") or record.get("text") or ""
        items.append(
            {
                "row_id": stable_id(source, index, url, title),
                "schema_version": SCHEMA_VERSION,
                "source": source,
                "source_kind": record.get("type") or "item",
                "source_id": record.get("id") or record.get("objectID") or url or str(index),
                "source_url": url,
                "discussion_url": record.get("discussion_url") or "",
                "title": text_from_html(title)[:500],
                "author": record.get("author") or record.get("by") or record.get("user") or "",
                "published_at": record.get("published_at") or record.get("created_at") or record.get("time") or "",
                "score": record.get("score") or record.get("points") or record.get("likes"),
                "comment_count": record.get("comment_count") or record.get("num_comments"),
                "summary": text_from_html(record.get("summary") or record.get("description") or record.get("text") or "")[:1000],
                "tags": record.get("tags") or [],
                "source_priority": "secondary" if source in {"reddit", "bluesky", "x"} else "primary",
                "fetched_at": fetched_at,
                "raw_ref": record.get("id") or str(index),
            }
        )
    return items, comments, sources


def normalize(args: argparse.Namespace) -> Dict[str, Any]:
    input_path = Path(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    source = args.source.lower()
    if source == "hn":
        items, comments, sources = normalize_hn(payload)
    elif source == "rss":
        items, comments, sources = normalize_rss(payload)
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
                "note": route.get("why", ""),
            }
        )
    with (out / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "source_type", "source_url", "priority", "status", "auth_required", "note"])
        writer.writeheader()
        writer.writerows(sources_rows)
    (out / "reports" / "summary.md").write_text(
        f"# Early Signal Summary\n\nTarget: {args.target}\n\nFill this from normalized row IDs.\n",
        encoding="utf-8",
    )
    return {
        "output_dir": str(out),
        "created": ["raw/", "normalized/", "reports/", "manifest.json", "sources.csv", "reports/summary.md"],
    }


def print_result(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Early signal intelligence helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="Print a source route plan")
    p.add_argument("--target", required=True)
    p.add_argument("--needs", action="append", help="Comma-separated needs: alphaxiv,hn,rss,bluesky,reddit,x,report")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("inspect-url", help="Classify a URL and recommend routes")
    p.add_argument("url")

    sub.add_parser("schema", help="Print normalized output schema summary")

    p = sub.add_parser("scaffold", help="Create a run directory")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--needs", action="append")
    p.add_argument("--scale", default="small", choices=["small", "medium", "large", "bulk"])

    p = sub.add_parser("fetch-hn", help="Fetch Hacker News search hits or a story thread")
    p.add_argument("--query")
    p.add_argument("--item-id", type=int)
    p.add_argument("--include-comments", action="store_true")
    p.add_argument("--max-comments", type=int, default=40)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--tags", default="story")
    p.add_argument("--delay", type=float, default=0.0)
    p.add_argument("--output")

    p = sub.add_parser("fetch-rss", help="Fetch RSS/Atom feeds")
    p.add_argument("--feed", action="append", required=True)
    p.add_argument("--max-entries", type=int, default=20)
    p.add_argument("--output")

    p = sub.add_parser("normalize", help="Normalize raw capture JSON into JSONL files")
    p.add_argument("--input", required=True)
    p.add_argument("--source", required=True, choices=["hn", "rss", "alphaxiv", "bluesky", "reddit", "x", "generic"])
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
        elif args.command == "fetch-hn":
            print_result(fetch_hn(args))
        elif args.command == "fetch-rss":
            print_result(fetch_rss(args))
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
