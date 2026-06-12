#!/usr/bin/env python3
"""Planning and normalization helpers for code/model/data/benchmark evidence workflows."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse


SCHEMA_VERSION = "0.1"

SCHEMA_SUMMARY = {
    "raw/": "Untouched API JSON, scraped HTML, CSV exports, downloaded files, and logs.",
    "normalized/repos.jsonl": "Repository, code, issue, PR, release, workflow, and implementation rows.",
    "normalized/models.jsonl": "Model, dataset, Space, model-card, dataset-card, and Hub metadata rows.",
    "normalized/benchmarks.jsonl": "Benchmark, task, leaderboard, score, evaluation result, run, and metric rows.",
    "normalized/artifacts.jsonl": "Local files, downloaded assets, notebooks, logs, screenshots, and reports.",
    "sources.csv": "Source review table with source URL, priority, and status.",
    "manifest.json": "Plan, commands, limits, credential policy, timestamps, and blockers.",
    "reports/summary.md": "Human synthesis grounded in normalized row IDs.",
}

NEED_ALIASES = {
    "repo": "code",
    "repos": "code",
    "repository": "code",
    "repositories": "code",
    "implementation": "code",
    "implementations": "code",
    "hf": "models",
    "model": "models",
    "dataset": "datasets",
    "leaderboard": "leaderboards",
    "leaderboards": "leaderboards",
    "benchmark": "benchmarks",
    "bench": "benchmarks",
    "eval": "eval-results",
    "evaluation": "eval-results",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def split_csv(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip().lower().replace("_", "-")
            if part:
                out.append(NEED_ALIASES.get(part, part))
    return out


def content_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def first_present(record: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in record and record.get(key) not in (None, ""):
            return record.get(key)
    for parent_key in ["content", "cardData", "metadata", "meta"]:
        parent = record.get(parent_key)
        if isinstance(parent, dict):
            for key in keys:
                if key in parent:
                    value = content_value(parent.get(key))
                    if value not in (None, ""):
                        return value
    return None


def inspect_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    query = parse_qs(parsed.query)
    parts = [part for part in path.split("/") if part]
    result: Dict[str, Any] = {
        "url": url,
        "host": host,
        "path": "/" + path if path else "/",
        "source": "unknown",
        "source_kind": "unknown",
        "ids": {},
        "recommended_needs": [],
        "recommended_routes": [],
    }

    if host == "github.com" and len(parts) >= 2:
        owner, repo = parts[0], parts[1]
        kind = "repo"
        ids: Dict[str, Any] = {"owner": owner, "repo": repo}
        if len(parts) >= 4 and parts[2] in {"issues", "pull"}:
            kind = "issue" if parts[2] == "issues" else "pull_request"
            ids["number"] = parts[3]
        elif len(parts) >= 4 and parts[2] in {"tree", "blob"}:
            kind = "code_file" if parts[2] == "blob" else "repo_tree"
            ids["ref"] = parts[3]
            ids["path"] = "/".join(parts[4:])
        elif len(parts) >= 3 and parts[2] == "releases":
            kind = "release"
        result.update(
            {
                "source": "github",
                "source_kind": kind,
                "ids": ids,
                "recommended_needs": ["code", "metadata", "report"],
                "recommended_routes": ["github-public-api", "git-clone-public"],
            }
        )
        return result

    if "huggingface.co" in host and parts:
        source = "huggingface"
        kind = "model"
        repo_parts = parts[:2]
        if parts[0] == "datasets" and len(parts) >= 3:
            kind = "dataset"
            repo_parts = parts[1:3]
        elif parts[0] == "spaces" and len(parts) >= 3:
            kind = "space"
            repo_parts = parts[1:3]
        elif parts[0] == "papers" and len(parts) >= 2:
            kind = "paper"
            repo_parts = parts[1:2]
        elif len(parts) >= 4 and parts[2] == "blob":
            kind = "hub_file"
        repo_id = "/".join(repo_parts)
        needs = ["models", "metadata", "report"] if kind == "model" else ["datasets", "metadata", "report"]
        if kind == "space":
            needs = ["spaces", "metadata", "report"]
        if kind == "paper":
            needs = ["papers", "code", "models", "report"]
        result.update(
            {
                "source": source,
                "source_kind": kind,
                "ids": {"repo_id": repo_id},
                "recommended_needs": needs,
                "recommended_routes": ["huggingface-public-api", "hf-cli-huggingface-hub"],
            }
        )
        return result

    if "kaggle.com" in host:
        kind = parts[0] if parts else "kaggle"
        ids = {"slug": "/".join(parts[1:]) if len(parts) > 1 else path}
        result.update(
            {
                "source": "kaggle",
                "source_kind": kind,
                "ids": ids,
                "recommended_needs": ["datasets", "benchmarks", "leaderboards", "report"],
                "recommended_routes": ["kaggle-public-page"],
            }
        )
        return result

    if "openml.org" in host:
        ids = {"path": path}
        for key in ["data_id", "task_id", "run_id", "flow_id"]:
            if key in query:
                ids[key] = query[key][0]
        result.update(
            {
                "source": "openml",
                "source_kind": "ml-benchmark-platform",
                "ids": ids,
                "recommended_needs": ["datasets", "benchmarks", "runs", "report"],
                "recommended_routes": ["openml-python", "openml-api"],
            }
        )
        return result

    if "livebench.ai" in host or (host == "github.com" and parts[:2] == ["LiveBench", "LiveBench"]):
        result.update(
            {
                "source": "livebench",
                "source_kind": "benchmark",
                "ids": {"path": path},
                "recommended_needs": ["benchmarks", "leaderboards", "datasets", "report"],
                "recommended_routes": ["livebench-repo", "livebench-hf-datasets"],
            }
        )
        return result

    if "arena.ai" in host or "lmarena" in host:
        result.update(
            {
                "source": "arena",
                "source_kind": "leaderboard",
                "ids": {"path": path},
                "recommended_needs": ["leaderboards", "benchmarks", "report"],
                "recommended_routes": ["arena-official-page", "arena-snapshot-json"],
            }
        )
        return result

    if "paperswithcode" in host or "codesota.com" in host:
        source = "paperswithcode-archive" if "paperswithcode" in host else "codesota"
        result.update(
            {
                "source": source,
                "source_kind": "paper-code-benchmark-linkage",
                "ids": {"path": path},
                "recommended_needs": ["code", "papers", "benchmarks", "report"],
                "recommended_routes": ["paperswithcode-archive", "codesota"],
            }
        )
        return result

    return result


def classify_target(target: str) -> Dict[str, Any]:
    if re.match(r"https?://", target):
        return inspect_url(target)
    return {
        "url": "",
        "host": "",
        "path": "",
        "source": "topic",
        "source_kind": "query",
        "ids": {"query": target},
        "recommended_needs": ["code", "models", "datasets", "benchmarks", "report"],
        "recommended_routes": ["github-public-api", "huggingface-public-api", "huggingface-leaderboard-api"],
    }


def route_for_needs(needs: List[str], target_info: Dict[str, Any], scale: str) -> List[Dict[str, Any]]:
    needset = set(needs)
    source = target_info.get("source")
    routes: List[Dict[str, Any]] = []

    if source == "github" or needset & {"code", "issues", "prs", "releases", "actions"}:
        routes.append(
            {
                "lane": "github-public-api",
                "priority": "primary",
                "why": "Default narrowed route for public GitHub metadata, code, issues, PRs, commits, releases, Actions, and discussions without requiring GitHub MCP.",
                "suggested_calls": [
                    "GET https://api.github.com/repos/{owner}/{repo}",
                    "GET public issues/PRs/releases endpoints as rate limits allow",
                    "git clone --depth 1 for public source inspection when needed",
                ],
                "setup": ["No token required for small public reads; record rate-limit blockers and use user-authorized tokens only when explicitly approved."],
            }
        )
        routes.append(
            {
                "lane": "github-mcp",
                "priority": "optional",
                "why": "Optional convenience route if the user already has GitHub MCP configured or needs richer authenticated access.",
                "setup": ["codex mcp add github --url https://api.githubcopilot.com/mcp/ --bearer-token-env-var GITHUB_PAT_TOKEN", "Set GITHUB_PAT_TOKEN only through user-approved secret handling."],
            }
        )

    if source == "huggingface" or needset & {"models", "datasets", "spaces", "papers", "eval-results"}:
        routes.append(
            {
                "lane": "huggingface-public-api",
                "priority": "primary",
                "why": "Default narrowed route for public HF model/dataset/Space/paper metadata and file listings without HF MCP.",
                "suggested_calls": [
                    "GET https://huggingface.co/api/models/{repo_id}",
                    "GET https://huggingface.co/api/datasets/{repo_id}",
                    "Use Dataset Viewer public endpoints where available",
                ],
                "setup": ["No token required for public resources; gated/private repos are blockers unless the user authorizes access."],
            }
        )
        routes.append(
            {
                "lane": "hf-cli-huggingface-hub",
                "priority": "primary",
                "why": "Optional local CLI/library lane for deterministic metadata, files, and dataset row access.",
                "suggested_calls": ["HfApi.model_info(...)", "HfApi.dataset_info(...)", "Dataset Viewer REST API"],
            }
        )
        routes.append(
            {
                "lane": "huggingface-mcp",
                "priority": "optional",
                "why": "Optional convenience route if HF MCP is already configured; not required for the narrowed closure.",
                "setup": ["Configure HF MCP from https://huggingface.co/settings/mcp.", "Generic Codex registration: codex mcp add huggingface --url https://huggingface.co/mcp"],
            }
        )

    if source == "kaggle" or needset & {"kaggle", "competitions", "kernels"}:
        routes.append(
            {
                "lane": "kaggle-public-page",
                "priority": "primary",
                "why": "Default narrowed route for public Kaggle pages and metadata visible without credentials.",
                "setup": ["No Kaggle token required for public page review; downloads, notebooks, and discussions may be blockers."],
            }
        )
        routes.append(
            {
                "lane": "kaggle-official-mcp",
                "priority": "optional",
                "why": "Optional route for authenticated Kaggle operations when the user explicitly approves credentials.",
                "setup": ["codex mcp add kaggle --url https://www.kaggle.com/mcp", "Run codex mcp login kaggle only when authenticated Kaggle access is needed."],
            }
        )
        routes.append(
            {
                "lane": "kaggle-mcp",
                "priority": "optional",
                "why": "Third-party local MCP adds discussion, solution write-up, and comment tools.",
                "setup": ["uvx kaggle-mcp-server with KAGGLE_API_TOKEN or kaggle.json kept private."],
            }
        )

    if source == "openml" or needset & {"openml", "runs", "tasks"}:
        routes.append(
            {
                "lane": "openml-python",
                "priority": "primary",
                "why": "OpenML Python/API covers datasets, tasks, flows, runs, evaluations, and benchmark suites.",
                "setup": ["pip install openml in an isolated environment."],
            }
        )

    if needset & {"benchmarks", "leaderboards", "eval-results"}:
        routes.append(
            {
                "lane": "huggingface-leaderboard-api",
                "priority": "primary",
                "why": "Official HF benchmark datasets expose ranked scores and per-model eval results.",
                "suggested_calls": [
                    "GET https://huggingface.co/api/datasets/{dataset_id}/leaderboard",
                    "HfApi.get_dataset_leaderboard(dataset_id)",
                    "HfApi.model_info(model_id, expand=['evalResults'])",
                ],
            }
        )
        routes.append(
            {
                "lane": "benchmark-official-repo",
                "priority": "primary",
                "why": "Use benchmark-specific official repos/datasets for LiveBench, SWE-bench, GAIA, LiveCodeBench, BigCodeBench, and similar sources.",
            }
        )

    if source in {"arena", "livebench"} or needset & {"arena", "lmarena"}:
        routes.append(
            {
                "lane": "arena-snapshot-json",
                "priority": "secondary",
                "why": "Arena/LMArena has no confirmed official public API; use official pages first and daily JSON snapshots as supplemental evidence.",
            }
        )

    if source in {"paperswithcode-archive", "codesota"} or needset & {"paper-code-linkage", "pwc"}:
        routes.append(
            {
                "lane": "paperswithcode-archive",
                "priority": "archive",
                "why": "Use historical PWC data for old paper-code-benchmark linkage; do not treat it as live leaderboard truth.",
            }
        )

    if scale in {"large", "deep"}:
        routes.append(
            {
                "lane": "aggregator-cross-check",
                "priority": "fallback",
                "why": "Use aggregators such as ALL-Bench/LLM Stats/CodeSOTA only to broaden coverage, preserving per-score provenance.",
            }
        )

    for lane in target_info.get("recommended_routes") or []:
        if not any(route.get("lane") == lane for route in routes):
            routes.append({"lane": lane, "priority": "source-specific", "why": "Suggested by URL/target inspection."})

    return dedupe_routes(routes)


def dedupe_routes(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for route in routes:
        lane = route.get("lane")
        if lane in seen:
            continue
        seen.add(lane)
        out.append(route)
    return out


def build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    needs = split_csv(args.needs)
    target_info = classify_target(args.target)
    if not needs:
        needs = target_info.get("recommended_needs") or ["code", "models", "datasets", "benchmarks", "report"]
    routes = route_for_needs(needs, target_info, args.scale)
    if not routes:
        routes = [
            {
                "lane": "manual-source-resolution",
                "priority": "fallback",
                "why": "Resolve exact repo, model/dataset ID, benchmark ID, or leaderboard URL before crawling.",
            }
        ]
    return {
        "schema_version": SCHEMA_VERSION,
        "target": args.target,
        "target_info": target_info,
        "needs": needs,
        "scale": args.scale,
        "recommended_routes": routes,
        "output_contract": SCHEMA_SUMMARY,
        "guardrails": [
            "Default to public official APIs, public pages, local clones, Hub metadata, and benchmark repos; do not require MCP, paid services, or private credentials for the base closure.",
            "Prefer official public API/Hub metadata and benchmark repos over search snippets.",
            "Keep GitHub/HF/Kaggle tokens, API keys, cookies, proxies, headers, and .env files local and untracked.",
            "Do not bypass gated/private data, paywalls, CAPTCHAs, login gates, or license controls.",
            "Record source IDs, URLs, fetch timestamps, benchmark versions, metrics, and blockers in the manifest.",
        ],
    }


def write_json(data: Any, output: Optional[str]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def command_plan(args: argparse.Namespace) -> None:
    write_json(build_plan(args), args.output)


def command_inspect_url(args: argparse.Namespace) -> None:
    write_json(inspect_url(args.url), args.output)


def command_schema(args: argparse.Namespace) -> None:
    write_json(
        {
            "schema_version": SCHEMA_VERSION,
            "directory_contract": SCHEMA_SUMMARY,
            "repo_row_required": ["row_type", "row_id", "source", "source_id", "source_url", "fetched_at"],
            "model_row_required": ["row_type", "row_id", "source", "source_id", "source_url", "fetched_at"],
            "benchmark_row_required": ["row_type", "row_id", "source", "source_id", "source_url", "fetched_at", "metric"],
            "artifact_row_required": ["row_type", "row_id", "artifact_type", "source", "local_path", "created_at"],
            "dedupe_keys": [
                "platform+owner/repo",
                "resource_type+repo_id",
                "benchmark/task/split/version/model/metric/source",
            ],
        },
        args.output,
    )


def command_scaffold(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    for rel in ["raw", "normalized", "reports"]:
        (output_dir / rel).mkdir(parents=True, exist_ok=True)
    plan = build_plan(args)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "target": args.target,
        "needs": plan["needs"],
        "created_at": now_iso(),
        "plan": plan,
        "commands": [],
        "limits": {"scale": args.scale},
        "credential_policy": "Keep GitHub/HF/Kaggle/OpenML credentials in local env or client config outside committed artifacts.",
        "blockers": [],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lane", "priority", "status", "source_url", "notes"])
        writer.writeheader()
        for route in plan["recommended_routes"]:
            writer.writerow(
                {
                    "lane": route.get("lane", ""),
                    "priority": route.get("priority", ""),
                    "status": "planned",
                    "source_url": route.get("source_hint", ""),
                    "notes": route.get("why", ""),
                }
            )
    (output_dir / "reports" / "summary.md").write_text(
        "# Code Model Benchmark Summary\n\n"
        "Status: scaffolded.\n\n"
        "Use normalized row IDs from `normalized/` when writing the final synthesis.\n",
        encoding="utf-8",
    )
    print(str(output_dir))


def load_records(path: Path) -> Iterable[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ["models", "datasets", "spaces", "items", "results", "data", "leaderboard", "runs", "tasks", "repos"]:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [data]
    return []


def infer_row_group(record: Dict[str, Any], source: str) -> str:
    text = json.dumps(record, ensure_ascii=False).lower()
    source_l = source.lower()
    if source_l in {"github", "github-mcp", "github-api"} or any(key in record for key in ["html_url", "clone_url", "full_name", "stargazers_count"]):
        return "repos"
    if "leaderboard" in source_l or "benchmark" in source_l or any(key in record for key in ["rank", "metric", "score", "value", "verified"]):
        return "benchmarks"
    if source_l in {"huggingface", "huggingface-mcp", "hf", "kaggle", "openml"} or any(token in text for token in ["model", "dataset", "space"]):
        return "models"
    return "models"


def normalize_repo(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    full_name = first_present(record, ["full_name", "nameWithOwner", "repo", "repository"])
    owner = first_present(record, ["owner"])
    if isinstance(owner, dict):
        owner = owner.get("login") or owner.get("name")
    name = first_present(record, ["name"])
    if isinstance(full_name, str) and "/" in full_name:
        owner, name = full_name.split("/", 1)
    source_id = str(first_present(record, ["id", "node_id", "sha", "number", "full_name"]) or full_name or name or "")
    source_url = first_present(record, ["html_url", "url", "source_url"]) or ""
    return {
        "row_type": "repo",
        "row_id": stable_id(source, source_id, source_url),
        "source": source,
        "source_priority": "primary" if source.startswith("github") else "secondary",
        "source_id": source_id,
        "source_url": source_url,
        "fetched_at": now_iso(),
        "owner": owner,
        "repo": name,
        "title": first_present(record, ["title", "name"]),
        "description": first_present(record, ["description"]),
        "language": first_present(record, ["language"]),
        "license": first_present(record, ["license"]),
        "stars": first_present(record, ["stargazers_count", "stars"]),
        "forks": first_present(record, ["forks_count", "forks"]),
        "open_issues": first_present(record, ["open_issues_count", "open_issues"]),
        "created_at": first_present(record, ["created_at"]),
        "updated_at": first_present(record, ["updated_at"]),
        "pushed_at": first_present(record, ["pushed_at"]),
        "raw_ref": raw_ref,
    }


def normalize_model(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    repo_id = first_present(record, ["repo_id", "modelId", "datasetId", "id", "name", "slug"])
    source_url = first_present(record, ["url", "html_url", "source_url"]) or ""
    row_type = first_present(record, ["resource_type", "type", "pipeline_tag"]) or "model"
    source_id = str(repo_id or first_present(record, ["id"]) or "")
    return {
        "row_type": str(row_type).lower().replace(" ", "_"),
        "row_id": stable_id(source, source_id, source_url),
        "source": source,
        "source_priority": "primary" if source.startswith(("huggingface", "kaggle", "openml")) else "secondary",
        "source_id": source_id,
        "source_url": source_url,
        "fetched_at": now_iso(),
        "repo_id": repo_id,
        "owner": first_present(record, ["author", "owner", "organization"]),
        "name": first_present(record, ["name", "modelId", "datasetId", "title"]),
        "resource_type": row_type,
        "task": first_present(record, ["pipeline_tag", "task", "task_categories"]),
        "library": first_present(record, ["library_name", "library"]),
        "tags": first_present(record, ["tags"]),
        "license": first_present(record, ["license"]),
        "gated": first_present(record, ["gated"]),
        "downloads": first_present(record, ["downloads", "downloadCount"]),
        "likes": first_present(record, ["likes"]),
        "created_at": first_present(record, ["created_at", "createdAt"]),
        "updated_at": first_present(record, ["lastModified", "updated_at", "updatedAt"]),
        "raw_ref": raw_ref,
    }


def normalize_benchmark(record: Dict[str, Any], source: str, raw_ref: str) -> Dict[str, Any]:
    benchmark_id = first_present(record, ["benchmark_id", "dataset_id", "datasetId", "benchmark", "leaderboard"])
    model_id = first_present(record, ["model_id", "modelId", "model", "model_name", "name"])
    metric = first_present(record, ["metric", "metric_name", "score_name"]) or "score"
    value = first_present(record, ["value", "score", "accuracy", "result"])
    source_id = str(first_present(record, ["id", "rank", "submission_id"]) or stable_id(benchmark_id, model_id, metric, value))
    source_url = first_present(record, ["url", "source_url", "leaderboard_url"]) or ""
    return {
        "row_type": "score",
        "row_id": stable_id(source, benchmark_id, model_id, metric, source_id),
        "source": source,
        "source_priority": "primary" if source in {"huggingface-leaderboard", "openml", "kaggle", "livebench"} else "secondary",
        "source_id": source_id,
        "source_url": source_url,
        "fetched_at": now_iso(),
        "benchmark_id": benchmark_id,
        "benchmark_name": first_present(record, ["benchmark_name", "benchmark"]),
        "task_name": first_present(record, ["task", "task_name"]),
        "dataset_id": first_present(record, ["dataset_id", "datasetId"]),
        "split": first_present(record, ["split"]),
        "version": first_present(record, ["version", "release"]),
        "model_id": model_id,
        "model_name": first_present(record, ["model_name", "model", "name"]),
        "provider": first_present(record, ["provider", "author", "vendor"]),
        "metric": metric,
        "value": value,
        "rank": first_present(record, ["rank"]),
        "confidence_interval": first_present(record, ["ci", "confidence_interval"]),
        "verified": first_present(record, ["verified"]),
        "verification_status": first_present(record, ["verification_status", "confidence", "level"]),
        "self_reported": first_present(record, ["self_reported"]),
        "submission_date": first_present(record, ["submission_date", "created_at"]),
        "notes": first_present(record, ["notes"]),
        "raw_ref": raw_ref,
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def command_normalize(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    records = list(load_records(input_path))
    repos: List[Dict[str, Any]] = []
    models: List[Dict[str, Any]] = []
    benchmarks: List[Dict[str, Any]] = []
    raw_ref = str(input_path)
    for record in records:
        group = args.kind or infer_row_group(record, args.source)
        if group == "repos":
            repos.append(normalize_repo(record, args.source, raw_ref))
        elif group == "benchmarks":
            benchmarks.append(normalize_benchmark(record, args.source, raw_ref))
        else:
            models.append(normalize_model(record, args.source, raw_ref))
    counts = {
        "repos": write_jsonl(output_dir / "repos.jsonl", repos),
        "models": write_jsonl(output_dir / "models.jsonl", models),
        "benchmarks": write_jsonl(output_dir / "benchmarks.jsonl", benchmarks),
        "artifacts": write_jsonl(output_dir / "artifacts.jsonl", []),
    }
    counts["output_dir"] = str(output_dir)
    write_json(counts, args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Plan source routes for a code/model/data/benchmark task.")
    plan.add_argument("--target", required=True)
    plan.add_argument("--needs", action="append", help="Comma-separated needs such as code,models,datasets,benchmarks,leaderboards,report.")
    plan.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="medium")
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    inspect = sub.add_parser("inspect-url", help="Classify a source URL.")
    inspect.add_argument("url")
    inspect.add_argument("--output")
    inspect.set_defaults(func=command_inspect_url)

    schema = sub.add_parser("schema", help="Print the normalized output schema.")
    schema.add_argument("--output")
    schema.set_defaults(func=command_schema)

    scaffold = sub.add_parser("scaffold", help="Create a run directory scaffold.")
    scaffold.add_argument("--output-dir", required=True)
    scaffold.add_argument("--target", required=True)
    scaffold.add_argument("--needs", action="append")
    scaffold.add_argument("--scale", choices=["small", "medium", "large", "deep"], default="medium")
    scaffold.set_defaults(func=command_scaffold)

    normalize = sub.add_parser("normalize", help="Normalize a raw JSON/JSONL capture into JSONL artifacts.")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--source", required=True)
    normalize.add_argument("--output-dir", required=True)
    normalize.add_argument("--kind", choices=["repos", "models", "benchmarks"])
    normalize.add_argument("--output")
    normalize.set_defaults(func=command_normalize)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
