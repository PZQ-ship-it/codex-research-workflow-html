#!/usr/bin/env python3
"""Deterministic human and retrieved-reference gates for quality-judge."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

EXIT_ACCEPTED = 0
EXIT_BLOCKED = 2
EXIT_INVALID = 3
EXIT_PROVISIONAL_PASS = 4
EXIT_PROVISIONAL_SHORTFALL = 5
EXIT_ANCHORED_DIAGNOSTIC = 6

CORE_FILES = ("gate-config.json", "structural-result.json", "quality-result.json")
TEMPLATE_FILES = CORE_FILES + (
    "human-reference.json",
    "rubric.json",
    "reference-set.json",
    "candidate-pool-ledger.json",
    "task-contract.json",
)
SHA256_LENGTH = 64


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


def nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def string_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must be a string list")
    if nonempty and not value:
        raise ValueError(f"{label} must not be empty")
    return [item.strip() for item in value]


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def validate_sha256(value: Any, label: str) -> str:
    text = nonempty_string(value, label).lower()
    if len(text) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    return text


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_run_path(run_dir: Path, locator: Any, label: str) -> Path:
    relative = Path(nonempty_string(locator, label))
    if relative.is_absolute():
        raise ValueError(f"{label} must be relative to the run directory")
    base = run_dir.resolve()
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the run directory") from exc
    return resolved


def config_dimensions(config: dict[str, Any]) -> list[str]:
    dimensions = config.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions or not all(isinstance(d, str) and d for d in dimensions):
        raise ValueError("config.dimensions must be a non-empty string list")
    weights = config.get("weights")
    if not isinstance(weights, dict) or set(weights) != set(dimensions):
        raise ValueError("config.weights must contain exactly config.dimensions")
    weight_sum = sum(finite_number(weights[d], f"config.weights.{d}") for d in dimensions)
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"config.weights must sum to 1.0, got {weight_sum}")
    return dimensions


def config_scale(config: dict[str, Any]) -> tuple[float, float]:
    scale = require_dict(config.get("scale"), "config.scale")
    lo = finite_number(scale.get("min"), "config.scale.min")
    hi = finite_number(scale.get("max"), "config.scale.max")
    if not lo < hi:
        raise ValueError("config.scale.min must be lower than max")
    return lo, hi


def validate_scores(
    scores: Any,
    dimensions: list[str],
    lo: float,
    hi: float,
    label: str,
) -> dict[str, float]:
    if not isinstance(scores, dict) or set(scores) != set(dimensions):
        raise ValueError(f"{label} must contain exactly config.dimensions")
    parsed = {dimension: finite_number(scores[dimension], f"{label}.{dimension}") for dimension in dimensions}
    out_of_range = [dimension for dimension, value in parsed.items() if value < lo or value > hi]
    if out_of_range:
        raise ValueError(f"{label} out of range {lo}-{hi}: {', '.join(out_of_range)}")
    return parsed


def weighted(scores: dict[str, float], config: dict[str, Any]) -> float:
    return sum(scores[dimension] * float(config["weights"][dimension]) for dimension in scores)


def load_config(run_dir: Path) -> tuple[dict[str, Any], list[str], float, float]:
    config = load_json(run_dir / "gate-config.json")
    dimensions = config_dimensions(config)
    lo, hi = config_scale(config)
    return config, dimensions, lo, hi


def human_reference_ready(
    run_dir: Path,
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> bool:
    path = run_dir / "human-reference.json"
    if not path.exists():
        return False
    reference = load_json(path)
    if reference.get("graded_by") != "human":
        return False
    validate_scores(reference.get("dimension_scores"), dimensions, lo, hi, "reference.dimension_scores")
    if int(reference.get("grader_count", 0) or 0) < 1:
        raise ValueError("human reference requires grader_count >= 1")
    if reference.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("reference.rubric_version must match config.rubric_version")
    return True


def legacy_reference_ready(
    run_dir: Path,
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> bool:
    path = run_dir / "human-reference.json"
    if not path.exists():
        return False
    reference = load_json(path)
    try:
        validate_scores(reference.get("dimension_scores"), dimensions, lo, hi, "reference.dimension_scores")
    except ValueError:
        return False
    return reference.get("rubric_version") == config.get("rubric_version")


def retrieval_state(run_dir: Path) -> tuple[str, Optional[dict[str, Any]]]:
    path = run_dir / "reference-set.json"
    if not path.exists():
        return "not_started", None
    reference_set = load_json(path)
    retrieval = reference_set.get("retrieval")
    status = retrieval.get("status", "not_started") if isinstance(retrieval, dict) else "not_started"
    references = reference_set.get("references")
    if reference_set.get("mode") == "retrieved_provisional" and isinstance(references, list) and references:
        return "completed", reference_set
    if status in {"no_eligible_reference", "failed"}:
        return status, reference_set
    return "not_started", reference_set


def determine_reference_mode(run_dir: Path) -> dict[str, Any]:
    config, dimensions, lo, hi = load_config(run_dir)
    if human_reference_ready(run_dir, config, dimensions, lo, hi):
        return {
            "reference_mode": "human_graded",
            "next_action": "run_reviewers",
            "auto_retrieve": False,
        }

    state, _ = retrieval_state(run_dir)
    if state == "completed":
        return {
            "reference_mode": "retrieved_provisional",
            "next_action": "run_reviewers_with_frozen_reference_set",
            "auto_retrieve": False,
        }
    if state in {"no_eligible_reference", "failed"}:
        return {
            "reference_mode": "reference_free_diagnostic",
            "next_action": "run_reviewers_and_route_to_needs_human",
            "auto_retrieve": False,
            "retrieval_status": state,
        }

    fallback = config.get("reference_fallback")
    auto_retrieve = isinstance(fallback, dict) and fallback.get("auto_retrieve_when_human_missing") is True
    if auto_retrieve:
        return {
            "reference_mode": "retrieve_required",
            "next_action": "search_and_freeze_reference_set_before_reviewers",
            "auto_retrieve": True,
        }
    if not isinstance(fallback, dict) and legacy_reference_ready(run_dir, config, dimensions, lo, hi):
        return {
            "reference_mode": "legacy_directional",
            "next_action": "run_reviewers",
            "auto_retrieve": False,
        }
    return {
        "reference_mode": "reference_free_diagnostic",
        "next_action": "run_reviewers_and_route_to_needs_human",
        "auto_retrieve": False,
        "retrieval_status": "disabled",
    }


def load_core_results(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    structural = load_json(run_dir / "structural-result.json")
    quality = load_json(run_dir / "quality-result.json")
    if structural.get("reviewer") != "structural_reviewer":
        raise ValueError("structural.reviewer must be structural_reviewer")
    if quality.get("reviewer") != "quality_judge":
        raise ValueError("quality.reviewer must be quality_judge")
    critical_failures = structural.get("critical_failures")
    if not isinstance(critical_failures, list):
        raise ValueError("structural.critical_failures must be a list")
    return structural, quality


def validate_quality_result(
    quality: dict[str, Any],
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> tuple[dict[str, float], float, list[str]]:
    scores = validate_scores(quality.get("dimension_scores"), dimensions, lo, hi, "quality.dimension_scores")
    confidence = finite_number(quality.get("confidence"), "quality.confidence")
    reasons: list[str] = []
    if confidence < finite_number(config.get("min_confidence", 0.8), "config.min_confidence"):
        reasons.append("quality_confidence_below_floor")
    if bool(config.get("require_quality_evidence", True)):
        evidence = quality.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            reasons.append("quality_evidence_required")
    require_list(quality.get("reference_comparisons"), "quality.reference_comparisons")
    require_list(quality.get("structural_concerns", []), "quality.structural_concerns")
    require_list(quality.get("counterexamples"), "quality.counterexamples")
    require_list(quality.get("revision_actions"), "quality.revision_actions")
    return scores, confidence, reasons


def structural_reasons(structural: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if structural.get("pass") is not True:
        reasons.append("structural_reviewer_failed")
    if structural.get("critical_failures") and "structural_reviewer_failed" not in reasons:
        reasons.append("structural_critical_failures_present")
    return reasons


def critical_dimensions(config: dict[str, Any], dimensions: list[str]) -> tuple[list[str], float]:
    critical = config.get("critical_dimensions", [])
    if not isinstance(critical, list) or not all(dimension in dimensions for dimension in critical):
        raise ValueError("config.critical_dimensions must reference configured dimensions")
    floor = finite_number(config.get("critical_floor", config["scale"]["min"]), "config.critical_floor")
    return critical, floor


def absolute_quality_contract(
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> tuple[float, dict[str, float]]:
    overall_floor = finite_number(config.get("absolute_quality_floor", lo), "config.absolute_quality_floor")
    if overall_floor < lo or overall_floor > hi:
        raise ValueError("config.absolute_quality_floor is outside the score scale")
    raw_floors = config.get("dimension_floors")
    if raw_floors is None:
        raw_floors = {dimension: lo for dimension in dimensions}
    floors = require_dict(raw_floors, "config.dimension_floors")
    if set(floors) != set(dimensions):
        raise ValueError("config.dimension_floors must contain exactly config.dimensions")
    parsed = {
        dimension: finite_number(floors[dimension], f"config.dimension_floors.{dimension}")
        for dimension in dimensions
    }
    if any(value < lo or value > hi for value in parsed.values()):
        raise ValueError("config.dimension_floors contains an out-of-range value")
    return overall_floor, parsed


def validate_comparison_mode(config: dict[str, Any]) -> str:
    mode = config.get("comparison_mode", "hybrid")
    if mode not in {"weighted_overall", "all_dimensions", "hybrid"}:
        raise ValueError(f"unsupported comparison_mode: {mode}")
    return mode


def evaluate_human(run_dir: Path) -> dict[str, Any]:
    config, dimensions, lo, hi = load_config(run_dir)
    reference_path = run_dir / "human-reference.json"
    reference = load_json(reference_path)
    structural, quality = load_core_results(run_dir)
    if reference.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("reference.rubric_version must match config.rubric_version")
    reference_scores = validate_scores(reference.get("dimension_scores"), dimensions, lo, hi, "reference.dimension_scores")
    quality_scores, confidence, reasons = validate_quality_result(quality, config, dimensions, lo, hi)
    if bool(config.get("require_human_reference", True)) and reference.get("graded_by") != "human":
        reasons.append("human_reference_required")
    if int(reference.get("grader_count", 0) or 0) < 1:
        reasons.append("reference_grader_count_missing")

    calibration = quality.get("calibration")
    calibration = calibration if isinstance(calibration, dict) else {}
    if bool(config.get("require_calibration", True)) and calibration.get("human_anchored") is not True:
        reasons.append("human_calibration_required")
    max_leniency = finite_number(config.get("max_abs_leniency", 0.25), "config.max_abs_leniency")
    leniency = calibration.get("leniency")
    if bool(config.get("require_calibration", True)):
        if leniency is None:
            reasons.append("leniency_missing")
        elif abs(finite_number(leniency, "quality.calibration.leniency")) > max_leniency:
            reasons.append("judge_leniency_above_limit")

    candidate_overall = weighted(quality_scores, config)
    reference_overall = weighted(reference_scores, config)
    margin = finite_number(config.get("reference_margin", 0.0), "config.reference_margin")
    critical, floor = critical_dimensions(config, dimensions)
    low_critical = [dimension for dimension in critical if quality_scores[dimension] < floor]
    if low_critical:
        reasons.append("critical_dimension_below_floor:" + ",".join(low_critical))

    mode = validate_comparison_mode(config)
    if mode in {"weighted_overall", "hybrid"} and candidate_overall < reference_overall + margin:
        reasons.append("weighted_score_below_reference_plus_margin")
    if mode == "all_dimensions":
        below = [dimension for dimension in dimensions if quality_scores[dimension] < reference_scores[dimension] + margin]
        if below:
            reasons.append("dimension_score_below_reference_plus_margin:" + ",".join(below))

    reasons.extend(structural_reasons(structural))
    if config.get("require_both_reviewers", True) and quality.get("pass") is False:
        reasons.append("quality_reviewer_failed")
    status = "accepted" if not reasons else "blocked"
    if any(reason in reasons for reason in (
        "human_reference_required",
        "human_calibration_required",
        "leniency_missing",
        "quality_confidence_below_floor",
    )):
        status = "needs_human"
    files = {name: run_dir / name for name in CORE_FILES}
    files["human-reference.json"] = reference_path
    return {
        "schema_version": "1.0",
        "status": status,
        "reference_mode": "human_graded" if reference.get("graded_by") == "human" else "legacy_directional",
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


def evaluate_reference_free(run_dir: Path, mode_info: dict[str, Any]) -> dict[str, Any]:
    config, dimensions, lo, hi = load_config(run_dir)
    structural, quality = load_core_results(run_dir)
    quality_scores, confidence, reasons = validate_quality_result(quality, config, dimensions, lo, hi)
    if require_list(quality.get("reference_comparisons"), "quality.reference_comparisons"):
        raise ValueError("reference-free diagnostic requires an empty reference_comparisons list")
    reasons.insert(0, "reference_unavailable")
    if mode_info.get("reference_mode") == "retrieve_required":
        reasons.append("reference_retrieval_not_completed")
    if quality.get("pass") is False:
        reasons.append("quality_reviewer_failed")
    hard_reasons = structural_reasons(structural)
    reasons.extend(hard_reasons)
    status = "blocked" if hard_reasons else "needs_human"
    files = {name: run_dir / name for name in CORE_FILES}
    reference_set_path = run_dir / "reference-set.json"
    if reference_set_path.exists():
        files["reference-set.json"] = reference_set_path
    if mode_info.get("retrieval_status") in {"no_eligible_reference", "failed"}:
        files.update(validate_terminal_retrieval_state(run_dir, config))
    return {
        "schema_version": config.get("schema_version", "1.1"),
        "status": status,
        "reference_mode": "reference_free_diagnostic",
        "reasons": reasons,
        "candidate_overall": round(weighted(quality_scores, config), 6),
        "reference_overall": None,
        "reference_margin": finite_number(config.get("reference_margin", 0.0), "config.reference_margin"),
        "comparison_mode": validate_comparison_mode(config),
        "comparison_pass": False,
        "order_consistent": None,
        "confidence": confidence,
        "structural_pass": structural.get("pass") is True,
        "quality_reviewer_pass": quality.get("pass") is not False,
        "provisional_reason": "no_eligible_reference",
        "input_hashes": {name: sha256(path) for name, path in files.items()},
    }


def validate_candidate_pool(
    run_dir: Path,
    retrieval: dict[str, Any],
    reference_set: dict[str, Any],
    fallback: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], Path, dict[str, Any]]:
    ledger_info = require_dict(retrieval.get("candidate_pool_ledger"), "reference_set.retrieval.candidate_pool_ledger")
    ledger_path = safe_run_path(run_dir, ledger_info.get("locator"), "candidate_pool_ledger.locator")
    expected_hash = validate_sha256(ledger_info.get("sha256"), "candidate_pool_ledger.sha256")
    if sha256(ledger_path) != expected_hash:
        raise ValueError("candidate_pool_ledger SHA-256 mismatch")
    ledger = load_json(ledger_path)
    if reference_set.get("schema_version") == "1.2" and ledger.get("schema_version") != "1.1":
        raise ValueError("schema 1.2 requires candidate-pool-ledger schema 1.1")
    if ledger.get("provider") != retrieval.get("provider"):
        raise ValueError("candidate pool provider must match reference-set retrieval")
    if ledger.get("queries") != retrieval.get("queries"):
        raise ValueError("candidate pool queries must match reference-set retrieval")
    if ledger.get("searched_at") != retrieval.get("searched_at"):
        raise ValueError("candidate pool searched_at must match reference-set retrieval")
    entries = require_list(ledger.get("entries"), "candidate_pool_ledger.entries")
    expected_count = int(ledger_info.get("entry_count", -1))
    pool_size = int(retrieval.get("pool_size", -1))
    if expected_count != len(entries) or pool_size != len(entries):
        raise ValueError("candidate pool entry counts must match")

    query_records = require_list(retrieval.get("queries"), "reference_set.retrieval.queries")
    query_ids: set[str] = set()
    for index, query_record in enumerate(query_records):
        record = require_dict(query_record, f"reference_set.retrieval.queries[{index}]")
        query_id = nonempty_string(record.get("query_id"), f"queries[{index}].query_id")
        nonempty_string(record.get("query"), f"queries[{index}].query")
        if query_id in query_ids:
            raise ValueError(f"duplicate query_id: {query_id}")
        query_ids.add(query_id)

    entries_by_id: dict[str, dict[str, Any]] = {}
    allowed_mime_types = set(string_list(
        fallback.get("allowed_mime_types", ["text/html", "text/plain", "application/pdf"]),
        "reference_fallback.allowed_mime_types",
        nonempty=True,
    ))
    max_snapshot_bytes = int(fallback.get("max_snapshot_bytes", 5_000_000))
    if max_snapshot_bytes < 1:
        raise ValueError("reference_fallback.max_snapshot_bytes must be positive")
    for index, raw_entry in enumerate(entries):
        entry = require_dict(raw_entry, f"candidate_pool_ledger.entries[{index}]")
        candidate_id = nonempty_string(entry.get("candidate_id"), f"entries[{index}].candidate_id")
        if candidate_id in entries_by_id:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        entry_query_ids = string_list(entry.get("query_ids"), f"entries[{index}].query_ids", nonempty=True)
        if not set(entry_query_ids).issubset(query_ids):
            raise ValueError(f"entries[{index}].query_ids reference unknown queries")
        ranks = require_list(entry.get("result_ranks"), f"entries[{index}].result_ranks")
        if len(ranks) != len(entry_query_ids) or not all(isinstance(rank, int) and rank > 0 for rank in ranks):
            raise ValueError(f"entries[{index}].result_ranks must align with query_ids")
        source_url = nonempty_string(entry.get("source_url"), f"entries[{index}].source_url")
        if not source_url.startswith(("https://", "http://")):
            raise ValueError(f"entries[{index}].source_url must be HTTP(S)")
        nonempty_string(entry.get("source_date"), f"entries[{index}].source_date")
        nonempty_string(entry.get("retrieved_at"), f"entries[{index}].retrieved_at")
        nonempty_string(entry.get("license_or_access_basis"), f"entries[{index}].license_or_access_basis")
        snapshot_path = safe_run_path(run_dir, entry.get("snapshot_locator"), f"entries[{index}].snapshot_locator")
        content_hash = validate_sha256(entry.get("content_sha256"), f"entries[{index}].content_sha256")
        if sha256(snapshot_path) != content_hash:
            raise ValueError(f"snapshot hash mismatch for {candidate_id}")
        size_bytes = int(entry.get("size_bytes", -1))
        if size_bytes != snapshot_path.stat().st_size:
            raise ValueError(f"snapshot size mismatch for {candidate_id}")
        if not isinstance(entry.get("included"), bool):
            raise ValueError(f"entries[{index}].included must be boolean")
        nonempty_string(entry.get("decision_reason"), f"entries[{index}].decision_reason")
        if reference_set.get("schema_version") == "1.2":
            nonempty_string(entry.get("mime_type"), f"entries[{index}].mime_type")
            if not isinstance(entry.get("active_content_neutralized"), bool):
                raise ValueError(f"entries[{index}].active_content_neutralized must be boolean")
            if not isinstance(entry.get("remote_resources_disabled"), bool):
                raise ValueError(f"entries[{index}].remote_resources_disabled must be boolean")
            if not isinstance(entry.get("suspicious_content"), bool):
                raise ValueError(f"entries[{index}].suspicious_content must be boolean")
        if entry["included"]:
            mime_type = nonempty_string(entry.get("mime_type"), f"entries[{index}].mime_type")
            if mime_type not in allowed_mime_types:
                raise ValueError(f"included snapshot MIME type is not allowed: {candidate_id}")
            if size_bytes > max_snapshot_bytes:
                raise ValueError(f"included snapshot exceeds max_snapshot_bytes: {candidate_id}")
            if entry.get("active_content_neutralized") is not True:
                raise ValueError(f"included snapshot active content is not neutralized: {candidate_id}")
            if entry.get("remote_resources_disabled") is not True:
                raise ValueError(f"included snapshot remote resources are not disabled: {candidate_id}")
            if entry.get("suspicious_content") is not False:
                raise ValueError(f"included snapshot has suspicious content: {candidate_id}")
        entries_by_id[candidate_id] = entry

    references = require_list(reference_set.get("references"), "reference_set.references")
    included_ids = {candidate_id for candidate_id, entry in entries_by_id.items() if entry["included"]}
    source_ids = {
        nonempty_string(require_dict(reference, "reference").get("source_candidate_id"), "reference.source_candidate_id")
        for reference in references
    }
    if not source_ids.issubset(included_ids):
        raise ValueError("every reference must map to an included candidate-pool entry")
    return entries_by_id, ledger_path, ledger


def validate_terminal_retrieval_state(run_dir: Path, config: dict[str, Any]) -> dict[str, Path]:
    reference_set_path = run_dir / "reference-set.json"
    reference_set = load_json(reference_set_path)
    if reference_set.get("schema_version") != "1.2":
        return {"reference-set.json": reference_set_path}
    if reference_set.get("mode") != "auto":
        raise ValueError("terminal retrieval state must retain auto mode")
    task = require_dict(reference_set.get("task_fingerprint"), "reference_set.task_fingerprint")
    if task.get("fingerprint_minimized") is not True or task.get("outbound_query_safe") is not True:
        raise ValueError("terminal retrieval task fingerprint must be minimized and outbound-safe")
    if task.get("contains_private_data") is not False:
        raise ValueError("terminal retrieval task fingerprint contains private data")
    retrieval = require_dict(reference_set.get("retrieval"), "reference_set.retrieval")
    status = retrieval.get("status")
    if status not in {"no_eligible_reference", "failed"}:
        raise ValueError("terminal retrieval status is invalid")
    nonempty_string(retrieval.get("provider"), "retrieval.provider")
    nonempty_string(retrieval.get("searched_at"), "retrieval.searched_at")
    queries = require_list(retrieval.get("queries"), "retrieval.queries")
    fallback = require_dict(config.get("reference_fallback"), "config.reference_fallback")
    if status == "no_eligible_reference" and len(queries) < int(fallback.get("min_queries", 2)):
        raise ValueError("no_eligible_reference requires the configured query budget")
    if status == "failed":
        nonempty_string(retrieval.get("failure_reason"), "retrieval.failure_reason")
    if require_list(reference_set.get("references"), "reference_set.references"):
        raise ValueError("terminal retrieval state must not contain selected references")
    entries_by_id, ledger_path, _ = validate_candidate_pool(run_dir, retrieval, reference_set, fallback)
    files = {
        "reference-set.json": reference_set_path,
        "candidate-pool-ledger.json": ledger_path,
    }
    for candidate_id, entry in entries_by_id.items():
        files[f"snapshot:{candidate_id}"] = safe_run_path(run_dir, entry["snapshot_locator"], f"snapshot.{candidate_id}")
    return files


def add_run_evidence_files(
    run_dir: Path,
    locators: Any,
    label: str,
    files: dict[str, Path],
) -> None:
    for index, locator in enumerate(string_list(locators, label, nonempty=True)):
        path = safe_run_path(run_dir, locator, f"{label}[{index}]")
        if not path.is_file():
            raise ValueError(f"evidence locator does not exist: {locator}")
        files[f"{label}:{index}"] = path


def summarize_anchor_panel(
    records: dict[str, dict[str, Any]],
    panel: dict[str, Any],
) -> dict[str, Any]:
    anchors = {
        reference_id: record
        for reference_id, record in records.items()
        if "calibration_anchor" in record["roles"]
    }
    preferred_min = int(panel.get("preferred_min", 3))
    preferred_max = int(panel.get("preferred_max", 5))
    if preferred_min < 1 or preferred_max < preferred_min:
        raise ValueError("anchor_panel preferred_min/preferred_max are invalid")
    if len(anchors) > preferred_max:
        raise ValueError("anchor panel exceeds preferred_max")
    required_bands = string_list(panel.get("required_bands"), "anchor_panel.required_bands", nonempty=True)
    if not set(required_bands).issubset({"low", "boundary", "high"}):
        raise ValueError("anchor_panel.required_bands contains an unsupported band")
    separation = finite_number(panel.get("min_score_separation", 0.2), "anchor_panel.min_score_separation")
    if separation < 0:
        raise ValueError("anchor_panel.min_score_separation must be non-negative")
    if not isinstance(panel.get("allow_one_shot"), bool):
        raise ValueError("anchor_panel.allow_one_shot must be boolean")
    if len(anchors) == 1 and panel.get("allow_one_shot") is not True:
        raise ValueError("one-shot anchor panel is disabled")

    band_scores: dict[str, list[float]] = {"low": [], "boundary": [], "high": []}
    self_labeled: list[str] = []
    for reference_id, record in anchors.items():
        band_scores[record["quality_band"]].append(record["overall"])
        if record["band_provenance"] == "self_labeled":
            self_labeled.append(reference_id)

    order_consistent = True
    ordered_bands = ("low", "boundary", "high")
    populated = [band for band in ordered_bands if band_scores[band]]
    for lower, higher in zip(populated, populated[1:]):
        if max(band_scores[lower]) + separation > min(band_scores[higher]):
            order_consistent = False
    coverage_complete = len(anchors) >= preferred_min and set(required_bands).issubset(set(populated))
    return {
        "reference_ids": sorted(anchors),
        "count": len(anchors),
        "bands_present": populated,
        "coverage_complete": coverage_complete,
        "order_consistent": order_consistent,
        "self_labeled_reference_ids": sorted(self_labeled),
        "band_score_ranges": {
            band: [round(min(scores), 6), round(max(scores), 6)]
            for band, scores in band_scores.items()
            if scores
        },
    }


def validate_retrieved_reference_set_v12(
    run_dir: Path,
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str], dict[str, Path], int, str, dict[str, Any]]:
    reference_set_path = run_dir / "reference-set.json"
    reference_set = load_json(reference_set_path)
    task = require_dict(reference_set.get("task_fingerprint"), "reference_set.task_fingerprint")
    artifact_type = nonempty_string(task.get("artifact_type"), "task_fingerprint.artifact_type")
    audience = nonempty_string(task.get("audience"), "task_fingerprint.audience")
    if task.get("fingerprint_minimized") is not True or task.get("outbound_query_safe") is not True:
        raise ValueError("task fingerprint must be minimized and safe for outbound search")
    if task.get("contains_private_data") is not False:
        raise ValueError("task_fingerprint.contains_private_data must be false")
    if task.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("task_fingerprint.rubric_version must match config")
    critical, _ = critical_dimensions(config, dimensions)
    if set(string_list(task.get("critical_dimensions"), "task_fingerprint.critical_dimensions")) != set(critical):
        raise ValueError("task_fingerprint.critical_dimensions must match config")

    policy = require_dict(reference_set.get("evaluation_policy"), "reference_set.evaluation_policy")
    if policy.get("policy_version") != "1.2":
        raise ValueError("schema 1.2 requires evaluation policy 1.2")
    if validate_sha256(policy.get("policy_sha256"), "evaluation_policy.policy_sha256") != sha256(run_dir / "gate-config.json"):
        raise ValueError("evaluation_policy.policy_sha256 must hash gate-config.json")
    if policy.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("evaluation_policy.rubric_version must match config")
    rubric_path = safe_run_path(run_dir, policy.get("rubric_locator"), "evaluation_policy.rubric_locator")
    rubric_hash = validate_sha256(policy.get("rubric_sha256"), "evaluation_policy.rubric_sha256")
    if rubric_hash != sha256(rubric_path):
        raise ValueError("evaluation_policy.rubric_sha256 must hash the rubric artifact")
    rubric = load_json(rubric_path)
    if rubric.get("schema_version") != "1.2" or rubric.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("rubric must use schema 1.2 and match config.rubric_version")

    generation = require_dict(rubric.get("generation"), "rubric.generation")
    if generation.get("authority") != "task_contract":
        raise ValueError("rubric authority must be task_contract")
    task_contract_path = safe_run_path(run_dir, generation.get("task_contract_locator"), "rubric.generation.task_contract_locator")
    if validate_sha256(generation.get("task_contract_sha256"), "rubric.generation.task_contract_sha256") != sha256(task_contract_path):
        raise ValueError("rubric task contract hash mismatch")
    task_contract = load_json(task_contract_path)
    if task_contract.get("artifact_type") != artifact_type or task_contract.get("audience") != audience:
        raise ValueError("task contract must match the frozen task fingerprint")
    nonempty_string(task_contract.get("use_case"), "task_contract.use_case")
    string_list(task_contract.get("goals"), "task_contract.goals", nonempty=True)
    string_list(task_contract.get("constraints"), "task_contract.constraints")
    string_list(task_contract.get("non_goals"), "task_contract.non_goals")
    string_list(task_contract.get("quality_outcomes"), "task_contract.quality_outcomes", nonempty=True)
    validate_sha256(task_contract.get("candidate_sha256"), "task_contract.candidate_sha256")
    if generation.get("candidate_seen_during_drafting") is not False:
        raise ValueError("candidate must remain hidden while drafting the rubric")
    example_audit = require_dict(generation.get("example_audit"), "rubric.generation.example_audit")
    if example_audit.get("performed") is not True or example_audit.get("rubric_refrozen_after_audit") is not True:
        raise ValueError("retrieved mode requires a completed example audit and refrozen rubric")
    audited_reference_ids = string_list(example_audit.get("reference_ids"), "rubric.example_audit.reference_ids", nonempty=True)
    require_list(example_audit.get("dimension_proposals"), "rubric.example_audit.dimension_proposals")

    lane_contract = require_dict(rubric.get("quality_lane_contract"), "rubric.quality_lane_contract")
    if lane_contract.get("structural_result_hidden_until_scoring") is not True:
        raise ValueError("quality judge must be blind to the structural verdict while scoring")
    string_list(lane_contract.get("hard_checks_excluded"), "rubric.quality_lane_contract.hard_checks_excluded", nonempty=True)
    rubric_dimensions = require_dict(rubric.get("dimensions"), "rubric.dimensions")
    if set(rubric_dimensions) != set(dimensions):
        raise ValueError("rubric.dimensions must match config.dimensions")
    for dimension in dimensions:
        record = require_dict(rubric_dimensions[dimension], f"rubric.dimensions.{dimension}")
        nonempty_string(record.get("description"), f"rubric.dimensions.{dimension}.description")
        scale_anchors = require_dict(record.get("scale_anchors"), f"rubric.dimensions.{dimension}.scale_anchors")
        low_anchor = str(int(lo)) if lo.is_integer() else str(lo)
        high_anchor = str(int(hi)) if hi.is_integer() else str(hi)
        if low_anchor not in scale_anchors or high_anchor not in scale_anchors:
            raise ValueError(f"rubric scale anchors must define {low_anchor} and {high_anchor}: {dimension}")
        nonempty_string(scale_anchors[low_anchor], f"rubric.dimensions.{dimension}.scale_anchors.{low_anchor}")
        nonempty_string(scale_anchors[high_anchor], f"rubric.dimensions.{dimension}.scale_anchors.{high_anchor}")
        if record.get("origin") not in {"task_contract", "human_example", "mixed"}:
            raise ValueError(f"gating dimension has an unsupported origin: {dimension}")
        if record.get("lane_owner") != "quality_judge":
            raise ValueError(f"quality rubric dimension has the wrong lane owner: {dimension}")
        nonempty_string(record.get("task_trace"), f"rubric.dimensions.{dimension}.task_trace")
        if record.get("structural_overlap_check") != "passed":
            raise ValueError(f"quality rubric dimension overlaps the structural lane: {dimension}")
        if record.get("gating") is not True:
            raise ValueError(f"config dimensions must be gating quality dimensions: {dimension}")

    margin = finite_number(policy.get("reference_margin"), "evaluation_policy.reference_margin")
    if abs(margin - finite_number(config.get("reference_margin", 0.0), "config.reference_margin")) > 1e-9:
        raise ValueError("evaluation_policy.reference_margin must match config")
    overall_floor, dimension_floors = absolute_quality_contract(config, dimensions, lo, hi)
    if abs(finite_number(policy.get("absolute_quality_floor"), "evaluation_policy.absolute_quality_floor") - overall_floor) > 1e-9:
        raise ValueError("evaluation_policy.absolute_quality_floor must match config")
    policy_dimensions = require_dict(policy.get("dimensions"), "evaluation_policy.dimensions")
    if set(policy_dimensions) != set(dimensions):
        raise ValueError("evaluation_policy.dimensions must match config.dimensions")
    for dimension in dimensions:
        dimension_policy = require_dict(policy_dimensions[dimension], f"evaluation_policy.dimensions.{dimension}")
        if abs(finite_number(dimension_policy.get("weight"), f"evaluation_policy.dimensions.{dimension}.weight") - float(config["weights"][dimension])) > 1e-9:
            raise ValueError(f"evaluation_policy weight mismatch: {dimension}")
        if abs(finite_number(dimension_policy.get("floor"), f"evaluation_policy.dimensions.{dimension}.floor") - dimension_floors[dimension]) > 1e-9:
            raise ValueError(f"evaluation_policy floor mismatch: {dimension}")
        if dimension_policy.get("critical") is not (dimension in critical):
            raise ValueError(f"evaluation_policy critical flag mismatch: {dimension}")
    scoring_lanes = string_list(policy.get("scoring_lanes"), "evaluation_policy.scoring_lanes", nonempty=True)
    if len(scoring_lanes) != 1:
        raise ValueError("schema 1.2 retrieved mode requires exactly one scoring lane")
    scoring_lane = scoring_lanes[0]

    retrieval = require_dict(reference_set.get("retrieval"), "reference_set.retrieval")
    if retrieval.get("status") != "completed":
        raise ValueError("retrieval.status must be completed")
    nonempty_string(retrieval.get("provider"), "retrieval.provider")
    nonempty_string(retrieval.get("searched_at"), "retrieval.searched_at")
    if retrieval.get("selector_blinded_to_candidate") is not True or retrieval.get("reference_set_frozen") is not True:
        raise ValueError("selector blinding and a frozen reference set are required")
    selector = require_dict(retrieval.get("selector"), "reference_set.retrieval.selector")
    nonempty_string(selector.get("selector_id"), "retrieval.selector.selector_id")
    nonempty_string(selector.get("model"), "retrieval.selector.model")
    validate_sha256(selector.get("prompt_sha256"), "retrieval.selector.prompt_sha256")
    if selector.get("independence") not in {"model", "prompt_only"}:
        raise ValueError("retrieval.selector.independence must be model or prompt_only")

    fallback = require_dict(config.get("reference_fallback"), "config.reference_fallback")
    min_queries = int(fallback.get("min_queries", 2))
    if len(require_list(retrieval.get("queries"), "retrieval.queries")) < min_queries:
        raise ValueError(f"retrieval requires at least {min_queries} queries")
    entries_by_id, ledger_path, _ = validate_candidate_pool(run_dir, retrieval, reference_set, fallback)
    references = require_list(reference_set.get("references"), "reference_set.references")
    if not references:
        raise ValueError("reference_set.references must not be empty")
    if len(references) > int(fallback.get("max_references", 5)):
        raise ValueError("reference set exceeds max_references")

    records: dict[str, dict[str, Any]] = {}
    tiers: list[str] = []
    blocking_issues: list[str] = []
    diagnostic_reasons: list[str] = []
    evidence_files: dict[str, Path] = {}
    for index, raw_reference in enumerate(references):
        reference = require_dict(raw_reference, f"reference_set.references[{index}]")
        reference_id = nonempty_string(reference.get("reference_id"), f"references[{index}].reference_id")
        if reference_id in records:
            raise ValueError(f"duplicate reference_id: {reference_id}")
        roles = string_list(reference.get("roles"), f"references[{index}].roles", nonempty=True)
        if not set(roles).issubset({"calibration_anchor", "challenge_frontier"}):
            raise ValueError(f"unsupported reference role: {reference_id}")
        quality_band = reference.get("quality_band")
        if quality_band not in {"low", "boundary", "high"}:
            raise ValueError(f"invalid quality band: {reference_id}")
        band_provenance = reference.get("band_provenance")
        if band_provenance not in {"human", "objective_metric", "independent_judge", "self_labeled"}:
            raise ValueError(f"invalid band provenance: {reference_id}")
        tier = reference.get("tier")
        if tier not in {"retrieved_verified", "retrieved_ungraded", "model_adapted"}:
            raise ValueError(f"unsupported reference tier: {tier}")
        tiers.append(tier)
        source_candidate_id = nonempty_string(reference.get("source_candidate_id"), f"references[{index}].source_candidate_id")
        if source_candidate_id not in entries_by_id:
            raise ValueError(f"reference maps to an unknown candidate-pool entry: {reference_id}")
        candidate_entry = entries_by_id[source_candidate_id]
        source_url = nonempty_string(reference.get("source_url"), f"references[{index}].source_url")
        if source_url != candidate_entry["source_url"]:
            raise ValueError(f"reference source URL mismatch: {reference_id}")
        content_hash = validate_sha256(reference.get("content_sha256"), f"references[{index}].content_sha256")
        if content_hash != candidate_entry["content_sha256"]:
            raise ValueError(f"reference content hash mismatch: {reference_id}")
        for field in ("source_date", "retrieved_at", "license_or_access_basis"):
            if nonempty_string(reference.get(field), f"references[{index}].{field}") != candidate_entry[field]:
                raise ValueError(f"reference {field} mismatch: {reference_id}")
        if reference.get("authorship") not in {"human", "model", "mixed", "unknown"}:
            raise ValueError(f"invalid authorship: {reference_id}")
        selection = require_dict(reference.get("selection"), f"references[{index}].selection")
        if string_list(selection.get("query_ids"), f"references[{index}].selection.query_ids", nonempty=True) != candidate_entry["query_ids"]:
            raise ValueError(f"reference query provenance mismatch: {reference_id}")
        if require_list(selection.get("result_ranks"), f"references[{index}].selection.result_ranks") != candidate_entry["result_ranks"]:
            raise ValueError(f"reference rank provenance mismatch: {reference_id}")
        nonempty_string(selection.get("inclusion_reason"), f"references[{index}].selection.inclusion_reason")
        comparability = require_dict(reference.get("comparability"), f"references[{index}].comparability")
        string_list(comparability.get("reasons"), f"references[{index}].comparability.reasons", nonempty=True)
        if comparability.get("hard_pass") is not True:
            blocking_issues.append(f"reference_not_comparable:{reference_id}")

        verification = require_dict(reference.get("verification"), f"references[{index}].verification")
        verified = tier == "retrieved_verified" and verification.get("status") == "verified"
        if verified:
            verification_dimensions = require_dict(verification.get("dimensions"), f"references[{index}].verification.dimensions")
            for dimension in critical:
                verification_record = require_dict(verification_dimensions.get(dimension), f"verification.{reference_id}.{dimension}")
                if verification_record.get("status") != "verified":
                    raise ValueError(f"critical dimension is not verified: {reference_id}/{dimension}")
                nonempty_string(verification_record.get("method"), f"verification.{reference_id}.{dimension}.method")
                add_run_evidence_files(run_dir, verification_record.get("evidence_locators"), f"verification.{reference_id}.{dimension}", evidence_files)
                nonempty_string(verification_record.get("verified_by"), f"verification.{reference_id}.{dimension}.verified_by")
                if verification_record.get("verifier_independence") not in {"independent", "prompt_only"}:
                    raise ValueError(f"invalid verifier independence: {reference_id}/{dimension}")
                nonempty_string(verification_record.get("verified_at"), f"verification.{reference_id}.{dimension}.verified_at")
            if require_list(verification.get("conflicts"), f"references[{index}].verification.conflicts"):
                blocking_issues.append(f"reference_verification_conflict:{reference_id}")
        elif "challenge_frontier" in roles:
            blocking_issues.append(f"challenge_frontier_not_verified:{reference_id}")
        else:
            diagnostic_reasons.append(f"anchor_not_verified:{reference_id}:{tier}")

        if "challenge_frontier" in roles:
            if quality_band != "high":
                blocking_issues.append(f"challenge_frontier_not_high_band:{reference_id}")
            if band_provenance == "self_labeled":
                blocking_issues.append(f"challenge_frontier_self_labeled:{reference_id}")

        scoring = require_dict(reference.get("scoring"), f"references[{index}].scoring")
        if scoring.get("rubric_version") != config.get("rubric_version"):
            raise ValueError(f"reference rubric version mismatch: {reference_id}")
        if validate_sha256(scoring.get("rubric_sha256"), f"scoring.{reference_id}.rubric_sha256") != rubric_hash:
            raise ValueError(f"reference rubric hash mismatch: {reference_id}")
        scoring_dimensions = require_dict(scoring.get("dimensions"), f"references[{index}].scoring.dimensions")
        if set(scoring_dimensions) != set(dimensions):
            raise ValueError(f"reference scoring dimensions mismatch: {reference_id}")
        scores: dict[str, float] = {}
        for dimension in dimensions:
            score_record = require_dict(scoring_dimensions[dimension], f"scoring.{reference_id}.{dimension}")
            score = finite_number(score_record.get("score"), f"scoring.{reference_id}.{dimension}.score")
            if score < lo or score > hi:
                raise ValueError(f"reference score out of range: {reference_id}/{dimension}")
            add_run_evidence_files(run_dir, score_record.get("evidence_locators"), f"scoring.{reference_id}.{dimension}", evidence_files)
            if nonempty_string(score_record.get("judge_id"), f"scoring.{reference_id}.{dimension}.judge_id") != scoring_lane:
                raise ValueError(f"reference score uses an unconfigured lane: {reference_id}")
            nonempty_string(score_record.get("model"), f"scoring.{reference_id}.{dimension}.model")
            validate_sha256(score_record.get("prompt_sha256"), f"scoring.{reference_id}.{dimension}.prompt_sha256")
            string_list(score_record.get("trial_ids"), f"scoring.{reference_id}.{dimension}.trial_ids", nonempty=True)
            if score_record.get("conflict_state") not in {"none", "resolved", "unresolved"}:
                raise ValueError(f"invalid conflict state: {reference_id}/{dimension}")
            if score_record.get("conflict_state") == "unresolved":
                blocking_issues.append(f"reference_score_conflict:{reference_id}:{dimension}")
            scores[dimension] = score
        if require_list(scoring.get("conflicts"), f"references[{index}].scoring.conflicts"):
            blocking_issues.append(f"reference_scoring_conflict:{reference_id}")
        snapshot_path = safe_run_path(run_dir, candidate_entry["snapshot_locator"], f"snapshot.{reference_id}")
        evidence_files[f"snapshot:{reference_id}"] = snapshot_path
        records[reference_id] = {
            "scores": scores,
            "overall": weighted(scores, config),
            "tier": tier,
            "roles": roles,
            "quality_band": quality_band,
            "band_provenance": band_provenance,
        }

    if set(audited_reference_ids) != set(records):
        raise ValueError("rubric example audit must cover the frozen reference set")
    aggregation = require_dict(reference_set.get("aggregation"), "reference_set.aggregation")
    if aggregation.get("method") != "anchor_panel_plus_frontier":
        raise ValueError("schema 1.2 requires anchor_panel_plus_frontier aggregation")
    panel = require_dict(aggregation.get("anchor_panel"), "aggregation.anchor_panel")
    configured_panel = require_dict(fallback.get("anchor_panel"), "reference_fallback.anchor_panel")
    if panel != configured_panel:
        raise ValueError("aggregation.anchor_panel must match gate config")
    anchor_summary = summarize_anchor_panel(records, panel)
    if not anchor_summary["order_consistent"]:
        blocking_issues.append("anchor_panel_non_monotonic")
    if not anchor_summary["coverage_complete"]:
        diagnostic_reasons.append("few_shot_anchor_coverage_incomplete")
    if anchor_summary["self_labeled_reference_ids"]:
        diagnostic_reasons.append("self_labeled_anchors_are_diagnostic_only")
    frontier_ids = sorted(
        reference_id for reference_id, record in records.items()
        if "challenge_frontier" in record["roles"]
    )
    if not frontier_ids:
        diagnostic_reasons.append("no_verified_challenge_frontier")
    if aggregation.get("pairwise_order_swap") is not True or aggregation.get("require_no_critical_regression") is not True:
        raise ValueError("frontier comparison requires order swap and no critical regression")
    artifact_level = require_dict(aggregation.get("artifact_level"), "aggregation.artifact_level")
    trials_per_order = int(artifact_level.get("trials_per_order", 0))
    if trials_per_order < 1 or trials_per_order > 20:
        raise ValueError("aggregation.artifact_level.trials_per_order must be 1-20")
    if artifact_level.get("decision_rule") != "unanimous_across_orders_and_trials":
        raise ValueError("unsupported artifact-level decision rule")
    if artifact_level.get("confidence_intervals") is not False:
        raise ValueError("single-artifact confidence intervals must be false")

    files = {
        "reference-set.json": reference_set_path,
        "candidate-pool-ledger.json": ledger_path,
        "rubric.json": rubric_path,
        "task-contract.json": task_contract_path,
        **evidence_files,
    }
    metadata = {
        "schema_version": "1.2",
        "frontier_ids": frontier_ids,
        "anchor_panel": anchor_summary,
        "diagnostic_reasons": diagnostic_reasons,
        "absolute_quality_floor": overall_floor,
        "dimension_floors": dimension_floors,
    }
    return records, tiers, blocking_issues, files, trials_per_order, scoring_lane, metadata


def validate_retrieved_reference_set(
    run_dir: Path,
    config: dict[str, Any],
    dimensions: list[str],
    lo: float,
    hi: float,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str], dict[str, Path], int, str, dict[str, Any]]:
    reference_set_path = run_dir / "reference-set.json"
    reference_set = load_json(reference_set_path)
    if reference_set.get("schema_version") == "1.2":
        if reference_set.get("mode") != "retrieved_provisional":
            raise ValueError("reference-set mode must be retrieved_provisional")
        return validate_retrieved_reference_set_v12(run_dir, config, dimensions, lo, hi)
    if reference_set.get("schema_version") != "1.1" or reference_set.get("mode") != "retrieved_provisional":
        raise ValueError("reference-set must use schema 1.1 and retrieved_provisional mode")
    task = require_dict(reference_set.get("task_fingerprint"), "reference_set.task_fingerprint")
    nonempty_string(task.get("artifact_type"), "task_fingerprint.artifact_type")
    nonempty_string(task.get("audience"), "task_fingerprint.audience")
    if task.get("fingerprint_minimized") is not True:
        raise ValueError("task_fingerprint.fingerprint_minimized must be true")
    if task.get("outbound_query_safe") is not True:
        raise ValueError("task_fingerprint.outbound_query_safe must be true")
    if task.get("contains_private_data") is not False:
        raise ValueError("task_fingerprint.contains_private_data must be false")
    if task.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("task_fingerprint.rubric_version must match config")
    critical, floor = critical_dimensions(config, dimensions)
    if set(string_list(task.get("critical_dimensions"), "task_fingerprint.critical_dimensions")) != set(critical):
        raise ValueError("task_fingerprint.critical_dimensions must match config")

    policy = require_dict(reference_set.get("evaluation_policy"), "reference_set.evaluation_policy")
    nonempty_string(policy.get("policy_version"), "evaluation_policy.policy_version")
    policy_hash = validate_sha256(policy.get("policy_sha256"), "evaluation_policy.policy_sha256")
    if policy_hash != sha256(run_dir / "gate-config.json"):
        raise ValueError("evaluation_policy.policy_sha256 must hash gate-config.json")
    if policy.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("evaluation_policy.rubric_version must match config")
    rubric_path = safe_run_path(run_dir, policy.get("rubric_locator"), "evaluation_policy.rubric_locator")
    rubric_hash = validate_sha256(policy.get("rubric_sha256"), "evaluation_policy.rubric_sha256")
    if rubric_hash != sha256(rubric_path):
        raise ValueError("evaluation_policy.rubric_sha256 must hash the rubric artifact")
    rubric = load_json(rubric_path)
    if rubric.get("rubric_version") != config.get("rubric_version"):
        raise ValueError("rubric.rubric_version must match config")
    rubric_dimensions = require_dict(rubric.get("dimensions"), "rubric.dimensions")
    if set(rubric_dimensions) != set(dimensions):
        raise ValueError("rubric.dimensions must match config.dimensions")
    for dimension in dimensions:
        rubric_dimension = require_dict(rubric_dimensions[dimension], f"rubric.dimensions.{dimension}")
        nonempty_string(rubric_dimension.get("description"), f"rubric.dimensions.{dimension}.description")
        require_dict(rubric_dimension.get("scale_anchors"), f"rubric.dimensions.{dimension}.scale_anchors")
    margin = finite_number(policy.get("reference_margin"), "evaluation_policy.reference_margin")
    if abs(margin - finite_number(config.get("reference_margin", 0.0), "config.reference_margin")) > 1e-9:
        raise ValueError("evaluation_policy.reference_margin must match config")
    policy_dimensions = require_dict(policy.get("dimensions"), "evaluation_policy.dimensions")
    if set(policy_dimensions) != set(dimensions):
        raise ValueError("evaluation_policy.dimensions must match config.dimensions")
    for dimension in dimensions:
        dimension_policy = require_dict(policy_dimensions[dimension], f"evaluation_policy.dimensions.{dimension}")
        weight = finite_number(dimension_policy.get("weight"), f"evaluation_policy.dimensions.{dimension}.weight")
        if abs(weight - float(config["weights"][dimension])) > 1e-9:
            raise ValueError(f"evaluation_policy weight mismatch: {dimension}")
        dimension_floor = finite_number(dimension_policy.get("floor"), f"evaluation_policy.dimensions.{dimension}.floor")
        if dimension_floor < lo or dimension_floor > hi:
            raise ValueError(f"evaluation_policy floor out of range: {dimension}")
        if dimension_policy.get("critical") is not (dimension in critical):
            raise ValueError(f"evaluation_policy critical flag mismatch: {dimension}")
    scoring_lanes = string_list(policy.get("scoring_lanes"), "evaluation_policy.scoring_lanes", nonempty=True)
    if len(scoring_lanes) != 1:
        raise ValueError("schema 1.1 retrieved mode requires exactly one scoring lane")
    scoring_lane = scoring_lanes[0]

    retrieval = require_dict(reference_set.get("retrieval"), "reference_set.retrieval")
    if retrieval.get("status") != "completed":
        raise ValueError("retrieval.status must be completed")
    nonempty_string(retrieval.get("provider"), "retrieval.provider")
    nonempty_string(retrieval.get("searched_at"), "retrieval.searched_at")
    if retrieval.get("selector_blinded_to_candidate") is not True:
        raise ValueError("retrieval.selector_blinded_to_candidate must be true")
    if retrieval.get("reference_set_frozen") is not True:
        raise ValueError("retrieval.reference_set_frozen must be true")
    selector = require_dict(retrieval.get("selector"), "retrieval.selector")
    nonempty_string(selector.get("selector_id"), "retrieval.selector.selector_id")
    nonempty_string(selector.get("model"), "retrieval.selector.model")
    validate_sha256(selector.get("prompt_sha256"), "retrieval.selector.prompt_sha256")
    if selector.get("independence") not in {"model", "prompt_only"}:
        raise ValueError("retrieval.selector.independence must be model or prompt_only")

    fallback = config.get("reference_fallback") if isinstance(config.get("reference_fallback"), dict) else {}
    if fallback.get("provisional_policy", "report_only") not in {"report_only", "block_iteration"}:
        raise ValueError("reference_fallback.provisional_policy is unsupported")
    min_queries = int(fallback.get("min_queries", 2))
    if len(require_list(retrieval.get("queries"), "retrieval.queries")) < min_queries:
        raise ValueError(f"retrieval requires at least {min_queries} queries")
    entries_by_id, ledger_path, _ = validate_candidate_pool(run_dir, retrieval, reference_set, fallback)

    references = require_list(reference_set.get("references"), "reference_set.references")
    if not references:
        raise ValueError("reference_set.references must not be empty")
    max_references = int(fallback.get("max_references", 5))
    min_references = int(fallback.get("min_references", 1))
    if len(references) > max_references:
        raise ValueError(f"reference set exceeds max_references={max_references}")
    eligibility_issues: list[str] = []
    if len(references) < min_references:
        eligibility_issues.append("retrieved_reference_set_too_small")

    reference_records: dict[str, dict[str, Any]] = {}
    tiers: list[str] = []
    snapshot_files: dict[str, Path] = {}
    for index, raw_reference in enumerate(references):
        reference = require_dict(raw_reference, f"reference_set.references[{index}]")
        reference_id = nonempty_string(reference.get("reference_id"), f"references[{index}].reference_id")
        if reference_id in reference_records:
            raise ValueError(f"duplicate reference_id: {reference_id}")
        if reference.get("frontier") is not True:
            raise ValueError(f"reference {reference_id} must be on the frozen frontier")
        tier = reference.get("tier")
        if tier not in {"retrieved_verified", "retrieved_ungraded", "model_adapted"}:
            raise ValueError(f"unsupported reference tier: {tier}")
        tiers.append(tier)
        source_candidate_id = nonempty_string(reference.get("source_candidate_id"), f"references[{index}].source_candidate_id")
        if source_candidate_id not in entries_by_id:
            raise ValueError(f"reference maps to an unknown candidate-pool entry: {reference_id}")
        candidate_entry = entries_by_id[source_candidate_id]
        source_url = nonempty_string(reference.get("source_url"), f"references[{index}].source_url")
        if source_url != candidate_entry["source_url"]:
            raise ValueError(f"reference source URL mismatch: {reference_id}")
        content_hash = validate_sha256(reference.get("content_sha256"), f"references[{index}].content_sha256")
        if content_hash != candidate_entry["content_sha256"]:
            raise ValueError(f"reference content hash mismatch: {reference_id}")
        if nonempty_string(reference.get("source_date"), f"references[{index}].source_date") != candidate_entry["source_date"]:
            raise ValueError(f"reference source date mismatch: {reference_id}")
        if nonempty_string(reference.get("retrieved_at"), f"references[{index}].retrieved_at") != candidate_entry["retrieved_at"]:
            raise ValueError(f"reference retrieval time mismatch: {reference_id}")
        if nonempty_string(reference.get("license_or_access_basis"), f"references[{index}].license_or_access_basis") != candidate_entry["license_or_access_basis"]:
            raise ValueError(f"reference access basis mismatch: {reference_id}")
        selection = require_dict(reference.get("selection"), f"references[{index}].selection")
        selection_query_ids = string_list(selection.get("query_ids"), f"references[{index}].selection.query_ids", nonempty=True)
        selection_ranks = require_list(selection.get("result_ranks"), f"references[{index}].selection.result_ranks")
        if selection_query_ids != candidate_entry["query_ids"] or selection_ranks != candidate_entry["result_ranks"]:
            raise ValueError(f"reference selection provenance mismatch: {reference_id}")
        nonempty_string(selection.get("inclusion_reason"), f"references[{index}].selection.inclusion_reason")
        if reference.get("authorship") not in {"human", "model", "mixed", "unknown"}:
            raise ValueError(f"invalid authorship: {reference_id}")
        comparability = require_dict(reference.get("comparability"), f"references[{index}].comparability")
        require_list(comparability.get("reasons"), f"references[{index}].comparability.reasons")
        if comparability.get("hard_pass") is not True:
            eligibility_issues.append(f"reference_not_comparable:{reference_id}")

        verification = require_dict(reference.get("verification"), f"references[{index}].verification")
        if tier == "retrieved_verified":
            if verification.get("status") != "verified":
                raise ValueError(f"retrieved_verified reference is not verified: {reference_id}")
            verification_dimensions = require_dict(verification.get("dimensions"), f"references[{index}].verification.dimensions")
            for dimension in critical:
                verification_record = require_dict(
                    verification_dimensions.get(dimension),
                    f"references[{index}].verification.dimensions.{dimension}",
                )
                if verification_record.get("status") != "verified":
                    raise ValueError(f"critical dimension is not verified: {reference_id}/{dimension}")
                nonempty_string(verification_record.get("method"), f"verification.{reference_id}.{dimension}.method")
                string_list(
                    verification_record.get("evidence_locators"),
                    f"verification.{reference_id}.{dimension}.evidence_locators",
                    nonempty=True,
                )
                nonempty_string(verification_record.get("verified_by"), f"verification.{reference_id}.{dimension}.verified_by")
                if verification_record.get("verifier_independence") not in {"independent", "prompt_only"}:
                    raise ValueError(f"invalid verifier independence: {reference_id}/{dimension}")
                nonempty_string(verification_record.get("verified_at"), f"verification.{reference_id}.{dimension}.verified_at")
            if require_list(verification.get("conflicts"), f"references[{index}].verification.conflicts"):
                eligibility_issues.append(f"reference_verification_conflict:{reference_id}")
        else:
            eligibility_issues.append(f"reference_tier_not_verified:{reference_id}:{tier}")

        scoring = require_dict(reference.get("scoring"), f"references[{index}].scoring")
        if scoring.get("rubric_version") != config.get("rubric_version"):
            raise ValueError(f"reference rubric version mismatch: {reference_id}")
        if validate_sha256(scoring.get("rubric_sha256"), f"scoring.{reference_id}.rubric_sha256") != rubric_hash:
            raise ValueError(f"reference rubric hash mismatch: {reference_id}")
        scoring_dimensions = require_dict(scoring.get("dimensions"), f"references[{index}].scoring.dimensions")
        if set(scoring_dimensions) != set(dimensions):
            raise ValueError(f"reference scoring dimensions mismatch: {reference_id}")
        scores: dict[str, float] = {}
        for dimension in dimensions:
            score_record = require_dict(scoring_dimensions[dimension], f"scoring.{reference_id}.{dimension}")
            score = finite_number(score_record.get("score"), f"scoring.{reference_id}.{dimension}.score")
            if score < lo or score > hi:
                raise ValueError(f"reference score out of range: {reference_id}/{dimension}")
            string_list(score_record.get("evidence_locators"), f"scoring.{reference_id}.{dimension}.evidence_locators", nonempty=True)
            judge_id = nonempty_string(score_record.get("judge_id"), f"scoring.{reference_id}.{dimension}.judge_id")
            if judge_id not in scoring_lanes:
                raise ValueError(f"reference score uses an unconfigured lane: {judge_id}")
            nonempty_string(score_record.get("model"), f"scoring.{reference_id}.{dimension}.model")
            validate_sha256(score_record.get("prompt_sha256"), f"scoring.{reference_id}.{dimension}.prompt_sha256")
            string_list(score_record.get("trial_ids"), f"scoring.{reference_id}.{dimension}.trial_ids", nonempty=True)
            if score_record.get("conflict_state") not in {"none", "resolved", "unresolved"}:
                raise ValueError(f"invalid conflict state: {reference_id}/{dimension}")
            if score_record.get("conflict_state") == "unresolved":
                eligibility_issues.append(f"reference_score_conflict:{reference_id}:{dimension}")
            scores[dimension] = score
        if require_list(scoring.get("conflicts"), f"references[{index}].scoring.conflicts"):
            eligibility_issues.append(f"reference_scoring_conflict:{reference_id}")
        snapshot_path = safe_run_path(run_dir, candidate_entry["snapshot_locator"], f"snapshot.{reference_id}")
        snapshot_files[f"snapshot:{reference_id}"] = snapshot_path
        reference_records[reference_id] = {
            "scores": scores,
            "overall": weighted(scores, config),
            "tier": tier,
        }

    aggregation = require_dict(reference_set.get("aggregation"), "reference_set.aggregation")
    if aggregation.get("method") != "pareto_frontier":
        raise ValueError("aggregation.method must be pareto_frontier")
    if aggregation.get("pairwise_order_swap") is not True:
        raise ValueError("aggregation.pairwise_order_swap must be true")
    if aggregation.get("require_no_critical_regression") is not True:
        raise ValueError("aggregation.require_no_critical_regression must be true")
    artifact_level = require_dict(aggregation.get("artifact_level"), "aggregation.artifact_level")
    trials_per_order = int(artifact_level.get("trials_per_order", 0))
    if trials_per_order < 1 or trials_per_order > 20:
        raise ValueError("aggregation.artifact_level.trials_per_order must be 1-20")
    if artifact_level.get("decision_rule") != "unanimous_across_orders_and_trials":
        raise ValueError("unsupported artifact-level decision rule")
    if artifact_level.get("confidence_intervals") is not False:
        raise ValueError("single-artifact confidence intervals must be false")

    files = {
        "reference-set.json": reference_set_path,
        "candidate-pool-ledger.json": ledger_path,
        "rubric.json": rubric_path,
        **snapshot_files,
    }
    metadata = {
        "schema_version": "1.1",
        "frontier_ids": sorted(reference_records),
        "anchor_panel": {
            "reference_ids": [],
            "count": 0,
            "bands_present": [],
            "coverage_complete": False,
            "order_consistent": True,
            "self_labeled_reference_ids": [],
            "band_score_ranges": {},
        },
        "diagnostic_reasons": [],
        "absolute_quality_floor": lo,
        "dimension_floors": {dimension: lo for dimension in dimensions},
    }
    return reference_records, tiers, eligibility_issues, files, trials_per_order, scoring_lane, metadata


def pairwise_state(values: list[Any], trials: int, label: str) -> str:
    if len(values) != trials or any(value not in {"candidate", "reference", "tie"} for value in values):
        raise ValueError(f"{label} must contain {trials} candidate/reference/tie outcomes")
    unique = set(values)
    if unique == {"candidate"}:
        return "candidate"
    if unique == {"reference"}:
        return "reference"
    return "inconsistent"


def evaluate_retrieved(run_dir: Path) -> dict[str, Any]:
    config, dimensions, lo, hi = load_config(run_dir)
    structural, quality = load_core_results(run_dir)
    quality_scores, confidence, quality_reasons = validate_quality_result(quality, config, dimensions, lo, hi)
    reference_records, tiers, eligibility_issues, reference_files, trials, scoring_lane, metadata = validate_retrieved_reference_set(
        run_dir, config, dimensions, lo, hi
    )
    if quality.get("scoring_lane") != scoring_lane:
        raise ValueError("quality.scoring_lane must match the frozen evaluation policy")
    critical, _ = critical_dimensions(config, dimensions)
    margin = finite_number(config.get("reference_margin", 0.0), "config.reference_margin")
    candidate_overall = weighted(quality_scores, config)
    absolute_floor = float(metadata["absolute_quality_floor"])
    dimension_floors = metadata["dimension_floors"]
    below_absolute_dimensions = [
        dimension for dimension in dimensions
        if quality_scores[dimension] < dimension_floors[dimension]
    ]
    absolute_pass = candidate_overall >= absolute_floor and not below_absolute_dimensions
    frontier_ids = metadata["frontier_ids"]
    comparisons = require_list(quality.get("reference_comparisons"), "quality.reference_comparisons")
    comparison_by_id: dict[str, dict[str, Any]] = {}
    for index, raw_comparison in enumerate(comparisons):
        comparison = require_dict(raw_comparison, f"quality.reference_comparisons[{index}]")
        reference_id = nonempty_string(comparison.get("reference_id"), f"reference_comparisons[{index}].reference_id")
        if reference_id in comparison_by_id:
            raise ValueError(f"duplicate reference comparison: {reference_id}")
        bias_audit = require_dict(comparison.get("bias_audit"), f"reference_comparisons[{index}].bias_audit")
        if bias_audit.get("verbosity_relation") not in {"candidate_longer", "reference_longer", "similar", "unknown"}:
            raise ValueError(f"invalid verbosity_relation for {reference_id}")
        if bias_audit.get("format_relation") not in {"material", "minor", "none", "unknown"}:
            raise ValueError(f"invalid format_relation for {reference_id}")
        if bias_audit.get("source_family_overlap") not in {True, False, "unknown"}:
            raise ValueError(f"invalid source_family_overlap for {reference_id}")
        if bias_audit.get("judge_family_overlap") not in {True, False, "unknown"}:
            raise ValueError(f"invalid judge_family_overlap for {reference_id}")
        string_list(bias_audit.get("suspected_confounds"), f"bias_audit.{reference_id}.suspected_confounds")
        if not isinstance(bias_audit.get("unresolved"), bool):
            raise ValueError(f"bias_audit.unresolved must be boolean for {reference_id}")
        comparison_by_id[reference_id] = comparison
    if set(comparison_by_id) != set(frontier_ids):
        raise ValueError("quality.reference_comparisons must cover exactly the challenge frontier")

    comparison_results: list[dict[str, Any]] = []
    comparison_states: list[str] = []
    order_consistent = True
    for reference_id in frontier_ids:
        reference = reference_records[reference_id]
        comparison = comparison_by_id[reference_id]
        if comparison["bias_audit"]["unresolved"]:
            eligibility_issues.append(f"reference_comparison_bias_unresolved:{reference_id}")
        first_state = pairwise_state(
            require_list(comparison.get("candidate_first"), f"comparison.{reference_id}.candidate_first"),
            trials,
            f"comparison.{reference_id}.candidate_first",
        )
        second_state = pairwise_state(
            require_list(comparison.get("reference_first"), f"comparison.{reference_id}.reference_first"),
            trials,
            f"comparison.{reference_id}.reference_first",
        )
        if first_state != second_state or first_state == "inconsistent":
            pairwise = "inconsistent"
            order_consistent = False
        else:
            pairwise = first_state
        pointwise_pass = candidate_overall >= reference["overall"] + margin
        pointwise_pass = pointwise_pass and all(
            quality_scores[dimension] >= reference["scores"][dimension]
            for dimension in critical
        )
        if pairwise == "candidate" and pointwise_pass:
            state = "pass"
        elif pairwise == "reference" and not pointwise_pass:
            state = "shortfall"
        else:
            state = "inconsistent"
            order_consistent = False
        comparison_states.append(state)
        comparison_results.append({
            "reference_id": reference_id,
            "tier": reference["tier"],
            "roles": reference.get("roles", ["challenge_frontier"]),
            "quality_band": reference.get("quality_band"),
            "candidate_overall": round(candidate_overall, 6),
            "reference_overall": round(reference["overall"], 6),
            "pointwise_pass": pointwise_pass,
            "pairwise_state": pairwise,
            "result": state,
        })

    hard_reasons = structural_reasons(structural)
    needs_human_reasons = list(quality_reasons) + eligibility_issues
    if not order_consistent:
        needs_human_reasons.append("reference_comparison_inconsistent")
    if quality.get("pass") is False and comparison_states and all(state == "pass" for state in comparison_states):
        needs_human_reasons.append("quality_pass_conflicts_with_reference_comparisons")

    reasons = list(hard_reasons)
    reasons.extend(needs_human_reasons)
    reasons.extend(metadata["diagnostic_reasons"])
    if hard_reasons:
        status = "blocked"
        provisional_reason = "structural_failure"
    elif needs_human_reasons:
        status = "needs_human"
        provisional_reason = "reference_or_judge_evidence_insufficient"
    elif not absolute_pass:
        status = "provisional_shortfall"
        provisional_reason = "absolute_quality_floor_not_met"
        reasons.append("human_calibration_pending")
        if candidate_overall < absolute_floor:
            reasons.append("candidate_overall_below_absolute_floor")
        if below_absolute_dimensions:
            reasons.append("candidate_dimensions_below_absolute_floor:" + ",".join(below_absolute_dimensions))
    elif frontier_ids and all(state == "pass" for state in comparison_states):
        status = "provisional_outperforms_retrieved"
        provisional_reason = "all_frontier_references_outperformed"
        reasons.append("human_calibration_pending")
    elif frontier_ids and all(state in {"pass", "shortfall"} for state in comparison_states) and "shortfall" in comparison_states:
        status = "provisional_shortfall"
        provisional_reason = "one_or_more_frontier_references_not_outperformed"
        reasons.append("human_calibration_pending")
    elif metadata["anchor_panel"]["count"] > 0 and not frontier_ids:
        status = "anchored_diagnostic"
        provisional_reason = "anchors_calibrated_scale_without_challenge_frontier"
        reasons.append("human_calibration_pending")
    else:
        status = "needs_human"
        provisional_reason = "comparison_not_separable"
        reasons.append("reference_comparison_not_separable")

    files = {name: run_dir / name for name in CORE_FILES}
    files.update(reference_files)
    reference_set_hash = sha256(run_dir / "reference-set.json")
    return {
        "schema_version": metadata["schema_version"],
        "status": status,
        "reference_mode": "retrieved_provisional",
        "reference_tiers": sorted(set(tiers)),
        "reference_set_hash": reference_set_hash,
        "reasons": reasons,
        "candidate_overall": round(candidate_overall, 6),
        "reference_overall": None,
        "reference_margin": margin,
        "absolute_quality_floor": absolute_floor,
        "absolute_floor_pass": absolute_pass,
        "below_absolute_dimensions": below_absolute_dimensions,
        "anchor_panel": metadata["anchor_panel"],
        "frontier_reference_ids": frontier_ids,
        "comparison_mode": "anchor_panel_plus_frontier" if metadata["schema_version"] == "1.2" else "all_frontier_conjunction",
        "comparison_pass": status == "provisional_outperforms_retrieved",
        "order_consistent": order_consistent,
        "comparisons": comparison_results,
        "confidence": confidence,
        "structural_pass": structural.get("pass") is True,
        "quality_reviewer_pass": quality.get("pass") is not False,
        "provisional_reason": provisional_reason,
        "input_hashes": {name: sha256(path) for name, path in files.items()},
    }


def evaluate(run_dir: Path) -> dict[str, Any]:
    mode_info = determine_reference_mode(run_dir)
    mode = mode_info["reference_mode"]
    if mode == "human_graded":
        return evaluate_human(run_dir)
    if mode == "legacy_directional":
        return evaluate_human(run_dir)
    if mode == "retrieved_provisional":
        return evaluate_retrieved(run_dir)
    return evaluate_reference_free(run_dir, mode_info)


def init_run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).resolve().parent.parent / "assets" / "templates"
    for name in TEMPLATE_FILES:
        shutil.copyfile(template_dir / name, out_dir / name)
    print(f"initialized {out_dir}")


def result_exit_code(status: str) -> int:
    if status == "accepted":
        return EXIT_ACCEPTED
    if status == "provisional_outperforms_retrieved":
        return EXIT_PROVISIONAL_PASS
    if status == "provisional_shortfall":
        return EXIT_PROVISIONAL_SHORTFALL
    if status == "anchored_diagnostic":
        return EXIT_ANCHORED_DIAGNOSTIC
    return EXIT_BLOCKED


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--out", required=True, type=Path)
    reference_mode = sub.add_parser("reference-mode")
    reference_mode.add_argument("--run-dir", required=True, type=Path)
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
        if args.command == "reference-mode":
            print(json.dumps(determine_reference_mode(args.run_dir), ensure_ascii=False, indent=2))
            return EXIT_ACCEPTED
        result = evaluate(args.run_dir)
        if args.command == "validate":
            print(json.dumps({"valid": True, "status_preview": result["status"]}, indent=2))
            return EXIT_ACCEPTED
        if args.out:
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result_exit_code(result["status"])
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
