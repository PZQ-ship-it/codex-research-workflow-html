# Private Source Handling

Use these rules whenever processing private advisor-related material.

## Source Types

- Original private text: email, chat, comments, track changes, paper annotations.
- User summary: the user's paraphrase of a meeting, call, or hallway conversation.
- Observation: user notes about timing, tone, body language, meeting dynamics, or repeated patterns.
- Public source: homepage, paper, talk, social media, lab page, public syllabus.

## Intake Rules

- Ask for the smallest useful excerpt or summary.
- If raw material is long, summarize first and ask whether to persist the summary only.
- Strip unrelated personal details.
- Do not store passwords, tokens, phone numbers, addresses, student IDs, medical details, family details, or third-party secrets.
- When multiple people appear in a source, avoid profiling non-target people unless needed and approved.

## Evidence Extraction Rules

For each source, extract:

- what happened or was said;
- what advisor preference or pattern it may indicate;
- whether it is direct evidence, user recollection, or inference;
- whether there is a benign alternative explanation;
- how confident the update should be.

Do not convert frustration into fact. If the user says "they hate my work", record the concrete evidence instead, such as "they asked for a clearer baseline table twice."

## Privacy Before External Tools

Never send private material to:

- web search;
- public APIs;
- third-party summarization services;
- issue trackers;
- shared logs;
- public repos.

If public context is needed, search only public identifiers or anonymized topic terms. Example:

- Safe: `"NeurIPS reproducibility checklist"`
- Unsafe: a private email sentence, unpublished title, reviewer identity, student name, or meeting note.

## Update Confirmation

Before writing persisted files, show:

- new evidence entries to append;
- synthesized profile claims to add or revise;
- any sensitive material that would be stored;
- target file paths.

Proceed only after user approval.

## Consultation Safety

When using the profile to advise the user:

- frame predictions as "based on the profile, they may care about...";
- recommend preparation, clarity, and respectful communication;
- avoid manipulation, surveillance, guilt tactics, or pressure tactics;
- remind the user when direct clarification with the advisor is better than inference.

## Staleness

Mark a profile as stale when:

- no updates for 90+ days in an active relationship;
- the advisor changed role, lab, institution, project, or committee position;
- the user's relationship changed;
- recent evidence contradicts older profile claims.

For stale profiles, consult with a warning and propose a refresh instead of overconfident advice.
