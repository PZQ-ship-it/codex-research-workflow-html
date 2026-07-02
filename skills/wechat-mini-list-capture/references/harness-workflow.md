# Harness Workflow Reference

## Commands

Run from:

```powershell
cd D:\agent-workflow-lab\harnesses\wechat-mini-list-capture
```

Health check:

```powershell
.\scripts\doctor.ps1
```

Visual calibration only:

```powershell
.\scripts\bootstrap-after-open.ps1 -SkipRun
```

Calibrate current visible list directly:

```powershell
.\scripts\calibrate-visible-list.ps1 -ListId list_a
.\scripts\calibrate-visible-list.ps1 -ListId list_b
```

Codex-reviewed manual row-slot config:

```powershell
.\scripts\configure-list.ps1 -ListId list_a -AppRegion "765,96,1392,1274" -ListRegion "765,690,1392,1274" -CandidateMode row_slots -RowSlot "790,690,1368,962","790,965,1368,1238"
```

Small sample run:

```powershell
.\scripts\run-desktop.ps1 -ListId list_a -MaxItems 3
```

Export review:

```powershell
.\scripts\export-review.ps1 -RunDir <run-dir>
```

## Calibration Review Criteria

Good calibration:

- `app` rectangle surrounds only the mini-program window.
- `list` rectangle excludes header, tabs, and announcements unless they are intended list items.
- visible item candidates each cover one full card.
- first full item card is not merged with announcement text.
- one item card is not split into separate title and body boxes.

Bad calibration routes:

- `app` wrong: rerun with the mini program centered/visible, or pass `-AppRegion`.
- `list` starts too high: use `configure-list.ps1` with a lower `-ListRegion`.
- item cards split: use `candidate_mode=row_slots`.
- item candidates include announcements: set `list_region` below announcement and use row slots.
- OCR text noisy but boxes good: run a small sample and inspect `review.csv`; do not over-tune before seeing detail capture.

## Runtime Files

Expected private files:

```text
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\config.local.json
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\calibration-<list-id>-annotated.png
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\calibration-<list-id>-candidates.json
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\runs\<run-id>\
```

Do not commit runtime files.

## Todo Writeback

Use these durable records when progress changes:

```text
D:\todo\projects\wechat-mini-list-capture\INDEX.md
D:\todo\tasks\graph\agent-workflow-lab.wechat-mini-list-capture-first-run.md
D:\todo\reports\work-traces\agent-workflow-lab\2026-07-01-wechat-mini-list-capture-harness.md
```
