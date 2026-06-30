#!/usr/bin/env python
"""Watch public official recruiting pages for lightweight change signals.

This script intentionally stores metadata, hashes, and keyword hit counts only.
It does not archive raw HTML or full page text.
"""

from __future__ import print_function

import argparse
import csv
import datetime as _dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
import sys
import time

try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse
    from urllib.request import Request, build_opener
except ImportError:  # pragma: no cover - Python 2 fallback is not expected here.
    from urllib2 import HTTPError, URLError, Request, build_opener
    from urlparse import urlparse


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

DEFAULT_SEEDS = os.path.join(SKILL_DIR, "references", "default-seeds.json")
DEFAULT_OUT_DIR = os.path.join(
    "references", "recruiting", "official-career-page-watcher", "runs"
)


class VisibleTextExtractor(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._skip_depth = 0
        self._in_title = False
        self.title_parts = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "noscript") and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._in_title:
            self.title_parts.append(data)
        elif not self._skip_depth:
            self.text_parts.append(data)


def utc_now_iso():
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def decode_bytes(raw, content_type):
    match = re.search(r"charset=([\w.\-]+)", content_type or "", re.I)
    encodings = []
    if match:
        encodings.append(match.group(1).strip())
    encodings.extend(["utf-8", "gb18030", "latin-1"])
    for encoding in encodings:
        try:
            return raw.decode(encoding), encoding
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace"), "utf-8-replace"


def normalize_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text(markup):
    parser = VisibleTextExtractor()
    try:
        parser.feed(markup)
    except Exception:
        # Some recruiting pages contain malformed markup; keep whatever was parsed.
        pass
    title = normalize_text(" ".join(parser.title_parts))
    visible_text = normalize_text(" ".join(parser.text_parts))
    return title, visible_text


def count_keywords(text, keywords):
    lower_text = text.lower()
    hits = {}
    for keyword in keywords:
        keyword = str(keyword).strip()
        if not keyword:
            continue
        count = lower_text.count(keyword.lower())
        if count:
            hits[keyword] = count
    return hits


def content_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_url(url, timeout, max_bytes):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36 "
            "todo-official-career-page-watcher/1.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "close",
    }
    request = Request(url, headers=headers)
    opener = build_opener()
    response = opener.open(request, timeout=timeout)
    raw = response.read(max_bytes + 1)
    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    content_type = response.headers.get("Content-Type", "")
    decoded, encoding = decode_bytes(raw, content_type)
    return {
        "http_status": getattr(response, "status", response.getcode()),
        "final_url": response.geturl(),
        "content_type": content_type,
        "encoding": encoding,
        "truncated": truncated,
        "text": decoded,
    }


def validate_seed(seed):
    required = ["id", "company", "url"]
    missing = [key for key in required if not seed.get(key)]
    if missing:
        raise ValueError("seed missing required keys %s: %r" % (missing, seed))
    parsed = urlparse(seed["url"])
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("seed has invalid URL: %r" % seed["url"])


def load_previous(path):
    if not os.path.exists(path):
        return {}
    try:
        payload = load_json(path)
    except Exception:
        return {}
    return {item.get("seed_id"): item for item in payload.get("results", [])}


