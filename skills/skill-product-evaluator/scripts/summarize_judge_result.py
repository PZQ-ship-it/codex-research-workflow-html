#!/usr/bin/env python3
"""Create a concise Markdown report from suite_judge_result.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def make_report(data: dict, target_skill: str | None = None) -> str:
    target = target_skill or data.get("target_skill") or "target skill"
    lines: list[str] = []
    lines.append(f"# {target} Product Quality Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Overall pass: `{data.get('overall_pass')}`")
    lines.append(f"- Overall score: `{data.get('overall_score')}`")
    lines.append(f"- Product score: `{data.get('product_score')}`")
    lines.append(f"- Process score: `{data.get('process_score')}`")
    lines.append(f"- Benchmark alignment: `{data.get('benchmark_alignment')}`")
    lines.append(f"- Judge confidence: `{data.get('judge_confidence')}`")
    lines.append("")

    lines.append("## Dimension Scores")
    lines.append("")
    lines.append("| Dimension | Score |")
    lines.append("|---|---:|")
    for key, value in (data.get("dimension_scores") or {}).items():
        lines.append(f"| `{key}` | {value} |")
    lines.append("")

    lines.append("## Case Results")
    lines.append("")
    lines.append("| Case | Pass | Product | Process | Overall | Note |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for row in data.get("case_scores") or []:
        note = str(row.get("main_failure_or_note", "")).replace("|", "\\|")
        lines.append(
            f"| `{row.get('case_id')}` | {row.get('pass')} | "
            f"{row.get('product_score')} | {row.get('process_score')} | "
            f"{row.get('overall_score')} | {note} |"
        )
    lines.append("")

    lines.append("## Evidence")
    lines.append("")
    for item in data.get("evidence") or []:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Recommended Fixes")
    lines.append("")
    for idx, item in enumerate(data.get("recommended_fixes") or [], start=1):
        lines.append(f"{idx}. {item}")
    lines.append("")

    failures = data.get("critical_failures") or []
    lines.append("## Critical Failures")
    lines.append("")
    if failures:
        for item in failures:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge-result", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--target-skill", default=None)
    args = parser.parse_args()

    report = make_report(load_json(args.judge_result), args.target_skill)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

