# Array-Plugin für IngeTrazo (wie 3ds Max ▸ Tools ▸ Array)

## Installation
1. In IngeTrazo: **Extensiones ▸ Abrir carpeta de complementos** (Windows: `%APPDATA%\ingetrazo\plugins\`).
2. `array_tool.py` dort hineinkopieren.
3. IngeTrazo neu starten → **Extensiones ▸ Array…** bzw. Rechtsklick ▸ **Array…**

Voraussetzung: IngeTrazo ≥ 0.5.6 (Extension-API 2) · getestet mit IngeTrazo 0.6.0.

## Funktionen
- **Move / Rotate / Scale** je Achse, pro Zeile **Incremental** oder **Totals** (Buttons `<` / `>`); die inaktive Seite zeigt den berechneten Wert.
- **Re-Orient**, **Uniform**
- **Center**: Selection Center · Pivot Point Center · World Origin
- **Type of Object**: Copy (unabhängig) · Instance (Component, geteilte Geometrie)
- **Array Dimensions** 1D / 2D / 3D mit Count + Incremental Row Offsets, **Total in Array**
- **Preview** (live im Modell) — solange sie läuft, ist der Button grün (**● Live Preview ON**) und eine Statuszeile zeigt die Anzahl der Kopien; jede Änderung aktualisiert das Modell von selbst. Der Dialog blockiert den Viewport nicht: Orbit, Pan und Zoom funktionieren während der Vorschau. **Reset All Parameters**, OK / Cancel
- Ganzes Array = **ein Undo-Schritt**; Einstellungen werden gemerkt.
- Alle Werte in den **Einheiten des Dokuments**, siehe [Einheiten](#einheiten).

## Einheiten
Die Felder verwenden die **Einheiten des geöffneten Dokuments**, eingestellt in IngeTrazo unter **Fenster ▸ Einheiten…** (Strg+U) oder **Fenster ▸ Einstellungen… ▸ Einheiten** (Länge, Winkel, Dezimaltrennzeichen):
- **Move** und **Incremental Row Offsets** zeigen und lesen Längen in der Längeneinheit des Dokuments: m, cm, mm, in, ft, **Fuß-Zoll** (`9'10.11"`) oder **Fuß-Zoll mit Brüchen** (`9'10 1/8"`).
- Werte mit oder ohne Einheit eintippen, so wie IngeTrazo sie überall liest: `25`, `2,5 cm`, `1'2"`, `3/4"`, `1-2 1/2`. Eine Zahl ohne Einheit gilt in der Dokumenteinheit (im Fuß-Zoll-Dokument: Zoll).
- **Rotate** zeigt und liest die Winkeleinheit des Dokuments (Grad, Radiant oder Gon), mindestens auf zwei Nachkommastellen.
- **Scale** bleibt in Prozent. Alle Felder folgen dem Dezimaltrennzeichen des Dokuments; beim Tippen gehen `.` und `,`.
- Ein Wechsel der Einheiten ändert nur Anzeige und Eingabe — das Modell bleibt exakt gleich. Danach den Array-Dialog neu öffnen.
- In IngeTrazo-Versionen vor 0.5.8 sind die Felder einfache Zahlen mit der Einheit daneben.

## Versionen
- **1.3** — **Dokumenteinheiten**: Move, Rotate und die Row Offsets zeigen und lesen die Einheiten aus Einstellungen ▸ Einheiten, auch Fuß-Zoll und Fuß-Zoll mit Brüchen (`1'2"`), Radiant und Gon sowie das Dezimaltrennzeichen (Issue #1, danke an PConn5); getestet mit IngeTrazo 0.6.0.
- **1.2.1** — getestet mit IngeTrazo 0.5.8; die Version steht im Dialogtitel.
- **1.2** — eigene Werkzeugleiste **Array** mit einem Icon je Befehl (Array…). Sie erscheint in einer eigenen Zeile unter den eingebauten Leisten und lässt sich wie diese verschieben, abdocken oder ausblenden (Rechtsklick auf eine Leiste). Icons im Stil von IngeTrazo, passend zum hellen/dunklen Theme.
- **1.1** — deutliche Live-Preview-Anzeige: grüner Button, Statuszeile (live / aktualisiert / pausiert oder Fehler), Hinweis wenn Total in Array über 20.000 liegt; der Dialog blockiert den Viewport nicht mehr — Orbit, Pan und Zoom während der Vorschau (kopiert werden die beim Öffnen gewählten Objekte).
- **1.0** — erste Veröffentlichung.

## Unterschiede zu 3ds Max
- Kein **Reference** (gibt es in IngeTrazo nicht), kein **Display as Box**.
- Nur **World Coordinates** (keine lokalen Achsen).
- Lose Geometrie (Flächen/Kanten) wird immer kopiert; **Instance** wirkt nur auf Gruppen/Components – eine klassische Gruppe wird dabei zuerst in eine Component umgewandelt.
- Scale wird linear pro Kopie aufaddiert (110 % → 110, 120, 130 %) und um den eigenen Bezugspunkt des Objekts skaliert; Rotation um das gewählte Center.
- Rotationsreihenfolge X → Y → Z (Weltachsen).
