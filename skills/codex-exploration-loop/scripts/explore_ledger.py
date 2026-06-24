#!/usr/bin/env python3
"""State helper for codex-exploration-loop.

This script does not call Codex or any LLM. It creates run directories, validates
basic round records, appends JSONL, updates frontier state, and writes digests.
"""

from __future__ import annotations

import argparse
import json
import re
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
    if not isinstance(loaded, dict):
        raise ValueError("JSON value must be an object")
    return loaded


def load_json_arg(value: str) -> Dict[str, Any]:
    candidate = Path(value)
    if candidate.exists():
        return parse_json_text(read_text(candidate))
    return parse_json_text(value)


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


def write_pending_round(run_dir: Path, round_number: int, branch_id: str, timebox_minutes: float) -> Dict[str, Any]:
    pending = {
        "round": round_number,
        "branch_id": branch_id,
        "timebox_minutes": timebox_minutes,
        "started_at": now_iso(),
        "status": "pending",
    }
    write_json(run_dir / "pending_round.json", pending)
    return pending


def initial_frontier(question: str) -> Dict[str, Any]:
    return {
        "active": ["b001"],
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

    active = []
    for bid, item in branches.items():
        if item.get("status") == "active":
            active.append(bid)
    active.sort(key=lambda bid: branches[bid].get("last_score", 0), reverse=True)
    frontier["active"] = active[:3]
    write_json(frontier_path, frontier)
    return frontier


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
    pending = {
        "round": args.round,
        "branch_id": args.branch_id,
        "timebox_minutes": args.timebox_minutes,
        "started_at": now_iso(),
        "status": "pending",
    }
    write_json(run_dir / "pending_round.json", pending)
    print(json.dumps(pending, ensure_ascii=False))
    return 0


def finish_record(run_dir: Path, record: Dict[str, Any]) -> Dict[str, Any]:
    ensure_run_dir(run_dir)
    pending_path = run_dir / "pending_round.json"
    if pending_path.exists():
        pending = read_json(pending_path, {})
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
    if pending_path.exists():
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


def cmd_prepare_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    run_meta = read_json(run_dir / "run.json", {})
    frontier = read_json(run_dir / "frontier.json", {})
    branch_id = choose_branch(frontier, args.branch_id)
    branch = frontier.get("branches", {}).get(branch_id)
    if not branch:
        raise ValueError(f"unknown branch_id: {branch_id}")
    round_number = args.round
    timebox_minutes = args.timebox_minutes or float(run_meta.get("round_timebox_minutes", 10))
    workspace = args.workspace or run_meta.get("scratch_worktree") or run_meta.get("root") or str(Path.cwd())
    probe = args.probe or branch.get("next_probe") or "Run the next smallest useful probe."
    hypothesis = args.hypothesis or branch.get("hypothesis") or run_meta.get("question", "")
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else SKILL_DIR
    schema_path = Path(args.schema_path).resolve() if args.schema_path else skill_dir / "schemas" / "round-result.schema.json"
    template_path = skill_dir / "prompts" / "round-worker.prompt.md"
    template = read_text(template_path)
    prefix = f"{branch_id}-round-{round_number:03d}"
    artifacts_dir = run_dir / "artifacts"
    prompt_path = artifacts_dir / f"{prefix}.prompt.md"
    result_path = artifacts_dir / f"{prefix}.result.json"
    events_path = artifacts_dir / f"{prefix}.events.jsonl"
    script_path = artifacts_dir / f"{prefix}.codex-exec.ps1"
    manifest_path = artifacts_dir / f"{prefix}.worker.json"
    if args.portable:
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
        args.allowed_actions,
    )
    write_text(prompt_path, prompt)
    write_codex_exec_script(
        script_path,
        prompt_path,
        workspace,
        args.sandbox,
        args.profile,
        worker_schema_path,
        result_path,
        events_path,
        args.portable,
    )
    pending = None
    if not args.no_start:
        pending = write_pending_round(run_dir, round_number, branch_id, timebox_minutes)
    manifest = {
        "round": round_number,
        "branch_id": branch_id,
        "workspace": workspace,
        "sandbox": args.sandbox,
        "profile": args.profile,
        "schema_path": worker_schema_path.name if args.portable else str(worker_schema_path),
        "prompt_path": prompt_path.name if args.portable else str(prompt_path),
        "result_path": result_path.name if args.portable else str(result_path),
        "events_path": events_path.name if args.portable else str(events_path),
        "script_path": script_path.name if args.portable else str(script_path),
        "portable": bool(args.portable),
        "pending_started": bool(pending),
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def cmd_finish_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    record = load_json_arg(args.worker_output)
    record = finish_record(run_dir, record)
    print(json.dumps({"imported": True, "total": record["scores"]["total"]}, ensure_ascii=False))
    return 0


def cmd_abort_round(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ensure_run_dir(run_dir)
    pending_path = run_dir / "pending_round.json"
    pending = read_json(pending_path, {})
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
    if pending_path.exists():
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
    promoted = [r for r in records if r.get("decision") == "promote"]
    pruned = [r for r in records if r.get("decision") == "prune"]
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
