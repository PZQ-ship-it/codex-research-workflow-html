# Full Setup

Use this reference when the user asks to complete, repair, or MCP-enable `code-model-benchmark-intel`. The default closure remains public-source and no-secret: GitHub public API/local clone, Hugging Face public API/Dataset Viewer, Kaggle public pages, OpenML public metadata, and benchmark official repos/datasets.

## Safe Default

Run from the repo or from the installed global skill:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\code-model-benchmark-intel\scripts\setup_code_model_benchmark_intel.ps1 -RunNetworkSmoke
```

The script defaults to the user-level global skill directory when it exists:

```text
%USERPROFILE%\.codex\skills\code-model-benchmark-intel
```

It creates an isolated runtime under `runtime/code-model-benchmark` with:

- `huggingface_hub` and `datasets` for HF model/dataset/leaderboard metadata.
- `openml` for OpenML datasets, tasks, runs, evaluations, and benchmark suites.
- `kaggle` and `kagglehub` for user-authorized Kaggle API workflows.
- `requests`, `pandas`, and `pyarrow` for small API captures and tabular normalization.

Do not commit `runtime/`, `.env`, token files, downloaded gated/private data, notebooks with private outputs, or raw credential-bearing logs.

## Source Facts

- GitHub's official Codex install guide registers the hosted MCP at `https://api.githubcopilot.com/mcp/` with `--bearer-token-env-var GITHUB_PAT_TOKEN`.
- Hugging Face's official MCP docs route users through `https://huggingface.co/settings/mcp` and expose the server at `https://huggingface.co/mcp`.
- Kaggle's official MCP docs list the remote server URL as `https://www.kaggle.com/mcp`.
- OpenML automation uses the official `openml` Python package; persistent authentication uses the OpenML account API key in `~/.openml/config` or the `openml configure apikey` command.

Primary URLs:

- https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-codex.md
- https://huggingface.co/docs/hub/en/agents-mcp
- https://huggingface.co/settings/mcp
- https://www.kaggle.com/docs/mcp
- https://docs.openml.org/examples/20_basic/introduction_tutorial/
- https://huggingface.co/docs/hub/en/leaderboard-data-guide

## MCP Registration

### GitHub MCP

Register the official hosted MCP:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\code-model-benchmark-intel\scripts\setup_code_model_benchmark_intel.ps1 -RegisterGitHubMcp
```

Equivalent Codex command:

```powershell
codex mcp add github --url https://api.githubcopilot.com/mcp/ --bearer-token-env-var GITHUB_PAT_TOKEN
```

This registers only the env var name. It does not store the token. For authenticated use, set `GITHUB_PAT_TOKEN` in the environment of the Codex process with least-privilege read scopes. Prefer fine-grained, expiring, repo-limited tokens; expand scopes only when a tool request fails due to permission.

### Hugging Face MCP

Preferred official path:

1. Open https://huggingface.co/settings/mcp while logged in.
2. Select the desired built-in tools and any MCP Spaces.
3. Copy the Codex/client-specific URL or config from the settings page.

The setup script can register the generic official endpoint by writing the MCP config without starting a blocking OAuth flow:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\code-model-benchmark-intel\scripts\setup_code_model_benchmark_intel.ps1 -RegisterHuggingFaceMcp
```

Equivalent Codex command, if you are ready to complete OAuth immediately:

```powershell
codex mcp add huggingface --url https://huggingface.co/mcp
```

If Codex reports OAuth or auth required, run this as a separate human-approved step:

```powershell
codex mcp login huggingface
```

Public HF API and `huggingface_hub` metadata workflows do not require HF MCP.

### Kaggle MCP

Register the official hosted MCP config:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\code-model-benchmark-intel\scripts\setup_code_model_benchmark_intel.ps1 -RegisterKaggleMcp
```

Equivalent Codex command, if you are ready to complete OAuth immediately:

```powershell
codex mcp add kaggle --url https://www.kaggle.com/mcp
```

Then authenticate only if needed, as a separate human-approved step:

```powershell
codex mcp login kaggle
```

Kaggle API package downloads and notebook/competition access may also require `kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`. Do not configure them unless the user accepts Kaggle terms for the specific asset.

## Credential Matrix

Required API keys: none for the default public closure.

Use `$external-api-onboarding` before setting any optional credential. Store secrets only in private user-level storage and never in committed files. Do not paste secrets into chat.

Recommended private path for local helper workflows:

```text
%USERPROFILE%\.codex\skills\code-model-benchmark-intel\.env
```

Current verified variables:

- `GITHUB_PAT_TOKEN`: optional for GitHub hosted MCP. Required by the official remote MCP when authenticated GitHub tools are used.
- `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN`: optional for gated/private HF repos, higher limits, or write-capable Hub workflows. Public metadata and public leaderboard reads do not require it.
- `KAGGLE_USERNAME` / `KAGGLE_KEY`: optional for Kaggle API package workflows. Official remote Kaggle MCP should use its own OAuth flow where supported by Codex.
- `OPENML_API_KEY`: optional for OpenML upload/publish/authenticated operations. Read-only public metadata should be attempted first and treated as blocked if the server requires auth.

Hidden prompt example for local `.env` storage:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\external-api-onboarding\scripts\set_env_secret.ps1 `
  -EnvFile "$env:USERPROFILE\.codex\skills\code-model-benchmark-intel\.env" `
  -Name HF_TOKEN
```

For remote MCP bearer-token env vars, the Codex process must actually see the env var. A `.env` file alone is not enough unless the launcher loads it. Prefer a user environment variable or a wrapper that exports the variable before starting Codex.

Never print, summarize, screenshot, commit, or paste secret values.

## Benchmark Repos

Read `references/benchmark-repos.md` before cloning. By default, do not clone benchmark repos; use official public APIs and repo pages first.

Optional shallow clone:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\code-model-benchmark-intel\scripts\setup_code_model_benchmark_intel.ps1 `
  -CloneBenchmarkRepos `
  -BenchmarkRepo swebench,livebench,livecodebench,bigcodebench
```

Repos are cloned under:

```text
%USERPROFILE%\.codex\skills\code-model-benchmark-intel\runtime\benchmark-repos
```

## Smoke Tests

Planner:

```powershell
python %USERPROFILE%\.codex\skills\code-model-benchmark-intel\scripts\code_model_benchmark_intel.py plan --target "Qwen code models SWE-bench leaderboard and GitHub implementations" --needs code,models,benchmarks,leaderboards,report --scale medium
```

Python runtime import:

```powershell
%USERPROFILE%\.codex\skills\code-model-benchmark-intel\runtime\code-model-benchmark\.venv\Scripts\python.exe -c "import huggingface_hub, datasets, openml, kaggle, kagglehub; print('ok')"
```

HF public API:

```powershell
%USERPROFILE%\.codex\skills\code-model-benchmark-intel\runtime\code-model-benchmark\.venv\Scripts\python.exe -c "from huggingface_hub import HfApi; print(HfApi().model_info('distilbert/distilbert-base-uncased').modelId)"
```

OpenML public metadata:

```powershell
%USERPROFILE%\.codex\skills\code-model-benchmark-intel\runtime\code-model-benchmark\.venv\Scripts\python.exe -c "import openml; ds=openml.datasets.get_dataset(61, download_data=False); print(ds.dataset_id, ds.name)"
```

MCP list:

```powershell
codex mcp list
```

After MCP registration or OAuth login, restart Codex if the current session does not show the new tools.
