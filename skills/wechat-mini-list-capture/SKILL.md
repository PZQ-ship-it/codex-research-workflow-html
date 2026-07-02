---
name: wechat-mini-list-capture
description: Cooperative visible-UI workflow for collecting simple WeChat mini-program list/detail pages with Codex-generated screenshot annotations. Use when the user wants Codex to mark app/list/item boxes on WeChat mini-program screenshots, apply those annotations to config, guide tab switching, run sample captures, or export review files without private API replay.
---

# WeChat Mini List Capture

Use this skill as a human-Codex operating loop, not as a blind crawler. The user keeps the mini program visible and performs login/tab switching when needed; Codex directly annotates screenshots, applies those annotations to config, runs small samples, and exports review artifacts.

## Boundaries

- Use only user-visible, already-open UI state.
- Do not read, copy, or store cookies, tokens, headers, localStorage, private APIs, or credentials.
- Keep raw screenshots, OCR text, checkpoints, and logs under the ignored runtime directory.
- Put only status and sanitized review/export summaries in `D:\todo`.
- Treat OCR and AI outputs as candidates until human-reviewed.

## Local Harness

Default local code path:

```powershell
D:\agent-workflow-lab\harnesses\wechat-mini-list-capture
```

Default private runtime:

```powershell
D:\agent-workflow-lab\runtime\wechat-mini-list-capture
```

Before running commands, read `references/harness-workflow.md` for exact command usage and screenshot-review criteria.

## Operating Loop

1. Inspect the raw current screenshot, usually `runtime\wechat-mini-list-capture\calibration-<list-id>-screen.png`.
2. Create a Codex annotation JSON with `app_region`, `list_region`, and full-card `items[]` boxes.
3. Apply the annotation with `apply-annotation.ps1`; this renders a review image and writes `config.local.json`.
4. Inspect the rendered review image. If boxes are good, run a small sample first, usually `-MaxItems 3`.
5. If boxes are bad, revise the annotation JSON and reapply it. Do not ask the user to manually mark row slots.
6. After sample capture, export a review CSV and ask the user to confirm field quality before full capture.
7. Write back durable status in `D:\todo` when the workflow meaningfully progresses.

## Codex Annotation Format

Generate JSON like this under the private runtime:

```json
{
  "list_id": "list_a",
  "source_image": "D:\\agent-workflow-lab\\runtime\\wechat-mini-list-capture\\calibration-list_a-screen.png",
  "annotator": "codex",
  "app_region": [765, 96, 1392, 1274],
  "list_region": [765, 690, 1392, 1274],
  "items": [
    {
      "id": "list_a_visible_1",
      "label": "visible card title",
      "box": [790, 690, 1368, 962],
      "confidence": 0.86,
      "note": "full visible card; excludes announcement"
    }
  ]
}
```

Apply it:

```powershell
.\scripts\apply-annotation.ps1 -Annotation D:\agent-workflow-lab\runtime\wechat-mini-list-capture\codex-annotation-list_a.json
```

The harness stores Codex item boxes as `candidate_mode=row_slots`, but the user does not manually mark them. The harness still OCRs each slot during runtime and uses OCR text for deduplication.

## Annotation Rules

- Make `app_region` cover the mini-program window only.
- Make `list_region` start below tabs and announcement boxes unless the announcement is an intended item.
- Make each `items[].box` cover one whole clickable card.
- Exclude announcement text, close buttons, floating share/add buttons, terminal text, and VS Code UI.
- Prefer 1-3 visible full cards over many uncertain partial boxes.
- If a card is partly covered by a floating button, either avoid the covered edge or mark confidence lower.

## User Coordination

Ask the user only for actions Codex cannot do reliably:

- open the mini program;
- keep the mini-program window visible and stable;
- switch from list A to list B;
- confirm a rendered Codex annotation review image, sample review CSV, or ambiguous screenshot;
- resolve login, QR, CAPTCHA, or platform prompts.

Do not ask the user to manually mark every row unless Codex annotation repeatedly fails and the user explicitly accepts manual fallback.
