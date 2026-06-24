#!/usr/bin/env python3
"""Generate batched RA mainline literature work orders.

This script is intentionally offline. It does not search or download papers.
It reads an existing ranking file and creates bounded jobs for later workers.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(value: str, max_len: int = 72) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value.lower())
    slug = "-".join(words) if words else "item"
    return slug[:max_len].strip("-") or "item"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_markdown_ranked_table(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    in_table = False
    directions: dict[str, dict[str, str]] = {}
    headers: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("| Rank | Direction |"):
            in_table = True
            headers = [cell.strip() for cell in line.strip("|").split("|")]
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if re.match(r"^\|\s*-+", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        direction = row.get("Direction")
        if direction:
            directions[direction] = row
    return directions


def discover_json(ranking_md: Path, explicit_json: str | None) -> Path | None:
    if explicit_json:
        candidate = Path(explicit_json)
        return candidate if candidate.exists() else None
    candidate = ranking_md.with_name("mainline-ranking-scored.json")
    return candidate if candidate.exists() else None


def normalize_jobs(scored_json: Path | None, ranking_md: Path, max_rank: int | None) -> list[dict[str, Any]]:
    md_rows = parse_markdown_ranked_table(ranking_md) if ranking_md.exists() else {}
    jobs: list[dict[str, Any]] = []

    if scored_json:
        data = read_json(scored_json)
        directions = data.get("ranked_directions", [])
        for idx, item in enumerate(directions, start=1):
            if max_rank and idx > max_rank:
                break
            direction = item.get("direction", f"rank {idx}")
            md = md_rows.get(direction, {})
            rank_slug = f"rank-{idx:02d}-{slugify(direction)}"
            teachers = []
            for professor in item.get("professors", []):
                name = professor.get("name", "")
                teachers.append(
                    {
                        "name": name,
                        "teacher_slug": slugify(name, max_len=48),
                        "pool": professor.get("pool"),
                        "priority": professor.get("priority"),
                        "direction_rank_for_teacher": professor.get("rank"),
                        "confidence": professor.get("confidence"),
                        "notes": professor.get("notes"),
                    }
                )
            jobs.append(
                {
                    "rank": idx,
                    "rank_slug": rank_slug,
                    "direction": direction,
                    "recommendation": md.get("Recommendation", ""),
                    "weighted_score": item.get("weighted_score"),
                    "professor_count": item.get("professor_count"),
                    "primary_count": item.get("primary_count"),
                    "rank1_count": item.get("rank1_count"),
                    "raw_labels": item.get("raw_labels", []),
                    "teachers": teachers,
                    "source_paths": item.get("sources", []),
                }
            )
        return jobs

    for direction, row in md_rows.items():
        try:
            rank = int(row.get("Rank", "").strip())
        except ValueError:
            continue
        if max_rank and rank > max_rank:
            continue
        rank_slug = f"rank-{rank:02d}-{slugify(direction)}"
        teachers = []
        mapping = row.get("Teacher mapping", "")
        for part in mapping.split(";"):
            name = part.strip().split("#")[0].strip()
            if name:
                teachers.append({"name": name, "teacher_slug": slugify(name, max_len=48)})
        jobs.append(
            {
                "rank": rank,
                "rank_slug": rank_slug,
                "direction": direction,
                "recommendation": row.get("Recommendation", ""),
                "weighted_score": row.get("Score"),
                "professor_count": row.get("Prof. count"),
                "primary_count": row.get("Primary count"),
                "rank1_count": row.get("Rank-1 count"),
                "raw_labels": [],
                "teachers": teachers,
                "source_paths": [],
            }
        )
    jobs.sort(key=lambda item: item["rank"])
    return jobs


def validate_target_repo(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"target repo does not exist: {path}")
    required = ["AGENTS.md", "papers", "sources"]
    missing = [name for name in required if not (path / name).exists()]
    if missing:
        raise SystemExit(f"target repo is missing required paths: {', '.join(missing)}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_job_markdown(job: dict[str, Any], target_repo: Path) -> str:
    teachers = "\n".join(
        f"- {t['name']} (`{t['teacher_slug']}`), teacher-rank={t.get('direction_rank_for_teacher', 'n/a')}, confidence={t.get('confidence', 'n/a')}"
        for t in job.get("teachers", [])
    )
    sources = "\n".join(f"- {p}" for p in job.get("source_paths", [])) or "- Not available in this job JSON; consult the ranking markdown."
    return f"""# Job {job['rank']}: {job['direction']}

Target repo: `{target_repo}`
Rank slug: `{job['rank_slug']}`
Recommendation: {job.get('recommendation') or 'n/a'}

## Teachers

{teachers or '- No teacher mapping parsed.'}

## Direction-Map Sources

{sources}

## Required Worker Action

Follow the skill worker contract. Find and verify:

- 1 high-quality field survey/review for this direction.
- 1-2 representative open-access papers per mapped teacher for this direction.

Write outputs only under:

