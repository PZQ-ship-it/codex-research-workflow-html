#!/usr/bin/env python3
"""Record one page-worker result in a deck-build run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATUSES = {"done", "needs_repair", "blocked", "failed"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def append_repair(backlog: Path, result: dict[str, Any], result_path: Path, repo_root: Path) -> None:
    status = result["status"]
    if status == "done":
        return
    slide_id = result.get("slide_id", "")
    slide_number = result.get("slide_number", "")
    defects = result.get("known_defects") or []
    notes = result.get("repair_notes") or []
    lines = [
        f"## Slide {slide_number} `{slide_id}`",
        "",
        f"- status: `{status}`",
        f"- result: `{rel(result_path, repo_root)}`",
    ]
    if defects:
        lines.append("- defects:")
        lines.extend(f"  - {item}" for item in defects)
    if notes:
        lines.append("- repair notes:")
        lines.extend(f"  - {item}" for item in notes)
    lines.append("")
    with backlog.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def update_manifest_counts(run_dir: Path) -> None:
    status_data = read_json(run_dir / "page_jobs_status.json")
    jobs = status_data.get("jobs", [])
    counts = Counter(str(job.get("status", "unknown")) for job in jobs)
    manifest_path = run_dir / "deck_build_manifest.json"
    manifest = read_json(manifest_path)
    manifest["updated_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["page_counts"] = {
        "total": len(jobs),
        "queued": counts.get("queued", 0),
        "running": counts.get("running", 0),
        "done": counts.get("done", 0),
        "needs_repair": counts.get("needs_repair", 0),
        "blocked": counts.get("blocked", 0),
        "failed": counts.get("failed", 0),
    }
    write_json(manifest_path, manifest)


def record_result(repo_root: Path, run_dir: Path, result_path: Path) -> None:
    result = read_json(result_path)
    if result.get("schema") != "ppt_page_result.v1":
        raise SystemExit("ERROR: page result schema must be ppt_page_result.v1")
    status = str(result.get("status", "")).lower()
    if status not in VALID_STATUSES:
        raise SystemExit(f"ERROR: unsupported page result status: {status}")

    status_path = run_dir / "page_jobs_status.json"
    status_data = read_json(status_path)
    jobs = status_data.get("jobs", [])
    slide_id = result.get("slide_id")
    matched = False
    for job in jobs:
        if job.get("slide_id") == slide_id:
            job["status"] = status
            job["result_path"] = rel(result_path, repo_root)
            job["updated_utc"] = datetime.now(timezone.utc).isoformat()
            matched = True
            break
    if not matched:
        raise SystemExit(f"ERROR: no matching job found for slide_id {slide_id!r}")

    status_data["updated_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(status_path, status_data)
    append_repair(run_dir / "repair_backlog.md", result, result_path, repo_root)
    update_manifest_counts(run_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--run-dir", required=True, help="Deck build run directory.")
    parser.add_argument("--result", required=True, help="Path to page_result.json.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_dir = (repo_root / args.run_dir).resolve() if not Path(args.run_dir).is_absolute() else Path(args.run_dir)
    result_path = (repo_root / args.result).resolve() if not Path(args.result).is_absolute() else Path(args.result)
    record_result(repo_root, run_dir, result_path)
    print(run_dir / "page_jobs_status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
