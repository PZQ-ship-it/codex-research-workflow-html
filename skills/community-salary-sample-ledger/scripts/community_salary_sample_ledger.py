#!/usr/bin/env python3
"""Manage anonymized community salary / offer-signal ledgers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


COLUMNS = [
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

ALLOWED_CONFIDENCE = {"high", "medium", "low", ""}
ALLOWED_SALARY_PERIOD = {"monthly", "annual_base", "total_comp", "range", "unknown", "not_salary", ""}
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    out = {col: str(row.get(col, "") or "").strip() for col in COLUMNS}
    if not out["collected_at"]:
        out["collected_at"] = utc_now()
    if not out["sample_year"]:
        out["sample_year"] = "unknown"
    if not out["city"]:
        out["city"] = "unknown"
    if not out["region"]:
        out["region"] = infer_region(out["city"])
    if not out["degree"]:
        out["degree"] = "unknown"
    if not out["entry_type"]:
        out["entry_type"] = "unknown"
    if not out["salary_period"]:
        out["salary_period"] = "unknown"
    if not out["currency"]:
        out["currency"] = "CNY"
    if not out["pre_tax_or_after_tax"]:
        out["pre_tax_or_after_tax"] = "unknown"
    if not out["confidence"]:
        out["confidence"] = "low"
    if not out["sample_id"]:
        out["sample_id"] = stable_id(out)
    return out


def read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [normalize_row(row) for row in reader]


def write_rows(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(normalize_row(row))


def validate_rows(rows: List[Dict[str, str]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    seen = set()
    for idx, row in enumerate(rows, start=2):
        sid = row.get("sample_id", "")
        if sid in seen:
            warnings.append(f"row {idx}: duplicate sample_id {sid}")
        seen.add(sid)
        for field in ["company", "job_family", "source_platform", "source_type"]:
            if not row.get(field):
                errors.append(f"row {idx}: missing {field}")
        if row.get("confidence") not in ALLOWED_CONFIDENCE:
            errors.append(f"row {idx}: invalid confidence {row.get('confidence')!r}")
        if row.get("salary_period") not in ALLOWED_SALARY_PERIOD:
            errors.append(f"row {idx}: invalid salary_period {row.get('salary_period')!r}")
        if row.get("confidence") == "high" and row.get("source_type") not in {"official_jd", "salary_site"}:
            warnings.append(f"row {idx}: high confidence on non-official/non-salary-site source")
        if row.get("salary_period") != "not_salary" and not any(row.get(k) for k in ["monthly_base", "annual_base", "bonus", "stock_or_options", "signing_bonus", "subsidy", "total_comp"]):
            warnings.append(f"row {idx}: salary_period is {row.get('salary_period')} but no salary component is filled")
        if row.get("degree") != "博士" and "博士" not in row.get("entry_type", ""):
            warnings.append(f"row {idx}: not a PhD-specific row; use only as low-confidence context")
    return errors, warnings


def print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_schema(_args) -> None:
    print_json({"columns": COLUMNS, "allowed_confidence": sorted(ALLOWED_CONFIDENCE), "allowed_salary_period": sorted(ALLOWED_SALARY_PERIOD)})


def cmd_init(args) -> None:
    path = Path(args.output)
    if path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing ledger: {path}. Use --force if intended.")
    write_rows(path, [])
    print_json({"ok": True, "output": str(path), "columns": len(COLUMNS)})


def row_from_args(args) -> Dict[str, str]:
    mapping = {}
    for col in COLUMNS:
        attr = col.replace("_", "-")
        value = getattr(args, col, None)
        if value is not None:
            mapping[col] = value
    return normalize_row(mapping)


def cmd_append(args) -> None:
    path = Path(args.ledger)
    rows = read_rows(path)
    row = row_from_args(args)
    rows.append(row)
    write_rows(path, rows)
    errors, warnings = validate_rows(rows)
    print_json({"ok": not errors, "ledger": str(path), "appended": row["sample_id"], "rows": len(rows), "errors": errors, "warnings": warnings[-5:]})


def cmd_validate(args) -> None:
    path = Path(args.ledger)
    rows = read_rows(path)
    errors, warnings = validate_rows(rows)
    print_json({"ok": not errors, "ledger": str(path), "rows": len(rows), "errors": errors, "warnings": warnings})
    if errors:
        raise SystemExit(1)


def split_ranks(value: str) -> List[str]:
    if not value:
        return ["unmapped"]
    parts = []
    for chunk in value.replace(",", ";").replace("|", ";").split(";"):
        c = chunk.strip()
        if c:
            parts.append(c)
    return parts or ["unmapped"]


def cmd_summarize(args) -> None:
    rows = read_rows(Path(args.ledger))
    summary = {
        "rows": len(rows),
        "by_confidence": Counter(r["confidence"] for r in rows),
        "by_platform": Counter(r["source_platform"] for r in rows),
        "by_region": Counter(r["region"] for r in rows),
        "by_degree": Counter(r["degree"] for r in rows),
        "by_job_family": Counter(r["job_family"] for r in rows),
        "by_direction_rank": Counter(rank for r in rows for rank in split_ranks(r.get("matched_direction_ranks", ""))),
        "phd_rows": sum(1 for r in rows if r["degree"] == "博士" or "博士" in r["entry_type"]),
    }
    print_json(summary)


def cmd_export_matrix(args) -> None:
    rows = read_rows(Path(args.ledger))
    grouped = defaultdict(list)
    for row in rows:
        for rank in split_ranks(row.get("matched_direction_ranks", "")):
            grouped[(rank, row.get("matched_direction_names", ""))].append(row)
    matrix_cols = [
        "direction_rank",
        "direction_names",
        "sample_count",
        "phd_sample_count",
        "companies",
        "regions",
        "job_families",
        "platforms",
        "salary_signals",
        "confidence_mix",
        "risk_notes",
    ]
    out_rows = []
    for (rank, names), items in sorted(grouped.items(), key=lambda kv: kv[0][0]):
        salary_bits = []
        for r in items:
            bit = r.get("total_comp") or r.get("annual_base") or r.get("monthly_base") or r.get("salary_period")
            if bit and bit not in {"unknown", "not_salary"}:
                salary_bits.append(f"{r.get('company')} {r.get('city')} {bit}")
        risk_notes = []
        if not any(r["degree"] == "博士" or "博士" in r["entry_type"] for r in items):
            risk_notes.append("no PhD-specific samples")
        if not any(r["region"] in {"深圳", "大湾区", "香港"} for r in items):
            risk_notes.append("no Shenzhen/GBA samples")
        if all(r["confidence"] == "low" for r in items):
            risk_notes.append("all low confidence")
        out_rows.append({
            "direction_rank": rank,
            "direction_names": names,
            "sample_count": str(len(items)),
            "phd_sample_count": str(sum(1 for r in items if r["degree"] == "博士" or "博士" in r["entry_type"])),
            "companies": "; ".join(sorted({r["company"] for r in items if r["company"]})),
            "regions": "; ".join(sorted({r["region"] for r in items if r["region"]})),
            "job_families": "; ".join(sorted({r["job_family"] for r in items if r["job_family"]})),
            "platforms": "; ".join(sorted({r["source_platform"] for r in items if r["source_platform"]})),
            "salary_signals": " | ".join(salary_bits[:8]),
            "confidence_mix": "; ".join(f"{k}:{v}" for k, v in sorted(Counter(r["confidence"] for r in items).items())),
            "risk_notes": "; ".join(risk_notes),
        })
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=matrix_cols)
        writer.writeheader()
        writer.writerows(out_rows)
    print_json({"ok": True, "output": str(out), "rows": len(out_rows)})


def add_row_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ledger", required=True)
    for col in COLUMNS:
        if col in {"sample_id", "collected_at"}:
            parser.add_argument(f"--{col.replace('_', '-')}")
        else:
            parser.add_argument(f"--{col.replace('_', '-')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema").set_defaults(func=cmd_schema)
    p_init = sub.add_parser("init")
    p_init.add_argument("--output", required=True)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)
    p_append = sub.add_parser("append")
    add_row_args(p_append)
    p_append.set_defaults(func=cmd_append)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--ledger", required=True)
    p_validate.set_defaults(func=cmd_validate)
    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("--ledger", required=True)
    p_sum.set_defaults(func=cmd_summarize)
    p_matrix = sub.add_parser("export-matrix")
    p_matrix.add_argument("--ledger", required=True)
    p_matrix.add_argument("--output", required=True)
    p_matrix.set_defaults(func=cmd_export_matrix)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
