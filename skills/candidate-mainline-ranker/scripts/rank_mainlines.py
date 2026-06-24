#!/usr/bin/env python3
"""Rank current mainline directions across professor candidates.

Input: JSON following references/input-schema.md.
Output: Markdown ranking table and optional JSON.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


POOL_MULTIPLIER = {
    "primary": 1.0,
    "extended": 0.6,
    "historical": 0.25,
}

PRIORITY_MULTIPLIER = {
    "P1": 1.0,
    "P2": 0.8,
    "P3": 0.6,
    "E1": 0.6,
    "E2": 0.45,
    "E3": 0.3,
    "unknown": 0.5,
}

CONFIDENCE_MULTIPLIER = {
    "high": 1.0,
    "medium": 0.75,
    "low": 0.45,
}

EVIDENCE_MULTIPLIER = {
    "complete": 1.0,
    "sampled": 0.8,
    "weak": 0.55,
    "stale": 0.35,
    "unknown": 0.7,
}


def norm_key(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def rank_bonus(rank: Any) -> float:
    try:
        rank_int = int(rank)
    except (TypeError, ValueError):
        return 0.0
    if rank_int == 1:
        return 0.75
    if rank_int == 2:
        return 0.35
    return 0.0


def record_score(record: dict[str, Any], mainline: dict[str, Any]) -> float:
    pool = norm_key(record.get("pool"))
    priority = norm_key(record.get("candidate_priority"))
    confidence = norm_key(mainline.get("confidence"), "medium").lower()
    evidence = norm_key(mainline.get("evidence_status"), "unknown").lower()

    return (
        (1.0 + rank_bonus(mainline.get("rank")))
        * POOL_MULTIPLIER.get(pool, POOL_MULTIPLIER["extended"])
        * PRIORITY_MULTIPLIER.get(priority, PRIORITY_MULTIPLIER["unknown"])
        * CONFIDENCE_MULTIPLIER.get(confidence, CONFIDENCE_MULTIPLIER["medium"])
        * EVIDENCE_MULTIPLIER.get(evidence, EVIDENCE_MULTIPLIER["unknown"])
    )


def aggregate(data: dict[str, Any]) -> list[dict[str, Any]]:
    directions: dict[str, dict[str, Any]] = {}

    for record in data.get("records", []):
        professor = norm_key(record.get("professor"), "unknown professor")
        pool = norm_key(record.get("pool"), "extended")
        priority = norm_key(record.get("candidate_priority"))
        source = norm_key(record.get("source"), "")

        seen_for_professor: set[str] = set()
        for mainline in record.get("mainlines", []):
            label = norm_key(mainline.get("label"), "unlabeled direction")
            key = label.lower()
            if key in seen_for_professor:
                continue
            seen_for_professor.add(key)

            score = record_score(record, mainline)
            rank = mainline.get("rank")
            confidence = norm_key(mainline.get("confidence"), "medium").lower()
            evidence = norm_key(mainline.get("evidence_status"), "unknown").lower()

            entry = directions.setdefault(
                key,
                {
                    "direction": label,
                    "weighted_score": 0.0,
                    "professors": [],
                    "raw_labels": [],
                    "sources": [],
                    "confidence_mix": Counter(),
                    "evidence_mix": Counter(),
                    "primary_count": 0,
                    "rank1_count": 0,
                },
            )
            entry["weighted_score"] += score
            entry["professors"].append(
                {
                    "name": professor,
                    "pool": pool,
                    "priority": priority,
                    "rank": rank,
                    "score": round(score, 4),
                    "confidence": confidence,
                    "evidence_status": evidence,
                    "notes": mainline.get("notes", ""),
                }
            )
            raw = norm_key(mainline.get("raw_label"), label)
            entry["raw_labels"].append(raw)
            if source:
                entry["sources"].append(source)
            entry["confidence_mix"][confidence] += 1
            entry["evidence_mix"][evidence] += 1
            if pool == "primary":
                entry["primary_count"] += 1
            try:
                if int(rank) == 1:
                    entry["rank1_count"] += 1
            except (TypeError, ValueError):
                pass

    ranked = []
    for entry in directions.values():
        professors = entry["professors"]
        ranked.append(
            {
                "direction": entry["direction"],
                "weighted_score": round(entry["weighted_score"], 4),
                "professor_count": len(professors),
                "primary_count": entry["primary_count"],
                "rank1_count": entry["rank1_count"],
                "confidence_mix": dict(entry["confidence_mix"]),
                "evidence_mix": dict(entry["evidence_mix"]),
                "professors": professors,
                "raw_labels": sorted(set(entry["raw_labels"])),
                "sources": sorted(set(entry["sources"])),
            }
        )

    ranked.sort(
        key=lambda item: (
            item["weighted_score"],
            item["professor_count"],
            item["primary_count"],
            item["rank1_count"],
        ),
        reverse=True,
    )
    return ranked


def markdown_report(data: dict[str, Any], ranked: list[dict[str, Any]]) -> str:
    metadata = data.get("metadata", {})
    lines = [
        "# Candidate Mainline Ranking",
        "",
        "## Scope",
        "",
        f"- Candidate set: {metadata.get('dataset_name', 'unknown')}",
        f"- Date: {metadata.get('date', 'unknown')}",
        f"- Professor records: {len(data.get('records', []))}",
        "",
        "## Scoring Policy",
        "",
        "- score = (1.0 + rank_bonus) * pool_multiplier * priority_multiplier * confidence_multiplier * evidence_multiplier",
        "- rank-1 bonus: +0.75; rank-2 bonus: +0.35; rank-3+: +0.0",
        "",
        "## Ranked Directions",
        "",
        "| Rank | Direction | Weighted score | Professor count | Primary count | Rank-1 count | Confidence mix | Evidence mix |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    for idx, item in enumerate(ranked, start=1):
        lines.append(
            "| {rank} | {direction} | {score:.4f} | {prof_count} | {primary} | {rank1} | {confidence} | {evidence} |".format(
                rank=idx,
                direction=item["direction"],
                score=item["weighted_score"],
                prof_count=item["professor_count"],
                primary=item["primary_count"],
                rank1=item["rank1_count"],
                confidence=", ".join(f"{k}:{v}" for k, v in sorted(item["confidence_mix"].items())),
                evidence=", ".join(f"{k}:{v}" for k, v in sorted(item["evidence_mix"].items())),
            )
        )

    lines.extend(["", "## Direction Evidence", ""])
    for item in ranked:
        profs = "; ".join(
            f"{p['name']}({p['priority']}, r{p['rank']}, {p['score']})"
            for p in item["professors"]
        )
        raw_labels = "; ".join(item["raw_labels"])
        sources = "; ".join(item["sources"])
        lines.extend(
            [
                f"### {item['direction']}",
                "",
                f"- Professors: {profs}",
                f"- Raw labels: {raw_labels}",
                f"- Sources: {sources}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    data = json.loads(args.input_json.read_text(encoding="utf-8-sig"))
    ranked = aggregate(data)
    report = markdown_report(data, ranked)

    if args.output_md:
        args.output_md.write_text(report, encoding="utf-8")
    else:
        print(report)

    if args.output_json:
        args.output_json.write_text(
            json.dumps({"ranked_directions": ranked}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