- `papers/mainline-literature/{job['rank_slug']}/`
- `sources/mainline-literature/{job['rank_slug']}/`
"""


def render_batch_markdown(batch_no: int, jobs: list[dict[str, Any]], run_dir: Path, target_repo: Path, skill_dir_hint: str) -> str:
    lines = [
        f"# RA Mainline Literature Batch {batch_no:02d}",
        "",
        f"Target repo: `{target_repo}`",
        f"Run dir: `{run_dir}`",
        "",
        "Launch one subagent per job when possible.",
        "",
        "## Jobs",
        "",
    ]
    for job in jobs:
        job_path = run_dir / "jobs" / f"{job['rank_slug']}.json"
        lines.extend(
            [
                f"### Rank {job['rank']}: {job['direction']}",
                "",
                f"Job JSON: `{job_path}`",
                "",
                "Prompt:",
                "",
                "```text",
                "Use $paper-review-source-intel and $anysearch as needed.",
                f"Follow the worker contract at {skill_dir_hint}\\references\\worker-contract.md.",
                f"Process this RA mainline literature job: {job_path}.",
                f"Write all PDFs, manifests, and summaries only under {target_repo}.",
                "Do not bypass paywalls. If an open PDF is unavailable, record metadata and the reason.",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_dispatcher(run_id: str, jobs: list[dict[str, Any]], batch_size: int, run_dir: Path, target_repo: Path) -> str:
    lines = [
        f"# RA Mainline Literature Dispatch: {run_id}",
        "",
        f"Target repo: `{target_repo}`",
        f"Jobs: {len(jobs)}",
        f"Batch size: {batch_size}",
        "",
        "## Batches",
        "",
    ]
    total_batches = (len(jobs) + batch_size - 1) // batch_size
    for batch_no in range(1, total_batches + 1):
        batch_path = run_dir / "work-orders" / f"batch-{batch_no:02d}.md"
        lines.append(f"- Batch {batch_no:02d}: `{batch_path}`")
    lines.extend(
        [
            "",
            "## Merge Rule",
            "",
            "After each batch, inspect every `sources/mainline-literature/<rank-slug>/manifest.json` and update `status.json` before launching the next batch.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate RA literature collection work orders.")
    parser.add_argument("--ranking", required=True, help="Path to mainline-ranking.md")
    parser.add_argument("--ranking-json", help="Path to mainline-ranking-scored.json")
    parser.add_argument("--target-repo", default=r"D:\hkust-gz-ra-paper-reading")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-rank", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--out-subdir", default=r"sources\mainline-literature-runs")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--skill-dir-hint",
        default=r"C:\Users\Administrator\.codex\skills\ra-mainline-literature-orchestrator",
    )
    args = parser.parse_args()

    ranking_md = Path(args.ranking).resolve()
    target_repo = Path(args.target_repo).resolve()
    validate_target_repo(target_repo)
    scored_json = discover_json(ranking_md, args.ranking_json)

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")

    jobs = normalize_jobs(scored_json, ranking_md, args.max_rank)
    if not jobs:
        raise SystemExit("no jobs generated from ranking input")

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = target_repo / args.out_subdir / run_id
    if run_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"run dir already exists; pass --overwrite to replace: {run_dir}")
        shutil.rmtree(run_dir)
    (run_dir / "jobs").mkdir(parents=True, exist_ok=True)
    (run_dir / "work-orders").mkdir(parents=True, exist_ok=True)

    for job in jobs:
        job["artifact_paths"] = {
            "pdf_root": f"papers/mainline-literature/{job['rank_slug']}",
            "survey_pdf_dir": f"papers/mainline-literature/{job['rank_slug']}/surveys",
            "teacher_pdf_root": f"papers/mainline-literature/{job['rank_slug']}/teachers",
            "source_root": f"sources/mainline-literature/{job['rank_slug']}",
            "manifest": f"sources/mainline-literature/{job['rank_slug']}/manifest.json",
            "summary": f"sources/mainline-literature/{job['rank_slug']}/summary.md",
        }
        write_json(run_dir / "jobs" / f"{job['rank_slug']}.json", job)
        (run_dir / "jobs" / f"{job['rank_slug']}.md").write_text(
            render_job_markdown(job, target_repo), encoding="utf-8"
        )

    for i in range(0, len(jobs), args.batch_size):
        batch_no = i // args.batch_size + 1
        batch_jobs = jobs[i : i + args.batch_size]
        (run_dir / "work-orders" / f"batch-{batch_no:02d}.md").write_text(
            render_batch_markdown(batch_no, batch_jobs, run_dir, target_repo, args.skill_dir_hint),
            encoding="utf-8",
        )

    status = {
        "run_id": run_id,
        "ranking": str(ranking_md),
        "ranking_json": str(scored_json) if scored_json else None,
        "target_repo": str(target_repo),
        "batch_size": args.batch_size,
        "jobs": [
            {
                "rank": job["rank"],
                "direction": job["direction"],
                "rank_slug": job["rank_slug"],
                "status": "pending",
                "job_json": str(run_dir / "jobs" / f"{job['rank_slug']}.json"),
            }
            for job in jobs
        ],
    }
    write_json(run_dir / "status.json", status)
    (run_dir / "DISPATCH.md").write_text(
        render_dispatcher(run_id, jobs, args.batch_size, run_dir, target_repo), encoding="utf-8"
    )

    print(f"Generated {len(jobs)} jobs in {run_dir}")
    print(f"Open dispatcher: {run_dir / 'DISPATCH.md'}")


if __name__ == "__main__":
    main()
