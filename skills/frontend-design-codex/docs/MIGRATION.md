# Migration Notes

This repository packages `frontend-design-codex`, a Codex local skill adapted from the publicly available `frontend-design` Claude Code plugin workflow.

## Source Summary

The source plugin was locally available from the Claude official plugin marketplace cache and included:

- `frontend-design` skill instructions
- Claude plugin manifest
- README
- Apache-2.0 license

The source plugin metadata identifies Anthropic as the author. The migration preserves the workflow intent while rewriting the content for Codex execution.

## Preserved Intent

- Build frontend interfaces with a clear aesthetic point of view.
- Avoid generic AI UI defaults.
- Use deliberate typography, color, motion, spatial composition, and visual hierarchy.
- Match the visual direction to the product domain.
- Produce implementation-ready UI rather than abstract design advice.

## Codex Adaptation

The Codex skill replaces Claude-specific plugin semantics with Codex-native behavior:

- `SKILL.md` frontmatter controls discovery and triggering.
- Local file editing follows Codex workspace rules.
- Browser or Playwright verification is explicitly required for runnable UI.
- Existing project design systems take precedence over standalone aesthetics.
- Final responses must include evidence: files changed, URL or file path, commands, interaction path, and visual checks.

## Added Guardrails

- A style range matrix prevents the skill from collapsing into one fixed visual style.
- Anti-generic checks are mechanical and auditable.
- Dashboard and app UI guidance prioritizes scanability and workflow over marketing-style cards.
- Motion rules include reduced-motion handling.
- Responsive rules require desktop and mobile checks.

## Removed Claude-Only Material

- Claude marketplace metadata
- Claude-only command assumptions
- Claude identity language
- Any installation behavior specific to Claude Code plugins

## License

The original source was Apache-2.0 licensed. This adaptation is distributed under Apache-2.0 and includes the original license text.
