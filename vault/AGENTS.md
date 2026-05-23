# Vault Rules

## Purpose

This directory is a long-lived plain-text knowledge vault for project context, Codex usage notes, recurring decisions, and reusable personal workflows.

## What To Update

- `TODO.md`: active tasks, follow-ups, and unresolved questions.
- `agent/`: Codex behavior preferences, prompt patterns, workflow rules, and tool notes.
- `projects/`: project-specific summaries, decisions, milestones, and current state.
- `people/`: collaborator or stakeholder notes only when relevant and non-sensitive.
- `notes/`: general reusable notes that do not belong to one project.
- `sources/`: source lists, reading trails, links, and citation notes.
- `templates/`: reusable Markdown templates.

## Writing Rules

- Write in Chinese by default, preserving English feature names and commands.
- Prefer short, dated entries over long undated essays.
- Do not store secrets, API keys, credentials, private tokens, or sensitive personal data.
- Do not overwrite existing notes without reading them first.
- When adding factual or version-sensitive claims, include a source link or mark the item as needing verification.
- Keep notes practical: include paths, commands, prompts, examples, and next actions.

## When To Update

- After discovering a reusable Codex configuration or workflow.
- After completing a project step whose state should survive across sessions.
- After identifying a recurring problem, caveat, or decision.
- When the user explicitly asks to remember, archive, summarize, or maintain context.

## Non-Goals

- This is not a dump for generated reports.
- This is not a place for temporary screenshots or large binaries.
- This should not duplicate formal docs unless it adds a short index, decision, or personal working note.
