#!/usr/bin/env python3
"""Validate a benchmark-driven skill product eval directory."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_cases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def case_folder(eval_dir: Path, run_source: str) -> Path:
    if run_source == "existing_final":
        return eval_dir / "artifacts" / "final"
    if run_source == "new_product_run":
        return eval_dir / "artifacts" / "product-final"
    if run_source == "manual_artifact":
        return eval_dir / "artifacts" / "manual"
    return eval_dir / "artifacts" / "product-final"


def validate(eval_dir: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        eval_dir / "benchmarks" / "sources.md",
        eval_dir / "product_cases.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required file: {path}")

    cases: list[dict[str, str]] = []
    cases_path = eval_dir / "product_cases.csv"
    if cases_path.exists():
        cases = read_cases(cases_path)
        required_columns = {
            "id",
            "should_trigger",
            "prompt",
            "expected_behavior",
            "expected_artifacts",
            "benchmark_sources",
            "judge_focus",
            "run_source",
            "notes",
        }
        actual_columns = set(cases[0].keys()) if cases else set()
        missing_columns = sorted(required_columns - actual_columns)
        if missing_columns:
            errors.append("product_cases.csv missing columns: " + ", ".join(missing_columns))

        for row in cases:
            case_id = row.get("id", "").strip()
            if not case_id:
                errors.append("case with empty id")
                continue
            run_source = row.get("run_source", "").strip()
            if run_source == "not_run":
                warnings.append(f"{case_id}: planned but not run")
                continue
            last = case_folder(eval_dir, run_source) / f"{case_id}.last.md"
            if not last.exists():
                errors.append(f"{case_id}: missing final artifact {last}")

    json_paths = [
        eval_dir / "artifacts" / "judge" / "suite_judge_result.json",
        eval_dir / "product_quality_summary.json",
    ]
    for path in json_paths:
        if path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid json {path}: {exc}")

    validation_dir = eval_dir / "artifacts" / "validation"
    if not validation_dir.exists() or not list(validation_dir.glob("*.txt")):
        warnings.append("no validation logs found under artifacts/validation")

    return {
        "ok": not errors,
        "eval_dir": str(eval_dir),
        "case_count": len(cases),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    result = validate(args.eval_dir)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

