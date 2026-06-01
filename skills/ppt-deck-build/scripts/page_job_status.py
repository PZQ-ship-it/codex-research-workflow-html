#!/usr/bin/env python3
"""Summarize page-worker deck-build job status."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def summarize(run_dir: Path) -> dict[str, Any]:
    status_path = run_dir / "page_jobs_status.json"
    data = read_json(status_path)
    jobs = data.get("jobs", [])
    counts = Counter(str(job.get("status", "unknown")) for job in jobs)
    return {
        "run_id": data.get("run_id"),
        "status_path": str(status_path),
        "total": len(jobs),
        "counts": dict(sorted(counts.items())),
        "unfinished": [
            {
                "slide_id": job.get("slide_id"),
                "slide_number": job.get("slide_number"),
                "status": job.get("status"),
                "request_path": job.get("request_path"),
            }
            for job in jobs
            if job.get("status") not in {"done"}
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact text summary.")
    args = parser.parse_args()

    result = summarize(args.run_dir.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"run_id: {result['run_id']}")
        print(f"total: {result['total']}")
        for status, count in result["counts"].items():
            print(f"{status}: {count}")
        if result["unfinished"]:
            print("unfinished:")
            for job in result["unfinished"]:
                print(f"- S{job['slide_number']}: {job['slide_id']} [{job['status']}] {job['request_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
