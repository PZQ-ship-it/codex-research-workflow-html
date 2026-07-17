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

## Clone Website

- Skill directory: `skills/clone-website/`
- Upstream: `https://github.com/JCodesMore/ai-website-cloner-template`
- Upstream path: `.codex/skills/clone-website`
- Commit: `8dd9cb47dde0d49fec06ee1d69bedd04840f3c95`
- License: MIT
- Install note: moved the upstream `argument-hint` and `user-invocable` frontmatter fields under `metadata` to satisfy the local Codex skill validator while preserving the trigger metadata.

## AnySearch

- Skill directory: `skills/anysearch/`
- Upstream: `https://github.com/anysearch-ai/anysearch-skill`
- Upstream path: repository root
- Tag: `v2.1.0`
- Commit: `6ff6aa958ad9747659d669b5e9984f07c896f2aa`
- Install note: moved upstream `version`, `authors`, and `credentials` frontmatter fields under `metadata` to satisfy the local Codex skill validator while preserving their values. Local `.env` credentials are excluded from the repository mirror.

## Frontend Design Codex

- Skill directory: `skills/frontend-design-codex/`
- Upstream: `https://github.com/KilimiaoSix/frontend-design-codex-skill`
- Upstream path: repository root
- Commit: `d5cfacddf8ddd4ce82c8a0f9ce11a3135b78e7aa`
- License: Apache-2.0
- Install note: installed globally as `C:\Users\Administrator\.codex\skills\frontend-design-codex` and mirrored as a full runnable bundle.

## Claude Resume Kit

- Skill directory: `skills/claude-resume-kit/`
- Upstream: `https://github.com/ARPeeketi/claude-resume-kit`
- Upstream path: repository root
- Commit: `69930e9de21d5595f9b8c9427adc9c51a9fcbc0e`
- License: MIT
- Install note: installed as a Codex-native wrapper around the upstream Claude slash-skill project. The upstream snapshot is preserved under `assets/upstream-project/`; the top-level `SKILL.md` and `scripts/init_claude_resume_project.py` provide Codex routing and scaffold initialization.

## Resume Tailoring

- Skill directory: `skills/resume-tailoring/`
- Upstream: `https://github.com/varunr89/resume-tailoring-skill`
- Upstream path: `skills/resume-tailoring` plus root reference files
- Commit: `9a4a0f20f5983d1b533627b8c5191acd1ca0cd89`
- License: MIT
- Install note: adapted to a Codex-native wrapper that preserves the upstream skill and matching/discovery references under `references/upstream/`.

## Zotero MCP

- Skill directory: `skills/zotero-mcp/`
- Upstream: `https://github.com/54yyyu/zotero-mcp`
- Upstream path: repository root
- Commit: `f4eb88a2ee463cbddd4b83c9f38cc12d1263968a`
- License: MIT
- Install note: installed as a Codex-native wrapper around the upstream MCP server. The upstream checkout and isolated venv are intentionally kept outside Git under `%LOCALAPPDATA%\Codex\zotero-mcp`; the skill stores setup/status helpers, routing rules, local-read Codex MCP configuration, and provenance only.

## External Crawler Adapters

These sources are not vendored into this repository. Repo-local skills only store wrappers, setup helpers, and output contracts.

### Dianping Explore

- Skill directory: `skills/dianping-explore/`
- Default external crawler: `https://github.com/HDdssX/dianping_crawler`
- Storage note: clone into an external runtime directory such as `%LOCALAPPDATA%\Codex\dianping-explore\HDdssX_dianping_crawler` via `python scripts\cli.py setup-source`.
- Boundary note: keep real cookies, browser profiles, third-party source checkouts, and crawler outputs outside git.
