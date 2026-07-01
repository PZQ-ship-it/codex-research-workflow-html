#!/usr/bin/env python3
"""Prepare and validate redacted OfferShow manual review rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REVIEW_COLUMNS = [
    "selected",
    "review_id",
    "snapshot_file",
    "candidate_id",
    "visible_hint",
    "human_summary",
    "sample_year",
    "company",
    "city",
    "job_family",
    "job_title",
    "degree",
    "entry_type",
    "experience_years",
    "level",
    "salary_period",
    "monthly_base",
    "annual_base",
    "bonus",
    "stock_or_options",
    "signing_bonus",
    "subsidy",
    "total_comp",
    "currency",
    "pre_tax_or_after_tax",
    "source_date",
    "confidence",
    "uncertainty_notes",
    "matched_direction_ranks",
    "matched_direction_names",
    "skill_requirements",
    "ra_transfer_assets",
    "career_value_note",
    "notes",
]

LEDGER_COLUMNS = [
    "sample_id",
    "collected_at",
    "sample_year",
    "company",
    "city",
    "region",
    "job_family",
    "job_title",
    "degree",
    "entry_type",
    "experience_years",
    "level",
    "salary_period",
    "monthly_base",
    "annual_base",
    "bonus",
    "stock_or_options",
    "signing_bonus",
    "subsidy",
    "total_comp",
    "currency",
    "pre_tax_or_after_tax",
    "source_platform",
    "source_type",
    "source_url",
    "source_date",
    "quote_or_summary",
    "confidence",
    "uncertainty_notes",
    "matched_direction_ranks",
    "matched_direction_names",
    "skill_requirements",
    "ra_transfer_assets",
    "career_value_note",
    "notes",
]

REGION_BY_CITY = {
    "深圳": "深圳",
    "广州": "大湾区",
    "东莞": "大湾区",
    "珠海": "大湾区",
    "佛山": "大湾区",
    "香港": "香港",
    "北京": "北京",
    "上海": "上海",
    "杭州": "杭州",
}

ALLOWED_CONFIDENCE = {"low", "medium"}
ALLOWED_SALARY_PERIOD = {"monthly", "annual_base", "total_comp", "range", "unknown", "not_salary", ""}
PRIVATE_MARKERS = [
    "cookie",
    "token",
    "authorization",
    "localstorage",
    "phone",
    "手机号",
    "微信",
    "weChat",
    "qq",
    "邮箱",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def read_csv(path: Path, columns: List[str]) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({col: str(row.get(col, "") or "").strip() for col in columns})
        return rows


def write_csv(path: Path, rows: Iterable[Dict[str, str]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: str(row.get(col, "") or "").strip() for col in columns})


def infer_region(city: str) -> str:
    city = (city or "").strip()
    if not city or city.lower() == "unknown":
        return "unknown"
    for key, region in REGION_BY_CITY.items():
        if key in city:
            return region
    return "其他中国大陆"


def stable_id(row: Dict[str, str]) -> str:
    seed = "|".join(row.get(k, "") for k in [
        "sample_year",
        "company",
        "city",
        "job_family",
        "degree",
        "entry_type",
        "source_platform",
        "source_url",
        "quote_or_summary",
    ])
    return "cssl-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def stable_review_id(snapshot_file: str, candidate_id: str, visible_hint: str) -> str:
    seed = f"{snapshot_file}|{candidate_id}|{visible_hint[:160]}"
    return "osr-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def is_true(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "selected", "x"}


def is_snapshot(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".json" and any(
        marker in path.name for marker in ["export-visible", "inspect", "record", "sample-visible"]
    )


def load_snapshot(path: Path) -> Dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def row_from_candidate(snapshot_path: Path, data: Dict, candidate: Dict) -> Dict[str, str]:
    inferred = candidate.get("inferred") or {}
    visible_hint = str(candidate.get("visible_hint") or "").replace("\r", " ").replace("\n", " ").strip()
    candidate_id = str(candidate.get("candidate_id") or "")
    return {
        "selected": "",
        "review_id": stable_review_id(snapshot_path.name, candidate_id, visible_hint),
        "snapshot_file": str(snapshot_path),
        "candidate_id": candidate_id,
        "visible_hint": visible_hint,
        "human_summary": "",
        "sample_year": "unknown",
        "company": inferred.get("company", ""),
        "city": inferred.get("city", ""),
        "job_family": inferred.get("job_family", ""),
        "job_title": "",
        "degree": inferred.get("degree", ""),
        "entry_type": "unknown",
        "experience_years": "",
        "level": "",
        "salary_period": inferred.get("salary_period", "unknown"),
        "monthly_base": "",
        "annual_base": "",
        "bonus": "",
        "stock_or_options": "",
        "signing_bonus": "",
        "subsidy": "",
        "total_comp": inferred.get("salary_signal", ""),
        "currency": "CNY",
        "pre_tax_or_after_tax": "unknown",
        "source_date": str(data.get("collected_at", ""))[:10],
        "confidence": "low",
        "uncertainty_notes": "OfferShow visible-page candidate; human review and cross-check required.",
        "matched_direction_ranks": "",
        "matched_direction_names": "",
        "skill_requirements": "",
        "ra_transfer_assets": "",
        "career_value_note": "",
        "notes": f"query={data.get('query', '')}".strip(),
    }


def iter_snapshot_rows(snapshot_path: Path) -> List[Dict[str, str]]:
    data = load_snapshot(snapshot_path)
    candidates = data.get("candidates") or []
    if not isinstance(candidates, list):
        return []
    return [row_from_candidate(snapshot_path, data, c) for c in candidates if isinstance(c, dict)]


def cmd_inventory(args) -> None:
    snapshot_dir = Path(args.snapshot_dir)
    files = sorted([p for p in snapshot_dir.glob("*.json") if is_snapshot(p)], key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for path in files[: args.limit]:
        data = load_snapshot(path)
        items.append({
            "file": str(path),
            "label": data.get("label", ""),
            "collected_at": data.get("collected_at", ""),
            "title": data.get("title", ""),
            "url": data.get("url", ""),
            "candidate_count": len(data.get("candidates") or []),
            "has_text_excerpt": bool(data.get("text_excerpt")),
        })
    print_json({"ok": True, "snapshot_dir": str(snapshot_dir), "count": len(items), "items": items})


def cmd_new_review(args) -> None:
    rows: List[Dict[str, str]] = []
    for raw in args.snapshot or []:
        rows.extend(iter_snapshot_rows(Path(raw)))
    if not rows and args.snapshot_dir:
        files = sorted([p for p in Path(args.snapshot_dir).glob("*.json") if is_snapshot(p)], key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files[: args.limit]:
            rows.extend(iter_snapshot_rows(path))
    if args.empty:
        rows = []
    output = Path(args.output)
    write_csv(output, rows[: args.max_rows], REVIEW_COLUMNS)
    print_json({"ok": True, "output": str(output), "rows": min(len(rows), args.max_rows), "columns": REVIEW_COLUMNS})


def validate_review_rows(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for idx, row in enumerate(rows, start=2):
        selected = is_true(row.get("selected", ""))
        text_blob = " ".join(row.values()).lower()
        for marker in PRIVATE_MARKERS:
            if marker.lower() in text_blob:
                warnings.append(f"row {idx}: possible private marker {marker!r}; verify the row is redacted")
        if not selected:
            continue
        for field in ["human_summary", "company", "job_family", "salary_period", "confidence"]:
            if not row.get(field):
                errors.append(f"row {idx}: selected row missing {field}")
        if row.get("confidence") not in ALLOWED_CONFIDENCE:
            errors.append(f"row {idx}: OfferShow manual rows allow only low/medium confidence, got {row.get('confidence')!r}")
        if row.get("salary_period") not in ALLOWED_SALARY_PERIOD:
            errors.append(f"row {idx}: invalid salary_period {row.get('salary_period')!r}")
        if not any(row.get(k) for k in ["monthly_base", "annual_base", "bonus", "stock_or_options", "signing_bonus", "subsidy", "total_comp"]):
            warnings.append(f"row {idx}: selected salary row has no salary component; keep salary_period=unknown/not_salary if intentional")
        if len(row.get("human_summary", "")) > 420:
            warnings.append(f"row {idx}: human_summary is long; keep only a short summary, not raw platform text")
    return {"errors": errors, "warnings": warnings}


def cmd_validate_review(args) -> None:
    rows = read_csv(Path(args.review), REVIEW_COLUMNS)
    result = validate_review_rows(rows)
    result.update({"ok": not result["errors"], "review": args.review, "rows": len(rows), "selected_rows": sum(1 for r in rows if is_true(r.get("selected", "")))})
    print_json(result)
    if result["errors"]:
        raise SystemExit(1)


def ledger_row_from_review(row: Dict[str, str], source_url: str) -> Dict[str, str]:
    out = {col: "" for col in LEDGER_COLUMNS}
    out.update({
        "collected_at": utc_now(),
        "sample_year": row.get("sample_year") or "unknown",
        "company": row.get("company", ""),
        "city": row.get("city") or "unknown",
        "region": infer_region(row.get("city", "")),
        "job_family": row.get("job_family", ""),
        "job_title": row.get("job_title", ""),
        "degree": row.get("degree") or "unknown",
        "entry_type": row.get("entry_type") or "unknown",
        "experience_years": row.get("experience_years", ""),
        "level": row.get("level", ""),
        "salary_period": row.get("salary_period") or "unknown",
        "monthly_base": row.get("monthly_base", ""),
        "annual_base": row.get("annual_base", ""),
        "bonus": row.get("bonus", ""),
        "stock_or_options": row.get("stock_or_options", ""),
        "signing_bonus": row.get("signing_bonus", ""),
        "subsidy": row.get("subsidy", ""),
        "total_comp": row.get("total_comp", ""),
        "currency": row.get("currency") or "CNY",
        "pre_tax_or_after_tax": row.get("pre_tax_or_after_tax") or "unknown",
        "source_platform": "Offershow",
        "source_type": "manual_logged_in_summary",
        "source_url": source_url,
        "source_date": row.get("source_date", ""),
        "quote_or_summary": row.get("human_summary", ""),
        "confidence": row.get("confidence") or "low",
        "uncertainty_notes": row.get("uncertainty_notes", ""),
        "matched_direction_ranks": row.get("matched_direction_ranks", ""),
        "matched_direction_names": row.get("matched_direction_names", ""),
        "skill_requirements": row.get("skill_requirements", ""),
        "ra_transfer_assets": row.get("ra_transfer_assets", ""),
        "career_value_note": row.get("career_value_note", ""),
        "notes": row.get("notes", ""),
    })
    out["sample_id"] = stable_id(out)
    return out


def cmd_append_ledger(args) -> None:
    review_rows = read_csv(Path(args.review), REVIEW_COLUMNS)
    validation = validate_review_rows(review_rows)
    if validation["errors"] and not args.force:
        print_json({"ok": False, "errors": validation["errors"], "warnings": validation["warnings"], "hint": "Fix the review CSV or pass --force after manual audit."})
        raise SystemExit(1)
    selected = [r for r in review_rows if is_true(r.get("selected", ""))]
    append_rows = [ledger_row_from_review(r, args.source_url) for r in selected]
    ledger = Path(args.ledger)
    existing = read_csv(ledger, LEDGER_COLUMNS)
    existing_ids = {r.get("sample_id", "") for r in existing}
    deduped = [r for r in append_rows if r.get("sample_id") not in existing_ids]
    if args.dry_run:
        print_json({"ok": True, "dry_run": True, "selected": len(selected), "would_append": len(deduped), "warnings": validation["warnings"], "sample_ids": [r["sample_id"] for r in deduped]})
        return
    write_csv(ledger, existing + deduped, LEDGER_COLUMNS)
    print_json({"ok": True, "ledger": str(ledger), "selected": len(selected), "appended": len(deduped), "skipped_duplicates": len(append_rows) - len(deduped), "warnings": validation["warnings"][-8:]})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_inventory = sub.add_parser("inventory", help="List safe snapshot metadata without printing text excerpts.")
    p_inventory.add_argument("--snapshot-dir", required=True)
    p_inventory.add_argument("--limit", type=int, default=20)
    p_inventory.set_defaults(func=cmd_inventory)

    p_review = sub.add_parser("new-review", help="Create a human review CSV from export-visible/inspect snapshots.")
    p_review.add_argument("--snapshot", action="append", help="Snapshot JSON to convert; can be repeated.")
    p_review.add_argument("--snapshot-dir", help="Use recent snapshots from this directory.")
    p_review.add_argument("--output", required=True)
    p_review.add_argument("--limit", type=int, default=3, help="Number of recent snapshots when --snapshot-dir is used.")
    p_review.add_argument("--max-rows", type=int, default=120)
    p_review.add_argument("--empty", action="store_true", help="Create only the CSV header.")
    p_review.set_defaults(func=cmd_new_review)

    p_validate = sub.add_parser("validate-review", help="Validate selected review rows before ledger append.")
    p_validate.add_argument("--review", required=True)
    p_validate.set_defaults(func=cmd_validate_review)

    p_append = sub.add_parser("append-ledger", help="Append selected, human-reviewed rows to a community salary ledger.")
    p_append.add_argument("--review", required=True)
    p_append.add_argument("--ledger", required=True)
    p_append.add_argument("--source-url", default="https://www.offershow.cn/")
    p_append.add_argument("--dry-run", action="store_true")
    p_append.add_argument("--force", action="store_true")
    p_append.set_defaults(func=cmd_append_ledger)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
