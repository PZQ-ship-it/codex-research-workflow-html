# Harness Workflow Reference

## Commands

Run from:

```powershell
cd D:\agent-workflow-lab\harnesses\wechat-mini-list-capture
```

Health check:

```powershell
.\scripts\doctor.ps1
.\scripts\doctor-android.ps1 -Screenshot
```

Visual calibration only:

```powershell
.\scripts\bootstrap-after-open.ps1 -SkipRun
```

Calibrate current visible list directly:

```powershell
.\scripts\calibrate-visible-list.ps1 -ListId list_a
.\scripts\calibrate-visible-list.ps1 -ListId list_b
.\scripts\calibrate-android.ps1 -ListId list_a
```

Apply Codex-generated annotation:

```powershell
.\scripts\apply-annotation.ps1 -Annotation D:\agent-workflow-lab\runtime\wechat-mini-list-capture\codex-annotation-list_a.json
```

Manual row-slot config, fallback only:

```powershell
.\scripts\configure-list.ps1 -ListId list_a -AppRegion "765,96,1392,1274" -ListRegion "765,690,1392,1274" -CandidateMode row_slots -RowSlot "790,690,1368,962","790,965,1368,1238"
```

Small sample run:

```powershell
.\scripts\run-desktop.ps1 -ListId list_a -MaxItems 3
.\scripts\run-android.ps1 -ListId list_a -MaxItems 3
```

Export review:

```powershell
.\scripts\export-review.ps1 -RunDir <run-dir>
```

## Codex Annotation Procedure

1. Open the raw screenshot with visual inspection.
2. Create `codex-annotation-<list-id>.json` in the private runtime.
3. Include:
   - `list_id`
   - `source_image`
   - `app_region`
   - `list_region`
   - `items[]` with `id`, `label`, `box`, `confidence`, and optional `note`
4. Apply it with `apply-annotation.ps1`.
5. Inspect `codex-annotation-<list-id>-review.png`.
6. Revise JSON and reapply until the review image is acceptable.

## No-Mouse Android Mode

Use this path when the user wants to keep using the Windows desktop:

```powershell
.\scripts\doctor-android.ps1 -Screenshot
.\scripts\calibrate-android.ps1 -ListId list_a
.\scripts\run-android.ps1 -ListId list_a -MaxItems 3
```

If multiple ADB devices are connected, pass `-Serial <adb-device-id>`.
If `adb` is not on PATH, pass `-AdbPath "C:\path\to\adb.exe"`.
If Google Platform Tools was installed through WinGet, the Android scripts try
to discover that `adb.exe` automatically.

ADB mode controls only the Android device/emulator through screenshots, taps,
swipes, and back key events. It should not move the Windows mouse.

## Review Criteria

Good calibration:

- `app` rectangle surrounds only the mini-program window.
- `list` rectangle excludes header, tabs, and announcements unless they are intended list items.
- visible item candidates each cover one full card.
- first full item card is not merged with announcement text.
- one item card is not split into separate title and body boxes.

Bad calibration routes:

- `app` wrong: revise `app_region` in the Codex annotation JSON.
- `list` starts too high: revise `list_region` below announcement boxes.
- item cards split: replace split boxes with one full-card `items[].box`.
- item candidates include announcements: move `list_region` below announcement and exclude announcement from `items[]`.
- OCR text noisy but boxes good: run a small sample and inspect `review.csv`; do not over-tune before seeing detail capture.

## Runtime Files

Expected private files:

```text
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\config.local.json
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\codex-annotation-<list-id>.json
D:\agent-workflow-lab\runtime\wechat-mini-list-capture\codex-annotation-<list-id>-review.png
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
