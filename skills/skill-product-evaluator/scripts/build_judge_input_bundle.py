#!/usr/bin/env python3
"""Build a sanitized judge input bundle for skill product evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|cookie)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]+"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: m.group(1) + "[REDACTED]", redacted)
    return redacted


def clip(text: str, limit: int) -> str:
    text = redact(text.strip())
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[excerpt truncated]"


def add_fenced(lines: list[str], info: str, text: str) -> None:
    lines.append(f"```{info}")
    lines.append(text.rstrip())
    lines.append("```")


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def case_folder(eval_dir: Path, row: dict[str, str]) -> Path:
    run_source = row.get("run_source", "")
    if run_source == "existing_final":
        return eval_dir / "artifacts" / "final"
    if run_source == "new_product_run":
        return eval_dir / "artifacts" / "product-final"
    if run_source == "manual_artifact":
        return eval_dir / "artifacts" / "manual"
    return eval_dir / "artifacts" / "product-final"


def maybe_add_file(lines: list[str], heading: str, path: Path, info: str, limit: int) -> None:
    lines.append(f"### {heading}")
    if path.exists():
        add_fenced(lines, info, clip(read_text(path), limit))
    else:
        lines.append("MISSING")


def build_bundle(eval_dir: Path, cases_path: Path, out_path: Path, excerpt_chars: int) -> None:
    lines: list[str] = []
    target_skill = eval_dir.name
    lines.append(f"# Judge Input Bundle - {target_skill}")
    lines.append("")
    lines.append(f"- target_skill: {target_skill}")
    lines.append("- purpose: benchmark-driven product-quality judging")
    lines.append("")

    lines.append("## Validation Evidence")
    validation_dir = eval_dir / "artifacts" / "validation"
    if validation_dir.exists():
        for path in sorted(validation_dir.glob("*.txt")):
            maybe_add_file(lines, path.name, path, "text", excerpt_chars)
    else:
        lines.append("No validation directory found.")
    lines.append("")

    sources_path = eval_dir / "benchmarks" / "sources.md"
    lines.append("## Benchmark Sources")
    if sources_path.exists():
        add_fenced(lines, "markdown", clip(read_text(sources_path), excerpt_chars * 2))
    else:
        lines.append("MISSING benchmarks/sources.md")

    rows = load_cases(cases_path)
    for row in rows:
        case_id = row.get("id", "").strip()
        if not case_id:
            continue
        folder = case_folder(eval_dir, row)
        last = folder / f"{case_id}.last.md"
        jsonl = folder / f"{case_id}.jsonl"
        stderr = folder / f"{case_id}.stderr.txt"
        style = folder / f"{case_id}.style.json"

        lines.append("")
        lines.append(f"## Case: {case_id}")
        for key in [
            "should_trigger",
            "expected_behavior",
            "expected_artifacts",
            "benchmark_sources",
            "judge_focus",
            "run_source",
            "notes",
        ]:
            lines.append(f"- {key}: {row.get(key, '')}")
        lines.append(f"- artifact_last: {last}")
        if jsonl.exists():
            lines.append(f"- trace_jsonl_bytes: {jsonl.stat().st_size}")
        if stderr.exists():
            lines.append(f"- stderr_bytes: {stderr.stat().st_size}")
        if style.exists():
            lines.append("- prior_behavior_style_json:")
            try:
                parsed = json.loads(read_text(style))
                add_fenced(lines, "json", json.dumps(parsed, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                add_fenced(lines, "json", clip(read_text(style), excerpt_chars))
        lines.append("- artifact_excerpt:")
        if last.exists():
            add_fenced(lines, "markdown", clip(read_text(last), excerpt_chars))
        else:
            lines.append("MISSING")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-dir", required=True, type=Path)
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--excerpt-chars", type=int, default=2400)
    args = parser.parse_args()

    eval_dir = args.eval_dir
    cases = args.cases or eval_dir / "product_cases.csv"
    out = args.out or eval_dir / "artifacts" / "judge" / "judge_input_bundle.md"

    if not eval_dir.exists():
        raise SystemExit(f"eval dir not found: {eval_dir}")
    if not cases.exists():
        raise SystemExit(f"case pack not found: {cases}")
    build_bundle(eval_dir, cases, out, args.excerpt_chars)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

