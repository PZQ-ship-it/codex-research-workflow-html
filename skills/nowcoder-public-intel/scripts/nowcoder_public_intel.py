#!/usr/bin/env python
"""Low-volume public Nowcoder / 牛客 search normalizer.

This script uses public unauthenticated routes only. It never reads cookies,
browser profiles, auth headers, or private storage.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


NOWCODER_SEARCH_API = "https://gw-c.nowcoder.com/api/sparta/pc/search"
NOWCODER_SEARCH_PAGE = "https://www.nowcoder.com/search"
NOWCODER_DISCUSS_URL = "https://www.nowcoder.com/discuss"
NOWCODER_FEED_URL = "https://www.nowcoder.com/feed/main/detail"

TAG_OPTIONS = {
    "面经": {"name": "面经", "id": 818, "count": None},
    "求职进度": {"name": "求职进度", "id": 861, "count": None},
    "内推": {"name": "内推", "id": 823, "count": None},
    "公司评价": {"name": "公司评价", "id": 856, "count": None},
}

JOB_FAMILY_TERMS = {
    "llm": ["大模型", "llm", "aigc", "生成式", "foundation model"],
    "agent-rag": ["agent", "智能体", "rag", "知识库", "检索增强", "tool use"],
    "infra-serving": ["推理", "训练", "serving", "infra", "框架", "加速", "部署"],
    "medical-ai": ["医疗", "医学", "影像", "healthcare", "medical"],
    "algorithm-research": ["算法", "研究员", "research", "科学家"],
}

COMPANY_TERMS = [
    "腾讯",
    "华为",
    "字节",
    "阿里",
    "百度",
    "美团",
    "快手",
    "京东",
    "小米",
    "商汤",
    "鹏城",
    "IDEA",
]

CITY_TERMS = ["深圳", "广州", "香港", "东莞", "珠海", "北京", "上海", "杭州"]
DEGREE_TERMS = ["博士", "博士后", "phd", "校招", "社招", "应届", "0-3", "研究员"]
SALARY_TERMS = ["offer", "总包", "薪资", "base", "股票", "期权", "签字费", "开奖", "年薪", "月薪"]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any, limit: int = 500) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "..."
    return text


def timestamp_to_iso(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number > 10_000_000_000:
        number = number / 1000.0
    try:
        return dt.datetime.fromtimestamp(number, tz=dt.timezone.utc).replace(microsecond=0).isoformat()
    except (OverflowError, OSError, ValueError):
        return str(value)


def infer_terms(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    signal_terms: List[str] = []

    company = ""
    for term in COMPANY_TERMS:
        if term.lower() in lowered:
            company = term
            signal_terms.append(term)
            break

    city = ""
    for term in CITY_TERMS:
        if term.lower() in lowered:
            city = term
            signal_terms.append(term)
            break

    degree = ""
    for term in DEGREE_TERMS:
        if term.lower() in lowered:
            degree = term
            signal_terms.append(term)
            break

    families = []
    for family, terms in JOB_FAMILY_TERMS.items():
        if any(term.lower() in lowered for term in terms):
            families.append(family)
            signal_terms.extend([term for term in terms if term.lower() in lowered])

    salary = any(term.lower() in lowered for term in SALARY_TERMS)
    if salary:
        signal_terms.extend([term for term in SALARY_TERMS if term.lower() in lowered])

    return {
        "company_hint": company,
        "city_hint": city,
        "degree_hint": degree,
        "job_family_hint": ";".join(families),
        "salary_signal": bool(salary),
        "signal_terms": sorted(set(signal_terms)),
    }


def build_search_url(query: str, page: int = 1, search_type: str = "post") -> str:
    params = {"type": search_type, "query": query, "page": str(page)}
    return f"{NOWCODER_SEARCH_PAGE}?{urllib.parse.urlencode(params)}"


def request_json(url: str, payload: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "Codex nowcoder-public-intel/0.1 public-metadata",
            "Accept": "application/json, text/plain, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def public_search(query: str, page: int, tag: str = "", order: str = "") -> Dict[str, Any]:
    tag_list = [TAG_OPTIONS[tag]] if tag in TAG_OPTIONS else []
    payload = {
        "type": "all",
        "query": query,
        "page": page,
        "tag": tag_list,
        "order": order,
        "gioParams": {
            "searchFrom_var": "顶部导航栏",
            "searchEnter_var": "主站",
        },
    }
    return request_json(NOWCODER_SEARCH_API, payload)


def record_url(rc_type: int, data: Dict[str, Any]) -> str:
    if rc_type == 201:
        uuid = data.get("momentData", {}).get("uuid", "")
        return f"{NOWCODER_FEED_URL}/{uuid}" if uuid else ""
    if rc_type == 207:
        cid = data.get("contentData", {}).get("id", "")
        return f"{NOWCODER_DISCUSS_URL}/{cid}" if cid else ""
    return ""


def source_type(rc_type: int) -> str:
    if rc_type == 201:
        return "feed"
    if rc_type == 207:
        return "discuss"
    return "unknown"


def normalize_record(
    raw: Dict[str, Any],
    query: str,
    tag: str,
    order: str,
    page: int,
    collected_at: str,
) -> Optional[Dict[str, Any]]:
    rc_type = int(raw.get("rc_type") or 0)
    data = raw.get("data") or {}
    freq = data.get("frequencyData") or {}

    title = ""
    created_at = ""
    if rc_type == 201:
        moment = data.get("momentData") or {}
        title = clean_text(moment.get("title") or moment.get("content") or "")
        created_at = str(moment.get("createdAt") or "")
    elif rc_type == 207:
        content = data.get("contentData") or {}
        title = clean_text(content.get("title") or content.get("content") or "")
        created_at = str(content.get("createTime") or "")
    else:
        title = clean_text(data.get("title") or data.get("content") or "")

    if not title:
        return None

    user_brief = data.get("userBrief") or {}
    identities = user_brief.get("identityList") or []
    identity = identities[0] if identities else {}
    metadata_text = " ".join(
        [
            query,
            title,
            clean_text(identity.get("companyName", "")),
            clean_text(identity.get("jobName", "")),
        ]
    )
    inferred = infer_terms(metadata_text)

    record = {
        "platform": "nowcoder",
        "collected_at": collected_at,
        "query": query,
        "tag": tag,
        "order": order,
        "page": page,
        "title": title,
        "url": record_url(rc_type, data),
        "snippet": title,
        "source_type": source_type(rc_type),
        "created_at": timestamp_to_iso(created_at),
        "view_count": freq.get("viewCnt", 0),
        "like_count": freq.get("likeCnt", 0),
        "comment_count": freq.get("commentCnt", 0),
        "company_hint": inferred["company_hint"] or clean_text(identity.get("companyName", "")),
        "job_family_hint": inferred["job_family_hint"],
        "degree_hint": inferred["degree_hint"],
        "city_hint": inferred["city_hint"],
        "salary_signal": inferred["salary_signal"],
        "signal_terms": inferred["signal_terms"],
        "confidence": "low",
        "privacy_note": "public metadata only",
    }
    return record


def fallback_record(query: str, tag: str, order: str, page: int, reason: str) -> Dict[str, Any]:
    search_type = "post" if tag in ("面经", "求职进度", "公司评价") else "all"
    url = build_search_url(query, page=page, search_type=search_type)
    inferred = infer_terms(query)
    return {
        "platform": "nowcoder",
        "collected_at": utc_now(),
        "query": query,
        "tag": tag,
        "order": order,
        "page": page,
        "title": f"Manual public search fallback for: {query}",
        "url": url,
        "snippet": f"Public endpoint failed: {reason}. Open this URL manually or use AnySearch/web fallback.",
        "source_type": "search_fallback",
        "created_at": "",
        "view_count": "",
        "like_count": "",
        "comment_count": "",
        "company_hint": inferred["company_hint"],
        "job_family_hint": inferred["job_family_hint"],
        "degree_hint": inferred["degree_hint"],
        "city_hint": inferred["city_hint"],
        "salary_signal": inferred["salary_signal"],
        "signal_terms": inferred["signal_terms"],
        "confidence": "low",
        "privacy_note": "public metadata only; fallback URL, no private access",
    }


def collect_query(query: str, tag: str, order: str, max_pages: int, delay: float) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    collected_at = utc_now()
    for page in range(1, max_pages + 1):
        try:
            data = public_search(query=query, page=page, tag=tag, order=order)
            if data.get("code") not in (0, "0", None):
                raise RuntimeError(f"Nowcoder returned code={data.get('code')} msg={data.get('msg')}")
            records = ((data.get("data") or {}).get("records")) or []
            for raw in records:
                norm = normalize_record(raw, query=query, tag=tag, order=order, page=page, collected_at=collected_at)
                if norm:
                    out.append(norm)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            out.append(fallback_record(query, tag, order, page, str(exc)))
            break
        if delay and page < max_pages:
            time.sleep(delay)
    return out


def write_records(records: Iterable[Dict[str, Any]], output: str, fmt: str) -> None:
    rows = list(records)
    if not output or output == "-":
        if fmt == "json":
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                print(json.dumps(row, ensure_ascii=False))
        return

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        fields = list(SCHEMA.keys())
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                row = dict(row)
                row["signal_terms"] = ";".join(row.get("signal_terms") or [])
                writer.writerow(row)
    elif fmt == "json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


SCHEMA = {
    "platform": "always nowcoder",
    "collected_at": "UTC ISO timestamp",
    "query": "query string",
    "tag": "tag filter",
    "order": "order filter",
    "page": "page number",
    "title": "public title",
    "url": "public source URL",
    "snippet": "short public snippet",
    "source_type": "feed/discuss/search_fallback/unknown",
    "created_at": "source timestamp if available",
    "view_count": "public view count",
    "like_count": "public like count",
    "comment_count": "public comment count",
    "company_hint": "company hint",
    "job_family_hint": "job family hint",
    "degree_hint": "degree/seniority hint",
    "city_hint": "city hint",
    "salary_signal": "whether offer/salary terms matched",
    "signal_terms": "matched terms",
    "confidence": "low/medium/high",
    "privacy_note": "privacy handling note",
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public Nowcoder metadata.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--tag", default="", choices=["", *TAG_OPTIONS.keys()])
        p.add_argument("--order", default="", choices=["", "create"])
        p.add_argument("--max-pages", type=int, default=1)
        p.add_argument("--max-results", type=int, default=25)
        p.add_argument("--delay", type=float, default=1.0)
        p.add_argument("--output", default="-")
        p.add_argument("--format", default="jsonl", choices=["jsonl", "json", "csv"])

    p_search = sub.add_parser("search", help="Search one query.")
    p_search.add_argument("--query", required=True)
    add_common(p_search)

    p_batch = sub.add_parser("batch-search", help="Search multiple queries.")
    p_batch.add_argument("--query", action="append", required=True)
    add_common(p_batch)

    p_norm = sub.add_parser("normalize-file", help="Normalize simple title/url/snippet JSONL or JSON records.")
    p_norm.add_argument("--input", required=True)
    p_norm.add_argument("--output", default="-")
    p_norm.add_argument("--format", default="jsonl", choices=["jsonl", "json", "csv"])

    p_plan = sub.add_parser("plan", help="Print safe public search URLs for manual review.")
    p_plan.add_argument("--query", action="append", required=True)
    p_plan.add_argument("--tag", default="", choices=["", *TAG_OPTIONS.keys()])
    p_plan.add_argument("--pages", type=int, default=1)

    sub.add_parser("schema", help="Print normalized output schema.")
    return parser.parse_args(argv)


def load_records(path: str) -> List[Dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8-sig")
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        data = json.loads(stripped)
        return [dict(x) for x in data]
    rows = []
    for line in stripped.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def normalize_external(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    collected_at = utc_now()
    out = []
    for row in records:
        query = str(row.get("query") or "")
        title = clean_text(row.get("title") or row.get("name") or "")
        snippet = clean_text(row.get("snippet") or row.get("summary") or title)
        url = str(row.get("url") or row.get("link") or "")
        inferred = infer_terms(" ".join([query, title, snippet]))
        out.append(
            {
                "platform": "nowcoder",
                "collected_at": collected_at,
                "query": query,
                "tag": str(row.get("tag") or ""),
                "order": str(row.get("order") or ""),
                "page": row.get("page") or "",
                "title": title,
                "url": url,
                "snippet": snippet,
                "source_type": row.get("source_type") or "unknown",
                "created_at": row.get("created_at") or row.get("time") or "",
                "view_count": row.get("view_count") or "",
                "like_count": row.get("like_count") or "",
                "comment_count": row.get("comment_count") or "",
                "company_hint": row.get("company_hint") or inferred["company_hint"],
                "job_family_hint": row.get("job_family_hint") or inferred["job_family_hint"],
                "degree_hint": row.get("degree_hint") or inferred["degree_hint"],
                "city_hint": row.get("city_hint") or inferred["city_hint"],
                "salary_signal": row.get("salary_signal") if "salary_signal" in row else inferred["salary_signal"],
                "signal_terms": row.get("signal_terms") or inferred["signal_terms"],
                "confidence": row.get("confidence") or "low",
                "privacy_note": row.get("privacy_note") or "public metadata only",
            }
        )
    return out


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.cmd == "schema":
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "plan":
        for query in args.query:
            for page in range(1, args.pages + 1):
                print(build_search_url(query, page=page, search_type="post"))
        return 0
    if args.cmd == "search":
        records = collect_query(args.query, args.tag, args.order, max(1, args.max_pages), args.delay)
        records = records[: max(1, args.max_results)]
        write_records(records, args.output, args.format)
        return 0
    if args.cmd == "batch-search":
        records: List[Dict[str, Any]] = []
        for query in args.query:
            found = collect_query(query, args.tag, args.order, max(1, args.max_pages), args.delay)
            records.extend(found[: max(1, args.max_results)])
        write_records(records, args.output, args.format)
        return 0
    if args.cmd == "normalize-file":
        rows = normalize_external(load_records(args.input))
        write_records(rows, args.output, args.format)
        return 0
    raise ValueError(args.cmd)


if __name__ == "__main__":
    sys.exit(main())
