#!/usr/bin/env python3
"""Deterministic human-anchored quality gate for the quality-judge skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

EXIT_ACCEPTED = 0
EXIT_BLOCKED = 2
EXIT_INVALID = 3


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def config_dimensions(config: dict[str, Any]) -> list[str]:
    dimensions = config.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions or not all(isinstance(d, str) for d in dimensions):
        raise ValueError("config.dimensions must be a non-empty string list")
    weights = config.get("weights")
    if not isinstance(weights, dict) or set(weights) != set(dimensions):
        raise ValueError("config.weights must contain exactly config.dimensions")
    weight_sum = sum(finite_number(weights[d], f"config.weights.{d}") for d in dimensions)
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"config.weights must sum to 1.0, got {weight_sum}")
    return dimensions


def validate_scores(scores: Any, dimensions: list[str], lo: float, hi: float, label: str) -> dict[str, float]:
    if not isinstance(scores, dict) or set(scores) != set(dimensions):
        raise ValueError(f"{label} must contain exactly config.dimensions")
    parsed = {d: finite_number(scores[d], f"{label}.{d}") for d in dimensions}
    out_of_range = [d for d, value in parsed.items() if value < lo or value > hi]
    if out_of_range:
        raise ValueError(f"{label} out of range {lo}-{hi}: {', '.join(out_of_range)}")
    return parsed


def weighted(scores: dict[str, float], config: dict[str, Any]) -> float:
    return sum(scores[d] * float(config["weights"][d]) for d in scores)


def required_files(run_dir: Path) -> dict[str, Path]:
    return {name: run_dir / name for name in (
        "gate-config.json", "human-reference.json", "structural-result.json", "quality-result.json"
    )}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(run_dir: Path) -> dict[str, Any]:
    files = required_files(run_dir)
    data = {name: load_json(path) for name, path in files.items()}
    config = data["gate-config.json"]
    dimensions = config_dimensions(config)
    scale = config.get("scale")
    if not isinstance(scale, dict):
        raise ValueError("config.scale must be an object")
    lo = finite_number(scale.get("min"), "config.scale.min")
    hi = finite_number(scale.get("max"), "config.scale.max")
    if not lo < hi:
        raise ValueError("config.scale.min must be lower than max")

    reference = data["human-reference.json"]
    structural = data["structural-result.json"]
    quality = data["quality-result.json"]
    if reference.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("reference.rubric_version must match config.rubric_version")
    reference_scores = validate_scores(reference.get("dimension_scores"), dimensions, lo, hi, "reference.dimension_scores")
    quality_scores = validate_scores(quality.get("dimension_scores"), dimensions, lo, hi, "quality.dimension_scores")

    reasons: list[str] = []
    if bool(config.get("require_human_reference", True)) and reference.get("graded_by") != "human":
        reasons.append("human_reference_required")
    if int(reference.get("grader_count", 0) or 0) < 1:
        reasons.append("reference_grader_count_missing")

    confidence = finite_number(quality.get("confidence"), "quality.confidence")
    min_confidence = finite_number(config.get("min_confidence", 0.8), "config.min_confidence")
    if confidence < min_confidence:
        reasons.append("quality_confidence_below_floor")

    calibration = quality.get("calibration")
    if not isinstance(calibration, dict):
        calibration = {}
    if bool(config.get("require_calibration", True)) and calibration.get("human_anchored") is not True:
        reasons.append("human_calibration_required")
    max_leniency = finite_number(config.get("max_abs_leniency", 0.25), "config.max_abs_leniency")
    leniency = calibration.get("leniency")
    if bool(config.get("require_calibration", True)):
        if leniency is None:
            reasons.append("leniency_missing")
        elif abs(finite_number(leniency, "quality.calibration.leniency")) > max_leniency:
            reasons.append("judge_leniency_above_limit")
    if bool(config.get("require_quality_evidence", True)):
        evidence = quality.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            reasons.append("quality_evidence_required")

    candidate_overall = weighted(quality_scores, config)
    reference_overall = weighted(reference_scores, config)
    margin = finite_number(config.get("reference_margin", 0.0), "config.reference_margin")
    critical = config.get("critical_dimensions", [])
    if not isinstance(critical, list) or not all(d in dimensions for d in critical):
        raise ValueError("config.critical_dimensions must reference configured dimensions")
    floor = finite_number(config.get("critical_floor", lo), "config.critical_floor")
    low_critical = [d for d in critical if quality_scores[d] < floor]
    if low_critical:
        reasons.append("critical_dimension_below_floor:" + ",".join(low_critical))

    mode = config.get("comparison_mode", "hybrid")
    if mode not in {"weighted_overall", "all_dimensions", "hybrid"}:
        raise ValueError(f"unsupported comparison_mode: {mode}")
    if mode in {"weighted_overall", "hybrid"} and candidate_overall < reference_overall + margin:
        reasons.append("weighted_score_below_reference_plus_margin")
    if mode == "all_dimensions":
        below = [d for d in dimensions if quality_scores[d] < reference_scores[d] + margin]
        if below:
            reasons.append("dimension_score_below_reference_plus_margin:" + ",".join(below))

    if structural.get("pass") is not True:
        reasons.append("structural_reviewer_failed")
    critical_failures = structural.get("critical_failures")
    if not isinstance(critical_failures, list):
        raise ValueError("structural.critical_failures must be a list")
    if critical_failures and "structural_reviewer_failed" not in reasons:
        reasons.append("structural_critical_failures_present")
    if config.get("require_both_reviewers", True) and quality.get("pass") is False:
        reasons.append("quality_reviewer_failed")

    status = "accepted" if not reasons else "blocked"
    if any(reason in reasons for reason in ("human_reference_required", "human_calibration_required", "leniency_missing", "quality_confidence_below_floor")):
        status = "needs_human"
    return {
        "schema_version": "1.0",
        "status": status,
        "reasons": reasons,
        "candidate_overall": round(candidate_overall, 6),
        "reference_overall": round(reference_overall, 6),
        "reference_margin": margin,
        "comparison_mode": mode,
        "confidence": confidence,
        "structural_pass": structural.get("pass") is True,
        "quality_reviewer_pass": quality.get("pass") is not False,
        "input_hashes": {name: sha256(path) for name, path in files.items()},
    }


def init_run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).resolve().parent.parent / "assets" / "templates"
    for name in ("gate-config.json", "human-reference.json", "structural-result.json", "quality-result.json"):
        shutil.copyfile(template_dir / name, out_dir / name)
    print(f"initialized {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--out", required=True, type=Path)
    validate = sub.add_parser("validate")
    validate.add_argument("--run-dir", required=True, type=Path)
    gate = sub.add_parser("gate")
    gate.add_argument("--run-dir", required=True, type=Path)
    gate.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_run(args.out)
            return EXIT_ACCEPTED
        result = evaluate(args.run_dir)
        if args.command == "validate":
            print(json.dumps({"valid": True, "status_preview": result["status"]}, indent=2))
            return EXIT_ACCEPTED
        if args.out:
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return EXIT_ACCEPTED if result["status"] == "accepted" else EXIT_BLOCKED
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
