#!/usr/bin/env python3
"""Planning and normalization helpers for public Zhihu research workflows."""

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


SCHEMA_SUMMARY = {
    "raw/": "Untouched backend outputs, screenshots, or API captures.",
    "items.jsonl": "Questions, answers, articles, search results, and public users.",
    "comments.jsonl": "Comments and nested replies.",
    "sources.csv": "Flattened review table.",
    "manifest.json": "Plan, commands, limits, timestamps, and blockers.",
    "summary.md": "Human synthesis grounded in normalized source IDs.",
}


BACKENDS = {
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
        "recommended_needs": ["search", "answers", "report"],
    }


def choose_backend(needs: List[str], scale: str, prefer: Optional[str] = None) -> str:
    normalized = {need.lower().replace("_", "-") for need in needs}
    if prefer:
        return prefer
    if "bulk" in normalized or scale == "large":
        return "MediaCrawler"
    if "nested-comments" in normalized or normalized == {"comments"} or ("comments" in normalized and scale == "deep"):
        return "ZhihuApis"
    if {"comments", "user"} & normalized or "mcp" in normalized:
        return "zhihu-mcp"
    return "zhihu-k-search"


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
        "output_contract": SCHEMA_SUMMARY,
        "guardrails": [
            "Keep cookies.json, auth.json, storage state, .env, and headers local and untracked.",
            "Run a small smoke crawl before scaling.",
            "Do not bypass CAPTCHA automatically.",
            "Keep raw captures local; summarize and cite URLs in reports.",
        ],
    }
    return plan


def backend_reason(backend: str, needs: List[str], scale: str) -> str:
    if backend == "MediaCrawler":
        return "Selected for larger scale or cross-platform public crawling."
    if backend == "ZhihuApis":
        return "Selected because comment completeness or nested comments are the main need."
    if backend == "zhihu-mcp":
        return "Selected for Agent/MCP workflows, comments plus content, or user public profile/activity."
    return "Selected for lightweight public search and question/answer/article detail extraction."


def command_suggestions(backend: str, target: str, info: Dict[str, Any], needs: List[str]) -> List[str]:
    item_type = info.get("type")
    ids = info.get("ids") or {}
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
                "MCP tool: user_profile(token={!r})".format(ids.get("user_token", "")),
                "MCP tool: get_activities(user={!r}, count=...)".format(ids.get("user_token", "")),
            ]
        return ['MCP tool: search_content(keyword={!r}, content_type="all", count=20)'.format(ids.get("query") or target)]
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
