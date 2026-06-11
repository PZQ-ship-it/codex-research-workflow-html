#!/usr/bin/env python3
"""Planning and normalization helpers for public Zhihu research workflows."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse


SCHEMA_SUMMARY = {
    "raw/": "Untouched backend outputs, screenshots, or API captures.",
    "items.jsonl": "Questions, answers, articles, search results, and public users.",
    "comments.jsonl": "Comments and nested replies.",
    "sources.csv": "Flattened review table.",
    "manifest.json": "Plan, commands, limits, timestamps, and blockers.",
    "summary.md": "Human synthesis grounded in normalized source IDs.",
}


BACKENDS = {
    "zhihu-mcp-auth": {
        "best_for": ["search", "keyword", "people", "topic", "question", "answers", "article", "comments", "user", "report"],
        "setup": [
            "Check the private zhihu-mcp runtime before crawling.",
            "If login status is missing, stale, logged_in=false, or login_verified=false, immediately open the visible login helper and let the user complete Zhihu login/MFA/CAPTCHA.",
            "After login is verified, use zhihu-mcp tools for search, detail, comments, and user/profile capture.",
            "Use AnySearch only as a fallback when the user declines login, two assisted login attempts fail, the MCP runtime remains unavailable, or a quick public index cross-check is requested.",
        ],
    },
    "anysearch-discovery": {
        "best_for": ["fallback-search", "public-index", "declined-login"],
        "setup": [
            "Use AnySearch Python CLI only as a fallback or cross-check lane.",
            "Save search output under raw/ and normalize with --source anysearch.",
            "Treat results as URL/title/snippet discovery unless a Zhihu page or MCP detail tool later returns full content.",
        ],
    },
    "public-browser-lite": {
        "best_for": ["question", "answers", "article", "report", "public-local"],
        "setup": [
            "Use a normal browser or Playwright against already discovered public Zhihu URLs.",
            "No MCP server, external API key, paid scraper, or committed cookies are required.",
            "Save public raw captures under raw/ and normalize with --source public-browser-lite.",
            "When Zhihu search/detail pages hit a login wall, record the blocker and route to the zhihu-mcp authenticated helper before using fallback discovery.",
            "Treat CAPTCHA, hidden comments, and missing dynamic content as blockers.",
        ],
    },
    "zhihu-k-search": {
        "best_for": ["search", "question", "answers", "article", "markdown", "json"],
        "setup": [
            "cd path\\to\\zhihu-k-search\\scripts",
            "uv sync",
            "uv run playwright install chromium",
            "uv run python main.py login",
        ],
    },
    "zhihu-mcp": {
        "best_for": ["search", "question", "answers", "article", "comments", "user", "mcp", "report"],
        "setup": [
            "python -m venv .venv",
            ".venv\\Scripts\\python -m pip install -r requirements.txt",
            ".venv\\Scripts\\python -m playwright install chromium",
            ".venv\\Scripts\\python mcp_server.py --test",
        ],
    },
    "MediaCrawler": {
        "best_for": ["bulk", "scale", "comments", "cross-platform"],
        "setup": [
            "Follow the MediaCrawler project setup in an isolated environment.",
            "Run a small Zhihu smoke crawl before scaling.",
        ],
    },
    "ZhihuApis": {
        "best_for": ["comments", "nested-comments", "answer-comments", "article-comments"],
        "setup": [
            "pip install -r requirements.txt",
            "npm install",
            "python App.py",
        ],
    },
}


ANYSEARCH_ENTRYPOINT = r"python C:\Users\Administrator\.codex\skills\anysearch\scripts\anysearch_cli.py"


def default_runtime_root() -> Path:
    home = os.environ.get("USERPROFILE") or str(Path.home())
    return Path(home) / ".codex" / "skills" / "zhihu-public-intel" / "runtime"


def runtime_paths(runtime_root: Optional[str] = None) -> Dict[str, Path]:
    root = Path(runtime_root).expanduser() if runtime_root else default_runtime_root()
    checkout = root / "zhihu-mcp"
    return {
        "runtime_root": root,
        "checkout_dir": checkout,
        "venv_python": checkout / ".venv" / "Scripts" / "python.exe",
        "config_json": checkout / "config.json",
        "cookies_json": checkout / "cookies.json",
        "profile_dir": checkout / "zhihu-profile",
        "mcp_server": checkout / "mcp_server.py",
    }


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def split_csv(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def stable_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def inspect_zhihu_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": "/" + path if path else "/",
        "type": "unknown",
        "ids": {},
        "recommended_needs": [],
    }

    if "zhihu.com" not in host:
        return result

    question_answer = re.search(r"question/(\d+)/answer/(\d+)", path)
    if question_answer:
        result["type"] = "answer"
        result["ids"] = {"question_id": question_answer.group(1), "answer_id": question_answer.group(2)}
        result["recommended_needs"] = ["answer", "comments"]
        return result

    question = re.search(r"question/(\d+)", path)
    if question:
        result["type"] = "question"
        result["ids"] = {"question_id": question.group(1)}
        result["recommended_needs"] = ["question", "answers", "comments"]
        return result

    article = re.search(r"(?:p|post)/(\d+)", path)
    if "zhuanlan.zhihu.com" in host and article:
        result["type"] = "article"
        result["ids"] = {"article_id": article.group(1)}
        result["recommended_needs"] = ["article", "comments"]
        return result

    people = re.search(r"people/([^/]+)", path)
    if people:
        result["type"] = "user"
        result["ids"] = {"user_token": people.group(1)}
        result["recommended_needs"] = ["user"]
        return result

    if path == "search" or path.startswith("search/"):
        query = parse_qs(parsed.query).get("q", [""])[0]
        result["type"] = "search"
        result["ids"] = {"query": query}
        result["recommended_needs"] = ["search"]
        return result

    return result


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_zhihu_url(target)
    return {
        "url": "",
        "host": "",
        "path": "",
        "type": "keyword",
        "ids": {"query": target},
        "recommended_needs": ["search", "auth", "report"],
    }


def choose_backend(needs: List[str], scale: str, prefer: Optional[str] = None) -> str:
    if prefer:
        return prefer
    normalized = {need.lower().replace("_", "-") for need in needs}
    if normalized & {"search", "auth", "comments", "user", "activities", "article", "answers", "question"}:
        return "zhihu-mcp-auth"
    return "public-browser-lite"


def build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    needs = split_csv(args.needs)
    target_info = classify_target(args.target)
    if not needs:
        needs = target_info.get("recommended_needs") or ["search", "report"]
    backend = choose_backend(needs, args.scale, args.prefer_backend)
    plan = {
        "target": args.target,
        "target_info": target_info,
        "needs": needs,
        "scale": args.scale,
        "recommended_backend": backend,
        "backend_reason": backend_reason(backend, needs, args.scale),
        "setup": BACKENDS[backend]["setup"],
        "commands": command_suggestions(backend, args.target, target_info, needs),
        "optional_backends": optional_backend_notes(needs, args.scale),
        "login_wall_policy": login_wall_policy(args.target, target_info, needs),
        "output_contract": SCHEMA_SUMMARY,
        "guardrails": [
            "Default to public/local capture that does not require MCP, paid services, external API keys, or committed login state.",
            "Keep cookies.json, auth.json, storage state, .env, and headers local and untracked.",
            "Use logged-in state only after explicit user approval and only for content the user can legitimately access.",
            "Run a small smoke crawl before scaling.",
            "Do not bypass CAPTCHA automatically.",
            "Keep raw captures local; summarize and cite URLs in reports.",
        ],
    }
    return plan


def backend_reason(backend: str, needs: List[str], scale: str) -> str:
    if backend == "public-browser-lite":
        return "Selected for already discovered public Zhihu URLs and page/detail capture without required MCP."
    if backend == "anysearch-discovery":
        return "Fallback public-index lane when authenticated zhihu-mcp is declined, unavailable, or needs cross-checking."
    if backend == "zhihu-mcp-auth":
        return "Default lane for Zhihu research: guide local authentication first, then use zhihu-mcp tools."
    if backend == "MediaCrawler":
        return "Selected for larger scale or cross-platform public crawling."
    if backend == "ZhihuApis":
        return "Selected because comment completeness or nested comments are the main need."
    if backend == "zhihu-mcp":
        return "Selected for Agent/MCP workflows, comments plus content, or user public profile/activity."
    return "Selected for lightweight public search and question/answer/article detail extraction."


def optional_backend_notes(needs: List[str], scale: str) -> List[Dict[str, Any]]:
    normalized = {need.lower().replace("_", "-") for need in needs}
    notes: List[Dict[str, Any]] = []
    if "bulk" in normalized or scale == "large":
        notes.append(
            {
                "backend": "MediaCrawler",
                "when": "Only if the user explicitly accepts a larger external crawler checkout and setup.",
            }
        )
    if "nested-comments" in normalized or ("comments" in normalized and scale == "deep"):
        notes.append(
            {
                "backend": "ZhihuApis",
                "when": "Only for authorized logged-in comment completeness work; cookies stay local.",
            }
        )
    if {"comments", "user", "mcp"} & normalized:
        notes.append(
            {
                "backend": "zhihu-mcp",
                "when": "Default authenticated lane after check-runtime and visible-browser login if needed.",
            }
        )
    if normalized & {"search", "question", "answers", "article"}:
        notes.append(
            {"backend": "AnySearch discovery", "when": "Fallback only when the user declines login, two assisted login attempts fail, the MCP runtime remains unavailable, or public-index cross-checking is useful. Normalize snippets as discovery rows; do not claim full Zhihu content was captured."}
        )
        notes.append(
            {
                "backend": "zhihu-k-search",
                "when": "Optional convenience CLI if already installed; not required for the narrowed default lane.",
            }
        )
    return notes


def login_wall_policy(target: str, info: Dict[str, Any], needs: List[str]) -> Dict[str, Any]:
    query = (info.get("ids") or {}).get("query") or target
    needs_norm = {need.lower().replace("_", "-") for need in needs}
    needs_auth = bool(needs_norm & {"comments", "nested-comments", "user", "activities", "mcp", "full-detail"})
    return {
        "detect_as_blocker": [
            "URL redirects to /signin or returns 401/403.",
            "Zhihu tool returns zero results for an otherwise plausible exact-name/topic query.",
            "Article/detail APIs return request-parameter/login errors while search engines still index the URL.",
            "Comment/full activity fields are hidden or incomplete.",
        ],
        "auth_first": [
            "Guide the user through zhihu-mcp local authentication first.",
            "python skills\\zhihu-public-intel\\scripts\\zhihu_public_intel.py check-runtime",
            "Call MCP check_login_status() or cookie_status(); if logged_in=false/login_verified=false, do not search yet.",
            "powershell -ExecutionPolicy Bypass -File .\\skills\\zhihu-public-intel\\scripts\\assist_zhihu_login.ps1",
            "A present cookies.json is not enough; the helper refreshes stale cookies after successful visible login.",
            "After user login, verify again with MCP tool check_login_status() or cookie_status().",
        ],
        "authenticated_escalation": [
            "Tell the user what local state will be stored before opening the visible login helper.",
            r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1",
            r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1",
            "The user completes Zhihu login/MFA/CAPTCHA in the visible browser; Codex never asks for cookie values in chat.",
            "Restart Codex if the MCP server was newly registered, then smoke-test with check_login_status/cookie_status before crawling.",
        ],
        "public_fallback": [
            "Use only if authentication is declined, two assisted login attempts fail, the MCP runtime remains unavailable, or a public index cross-check is requested.",
            anysearch_discovery_command(query),
            "Store AnySearch output under raw/ and normalize with --source anysearch; mark it as discovery/snippet evidence, not full Zhihu page capture.",
        ],
        "auth_likely_needed": needs_auth,
    }


def anysearch_discovery_command(query: str) -> str:
    q = str(query).replace('"', '\\"')
    return (
        f'{ANYSEARCH_ENTRYPOINT} batch_search '
        f'--query "site:zhihu.com {q}" '
        f'--query "site:zhuanlan.zhihu.com {q}" '
        f'--query "\\"{q}\\" 知乎"'
    )


def command_suggestions(backend: str, target: str, info: Dict[str, Any], needs: List[str]) -> List[str]:
    item_type = info.get("type")
    ids = info.get("ids") or {}
    if backend == "public-browser-lite":
        if item_type in {"question", "answer", "article", "user"}:
            return [
                "Open the public URL in a normal browser/Playwright session and save raw HTML or extracted JSON-like fields under raw/.",
                "Normalize the captured public fields with: python skills/zhihu-public-intel/scripts/zhihu_public_intel.py normalize --source public-browser-lite --input raw/public_capture.json --output-dir normalized",
            ]
        query = ids.get("query") or target
        return [
            "Do not use public-browser-lite for keyword search directly.",
            "Switch to the auth-first lane: python skills\\zhihu-public-intel\\scripts\\zhihu_public_intel.py plan --target {!r} --needs search,auth,report".format(query),
            "If the user declines login, two assisted login attempts fail, or zhihu-mcp remains unavailable, then use AnySearch fallback: {}".format(anysearch_discovery_command(query)),
        ]
    if backend == "anysearch-discovery":
        query = ids.get("query") or target
        return [
            "Use AnySearch only as fallback/cross-check after authenticated zhihu-mcp login is declined, two assisted login attempts fail, the runtime is unavailable, or cross-checking is requested: {}".format(anysearch_discovery_command(query)),
            "Save the raw AnySearch result JSON under raw/.",
            "Normalize discovery rows with: python skills/zhihu-public-intel/scripts/zhihu_public_intel.py normalize --source anysearch --input raw/anysearch_discovery.json --output-dir normalized",
            "Only after URLs/IDs are found, use inspect-url to choose public-browser-lite or authenticated zhihu-mcp for detail capture.",
        ]
    if backend == "zhihu-mcp-auth":
        query = ids.get("query") or target
        return [
            "Run runtime check without reading cookies: python skills\\zhihu-public-intel\\scripts\\zhihu_public_intel.py check-runtime",
            "Call MCP check_login_status() or cookie_status(); if logged_in=false/login_verified=false, immediately open visible login: powershell -ExecutionPolicy Bypass -File .\\skills\\zhihu-public-intel\\scripts\\assist_zhihu_login.ps1",
            "Existing cookies.json may be stale; refresh it through the visible helper instead of switching to AnySearch.",
            "The user completes Zhihu login/MFA/CAPTCHA in the browser; do not ask for cookie values in chat.",
            "Verify with MCP tool: check_login_status() or cookie_status().",
            'Then run MCP tool: search_content(keyword={!r}, content_type="all", count=20)'.format(query),
            "Use get_question_detail/get_answer_detail/get_article_detail/get_comments/user_profile on selected results.",
            "Use AnySearch only if the user declines login, two assisted login attempts still fail, or zhihu-mcp remains unavailable: {}".format(anysearch_discovery_command(query)),
        ]
    if backend == "zhihu-k-search":
        if item_type in {"question", "answer", "article"}:
            return ['uv run python main.py detail "{}" -o raw_detail.json'.format(target)]
        query = ids.get("query") or target
        return ['uv run python main.py search "{}" -l 20 -o raw_search.json'.format(query)]
    if backend == "zhihu-mcp":
        if item_type == "question":
            return [
                "MCP tool: get_question_detail(question_id={})".format(ids.get("question_id", "")),
                "MCP tool: get_answer_detail(...) for selected answers",
                "MCP tool: get_comments(url=..., count=...) when comments are needed",
            ]
        if item_type == "answer":
            return [
                "MCP tool: get_answer_detail(question_id={}, answer_id={})".format(ids.get("question_id", ""), ids.get("answer_id", "")),
                "MCP tool: get_comments(url={!r}, count=...)".format(target),
            ]
        if item_type == "article":
            return [
                "MCP tool: get_article_detail(article_id={})".format(ids.get("article_id", "")),
                "MCP tool: get_comments(url={!r}, count=...)".format(target),
            ]
        if item_type == "user":
            return [
                "First run: python skills\\zhihu-public-intel\\scripts\\zhihu_public_intel.py check-runtime",
                "Then verify login with MCP tool: check_login_status() or cookie_status().",
                "MCP tool: user_profile(token={!r})".format(ids.get("user_token", "")),
                "MCP tool: get_activities(user={!r}, count=...)".format(ids.get("user_token", "")),
            ]
        return [
            "First run: python skills\\zhihu-public-intel\\scripts\\zhihu_public_intel.py check-runtime",
            "If needed, run visible login: powershell -ExecutionPolicy Bypass -File .\\skills\\zhihu-public-intel\\scripts\\assist_zhihu_login.ps1",
            "Verify login with MCP tool: check_login_status() or cookie_status().",
            'Then run MCP tool: search_content(keyword={!r}, content_type="all", count=20)'.format(ids.get("query") or target),
        ]
    if backend == "ZhihuApis":
        if item_type == "answer":
            return ["POST /get_answer_all_comment with answer_id={} and local cookies_str".format(ids.get("answer_id", ""))]
        if item_type == "article":
            return ["POST /get_article_all_comment with article_id={} and local cookies_str".format(ids.get("article_id", ""))]
        return ["Use ZhihuApis after resolving answer_id or article_id from search/detail results."]
    return ["Use MediaCrawler Zhihu lane with strict count/depth limits; normalize raw output afterward."]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_records(data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
        return
    if isinstance(data, dict):
        for key in ("items", "results", "data", "list", "answers", "articles", "comments"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return
        yield data


def pick(record: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return value
    return ""


def normalize_item(record: Dict[str, Any], source: str, raw_ref: str = "") -> Dict[str, Any]:
    url = str(pick(record, "url", "link", "href", "target_url"))
    info = inspect_zhihu_url(url) if url else {"type": str(pick(record, "type", "content_type") or "unknown"), "ids": {}}
    ids = info.get("ids") or {}
    title = pick(record, "title", "question_title", "name", "excerpt_title")
    body = pick(record, "body_text", "content", "text", "excerpt", "summary")
    author_value = pick(record, "author", "author_name", "user", "member")
    author: Dict[str, Any]
    if isinstance(author_value, dict):
        author = {
            "name": pick(author_value, "name", "username", "headline"),
            "url": pick(author_value, "url", "user_url", "homepage"),
            "headline": pick(author_value, "headline", "bio", "description"),
        }
    else:
        author = {"name": str(author_value or ""), "url": "", "headline": ""}
    return {
        "source_id": stable_id(url, title, ids.get("answer_id"), ids.get("article_id")),
        "platform": "zhihu",
        "type": info.get("type") or pick(record, "type", "content_type") or "unknown",
        "url": url,
        "title": title,
        "body_text": body,
        "author": author,
        "question_id": ids.get("question_id") or pick(record, "question_id"),
        "answer_id": ids.get("answer_id") or pick(record, "answer_id"),
        "article_id": ids.get("article_id") or pick(record, "article_id"),
        "topics": pick(record, "topics", "tags") or [],
        "counts": {
            "vote": pick(record, "vote_count", "upvote_count", "like_count"),
            "comment": pick(record, "comment_count", "comments_count"),
            "answer": pick(record, "answer_count"),
            "follower": pick(record, "follower_count"),
            "view": pick(record, "view_count"),
        },
        "published_at": pick(record, "published_at", "created_time", "created_at"),
        "updated_at": pick(record, "updated_at", "updated_time"),
        "captured_at": now_iso(),
        "backend": source,
        "raw_ref": raw_ref,
    }


def normalize_comment(record: Dict[str, Any], source: str, item_source_id: str = "", raw_ref: str = "") -> Dict[str, Any]:
    author_value = pick(record, "author", "member", "user")
    if isinstance(author_value, dict):
        author = {"name": pick(author_value, "name", "username"), "url": pick(author_value, "url", "user_url")}
    else:
        author = {"name": str(author_value or ""), "url": ""}
    comment_id = pick(record, "comment_id", "id")
    return {
        "source_id": stable_id(item_source_id, comment_id, pick(record, "content", "text")),
        "item_source_id": item_source_id,
        "url": pick(record, "url", "source_url"),
        "comment_id": comment_id,
        "parent_comment_id": pick(record, "parent_comment_id", "reply_to_id"),
        "author": author,
        "content_text": pick(record, "content_text", "content", "text"),
        "like_count": pick(record, "like_count", "vote_count"),
        "created_at": pick(record, "created_at", "created_time"),
        "captured_at": now_iso(),
        "backend": source,
        "raw_ref": raw_ref,
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_sources_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source_id", "type", "title", "url", "author", "published_at", "comment_count", "vote_count", "backend", "raw_ref"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            counts = row.get("counts") or {}
            author = row.get("author") or {}
            writer.writerow(
                {
                    "source_id": row.get("source_id", ""),
                    "type": row.get("type", ""),
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "author": author.get("name", "") if isinstance(author, dict) else "",
                    "published_at": row.get("published_at", ""),
                    "comment_count": counts.get("comment", "") if isinstance(counts, dict) else "",
                    "vote_count": counts.get("vote", "") if isinstance(counts, dict) else "",
                    "backend": row.get("backend", ""),
                    "raw_ref": row.get("raw_ref", ""),
                }
            )


def cmd_plan(args: argparse.Namespace) -> int:
    print(json.dumps(build_plan(args), ensure_ascii=False, indent=2))
    return 0


def cmd_inspect_url(args: argparse.Namespace) -> int:
    print(json.dumps(inspect_zhihu_url(args.url), ensure_ascii=False, indent=2))
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    print(json.dumps(SCHEMA_SUMMARY, ensure_ascii=False, indent=2))
    return 0


def cmd_auth_guide(args: argparse.Namespace) -> int:
    info = classify_target(args.target) if args.target else {"ids": {"query": ""}}
    needs = split_csv(args.needs)
    paths = runtime_paths(args.runtime_root)
    payload = {
        "target": args.target,
        "needs": needs,
        "runtime_paths": {key: str(value) for key, value in paths.items()},
        "policy": login_wall_policy(args.target or "", info, needs),
        "human_steps": [
            "Run setup_zhihu_mcp.ps1 if check-runtime reports missing runtime files.",
            "Call MCP check_login_status() or cookie_status() before searching.",
            "If logged_in=false, login_verified=false, cookies are missing/stale, or exact-name search returns an auth-looking empty result, run assist_zhihu_login.ps1 immediately.",
            "In the visible browser, the user logs in to Zhihu and completes MFA/CAPTCHA if shown.",
            "The helper saves only Zhihu Playwright cookies to the private runtime cookies.json, refreshes stale cookies after successful login, and prints no cookie values.",
            "Restart Codex if zhihu_mcp was newly registered, then run check_login_status/cookie_status.",
        ],
        "commands": {
            "check_runtime": r"python skills\zhihu-public-intel\scripts\zhihu_public_intel.py check-runtime",
            "setup_runtime": r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1",
            "visible_login": r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1",
            "visible_login_dry_run": r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1 -DryRun",
            "anysearch_discovery": anysearch_discovery_command((info.get("ids") or {}).get("query") or args.target or ""),
        },
        "fallback_gate": [
            "Do not run AnySearch before a visible zhihu-mcp login attempt unless the user explicitly declines login.",
            "AnySearch is allowed only after user decline, two assisted login failures, unavailable MCP runtime, or explicit public-index cross-check.",
            "If AnySearch is used, label results as discovery/snippet evidence, not full Zhihu capture.",
        ],
        "never_do": [
            "Do not paste z_c0, d_c0, cookies, request headers, or browser storage into chat.",
            "Do not bypass CAPTCHA/MFA/login controls.",
            "Do not commit cookies.json, auth.json, .env, storage_state.json, browser profiles, DB files, or logs.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def load_config_safely(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive CLI status.
        return {"_error": str(exc)}


def cmd_check_runtime(args: argparse.Namespace) -> int:
    paths = runtime_paths(args.runtime_root)
    config = load_config_safely(paths["config_json"])
    browser = config.get("browser") if isinstance(config, dict) else {}
    cookie_path = paths["cookies_json"]
    status = {
        "runtime_root": str(paths["runtime_root"]),
        "checkout_exists": paths["checkout_dir"].exists(),
        "venv_python_exists": paths["venv_python"].exists(),
        "mcp_server_exists": paths["mcp_server"].exists(),
        "config_exists": paths["config_json"].exists(),
        "config_path": str(paths["config_json"]),
        "chrome_cookie_extraction": browser.get("chrome_cookie_extraction") if isinstance(browser, dict) else None,
        "headless_default": browser.get("headless") if isinstance(browser, dict) else None,
        "cookies_path": str(cookie_path),
        "cookies_file_exists": cookie_path.exists(),
        "cookies_file_size_bytes": cookie_path.stat().st_size if cookie_path.exists() else 0,
        "profile_dir_exists": paths["profile_dir"].exists(),
        "setup_command": r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1",
        "visible_login_command": r"powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1",
        "notes": [
            "This command checks paths and config only; it does not read or print cookie values.",
            "chrome_cookie_extraction should normally remain false unless the user explicitly approves automatic browser-cookie extraction.",
            "If cookies_file_exists is false or login checks fail, run the visible login helper and let the user complete login in the browser.",
        ],
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    manifest_args = argparse.Namespace(
        target=args.target,
        needs=args.needs,
        scale=args.scale,
        prefer_backend=args.prefer_backend,
    )
    manifest = build_plan(manifest_args)
    manifest["created_at"] = now_iso()
    manifest["limits"] = {"count": args.limit, "depth": args.depth}
    manifest["blockers"] = []
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.md").write_text("# Zhihu Public Intel Summary\n\nPending normalized sources.\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(out_dir), "manifest": str(out_dir / "manifest.json")}, ensure_ascii=False, indent=2))
    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    data = load_json(in_path)
    raw_ref = args.raw_ref or str(in_path)
    records = list(iter_records(data))
    if args.kind == "comments":
        rows = [normalize_comment(record, args.source, item_source_id=args.item_source_id, raw_ref=raw_ref) for record in records]
        count = write_jsonl(Path(args.output_dir) / "comments.jsonl", rows)
        print(json.dumps({"comments": count, "output": str(Path(args.output_dir) / "comments.jsonl")}, ensure_ascii=False, indent=2))
        return 0
    rows = [normalize_item(record, args.source, raw_ref=raw_ref) for record in records]
    out_dir = Path(args.output_dir)
    count = write_jsonl(out_dir / "items.jsonl", rows)
    write_sources_csv(out_dir / "sources.csv", rows)
    print(json.dumps({"items": count, "items_output": str(out_dir / "items.jsonl"), "sources_output": str(out_dir / "sources.csv")}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan and normalize public Zhihu research crawls.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Choose backend and print suggested commands.")
    plan.add_argument("--target", required=True, help="Keyword or Zhihu URL.")
    plan.add_argument("--needs", action="append", help="Comma-separated needs: search,question,answers,article,comments,user,bulk,report.")
    plan.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="small")
    plan.add_argument("--prefer-backend", choices=sorted(BACKENDS), help="Force a backend choice.")
    plan.set_defaults(func=cmd_plan)

    inspect = sub.add_parser("inspect-url", help="Classify a Zhihu URL and extract IDs.")
    inspect.add_argument("url")
    inspect.set_defaults(func=cmd_inspect_url)

    schema = sub.add_parser("schema", help="Print normalized artifact contract.")
    schema.set_defaults(func=cmd_schema)

    auth = sub.add_parser("auth-guide", help="Print safe login-wall recovery and authenticated Zhihu setup guidance.")
    auth.add_argument("--target", default="", help="Keyword or Zhihu URL that hit a login wall.")
    auth.add_argument("--needs", action="append", help="Comma-separated needs that may require logged-in access.")
    auth.add_argument("--runtime-root", default="", help="Override private zhihu-mcp runtime root.")
    auth.set_defaults(func=cmd_auth_guide)

    runtime = sub.add_parser("check-runtime", help="Check private zhihu-mcp runtime paths without reading cookie values.")
    runtime.add_argument("--runtime-root", default="", help="Override private zhihu-mcp runtime root.")
    runtime.set_defaults(func=cmd_check_runtime)

    scaffold = sub.add_parser("scaffold", help="Create an output directory with raw/, manifest.json, and summary.md.")
    scaffold.add_argument("--output-dir", required=True)
    scaffold.add_argument("--target", required=True)
    scaffold.add_argument("--needs", action="append")
    scaffold.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="small")
    scaffold.add_argument("--prefer-backend", choices=sorted(BACKENDS))
    scaffold.add_argument("--limit", type=int, default=20)
    scaffold.add_argument("--depth", default="shallow")
    scaffold.set_defaults(func=cmd_scaffold)

    normalize = sub.add_parser("normalize", help="Normalize a backend JSON capture to JSONL/CSV.")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--source", required=True, choices=sorted(BACKENDS) + ["manual", "anysearch"])
    normalize.add_argument("--output-dir", required=True)
    normalize.add_argument("--kind", choices=["items", "comments"], default="items")
    normalize.add_argument("--item-source-id", default="", help="Parent item source_id when normalizing comments.")
    normalize.add_argument("--raw-ref", default="")
    normalize.set_defaults(func=cmd_normalize)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
