#!/usr/bin/env python3
"""Finalize page-worker deck-build evidence after page jobs have run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def finalize(repo_root: Path, run_dir: Path, generated_pptx: Path | None) -> Path:
    status_data = read_json(run_dir / "page_jobs_status.json")
    jobs = status_data.get("jobs", [])
    counts = Counter(str(job.get("status", "unknown")) for job in jobs)
    manifest_path = run_dir / "deck_build_manifest.json"
    manifest = read_json(manifest_path)
    manifest["updated_utc"] = datetime.now(timezone.utc).isoformat()
    if generated_pptx is not None:
        manifest["generated_pptx_path"] = rel(generated_pptx, repo_root)
    manifest["page_counts"] = {
        "total": len(jobs),
        "queued": counts.get("queued", 0),
        "running": counts.get("running", 0),
        "done": counts.get("done", 0),
        "needs_repair": counts.get("needs_repair", 0),
        "blocked": counts.get("blocked", 0),
        "failed": counts.get("failed", 0),
    }
    manifest["assembly_ready"] = (
        counts.get("queued", 0) == 0
        and counts.get("running", 0) == 0
        and counts.get("blocked", 0) == 0
        and counts.get("failed", 0) == 0
        and counts.get("needs_repair", 0) == 0
        and counts.get("done", 0) == len(jobs)
    )
    write_json(manifest_path, manifest)

    summary_path = run_dir / "assembly_log.md"
    lines = [
        "# Deck Build Assembly Summary",
        "",
        f"- run_id: `{manifest.get('run_id')}`",
        f"- generated_utc: `{datetime.now(timezone.utc).isoformat()}`",
        f"- stage_status: `{manifest.get('stage_status')}`",
        f"- generated_pptx_path: `{manifest.get('generated_pptx_path')}`",
        f"- assembly_ready: `{manifest.get('assembly_ready')}`",
        "",
        "## Page Counts",
        "",
    ]
    for status, count in manifest["page_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Jobs", ""])
    for job in sorted(jobs, key=lambda item: int(item.get("slide_number", 0))):
        lines.append(
            f"- {job.get('slide_number')}: `{job.get('slide_id')}` "
            f"[{job.get('status')}] result={job.get('result_path', '')}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--run-dir", required=True, help="Deck build run directory.")
    parser.add_argument("--generated-pptx", help="Optional assembled PPTX path.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_dir = (repo_root / args.run_dir).resolve() if not Path(args.run_dir).is_absolute() else Path(args.run_dir)
    generated_pptx = None
    if args.generated_pptx:
        generated_pptx = (repo_root / args.generated_pptx).resolve() if not Path(args.generated_pptx).is_absolute() else Path(args.generated_pptx)
    summary_path = finalize(repo_root, run_dir, generated_pptx)
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
