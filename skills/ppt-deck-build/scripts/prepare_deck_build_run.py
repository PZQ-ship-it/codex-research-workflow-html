#!/usr/bin/env python3
"""Create a resumable page-worker deck-build run from a confirmed work order."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERROR: {message}")


def normalize_run_id(work_order: dict[str, Any]) -> str:
    run_id = str(work_order.get("run_id") or "").strip()
    if run_id:
        return run_id
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def slide_output_dir(run_dir: Path, slide_number: int) -> Path:
    return run_dir / "pages" / f"slide_{slide_number:03d}"


def build_page_request(
    *,
    work_order: dict[str, Any],
    slide: dict[str, Any],
    run_id: str,
    run_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    slide_number = int(slide["slide_number"])
    output_dir = slide_output_dir(run_dir, slide_number)
    request = {
        "schema": "ppt_page_request.v1",
        "run_id": run_id,
        "slide_id": slide["slide_id"],
        "slide_number": slide_number,
        "slide_kind": slide.get("slide_kind", "main"),
        "action_title": slide["action_title"],
        "stage_status": "confirmed",
        "source_indices": slide.get("source_indices", []),
        "claim_indices": slide.get("claim_indices", []),
        "asset_indices": slide.get("asset_indices", []),
        "speaker_note_indices": slide.get("speaker_note_indices", []),
        "qa_backup_indices": slide.get("qa_backup_indices", []),
        "generated_visual_indices": slide.get("generated_visual_indices", []),
        "layout": slide.get("layout", work_order.get("default_layout", {})),
        "allowed_inputs": slide.get("allowed_inputs", work_order.get("allowed_inputs", [])),
        "output_dir": rel(output_dir, repo_root),
        "acceptance": slide.get(
            "acceptance",
            {
                "editable_text": True,
                "grounded_claims": True,
                "layout_plan_followed": True,
                "notes_preserved": True,
            },
        ),
        "forbidden": slide.get(
            "forbidden",
            [
                "invent new claims",
                "change slide order",
                "change slide count",
                "flatten editable content into a screenshot unless approved",
                "scan unrelated source sections",
            ],
        ),
        "known_risks": slide.get("known_risks", []),
    }
    return request


def prepare_run(repo_root: Path, work_order_path: Path, run_dir_arg: Path | None) -> Path:
    work_order = read_json(work_order_path)
    require(work_order.get("schema") == "ppt_deck_build_work_order.v1", "work order schema must be ppt_deck_build_work_order.v1")
    require(str(work_order.get("stage_status", "")).lower() == "confirmed", "work order stage_status must be confirmed before page jobs are prepared")
    slides = work_order.get("slides")
    require(isinstance(slides, list) and slides, "work order must include a non-empty slides list")

    run_id = normalize_run_id(work_order)
    run_dir = run_dir_arg if run_dir_arg else repo_root / "exp" / "ppt_deck_build" / run_id
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    copied_work_order = run_dir / "work_order.json"
    write_json(copied_work_order, work_order)

    jobs = []
    for slide in slides:
        for key in ("slide_id", "slide_number", "action_title"):
            require(key in slide, f"slide item missing required key: {key}")
        slide_number = int(slide["slide_number"])
        output_dir = slide_output_dir(run_dir, slide_number)
        output_dir.mkdir(parents=True, exist_ok=True)
        request = build_page_request(
            work_order=work_order,
            slide=slide,
            run_id=run_id,
            run_dir=run_dir,
            repo_root=repo_root,
        )
        request_path = output_dir / "page_request.json"
        write_json(request_path, request)
        jobs.append(
            {
                "slide_id": request["slide_id"],
                "slide_number": slide_number,
                "slide_kind": request["slide_kind"],
                "status": "queued",
                "request_path": rel(request_path, repo_root),
                "output_dir": rel(output_dir, repo_root),
            }
        )

    page_jobs = {
        "schema": "ppt_page_jobs.v1",
        "run_id": run_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "work_order_path": rel(copied_work_order, repo_root),
        "jobs": sorted(jobs, key=lambda item: int(item["slide_number"])),
    }
    write_json(run_dir / "page_jobs.json", page_jobs)
    write_json(run_dir / "page_jobs_status.json", page_jobs)

    manifest = {
        "schema": "ppt_deck_build_manifest.v1",
        "stage": "deck_build",
        "stage_status": "draft",
        "run_id": run_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "work_order_path": rel(copied_work_order, repo_root),
        "page_jobs_path": rel(run_dir / "page_jobs.json", repo_root),
        "status_path": rel(run_dir / "page_jobs_status.json", repo_root),
        "repair_backlog_path": rel(run_dir / "repair_backlog.md", repo_root),
        "generated_pptx_path": None,
        "page_counts": {
            "total": len(jobs),
            "queued": len(jobs),
            "running": 0,
            "done": 0,
            "needs_repair": 0,
            "blocked": 0,
            "failed": 0,
        },
        "allowed_next_stage": "ppt-render-qa-loop",
    }
    write_json(run_dir / "deck_build_manifest.json", manifest)
    (run_dir / "repair_backlog.md").write_text(f"# Repair Backlog\n\nRun: `{run_id}`\n\n", encoding="utf-8")
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--work-order", required=True, help="Confirmed ppt_deck_build_work_order.v1 JSON.")
    parser.add_argument("--run-dir", help="Optional output run directory.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    work_order_path = (repo_root / args.work_order).resolve() if not Path(args.work_order).is_absolute() else Path(args.work_order)
    run_dir_arg = None
    if args.run_dir:
        run_dir_arg = (repo_root / args.run_dir).resolve() if not Path(args.run_dir).is_absolute() else Path(args.run_dir)
    run_dir = prepare_run(repo_root, work_order_path, run_dir_arg)
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
