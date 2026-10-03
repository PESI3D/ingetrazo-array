# Array-Plugin für IngeTrazo (wie 3ds Max ▸ Tools ▸ Array)

## Installation
1. In IngeTrazo: **Extensiones ▸ Abrir carpeta de complementos** (Windows: `%APPDATA%\ingetrazo\plugins\`).
2. `array_tool.py` dort hineinkopieren.
3. IngeTrazo neu starten → **Extensiones ▸ Array…** bzw. Rechtsklick ▸ **Array…**

Voraussetzung: IngeTrazo ≥ 0.5 (Extension-API 2).

## Funktionen
- **Move / Rotate / Scale** je Achse, pro Zeile **Incremental** oder **Totals** (Buttons `<` / `>`); die inaktive Seite zeigt den berechneten Wert.
- **Re-Orient**, **Uniform**
- **Center**: Selection Center · Pivot Point Center · World Origin
- **Type of Object**: Copy (unabhängig) · Instance (Component, geteilte Geometrie)
- **Array Dimensions** 1D / 2D / 3D mit Count + Incremental Row Offsets, **Total in Array**
- **Preview** (live im Modell), **Reset All Parameters**, OK / Cancel
- Ganzes Array = **ein Undo-Schritt**; Einstellungen werden gemerkt.
- Move-Werte in der Dokumenteinheit (m / cm / mm …).

## Unterschiede zu 3ds Max
- Kein **Reference** (gibt es in IngeTrazo nicht), kein **Display as Box**.
- Nur **World Coordinates** (keine lokalen Achsen).
- Lose Geometrie (Flächen/Kanten) wird immer kopiert; **Instance** wirkt nur auf Gruppen/Components – eine klassische Gruppe wird dabei zuerst in eine Component umgewandelt.
- Scale wird linear pro Kopie aufaddiert (110 % → 110, 120, 130 %) und um den eigenen Bezugspunkt des Objekts skaliert; Rotation um das gewählte Center.
- Rotationsreihenfolge X → Y → Z (Weltachsen).

---
*3ds Max ist eine eingetragene Marke von Autodesk, Inc. Dieses Plugin steht in keiner Verbindung zu Autodesk und wird nicht von Autodesk unterstützt.*
