#!/usr/bin/env python3
"""Write align/ppt_workflow_state.json for the staged PPT workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


STAGES = [
    {
        "id": "production_brief",
        "patterns": ["align/ppt_production_brief_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "material_fact_ledger",
        "patterns": ["align/fact_ledger_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "defense_narrative",
        "patterns": ["align/ppt_defense_narrative_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "storyboard",
        "patterns": ["align/PPT_storyboard_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "speaker_notes_rehearsal",
        "patterns": ["align/ppt_speaker_notes_rehearsal_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "rehearsal_evidence",
        "patterns": ["align/rehearsal_evidence_v*.md"],
        "required_for_next": False,
    },
    {
        "id": "defense_qa_backup",
        "patterns": ["align/ppt_defense_qa_backup_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "asset_layout_plan",
        "patterns": [
            "align/PPT_asset_audit_v*.md",
            "align/visual_enrichment_plan_v*.md",
            "align/ppt_layout_plan_v*.json",
        ],
        "required_for_next": True,
    },
    {
        "id": "template_design_rules",
        "patterns": ["align/template_design_rules_v*.md"],
        "required_for_next": False,
    },
    {
        "id": "academic_figure_prompt",
        "patterns": ["align/academic_figure_prompt_v*.md"],
        "required_for_next": False,
    },
    {
        "id": "content_fidelity_qa",
        "patterns": ["align/ppt_content_fidelity_qa_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "deck_build",
        "patterns": ["align/ppt_deck_build_manifest_v*.md"],
        "required_for_next": True,
    },
    {
        "id": "render_qa",
        "patterns": ["qa/ppt_render_qa_v*.md"],
        "required_for_next": False,
    },
]

STATUS_RE = re.compile(r"(?im)^\s*(stage_status|status)\s*:\s*([A-Za-z0-9_-]+)\s*$")
REQUIRES_PROMPT_RE = re.compile(
    r"(?im)^\s*requires_academic_figure_prompt\s*:\s*(true|yes)\s*$"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stage_status(path: Path) -> str | None:
    match = STATUS_RE.search(read_text(path))
    return match.group(2).lower() if match else None


def latest_artifacts(repo: Path, patterns: list[str]) -> list[dict[str, object]]:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(repo.glob(pattern))
    files = sorted(
        [p for p in matches if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    artifacts = []
    for path in files:
        stat = path.stat()
        artifacts.append(
            {
                "path": path.as_posix(),
                "status": stage_status(path) if path.suffix.lower() == ".md" else None,
                "sha256": sha256(path),
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            }
        )
    return artifacts


def requires_academic_figure_prompt(repo: Path) -> bool:
    for path in repo.glob("align/visual_enrichment_plan_v*.md"):
        if path.is_file() and REQUIRES_PROMPT_RE.search(read_text(path)):
            return True
    return False


def compute_state(repo: Path) -> dict[str, object]:
    require_prompt = requires_academic_figure_prompt(repo)
    stages = []
    next_stage = None
    blocked_reason = None

    for stage in STAGES:
        artifacts = latest_artifacts(repo, stage["patterns"])
        latest = artifacts[0] if artifacts else None
        required = bool(stage["required_for_next"])
        if stage["id"] == "academic_figure_prompt":
            required = require_prompt
        statuses = [
            str(artifact["status"])
            for artifact in artifacts
            if artifact.get("status") is not None
        ]
        complete_statuses = {"confirmed"}
        if stage["id"] == "render_qa":
            complete_statuses.update({"pass", "needs_human_acceptance"})
        complete = any(status in complete_statuses for status in statuses)
        if required and not complete and next_stage is None:
            next_stage = stage["id"]
            blocked_reason = "missing_confirmed_artifact" if latest else "missing_artifact"
        stages.append(
            {
                "id": stage["id"],
                "required": required,
                "complete": complete,
                "statuses": statuses,
                "latest": latest,
                "artifacts": artifacts,
            }
        )

    return {
        "schema": "ppt_workflow_state.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": repo.as_posix(),
        "requires_academic_figure_prompt": require_prompt,
        "next_stage": next_stage or "complete_or_human_acceptance",
        "blocked_reason": blocked_reason,
        "stages": stages,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing align/ and qa/ directories.",
    )
    parser.add_argument(
        "--output",
        default="align/ppt_workflow_state.json",
        help="Output JSON path relative to repo root.",
    )
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    state = compute_state(repo)
    output = repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
