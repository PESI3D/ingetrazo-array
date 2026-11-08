# Array plugin for IngeTrazo (like 3ds Max ▸ Tools ▸ Array)

Copies the selection in 1D, 2D or 3D with move, rotate and scale per copy — modelled on the classic 3ds Max **Array** dialog.

## Installation
1. In IngeTrazo: **Extensions ▸ Open plugins folder** (Windows: `%APPDATA%\ingetrazo\plugins\`, Linux: `~/.local/share/ingetrazo/plugins/`).
2. Copy `array_tool.py` into that folder.
3. Restart IngeTrazo → **Extensions ▸ Array…** or right-click a selection ▸ **Array…**

Requires IngeTrazo ≥ 0.5.6 (extension API 2) · tested with IngeTrazo 0.6.0.

## Features
- **Move / Rotate / Scale** per axis; each row works either **Incremental** or **Totals** (buttons `<` / `>`). The inactive side shows the computed value.
- **Re-Orient**, **Uniform**
- **Center**: Selection Center · Pivot Point Center · World Origin
- **Type of Object**: Copy (independent) · Instance (component, shared geometry)
- **Array Dimensions** 1D / 2D / 3D with Count and Incremental Row Offsets, plus **Total in Array**
- **Preview** (live in the model) — while it runs the button turns green (**● Live Preview ON**) and a status line shows the number of copies; every change updates the model by itself. The dialog does not block the viewport: orbit, pan and zoom while the preview is on. **Reset All Parameters**, OK / Cancel
- The whole array is **one undo step**; settings are remembered between runs.
- All values in the **document's units**, see [Units](#units).

## Units
The fields use the **units of the open document**, set in IngeTrazo under **Window ▸ Units…** (Ctrl+U) or **Window ▸ Preferences… ▸ Units** (Length, Angle, Decimal separator):
- **Move** and **Incremental Row Offsets** show and take lengths in the document's length unit and form: m, cm, mm, in, ft, **Feet-and-inches** (`9'10.11"`) or **Fractional Feet-and-Inches** (`9'10 1/8"`).
- Type a value with or without a unit, the way IngeTrazo reads it everywhere: `25`, `2,5 cm`, `1'2"`, `3/4"`, `1-2 1/2`. A number without a unit is in the document's unit (inches in a feet-and-inches document).
- **Rotate** shows and takes the document's angle unit (degrees, radians or gon), at least to two decimals.
- **Scale** stays in per cent. All fields follow the document's decimal separator; both `.` and `,` are accepted when typing.
- Changing the units only changes how values are shown and typed — the model stays exactly as it is. After changing them, open the Array dialog again.
- On IngeTrazo builds before 0.5.8 the fields are plain numbers with the unit shown next to them.

## Differences from 3ds Max
- No **Reference** (IngeTrazo has no such object type) and no **Display as Box**.
- **World Coordinates** only (no local coordinate systems).
- Loose geometry (faces/edges) is always copied; **Instance** applies to groups/components only — a classic group is converted into a component first.
- Scale grows linearly per copy (110 % → 110, 120, 130 %) and scales each object about its own reference point; rotation turns about the chosen Center.
- Rotation order X → Y → Z (world axes).

## Changelog
- **1.3** — **document units**: Move, Rotate and the row offsets show and take the units set under Preferences ▸ Units, including feet-and-inches and fractional feet-and-inches (`1'2"`), radians and gon, and the decimal separator (issue #1, thanks to PConn5); tested with IngeTrazo 0.6.0.
- **1.2.1** — tested with IngeTrazo 0.5.8; the version shows in the dialog's title.
- **1.2** — own toolbar **Array** with one icon per command (Array…). It starts on a row of its own under the built-in toolbars; move, float or hide it like those (right-click on a toolbar). Icons drawn in IngeTrazo's own style, they follow the light/dark theme.
- **1.1** — clear live-preview indicator: green button, status line (live / updating / paused or failed), preview pause shown when Total in Array exceeds 20,000; the dialog no longer blocks the viewport — orbit, pan and zoom during the preview (the objects selected at opening are the ones copied).
- **1.0** — first release.

## Licence
GPL-3.0-or-later · © 2026 Pesi (pesi3d.de)
