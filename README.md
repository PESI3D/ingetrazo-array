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
- **Preview** (live in the model), **Reset All Parameters**, OK / Cancel
- The whole array is **one undo step**; settings are remembered between runs.
- Move values use the document's length unit (m / cm / mm …).

## Differences from 3ds Max
- No **Reference** (IngeTrazo has no such object type) and no **Display as Box**.
- **World Coordinates** only (no local coordinate systems).
- Loose geometry (faces/edges) is always copied; **Instance** applies to groups/components only — a classic group is converted into a component first.
- Scale grows linearly per copy (110 % → 110, 120, 130 %) and scales each object about its own reference point; rotation turns about the chosen Center.
- Rotation order X → Y → Z (world axes).

## Licence
GPL-3.0-or-later · © 2026 Pesi (pesi3d.de)

---
*3ds Max is a registered trademark of Autodesk, Inc. This plugin is not affiliated with or endorsed by Autodesk.*
