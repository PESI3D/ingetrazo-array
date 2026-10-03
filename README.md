# Array plugin for IngeTrazo (like 3ds Max ▸ Tools ▸ Array)

Copies the selection in 1D, 2D or 3D with move, rotate and scale per copy — modelled on the classic 3ds Max **Array** dialog.

## Installation
1. In IngeTrazo: **Extensions ▸ Open plugins folder** (Windows: `%APPDATA%\ingetrazo\plugins\`, Linux: `~/.local/share/ingetrazo/plugins/`).
2. Copy `array_tool.py` into that folder.
3. Restart IngeTrazo → **Extensions ▸ Array…** or right-click a selection ▸ **Array…**

Requires IngeTrazo ≥ 0.5 (extension API 2).

## Features
- **Move / Rotate / Scale** per axis; each row works either **Incremental** or **Totals** (buttons `<` / `>`). The inactive side shows the computed value.
- **Re-Orient**, **Uniform**
- **Center**: Selection Center · Pivot Point Center · World Origin
- **Type of Object**: Copy (independent) · Instance (component, shared geometry)
- **Array Dimensions** 1D / 2D / 3D with Count and Incremental Row Offsets, plus **Total in Array**
- **Preview** (live in the model) — while it runs the button turns green (**● Live Preview ON**) and a status line shows the number of copies; every change updates the model by itself. The dialog does not block the viewport: orbit, pan and zoom while the preview is on. **Reset All Parameters**, OK / Cancel
- The whole array is **one undo step**; settings are remembered between runs.
- Move values use the document's length unit (m / cm / mm …).

## Differences from 3ds Max
- No **Reference** (IngeTrazo has no such object type) and no **Display as Box**.
- **World Coordinates** only (no local coordinate systems).
- Loose geometry (faces/edges) is always copied; **Instance** applies to groups/components only — a classic group is converted into a component first.
- Scale grows linearly per copy (110 % → 110, 120, 130 %) and scales each object about its own reference point; rotation turns about the chosen Center.
- Rotation order X → Y → Z (world axes).

## Changelog
- **1.1** — clear live-preview indicator: green button, status line (live / updating / paused or failed), preview pause shown when Total in Array exceeds 20,000; the dialog no longer blocks the viewport — orbit, pan and zoom during the preview (the objects selected at opening are the ones copied).
- **1.0** — first release.

## Licence
GPL-3.0-or-later · © 2026 Pesi (pesi3d.de)
