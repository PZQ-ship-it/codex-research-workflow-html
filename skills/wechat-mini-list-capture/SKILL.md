---
name: wechat-mini-list-capture
description: Cooperative visible-UI workflow for collecting simple WeChat mini-program list/detail pages with Codex-in-the-loop calibration. Use when the user wants low-manual capture of WeChat mini-program lists, asks Codex to inspect calibration screenshots, fix list/item boxes, guide tab switching, run sample captures, or export review files without private API replay.
---

# WeChat Mini List Capture

Use this skill as a human-Codex operating loop, not as a blind crawler. The user keeps the mini program visible and performs login/tab switching when needed; Codex inspects screenshots and JSON, adjusts config, runs small samples, and exports review artifacts.

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

1. Inspect current artifacts:
   - `runtime\wechat-mini-list-capture\calibration-<list-id>-annotated.png`
   - `runtime\wechat-mini-list-capture\calibration-<list-id>-candidates.json`
   - `runtime\wechat-mini-list-capture\config.local.json`
2. Judge the calibration visually:
   - `app` should cover the mini-program window only.
   - `list` should start below tabs and announcement boxes unless the list itself begins there.
   - item boxes should cover whole clickable cards, not split title and description into separate candidates.
3. If boxes are good, run a small sample first, usually `-MaxItems 3`.
4. If boxes are bad, do not keep tuning automation blindly. Use `configure-list.ps1` to write Codex-reviewed `row_slots` for the visible item cards.
5. After sample capture, export a review CSV and ask the user to confirm field quality before full capture.
6. Write back durable status in `D:\todo` when the workflow meaningfully progresses.

## Preferred Fix For Bad Item Boxes

When auto OCR/card detection splits cards or includes announcement text, switch that list to `candidate_mode=row_slots`:

```powershell
.\scripts\configure-list.ps1 `
  -ListId list_a `
  -AppRegion "left,top,right,bottom" `
  -ListRegion "left,top,right,bottom" `
  -CandidateMode row_slots `
  -RowSlot "left,top,right,bottom","left,top,right,bottom"
```

Use row slots for visible full cards. The harness still OCRs each slot during runtime and uses OCR text for deduplication.

## User Coordination

Ask the user only for actions Codex cannot do reliably:

- open the mini program;
- keep the mini-program window visible and stable;
- switch from list A to list B;
- confirm a sample review CSV or ambiguous screenshot;
- resolve login, QR, CAPTCHA, or platform prompts.

Do not ask the user to manually mark every row unless both visual calibration and Codex-reviewed row slots fail.
