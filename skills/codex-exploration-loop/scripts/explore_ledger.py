#!/usr/bin/env python3
"""State and runner helper for codex-exploration-loop.

This script keeps deterministic state. It can also orchestrate external worker
commands such as codex exec, but it does not implement its own model/tool loop.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DECISIONS = {"continue", "pivot", "branch", "prune", "promote", "stop"}
SCORE_KEYS = ("novelty", "promise", "evidence", "risk", "cost")
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWED_ACTIONS = (
    "read/search, local shell probes, scratch edits, tests, local skills, "
    "and public network when useful"
)
RUNNER_STOP_DECISIONS = {"promote", "stop"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug or "exploration"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig") as f:
        return f.read()


def parse_json_text(text: str) -> Dict[str, Any]:
    loaded = parse_json_value_text(text)
    if not isinstance(loaded, dict):
        raise ValueError("JSON value must be an object")
    return loaded


def parse_json_value_text(text: str) -> Any:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        loaded = json.loads(value[start : end + 1])
    return loaded


def load_json_arg(value: str) -> Dict[str, Any]:
    candidate = Path(value)
    if candidate.exists():
        return parse_json_text(read_text(candidate))
    return parse_json_text(value)


def load_json_value_arg(value: str) -> Any:
    candidate = Path(value)
    if candidate.exists():
        return parse_json_value_text(read_text(candidate))
    return parse_json_value_text(value)


def load_json_file(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def iter_ledger(run_dir: Path) -> Iterable[Dict[str, Any]]:
    ledger = run_dir / "ledger.jsonl"
    if not ledger.exists():
        return []
    records: List[Dict[str, Any]] = []
    with ledger.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def compute_total(scores: Dict[str, Any]) -> float:
    total = (
        0.30 * float(scores.get("promise", 0))
        + 0.25 * float(scores.get("novelty", 0))
        + 0.25 * float(scores.get("evidence", 0))
        - 0.10 * float(scores.get("risk", 0))
        - 0.10 * float(scores.get("cost", 0))
        + float(scores.get("exploration_bonus", 0))
    )
    return round(total, 3)


def validate_record(record: Dict[str, Any]) -> None:
    required = [
        "round",
        "branch_id",
        "hypothesis",
        "probe",
        "actions",
        "evidence",
        "scores",
        "reflection",
        "decision",
        "next_probe",
    ]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")
    if not isinstance(record["round"], int) or record["round"] < 1:
        raise ValueError("round must be a positive integer")
    if not re.match(r"^b[0-9]{3,}$", str(record["branch_id"])):
        raise ValueError("branch_id must look like b001")
    if record["decision"] not in DECISIONS:
        raise ValueError(f"decision must be one of {sorted(DECISIONS)}")
    if not isinstance(record["actions"], list):
        raise ValueError("actions must be a list")
    if not isinstance(record["evidence"], list):
        raise ValueError("evidence must be a list")
    if "proposed_branches" in record and not isinstance(record["proposed_branches"], list):
        raise ValueError("proposed_branches must be a list when present")
    scores = record["scores"]
    if not isinstance(scores, dict):
        raise ValueError("scores must be an object")
    for key in SCORE_KEYS:
        value = scores.get(key)
        if not isinstance(value, int) or value < 0 or value > 5:
            raise ValueError(f"scores.{key} must be an integer from 0 to 5")


def ensure_run_dir(run_dir: Path) -> None:
    if not (run_dir / "frontier.json").exists():
        raise SystemExit(f"run dir is missing frontier.json: {run_dir}")


def active_pending_round(run_dir: Path) -> Dict[str, Any]:
    legacy = run_dir / "pending_round.json"
    if legacy.exists():
        pending = read_json(legacy, {})
        pending["_path"] = str(legacy)
        return pending
    pending_dir = run_dir / "pending_rounds"
    if not pending_dir.exists():
        return {}
    pending_files = sorted(pending_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not pending_files:
        return {}
    pending = read_json(pending_files[0], {})
    pending["_path"] = str(pending_files[0])
    return pending


def pending_round_path(run_dir: Path, round_number: int, branch_id: str) -> Path:
    return run_dir / "pending_rounds" / f"{branch_id}-round-{round_number:03d}.json"


def write_pending_round(run_dir: Path, round_number: int, branch_id: str, timebox_minutes: float) -> Dict[str, Any]:
    pending = {
        "round": round_number,
        "branch_id": branch_id,
        "timebox_minutes": timebox_minutes,
        "started_at": now_iso(),
        "status": "pending",
    }
    write_json(pending_round_path(run_dir, round_number, branch_id), pending)
    return pending


def append_attempt(run_dir: Path, attempt: Dict[str, Any]) -> None:
    attempt.setdefault("timestamp", now_iso())
    append_jsonl(run_dir / "runner-attempts.jsonl", attempt)


def read_runner_state(run_dir: Path) -> Dict[str, Any]:
    return read_json(run_dir / "runner-state.json", {"status": "new", "rounds_attempted": 0, "rounds_completed": 0})


def write_runner_state(run_dir: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    write_json(run_dir / "runner-state.json", state)


def next_round_number(run_dir: Path) -> int:
    records = list(iter_ledger(run_dir))
    if not records:
        pending = active_pending_round(run_dir)
        if pending.get("round"):
            return int(pending["round"])
        return 1
    return max(int(record.get("round", 0)) for record in records) + 1


def has_stop_decision(run_dir: Path) -> bool:
    records = list(iter_ledger(run_dir))
    return any(record.get("decision") in RUNNER_STOP_DECISIONS for record in records)


def choose_runner_branch(frontier: Dict[str, Any], branch_id: str) -> str:
    return choose_branch(frontier, branch_id or None)


def normalize_public_path(value: str) -> str:
    return value.replace("\\", "/")


def initial_frontier(question: str) -> Dict[str, Any]:
    return {
        "active": ["b001"],
        "max_active": 3,
        "fanout_width": 1,
        "beam_width": 2,
        "branches": {
            "b001": {
                "status": "active",
                "hypothesis": question,
                "last_score": 0,
                "rounds": [],
                "recent_reflections": [],
                "next_probe": "Inspect available context and choose the first concrete probe.",
            }
        },
    }


def next_branch_id(branches: Dict[str, Any]) -> str:
    highest = 0
    for branch_id in branches:
        match = re.match(r"^b([0-9]+)$", str(branch_id))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"b{highest + 1:03d}"


def active_branch_ids(frontier: Dict[str, Any]) -> List[str]:
    branches = frontier.get("branches", {})
    active = [bid for bid, item in branches.items() if item.get("status") == "active"]
    active.sort(key=lambda bid: branches[bid].get("last_score", 0), reverse=True)
    max_active = int(frontier.get("max_active", 3) or 3)
    return active[:max_active]


def update_frontier(run_dir: Path, record: Dict[str, Any]) -> Dict[str, Any]:
    frontier_path = run_dir / "frontier.json"
    frontier = read_json(frontier_path, initial_frontier(record["hypothesis"]))
    branches = frontier.setdefault("branches", {})
    branch_id = record["branch_id"]
    branch = branches.setdefault(
        branch_id,
        {
            "status": "active",
            "hypothesis": record["hypothesis"],
            "last_score": 0,
            "rounds": [],
            "recent_reflections": [],
            "next_probe": "",
        },
    )
    scores = record["scores"]
    if "total" not in scores:
        scores["total"] = compute_total(scores)
    branch["hypothesis"] = record["hypothesis"]
    branch["last_score"] = scores["total"]
    branch["last_scores"] = dict(scores)
    branch.setdefault("rounds", []).append(record["round"])
    recent = branch.setdefault("recent_reflections", [])
    recent.append(record["reflection"])
    branch["recent_reflections"] = recent[-3:]
    branch["next_probe"] = record.get("next_probe", "")

    decision = record["decision"]
    if decision in {"prune", "promote", "stop"}:
        branch["status"] = "promoted" if decision == "promote" else "pruned"
    elif decision in {"continue", "pivot", "branch"}:
        branch["status"] = "active"

    proposed = record.get("proposed_branches") or []
    if decision == "branch" and proposed:
        layer_id = f"l{int(frontier.get('next_layer', 1)):03d}"
        created = create_child_branches(run_dir, frontier, branch_id, proposed, layer_id)
        if created:
            branch["status"] = "branched"
            branch["child_branch_ids"] = branch.get("child_branch_ids", []) + created
            frontier["last_fanout"] = {
                "layer_id": layer_id,
                "parent_branch_id": branch_id,
                "branch_ids": created,
                "created_at": now_iso(),
                "source": "proposed_branches",
            }
            frontier["next_layer"] = int(frontier.get("next_layer", 1)) + 1
            append_jsonl(
                run_dir / "fanout.jsonl",
                {
                    "event": "proposed-branches",
                    "layer_id": layer_id,
                    "parent_branch_id": branch_id,
                    "branch_ids": created,
                    "timestamp": now_iso(),
                },
            )

    frontier["active"] = active_branch_ids(frontier)
    write_json(frontier_path, frontier)
    return frontier


def split_candidate(value: str) -> Dict[str, str]:
    separators = ["|||", "::", "=>"]
    for separator in separators:
        if separator in value:
            hypothesis, next_probe = value.split(separator, 1)
            return {"hypothesis": hypothesis.strip(), "next_probe": next_probe.strip()}
    stripped = value.strip()
    return {"hypothesis": stripped, "next_probe": "Run the smallest useful probe for this branch."}


def load_candidates(args: argparse.Namespace) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for item in args.candidate or []:
        candidates.append(split_candidate(item))
    if args.candidate_json:
        loaded = load_json_value_arg(args.candidate_json)
        if isinstance(loaded, dict) and "candidates" in loaded:
            raw_items = loaded["candidates"]
        else:
            raw_items = loaded
        if not isinstance(raw_items, list):
            raise ValueError("candidate-json must be a JSON array or an object with candidates")
        for raw in raw_items:
            if not isinstance(raw, dict):
                raise ValueError("each candidate-json item must be an object")
            hypothesis = str(raw.get("hypothesis") or "").strip()
            if not hypothesis:
                raise ValueError("each candidate-json item needs hypothesis")
            candidates.append(
                {
                    "hypothesis": hypothesis,
                    "next_probe": str(raw.get("next_probe") or raw.get("probe") or "Run the smallest useful probe for this branch.").strip(),
                    "notes": str(raw.get("notes") or "").strip(),
                    "operator": str(raw.get("operator") or "").strip(),
                }
            )
    if not candidates:
        raise ValueError("fanout needs at least one --candidate or --candidate-json item")
    return candidates


def write_branch_note(run_dir: Path, branch_id: str, branch: Dict[str, Any]) -> None:
    lines = [
        f"# {branch_id}",
        "",
        f"Hypothesis: {branch.get('hypothesis', '')}",
        "",
        f"Next probe: {branch.get('next_probe', '')}",
    ]
    if branch.get("parent_branch_id"):
        lines.extend(["", f"Parent: {branch.get('parent_branch_id')}"])
    if branch.get("layer_id"):
        lines.append(f"Layer: {branch.get('layer_id')}")
    if branch.get("notes"):
        lines.extend(["", f"Notes: {branch.get('notes')}"])
    write_text(run_dir / "branches" / f"{branch_id}.md", "\n".join(lines) + "\n")


def create_child_branches(
    run_dir: Path,
    frontier: Dict[str, Any],
    parent_branch_id: str,
    proposed_branches: List[Dict[str, Any]],
    layer_id: str,
) -> List[str]:
    branches = frontier.setdefault("branches", {})
    created: List[str] = []
    for raw in proposed_branches:
        if not isinstance(raw, dict):
            continue
        hypothesis = str(raw.get("hypothesis") or "").strip()
        if not hypothesis:
            continue
        branch_id = next_branch_id(branches)
        branch = {
            "status": "active",
            "hypothesis": hypothesis,
            "last_score": 0,
            "rounds": [],
            "recent_reflections": [],
            "next_probe": str(raw.get("next_probe") or raw.get("probe") or "Run the smallest useful probe for this branch.").strip(),
            "parent_branch_id": parent_branch_id,
            "layer_id": layer_id,
            "fanout_source": "proposed_branches",
            "diversity_key": str(raw.get("diversity_key") or "").strip(),
            "notes": str(raw.get("rationale") or raw.get("risk_note") or "").strip(),
            "estimated_cost": raw.get("estimated_cost"),
            "created_at": now_iso(),
        }
        branches[branch_id] = branch
        write_branch_note(run_dir, branch_id, branch)
        created.append(branch_id)
    return created


def cmd_fanout(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    frontier_path = run_dir / "frontier.json"
    frontier = read_json(frontier_path, {})
    branches = frontier.setdefault("branches", {})
    parent = choose_branch(frontier, args.parent_branch)
    if parent not in branches:
        raise ValueError(f"unknown parent branch: {parent}")
    candidates = load_candidates(args)
    layer_id = args.layer_id or f"l{int(frontier.get('next_layer', 1)):03d}"
    new_ids: List[str] = []
    for candidate in candidates:
        branch_id = next_branch_id(branches)
        branch = {
            "status": "active",
            "hypothesis": candidate["hypothesis"],
            "last_score": 0,
            "rounds": [],
            "recent_reflections": [],
            "next_probe": candidate.get("next_probe") or "Run the smallest useful probe for this branch.",
            "parent_branch_id": parent,
            "layer_id": layer_id,
            "fanout_source": "tot-fanout",
            "operator": candidate.get("operator", ""),
            "notes": candidate.get("notes", ""),
            "created_at": now_iso(),
        }
        branches[branch_id] = branch
        write_branch_note(run_dir, branch_id, branch)
        new_ids.append(branch_id)
    if not args.keep_parent_active:
        branches[parent]["status"] = "branched"
    active = [bid for bid in frontier.get("active", []) if branches.get(bid, {}).get("status") == "active"]
    for branch_id in new_ids:
        if branch_id not in active:
            active.append(branch_id)
    frontier["active"] = active
    frontier["max_active"] = max(int(frontier.get("max_active", 3) or 3), len(active))
    frontier["fanout_width"] = len(new_ids)
    frontier["beam_width"] = int(args.beam_width)
    frontier["last_fanout"] = {
        "layer_id": layer_id,
        "parent_branch_id": parent,
        "branch_ids": new_ids,
        "beam_width": int(args.beam_width),
        "created_at": now_iso(),
    }
    frontier["next_layer"] = int(frontier.get("next_layer", 1)) + 1
    write_json(frontier_path, frontier)
    append_jsonl(
        run_dir / "fanout.jsonl",
        {
            "event": "fanout",
            "layer_id": layer_id,
            "parent_branch_id": parent,
            "branch_ids": new_ids,
            "beam_width": int(args.beam_width),
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"layer_id": layer_id, "parent_branch_id": parent, "branch_ids": new_ids}, ensure_ascii=False, indent=2))
    return 0


def diversity_score(branch: Dict[str, Any]) -> float:
    scores = branch.get("last_scores") or {}
    novelty = float(scores.get("novelty", 0))
    cost = float(scores.get("cost", 0))
    return novelty - 0.5 * cost


def cmd_beam_select(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    frontier_path = run_dir / "frontier.json"
    frontier = read_json(frontier_path, {})
    branches = frontier.setdefault("branches", {})
    scoped = []
    for branch_id, branch in branches.items():
        if branch.get("status") != "active":
            continue
        if args.layer_id and branch.get("layer_id") != args.layer_id:
            continue
        scoped.append(branch_id)
    scoped.sort(key=lambda bid: branches[bid].get("last_score", 0), reverse=True)
    selected = scoped[: args.beam_width]
    remaining = [bid for bid in scoped if bid not in selected]
    if args.diversity_count:
        remaining.sort(key=lambda bid: diversity_score(branches[bid]), reverse=True)
        for branch_id in remaining:
            if branch_id not in selected:
                selected.append(branch_id)
            if len(selected) >= args.beam_width + args.diversity_count:
                break
    parked = [bid for bid in scoped if bid not in selected]
    for branch_id in selected:
        branches[branch_id]["status"] = "active"
    if not args.keep_unselected_active:
        for branch_id in parked:
            branches[branch_id]["status"] = "parked"
    frontier["beam_width"] = int(args.beam_width)
    frontier["max_active"] = max(int(args.beam_width) + int(args.diversity_count), 1)
    frontier["active"] = active_branch_ids(frontier)
    frontier["last_beam_select"] = {
        "layer_id": args.layer_id or "",
        "selected": selected,
        "parked": parked if not args.keep_unselected_active else [],
        "beam_width": int(args.beam_width),
        "diversity_count": int(args.diversity_count),
        "created_at": now_iso(),
    }
    write_json(frontier_path, frontier)
    append_jsonl(
        run_dir / "fanout.jsonl",
        {
            "event": "beam-select",
            "layer_id": args.layer_id or "",
            "selected": selected,
            "parked": parked if not args.keep_unselected_active else [],
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"selected": selected, "parked": parked if not args.keep_unselected_active else []}, ensure_ascii=False, indent=2))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    root_display = args.root_label or str(root)
    slug = slugify(args.slug)
    date = datetime.now().strftime("%Y-%m-%d")
    base = Path(args.output_dir).resolve() if args.output_dir else root / "explorations"
    run_dir = base / f"{date}-{slug}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "branches").mkdir()
    (run_dir / "artifacts").mkdir()

    metadata = {
        "question": args.question,
        "mode": args.mode,
        "max_rounds": args.max_rounds,
        "round_timebox_minutes": args.round_timebox_minutes,
        "root": root_display,
        "created_at": now_iso(),
        "scratch_worktree": args.scratch_worktree or "",
    }
    write_json(run_dir / "run.json", metadata)
    write_json(run_dir / "frontier.json", initial_frontier(args.question))
    (run_dir / "ledger.jsonl").write_text("", encoding="utf-8")
    write_text(
        run_dir / "branches" / "b001.md",
        f"# b001\n\nHypothesis: {args.question}\n\nNext probe: Inspect available context and choose the first concrete probe.\n",
    )
    write_text(
        run_dir / "brief.md",
        "\n".join(
            [
                f"# Exploration Brief: {args.question}",
                "",
                f"- Created: {metadata['created_at']}",
                f"- Mode: {args.mode}",
                f"- Max rounds: {args.max_rounds}",
                f"- Round timebox minutes: {args.round_timebox_minutes}",
                f"- Root: {root_display}",
                f"- Scratch worktree: {args.scratch_worktree or '(not set)'}",
                "",
                "## Safety",
                "",
                "- No credentials, paid calls, destructive edits, commit/push, or merge without explicit confirmation.",
            ]
        )
        + "\n",
    )
    print(str(run_dir))
    return 0


def cmd_start_round(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    pending = write_pending_round(run_dir, args.round, args.branch_id, args.timebox_minutes)
    print(json.dumps(pending, ensure_ascii=False))
    return 0


def finish_record(run_dir: Path, record: Dict[str, Any]) -> Dict[str, Any]:
    ensure_run_dir(run_dir)
    pending_paths = [
        pending_round_path(run_dir, int(record.get("round", 0) or 0), str(record.get("branch_id", ""))),
        run_dir / "pending_round.json",
    ]
    pending_path = next((path for path in pending_paths if path.exists()), None)
    if pending_path:
        pending = read_json(pending_path, {})
        if str(pending.get("branch_id", record.get("branch_id"))) == str(record.get("branch_id")):
            record.setdefault("started_at", pending.get("started_at"))
            record.setdefault("timebox_minutes", pending.get("timebox_minutes"))
    record.setdefault("ended_at", now_iso())
    record.setdefault("network_used", False)
    record.setdefault("skills_used", [])
    record.setdefault("subagents_used", [])
    record.setdefault("files_touched", [])
    validate_record(record)
    record["scores"]["total"] = compute_total(record["scores"])
    append_jsonl(run_dir / "ledger.jsonl", record)
    update_frontier(run_dir, record)
    if pending_path and pending_path.exists():
        pending_path.unlink()
    return record


def cmd_finish_round(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    record = load_json_arg(args.record_json)
    record = finish_record(run_dir, record)
    print(json.dumps({"appended": True, "total": record["scores"]["total"]}, ensure_ascii=False))
    return 0


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def choose_branch(frontier: Dict[str, Any], branch_id: Optional[str]) -> str:
    if branch_id:
        return branch_id
    active = frontier.get("active", [])
    if not active:
        raise ValueError("frontier has no active branches")
    return active[0]


def render_worker_prompt(
    template: str,
    question: str,
    round_number: int,
    branch_id: str,
    hypothesis: str,
    probe: str,
    workspace: str,
    minutes: float,
    allowed_actions: str,
) -> str:
    replacements = {
        "<question>": question,
        "<round>": str(round_number),
        "<branch-id>": branch_id,
        "<hypothesis>": hypothesis,
        "<probe>": probe,
        "<workspace>": workspace,
        "<minutes>": str(minutes),
        "<allowed-actions>": allowed_actions,
    }
    output = template
    for needle, replacement in replacements.items():
        output = output.replace(needle, replacement)
    return output


def write_codex_exec_script(
    script_path: Path,
    prompt_path: Path,
    workspace: str,
    sandbox: str,
    profile: str,
    schema_path: Path,
    result_path: Path,
    events_path: Path,
    portable: bool,
) -> None:
    if portable:
        prompt_ref = "$promptPath"
        schema_ref = "$schemaPath"
        result_ref = "$resultPath"
        header = [
            "$ErrorActionPreference = 'Stop'",
            "$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path",
            f"$promptPath = Join-Path $scriptDir {ps_quote(prompt_path.name)}",
            f"$schemaPath = Join-Path $scriptDir {ps_quote(schema_path.name)}",
            f"$resultPath = Join-Path $scriptDir {ps_quote(result_path.name)}",
            f"$eventsPath = Join-Path $scriptDir {ps_quote(events_path.name)}",
            "$prompt = Get-Content -Raw -Encoding UTF8 $promptPath",
        ]
        event_target = "$eventsPath"
    else:
        prompt_ref = str(prompt_path)
        schema_ref = str(schema_path)
        result_ref = str(result_path)
        header = [
            "$ErrorActionPreference = 'Stop'",
            f"$prompt = Get-Content -Raw -Encoding UTF8 {ps_quote(str(prompt_path))}",
        ]
        event_target = ps_quote(str(events_path))
    args = [
        "exec",
        "--cd",
        workspace,
        "--sandbox",
        sandbox,
        "--output-schema",
        schema_ref,
        "--output-last-message",
        result_ref,
        "--json",
    ]
    if profile:
        args[5:5] = ["--profile", profile]
    args.append("-")
    arg_lines = []
    for item in args:
        if portable and item.startswith("$"):
            arg_lines.append("  " + item)
        else:
            arg_lines.append("  " + ps_quote(item))
    content = "\n".join(header + ["$codexArgs = @(", ",\n".join(arg_lines), ")", f"$prompt | & codex @codexArgs 2>&1 | Tee-Object -FilePath {event_target}", ""])
    write_text(script_path, content)


def prepare_worker(
    run_dir: Path,
    round_number: int,
    branch_id_arg: Optional[str],
    timebox_minutes_arg: Optional[float],
    workspace_arg: str,
    probe_arg: str,
    hypothesis_arg: str,
    allowed_actions: str,
    sandbox: str,
    profile: str,
    skill_dir_arg: str,
    schema_path_arg: str,
    portable: bool,
    no_start: bool,
) -> Dict[str, Any]:
    ensure_run_dir(run_dir)
    run_meta = read_json(run_dir / "run.json", {})
    frontier = read_json(run_dir / "frontier.json", {})
    branch_id = choose_branch(frontier, branch_id_arg)
    branch = frontier.get("branches", {}).get(branch_id)
    if not branch:
        raise ValueError(f"unknown branch_id: {branch_id}")
    timebox_minutes = timebox_minutes_arg or float(run_meta.get("round_timebox_minutes", 10))
    workspace = workspace_arg or run_meta.get("scratch_worktree") or run_meta.get("root") or str(Path.cwd())
    probe = probe_arg or branch.get("next_probe") or "Run the next smallest useful probe."
    hypothesis = hypothesis_arg or branch.get("hypothesis") or run_meta.get("question", "")
    skill_dir = Path(skill_dir_arg).resolve() if skill_dir_arg else SKILL_DIR
    schema_path = Path(schema_path_arg).resolve() if schema_path_arg else skill_dir / "schemas" / "round-result.schema.json"
    template_path = skill_dir / "prompts" / "round-worker.prompt.md"
    template = read_text(template_path)
    prefix = f"{branch_id}-round-{round_number:03d}"
    artifacts_dir = run_dir / "artifacts"
    prompt_path = artifacts_dir / f"{prefix}.prompt.md"
    result_path = artifacts_dir / f"{prefix}.result.json"
    events_path = artifacts_dir / f"{prefix}.events.jsonl"
    script_path = artifacts_dir / f"{prefix}.codex-exec.ps1"
    manifest_path = artifacts_dir / f"{prefix}.worker.json"
    if portable:
        bundled_schema_path = artifacts_dir / f"{prefix}.schema.json"
        write_text(bundled_schema_path, read_text(schema_path))
        worker_schema_path = bundled_schema_path
    else:
        worker_schema_path = schema_path
    prompt = render_worker_prompt(
        template,
        run_meta.get("question", ""),
        round_number,
        branch_id,
        hypothesis,
        probe,
        workspace,
        timebox_minutes,
        allowed_actions,
    )
    write_text(prompt_path, prompt)
    write_codex_exec_script(
        script_path,
        prompt_path,
        workspace,
        sandbox,
        profile,
        worker_schema_path,
        result_path,
        events_path,
        portable,
    )
    pending = None
    if not no_start:
        pending = write_pending_round(run_dir, round_number, branch_id, timebox_minutes)
    manifest = {
        "round": round_number,
        "branch_id": branch_id,
        "workspace": workspace,
        "sandbox": sandbox,
        "profile": profile,
        "schema_path": worker_schema_path.name if portable else str(worker_schema_path),
        "prompt_path": prompt_path.name if portable else str(prompt_path),
        "result_path": result_path.name if portable else str(result_path),
        "events_path": events_path.name if portable else str(events_path),
        "script_path": script_path.name if portable else str(script_path),
        "portable": bool(portable),
        "pending_started": bool(pending),
    }
    write_json(manifest_path, manifest)
    manifest["_absolute_prompt_path"] = str(prompt_path)
    manifest["_absolute_result_path"] = str(result_path)
    manifest["_absolute_events_path"] = str(events_path)
    manifest["_absolute_script_path"] = str(script_path)
    manifest["_absolute_manifest_path"] = str(manifest_path)
    return manifest


def cmd_prepare_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = prepare_worker(
        run_dir,
        args.round,
        args.branch_id,
        args.timebox_minutes,
        args.workspace,
        args.probe,
        args.hypothesis,
        args.allowed_actions,
        args.sandbox,
        args.profile,
        args.skill_dir,
        args.schema_path,
        args.portable,
        args.no_start,
    )
    printable = {key: value for key, value in manifest.items() if not key.startswith("_absolute_")}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0


def cmd_finish_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    record = load_json_arg(args.worker_output)
    record = finish_record(run_dir, record)
    print(json.dumps({"imported": True, "total": record["scores"]["total"]}, ensure_ascii=False))
    return 0


def default_runner_plan(run_dir: Path) -> Dict[str, Any]:
    run_meta = read_json(run_dir / "run.json", {})
    return {
        "version": "2.1",
        "mode": "mock",
        "max_rounds": int(run_meta.get("max_rounds", 1)),
        "round_timebox_minutes": float(run_meta.get("round_timebox_minutes", 5)),
        "budget_unit": "branch_probe",
        "workspace": run_meta.get("root", ""),
        "sandbox": "workspace-write",
        "profile": "",
        "portable": True,
        "stop_on_decisions": sorted(RUNNER_STOP_DECISIONS),
        "max_failures": 2,
        "fanout_width": 3,
        "beam_width": 2,
        "diversity_count": 1,
        "rounds": [],
    }


def load_runner_plan(run_dir: Path, plan_path: str) -> Dict[str, Any]:
    if plan_path:
        plan = load_json_file(Path(plan_path), {})
    else:
        plan = load_json_file(run_dir / "runner-plan.json", None)
    if not plan:
        plan = default_runner_plan(run_dir)
    if not isinstance(plan, dict):
        raise ValueError("runner plan must be a JSON object")
    merged = default_runner_plan(run_dir)
    merged.update(plan)
    return merged


def write_plan_template(run_dir: Path, output_path: Path) -> Dict[str, Any]:
    ensure_run_dir(run_dir)
    frontier = read_json(run_dir / "frontier.json", {})
    active = frontier.get("active", ["b001"])
    branch_id = active[0] if active else "b001"
    branch = frontier.get("branches", {}).get(branch_id, {})
    plan = default_runner_plan(run_dir)
    plan["rounds"] = [
        {
            "round": next_round_number(run_dir),
            "branch_id": branch_id,
            "probe": branch.get("next_probe", "Run the next smallest useful probe."),
            "mode": "mock",
            "mock_decision": "continue",
        }
    ]
    write_json(output_path, plan)
    return plan


def round_spec_for(plan: Dict[str, Any], index: int) -> Dict[str, Any]:
    rounds = plan.get("rounds") or []
    if index < len(rounds):
        spec = dict(rounds[index])
    else:
        spec = {}
    return spec


def mock_record(run_dir: Path, round_number: int, branch_id: str, probe: str, decision: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    run_meta = read_json(run_dir / "run.json", {})
    frontier = read_json(run_dir / "frontier.json", {})
    branch = frontier.get("branches", {}).get(branch_id, {})
    return {
        "round": round_number,
        "branch_id": branch_id,
        "hypothesis": branch.get("hypothesis") or run_meta.get("question", "Mock runner branch."),
        "probe": probe or branch.get("next_probe") or "Mock runner probe.",
        "actions": [
            {
                "kind": "other",
                "summary": "v2.0 runner mock",
                "result": "Prepared a worker artifact and imported a deterministic schema-valid result.",
            }
        ],
        "network_used": False,
        "skills_used": ["codex-exploration-loop"],
        "subagents_used": [],
        "files_touched": [
            normalize_public_path(manifest.get("prompt_path", "")),
            normalize_public_path(manifest.get("script_path", "")),
            normalize_public_path(manifest.get("result_path", "")),
        ],
        "evidence": [
            {
                "path_or_url": normalize_public_path(manifest.get("script_path", "")),
                "supports": "The runner prepared a codex exec worker artifact for this round.",
                "confidence": "high",
            }
        ],
        "scores": {"novelty": 3, "promise": 4, "evidence": 4, "risk": 1, "cost": 1},
        "reflection": "The v2.0 runner can orchestrate a bounded round without replacing Codex worker execution.",
        "decision": decision,
        "next_probe": "Run the next planned branch or switch to external mode for a live codex exec worker.",
    }


def execute_external_script(script_path: Path, timeout_seconds: Optional[float]) -> int:
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return completed.returncode


def run_one_planned_round(run_dir: Path, plan: Dict[str, Any], spec: Dict[str, Any], default_round: int, dry_run: bool) -> Dict[str, Any]:
    frontier = read_json(run_dir / "frontier.json", {})
    branch_id = choose_runner_branch(frontier, str(spec.get("branch_id") or plan.get("branch_id") or ""))
    round_number = int(spec.get("round") or default_round)
    timebox_minutes = float(spec.get("timebox_minutes") or plan.get("round_timebox_minutes") or 5)
    mode = str(spec.get("mode") or plan.get("mode") or "mock")
    probe = str(spec.get("probe") or "")
    portable = bool(spec.get("portable", plan.get("portable", True)))
    sandbox = str(spec.get("sandbox") or plan.get("sandbox") or "workspace-write")
    profile = str(spec.get("profile") or plan.get("profile") or "")
    workspace = str(spec.get("workspace") or plan.get("workspace") or "")
    manifest = prepare_worker(
        run_dir,
        round_number,
        branch_id,
        timebox_minutes,
        workspace,
        probe,
        str(spec.get("hypothesis") or ""),
        str(spec.get("allowed_actions") or plan.get("allowed_actions") or DEFAULT_ALLOWED_ACTIONS),
        sandbox,
        profile,
        str(plan.get("skill_dir") or ""),
        str(plan.get("schema_path") or ""),
        portable,
        False,
    )
    printable_manifest = {key: value for key, value in manifest.items() if not key.startswith("_absolute_")}
    attempt = {
        "round": round_number,
        "branch_id": branch_id,
        "mode": mode,
        "status": "prepared" if dry_run else "running",
        "manifest": printable_manifest,
    }
    append_attempt(run_dir, attempt)
    if dry_run:
        return {"status": "prepared", "round": round_number, "branch_id": branch_id}

    if mode == "mock":
        decision = str(spec.get("mock_decision") or "continue")
        record = mock_record(run_dir, round_number, branch_id, probe, decision, printable_manifest)
        result_path = Path(manifest["_absolute_result_path"])
        write_json(result_path, record)
        record = finish_record(run_dir, record)
        append_attempt(run_dir, {"round": round_number, "branch_id": branch_id, "mode": mode, "status": "completed", "total": record["scores"]["total"], "decision": record["decision"]})
        return {"status": "completed", "round": round_number, "branch_id": branch_id, "decision": record["decision"]}

    if mode == "replay":
        replay_output = spec.get("worker_output")
        if not replay_output:
            raise ValueError("replay mode requires worker_output")
        record = load_json_arg(str(replay_output))
        record = finish_record(run_dir, record)
        append_attempt(run_dir, {"round": round_number, "branch_id": branch_id, "mode": mode, "status": "completed", "total": record["scores"]["total"], "decision": record["decision"]})
        return {"status": "completed", "round": round_number, "branch_id": branch_id, "decision": record["decision"]}

    if mode == "external":
        timeout_seconds = spec.get("timeout_seconds", plan.get("timeout_seconds"))
        timeout = float(timeout_seconds) if timeout_seconds else None
        try:
            code = execute_external_script(Path(manifest["_absolute_script_path"]), timeout)
        except subprocess.TimeoutExpired:
            append_attempt(run_dir, {"round": round_number, "branch_id": branch_id, "mode": mode, "status": "timeout"})
            raise TimeoutError(f"external worker timed out after {timeout} seconds")
        if code != 0:
            append_attempt(run_dir, {"round": round_number, "branch_id": branch_id, "mode": mode, "status": "failed", "exit_code": code})
            raise RuntimeError(f"external worker failed with exit code {code}")
        record = load_json_arg(manifest["_absolute_result_path"])
        record = finish_record(run_dir, record)
        append_attempt(run_dir, {"round": round_number, "branch_id": branch_id, "mode": mode, "status": "completed", "total": record["scores"]["total"], "decision": record["decision"]})
        return {"status": "completed", "round": round_number, "branch_id": branch_id, "decision": record["decision"]}

    raise ValueError(f"unknown runner round mode: {mode}")


def cmd_write_plan(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    output_path = Path(args.output).resolve() if args.output else run_dir / "runner-plan.json"
    plan = write_plan_template(run_dir, output_path)
    print(json.dumps({"written": str(output_path), "rounds": len(plan.get("rounds", []))}, ensure_ascii=False))
    return 0


def cmd_run_plan(args: argparse.Namespace) -> int:
    run_dir_display = args.run_dir
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    plan = load_runner_plan(run_dir, args.plan)
    max_rounds = int(args.max_rounds or plan.get("max_rounds") or 1)
    max_failures = int(args.max_failures if args.max_failures is not None else plan.get("max_failures", 2))
    stop_decisions = set(plan.get("stop_on_decisions") or sorted(RUNNER_STOP_DECISIONS))
    state = read_runner_state(run_dir)
    state.update({"status": "running", "started_at": state.get("started_at") or now_iso(), "plan_version": plan.get("version", "2.0")})
    write_runner_state(run_dir, state)
    failures = int(state.get("failures", 0))
    completed = 0
    results: List[Dict[str, Any]] = []
    for index in range(max_rounds):
        if has_stop_decision(run_dir):
            state["status"] = "stopped"
            state["reason"] = "stop decision already present"
            break
        frontier = read_json(run_dir / "frontier.json", {})
        if not frontier.get("active"):
            state["status"] = "stopped"
            state["reason"] = "no active branch"
            break
        spec = round_spec_for(plan, index)
        round_number = int(spec.get("round") or next_round_number(run_dir))
        try:
            result = run_one_planned_round(run_dir, plan, spec, round_number, args.dry_run)
            results.append(result)
            if result.get("status") == "completed":
                completed += 1
                state["rounds_completed"] = int(state.get("rounds_completed", 0)) + 1
            state["rounds_attempted"] = int(state.get("rounds_attempted", 0)) + 1
            if result.get("decision") in stop_decisions:
                state["status"] = "stopped"
                state["reason"] = f"decision={result.get('decision')}"
                break
        except Exception as exc:
            failures += 1
            state["rounds_attempted"] = int(state.get("rounds_attempted", 0)) + 1
            append_attempt(run_dir, {"round": round_number, "mode": spec.get("mode") or plan.get("mode"), "status": "error", "error": str(exc)})
            if active_pending_round(run_dir):
                abort_reason = f"runner error: {exc}"
                class AbortArgs:
                    pass
                abort_args = AbortArgs()
                abort_args.run_dir = str(run_dir)
                abort_args.reason = abort_reason
                abort_args.round = round_number
                abort_args.branch_id = spec.get("branch_id") or None
                cmd_abort_round(abort_args)
            if failures >= max_failures:
                state["status"] = "failed"
                state["reason"] = f"max failures reached: {failures}"
                break
    if args.dry_run:
        state["status"] = "prepared"
    elif state.get("status") == "running":
        state["status"] = "completed" if completed else "stopped"
    state["failures"] = failures
    state["finished_at"] = now_iso()
    write_runner_state(run_dir, state)
    if args.digest:
        cmd_digest(argparse.Namespace(run_dir=run_dir_display))
    print(json.dumps({"state": state, "results": results}, ensure_ascii=False, indent=2))
    return 0


def cmd_abort_round(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    round_number = int(args.round or 0)
    branch_id = args.branch_id or ""
    pending_paths = []
    if round_number and branch_id:
        pending_paths.append(pending_round_path(run_dir, round_number, branch_id))
    pending_paths.append(run_dir / "pending_round.json")
    pending_path = next((path for path in pending_paths if path.exists()), None)
    pending = read_json(pending_path, {}) if pending_path else {}
    record = {
        "round": int(pending.get("round", args.round or 1)),
        "started_at": pending.get("started_at", now_iso()),
        "ended_at": now_iso(),
        "timebox_minutes": pending.get("timebox_minutes", 0),
        "branch_id": pending.get("branch_id", args.branch_id or "b001"),
        "hypothesis": "Round aborted before completion.",
        "probe": args.reason,
        "actions": [{"kind": "other", "summary": "abort-round", "result": args.reason}],
        "network_used": False,
        "skills_used": [],
        "subagents_used": [],
        "files_touched": [],
        "evidence": [],
        "scores": {"novelty": 0, "promise": 0, "evidence": 0, "risk": 1, "cost": 1},
        "reflection": f"Round aborted: {args.reason}",
        "decision": "stop",
        "next_probe": "",
    }
    record["scores"]["total"] = compute_total(record["scores"])
    append_jsonl(run_dir / "ledger.jsonl", record)
    update_frontier(run_dir, record)
    if pending_path and pending_path.exists():
        pending_path.unlink()
    print(json.dumps({"aborted": True}, ensure_ascii=False))
    return 0


def cmd_append_round(args: argparse.Namespace) -> int:
    # Backward-compatible alias for finish-round without pending state.
    return cmd_finish_round(args)


def cmd_frontier(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    print(json.dumps(read_json(run_dir / "frontier.json", {}), ensure_ascii=False, indent=2))
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    run_dir_display = args.run_dir
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    records = list(iter_ledger(run_dir))
    frontier = read_json(run_dir / "frontier.json", {})
    branches = frontier.get("branches", {})
    promoted = [r for r in records if r.get("decision") == "promote"]
    pruned = [r for r in records if r.get("decision") == "prune"]
    parked = [bid for bid, item in branches.items() if item.get("status") == "parked"]
    lines = [
        "# Exploration Digest",
        "",
        f"- Run dir: {run_dir_display}",
        f"- Records: {len(records)}",
        f"- Active branches: {', '.join(frontier.get('active', [])) or '(none)'}",
        "",
        "## Best Leads",
    ]
    if promoted:
        for item in promoted:
            lines.append(f"- {item.get('branch_id')}: {item.get('reflection')}")
    elif records:
        best = sorted(records, key=lambda r: r.get("scores", {}).get("total", 0), reverse=True)[:3]
        for item in best:
            lines.append(
                f"- {item.get('branch_id')} round {item.get('round')} score {item.get('scores', {}).get('total')}: {item.get('reflection')}"
            )
    else:
        lines.append("- No records yet.")
    lines.extend(["", "## Dead Ends"])
    if pruned:
        for item in pruned:
            lines.append(f"- {item.get('branch_id')}: {item.get('reflection')}")
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Parked Branches"])
    if parked:
        for branch_id in parked:
            branch = branches.get(branch_id, {})
            lines.append(f"- {branch_id}: {branch.get('hypothesis', '')}")
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Recommended Next Lane"])
    if promoted:
        lines.append("- Run codex-completion-loop or codex-adversarial-qa on the promoted lead.")
    elif frontier.get("active"):
        lines.append("- Continue exploration on the highest-scoring active branch.")
    else:
        lines.append("- Stop or ask for a human decision; no active branch remains.")
    output = "\n".join(lines) + "\n"
    write_text(run_dir / "final-digest.md", output)
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage codex-exploration-loop state.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--root", required=True)
    p.add_argument("--root-label", default="")
    p.add_argument("--slug", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--max-rounds", type=int, default=6)
    p.add_argument("--round-timebox-minutes", type=float, default=10)
    p.add_argument("--max-round-minutes", type=float, dest="round_timebox_minutes")
    p.add_argument("--mode", choices=["scout", "standard", "bull"], default="standard")
    p.add_argument("--scratch-worktree", default="")
    p.add_argument("--output-dir", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("start-round")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--branch-id", required=True)
    p.add_argument("--timebox-minutes", type=float, required=True)
    p.set_defaults(func=cmd_start_round)

    p = sub.add_parser("finish-round")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--record-json", required=True)
    p.set_defaults(func=cmd_finish_round)

    p = sub.add_parser("fanout")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--parent-branch", default="")
    p.add_argument("--layer-id", default="")
    p.add_argument("--candidate", action="append", help="Use 'hypothesis ||| next probe'. Can be repeated.")
    p.add_argument("--candidate-json", default="", help="JSON object or path with a candidates array.")
    p.add_argument("--beam-width", type=int, default=2)
    p.add_argument("--keep-parent-active", action="store_true")
    p.set_defaults(func=cmd_fanout)

    p = sub.add_parser("beam-select")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--layer-id", default="")
    p.add_argument("--beam-width", type=int, default=2)
    p.add_argument("--diversity-count", type=int, default=1)
    p.add_argument("--keep-unselected-active", action="store_true")
    p.set_defaults(func=cmd_beam_select)

    p = sub.add_parser("prepare-worker")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--branch-id")
    p.add_argument("--timebox-minutes", type=float)
    p.add_argument("--workspace", default="")
    p.add_argument("--probe", default="")
    p.add_argument("--hypothesis", default="")
    p.add_argument("--allowed-actions", default=DEFAULT_ALLOWED_ACTIONS)
    p.add_argument("--sandbox", choices=["read-only", "workspace-write", "danger-full-access"], default="workspace-write")
    p.add_argument("--profile", default="")
    p.add_argument("--skill-dir", default="")
    p.add_argument("--schema-path", default="")
    p.add_argument("--portable", action="store_true")
    p.add_argument("--no-start", action="store_true")
    p.set_defaults(func=cmd_prepare_worker)

    p = sub.add_parser("finish-worker")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--worker-output", required=True)
    p.set_defaults(func=cmd_finish_worker)

    p = sub.add_parser("import-worker")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--worker-output", required=True)
    p.set_defaults(func=cmd_finish_worker)

    p = sub.add_parser("write-plan")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--output", default="")
    p.set_defaults(func=cmd_write_plan)

    p = sub.add_parser("run-plan")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--plan", default="")
    p.add_argument("--max-rounds", type=int)
    p.add_argument("--max-failures", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--digest", action="store_true")
    p.set_defaults(func=cmd_run_plan)

    p = sub.add_parser("abort-round")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--round", type=int)
    p.add_argument("--branch-id")
    p.set_defaults(func=cmd_abort_round)

    p = sub.add_parser("append-round")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--record-json", required=True)
    p.set_defaults(func=cmd_append_round)

    p = sub.add_parser("frontier")
    p.add_argument("--run-dir", required=True)
    p.set_defaults(func=cmd_frontier)

    p = sub.add_parser("digest")
    p.add_argument("--run-dir", required=True)
    p.set_defaults(func=cmd_digest)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
