# Deprecated Manuscript-to-PPT Agents

These native agents were removed from the active `.codex/agents/` directory because their work overlaps with the `manuscript-to-ppt-workflow` leader and existing skills:

- `ppt-production-alignment.toml`: replaced by main-thread `codex-deep-interview` orchestration.
- `manuscript-fact-extraction.toml`: replaced by main-thread source inspection and `research-fact-source-sync`.
- `ppt-asset-audit.toml`: replaced by leader-owned asset decisions while integrating storyboard, facts, templates, and figure pipeline outputs.
- `figma-layout-polish.toml`: removed from the default PPT-native workflow; Figma context is a separate experiment lane, not a default deck-production dependency.

Keep these files only as historical reference or migration material. They use `.toml.disabled` suffixes and live outside `.codex/*agents*` so native-agent discovery does not surface them as spawnable roles. Do not copy them back into `.codex/agents/` unless the workflow design changes and their responsibilities no longer overlap with skill-led orchestration.
