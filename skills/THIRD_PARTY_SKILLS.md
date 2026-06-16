# Third-Party Skills

This file records third-party skill snapshots vendored into this repository.

## Academic Research Suite

- Skill directory: `skills/academic-research-suite/`
- Upstream: `https://github.com/Imbad0202/academic-research-skills-codex`
- Upstream path: `skills/academic-research-suite`
- Commit: `35dd7722c43ed59ee05af3d2c2bf63a16ab79a01`
- Install note: `ars/tests/`, `ars/evals/`, `ars/scripts/fixtures/`, `ars/scripts/adapters/tests/`, `ars/docs/design/`, `codex/tests/`, and script-level `test_*.py` files were excluded to avoid Windows long-path checkout problems, reduce vendored test data and web snapshots, and keep the snapshot focused on skill usage.

## Supervisor Skills

- Upstream: `https://github.com/HKUSTDial/Supervisor-Skills`
- Upstream path: `plugins/phd-research/skills`
- Commit: `e36828dde1e59e3537afc4d62bb572ae815845d1`
- Vendored directories:
  - `skills/benchmark-paper-template/`
  - `skills/figure-designer/`
  - `skills/idea-evaluator/`
  - `skills/intro-drafter/`
  - `skills/pre-submission-reviewer/`
  - `skills/tech-paper-template/`
  - `skills/vibe-research-workflow/`

## Research Proposal

- Skill directory: `skills/research-proposal/`
- Upstream: `https://github.com/luwill/research-skills`
- Upstream path: `research-proposal`
- Commit: `269b448fe918f910a23e09e74fede45dc5d78f10`

## Professor Fit Analyzer

- Skill directory: `skills/professor-fit-analyzer/`
- Upstream: `https://github.com/voidful/academic-skills`
- Upstream path: `professor-fit-analyser`
- Commit: `71e9c42c60636602e87985f4306d134a3b63809e`
- Install note: moved the upstream `compatibility` frontmatter field under `metadata.compatibility` to satisfy the local Codex skill validator while preserving the compatibility note.

## External Crawler Adapters

These sources are not vendored into this repository. Repo-local skills only store wrappers, setup helpers, and output contracts.

### Dianping Explore

- Skill directory: `skills/dianping-explore/`
- Default external crawler: `https://github.com/HDdssX/dianping_crawler`
- Storage note: clone into an external runtime directory such as `%LOCALAPPDATA%\Codex\dianping-explore\HDdssX_dianping_crawler` via `python scripts\cli.py setup-source`.
- Boundary note: keep real cookies, browser profiles, third-party source checkouts, and crawler outputs outside git.