def run_watch(args):
    config = load_json(args.seeds)
    global_keywords = config.get("global_keywords", [])
    seeds = config.get("seeds", [])
    if args.limit:
        seeds = seeds[: args.limit]
    for seed in seeds:
        validate_seed(seed)

    if args.validate_only:
        return {
            "run_id": "validate-only",
            "created_at": utc_now_iso(),
            "seed_file": args.seeds,
            "summary": {"total": len(seeds), "validated": len(seeds)},
            "results": [],
        }

    ensure_dir(args.out_dir)
    latest_path = os.path.join(args.out_dir, "latest.json")
    previous = load_previous(latest_path)
    run_id = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []

    for index, seed in enumerate(seeds, 1):
        keywords = list(global_keywords) + list(seed.get("keywords", []))
        result = {
            "seed_id": seed["id"],
            "company": seed["company"],
            "url": seed["url"],
            "page_type": seed.get("page_type", ""),
            "priority": seed.get("priority", ""),
            "tags": seed.get("tags", []),
            "source_note": seed.get("source_note", ""),
            "checked_at": utc_now_iso(),
        }
        try:
            fetched = fetch_url(seed["url"], args.timeout, args.max_bytes)
            title, visible_text = extract_text(fetched["text"])
            normalized = normalize_text(" ".join([title, visible_text]))
            digest = content_hash(normalized)
            keyword_hits = count_keywords(normalized, keywords)
            old = previous.get(seed["id"])
            if old and old.get("content_hash") == digest:
                change_status = "unchanged"
            elif old:
                change_status = "changed"
            else:
                change_status = "new"
            result.update(
                {
                    "status": "ok",
                    "http_status": fetched["http_status"],
                    "final_url": fetched["final_url"],
                    "content_type": fetched["content_type"],
                    "encoding": fetched["encoding"],
                    "truncated": fetched["truncated"],
                    "title": title,
                    "visible_text_chars": len(normalized),
                    "content_hash": digest,
                    "previous_hash": old.get("content_hash") if old else "",
                    "change_status": change_status,
                    "matched_keywords": sorted(keyword_hits.keys()),
                    "keyword_hits": keyword_hits,
                }
            )
        except HTTPError as exc:
            result.update(
                {
                    "status": "http_error",
                    "http_status": exc.code,
                    "error": str(exc),
                    "change_status": "unknown",
                    "matched_keywords": [],
                    "keyword_hits": {},
                }
            )
        except (URLError, TimeoutError, OSError) as exc:
            result.update(
                {
                    "status": "fetch_error",
                    "http_status": "",
                    "error": str(exc),
                    "change_status": "unknown",
                    "matched_keywords": [],
                    "keyword_hits": {},
                }
            )
        results.append(result)
        if args.verbose:
            print(
                "[%d/%d] %s %s %s"
                % (index, len(seeds), result["company"], result["seed_id"], result["status"]),
                flush=True,
            )
        if args.sleep and index < len(seeds):
            time.sleep(args.sleep)

    summary = {
        "total": len(results),
        "ok": sum(1 for item in results if item["status"] == "ok"),
        "http_error": sum(1 for item in results if item["status"] == "http_error"),
        "fetch_error": sum(1 for item in results if item["status"] == "fetch_error"),
        "changed": sum(1 for item in results if item.get("change_status") == "changed"),
        "new": sum(1 for item in results if item.get("change_status") == "new"),
        "unchanged": sum(1 for item in results if item.get("change_status") == "unchanged"),
    }
    payload = {
        "run_id": run_id,
        "created_at": utc_now_iso(),
        "seed_file": args.seeds,
        "config_name": config.get("name", ""),
        "config_updated": config.get("updated", ""),
        "storage_policy": "metadata/hash/keyword counts only; no raw HTML or full page text",
        "summary": summary,
        "results": results,
    }

    run_path = os.path.join(args.out_dir, "%s.json" % run_id)
    write_json(run_path, payload)
    if not args.no_latest:
        write_json(latest_path, payload)
        write_csv(os.path.join(args.out_dir, "latest.csv"), results)
        write_markdown(os.path.join(args.out_dir, "latest.md"), payload)
    return payload


def write_csv(path, results):
    fieldnames = [
        "seed_id",
        "company",
        "status",
        "http_status",
        "change_status",
        "priority",
        "page_type",
        "title",
        "visible_text_chars",
        "matched_keywords",
        "url",
        "final_url",
        "checked_at",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            row = {key: item.get(key, "") for key in fieldnames}
            row["matched_keywords"] = ";".join(item.get("matched_keywords", []))
            writer.writerow(row)


def write_markdown(path, payload):
    lines = [
        "# Official Career Page Watcher Latest Run",
        "",
        "- Run: `%s`" % payload.get("run_id", ""),
        "- Created: `%s`" % payload.get("created_at", ""),
        "- Storage: metadata/hash/keyword counts only; no raw HTML or full page text.",
        "",
        "## Summary",
        "",
    ]
    for key in ["total", "ok", "http_error", "fetch_error", "new", "changed", "unchanged"]:
        lines.append("- `%s`: %s" % (key, payload.get("summary", {}).get(key, 0)))
    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Company | Seed | Status | HTTP | Change | Keywords | Title | URL |",
            "|---|---|---:|---:|---|---|---|---|",
        ]
    )
    for item in payload.get("results", []):
        title = (item.get("title") or "").replace("|", "\\|")
        if len(title) > 80:
            title = title[:77] + "..."
        keywords = ", ".join(item.get("matched_keywords", [])[:8]).replace("|", "\\|")
        url = item.get("url", "")
        lines.append(
            "| {company} | `{seed}` | {status} | {http} | {change} | {keywords} | {title} | <{url}> |".format(
                company=item.get("company", "").replace("|", "\\|"),
                seed=item.get("seed_id", ""),
                status=item.get("status", ""),
                http=item.get("http_status", ""),
                change=item.get("change_status", ""),
                keywords=keywords,
                title=title,
                url=url,
            )
        )
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Watch official public recruiting pages for metadata/hash/keyword signals."
    )
    parser.add_argument("--seeds", default=DEFAULT_SEEDS, help="Path to seeds.json")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Output run directory")
    parser.add_argument("--timeout", type=int, default=8, help="Per-page timeout in seconds")
    parser.add_argument("--max-bytes", type=int, default=500000, help="Max bytes to read per page")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between requests")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N seeds")
    parser.add_argument("--validate-only", action="store_true", help="Validate seed config without fetching")
    parser.add_argument("--no-latest", action="store_true", help="Do not update latest.json/csv/md")
    parser.add_argument("--verbose", action="store_true", help="Print per-seed progress")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = run_watch(args)
    print(json.dumps(payload.get("summary", {}), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
