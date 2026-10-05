# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pesi (pesi3d.de)
"""Array — the 3ds Max «Array» dialog for IngeTrazo.

Select groups, components and/or loose geometry, then run
Extensions ▸ Array…  (or right-click ▸ Array…).

What it does, like Tools ▸ Array in 3ds Max:

* Array Transformation (World Coordinates): Move / Rotate / Scale per copy,
  each row either **Incremental** (from one copy to the next) or **Totals**
  (spread over the whole row) — the ``<`` / ``>`` buttons switch a row.
  The inactive side shows the computed value.
* Re-Orient: the copies turn with the rotation (off = they only orbit and
  keep their orientation). Uniform: Scale X is used for all three axes.
* Center: Selection Center, Pivot Point Center (each object about its own
  axes origin) or World Origin.
* Type of Object: Copy (independent) or Instance (shared component).
  Loose geometry is always copied; Instance turns a classic group into a
  component first (one undo step with the array).
* Array Dimensions 1D / 2D / 3D with Count and Incremental Row Offsets,
  Total in Array.
* Preview (live, in the model), Reset All Parameters, OK, Cancel.

The whole array is ONE undo step. Settings are remembered between runs.

Install: copy this file into the plugins folder
(Extensions ▸ Open plugins folder; on Windows %APPDATA%\\ingetrazo\\plugins)
and restart IngeTrazo. Needs IngeTrazo ≥ 0.5 (extension API 2).
"""
from __future__ import annotations

import json
import math

KEY = "array_tool"
TITLE = "Array"
SETTINGS_KEY = "plugins/array_tool/params"
MAX_OBJECTS = 20000          # safety net: Total in Array above this is refused


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def default_params() -> dict:
    """3ds Max's defaults: everything zero, scale 100 %, 1D with 10 objects."""
    return {
        "move": {"mode": "inc", "inc": [0.0, 0.0, 0.0], "tot": [0.0, 0.0, 0.0]},
        "rotate": {"mode": "inc", "inc": [0.0, 0.0, 0.0], "tot": [0.0, 0.0, 0.0]},
        "scale": {"mode": "inc", "inc": [100.0, 100.0, 100.0],
                  "tot": [100.0, 100.0, 100.0]},
        "reorient": True,
        "uniform": False,
        "center": "selection",        # "selection" | "pivot" | "world"
        "type": "copy",               # "copy" | "instance"
        "dim": 1,                     # 1 | 2 | 3
        "count": [10, 1, 1],
        "row2": [0.0, 0.0, 0.0],      # metres
        "row3": [0.0, 0.0, 0.0],      # metres
    }


def total_in_array(p: dict) -> int:
    c = p["count"]
    n = max(1, int(c[0]))
    if p["dim"] >= 2:
        n *= max(1, int(c[1]))
    if p["dim"] >= 3:
        n *= max(1, int(c[2]))
    return n


def increments(p: dict) -> tuple[list, list, list]:
    """The per-copy (incremental) Move [m], Rotate [deg] and Scale [%]
    whichever side of each row is active."""
    n1 = max(1, int(p["count"][0]))
    steps = max(1, n1 - 1)

    def row(name):
        r = p[name]
        if r["mode"] == "inc":
            return [float(v) for v in r["inc"]]
        if name == "scale":
            return [100.0 + (float(v) - 100.0) / steps for v in r["tot"]]
        return [float(v) / steps for v in r["tot"]]

    move, rot, scl = row("move"), row("rotate"), row("scale")
    if p.get("uniform"):
        scl = [scl[0]] * 3
    return move, rot, scl


def totals_from_increments(p: dict) -> tuple[list, list, list]:
    """What the Totals side reads when the Incremental side is active."""
    steps = max(1, int(p["count"][0]) - 1)
    move, rot, scl = increments(p)
    return ([v * steps for v in move], [v * steps for v in rot],
            [100.0 + (v - 100.0) * steps for v in scl])


# ---------------------------------------------------------------------------
# Geometry helpers (no UI)
# ---------------------------------------------------------------------------

def _qv(x, y, z):
    from PySide6.QtGui import QVector3D
    return QVector3D(float(x), float(y), float(z))


def _bbox_center(points):
    """Centre of the bounding box of an iterable of (x, y, z)."""
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    any_pt = False
    for p in points:
        any_pt = True
        for i in range(3):
            v = float(p[i])
            lo[i] = min(lo[i], v)
            hi[i] = max(hi[i], v)
    if not any_pt:
        return None
    return _qv(*[(lo[i] + hi[i]) * 0.5 for i in range(3)])


def _group_points(group):
    from core.group import placement_points
    return placement_points(group).tolist()


def _loose_points(faces, edges):
    for f in faces:
        for v in f.vertices:
            yield (v.x(), v.y(), v.z())
    for e in edges:
        yield (e.a.x(), e.a.y(), e.a.z())
        yield (e.b.x(), e.b.y(), e.b.z())


def _is_identity(m) -> bool:
    from PySide6.QtGui import QMatrix4x4
    return m is None or m == QMatrix4x4()


def group_pivot(group):
    """The «pivot point» of a group: the origin of its own axes when it has
    any (a component's insertion point, Change Axes), else its box centre."""
    from core.group import frame_axes, group_frame
    frame = group_frame(group)
    if not _is_identity(frame):
        return frame_axes(frame)[0]
    return _bbox_center(_group_points(group))


def gather_selection(scene):
    """``(groups, faces, edges)`` of the current selection."""
    from core.group import Group
    from core.mesh import Edge, Face
    sel = list(scene.selection)
    groups = [e for e in sel if isinstance(e, Group)]
    faces = [e for e in sel if isinstance(e, Face)]
    face_edges = set()
    for f in faces:
        for lp in (list(f.vertices), *[list(h) for h in f.holes]):
            n = len(lp)
            for i in range(n):
                a, b = lp[i], lp[(i + 1) % n]
                face_edges.add(_ekey(a, b))
    # Edges that bound a selected face come with the face itself.
    edges = [e for e in sel if isinstance(e, Edge)
             and _ekey(e.a, e.b) not in face_edges]
    return groups, faces, edges


def _pkey(p):
    return (round(p.x(), 6), round(p.y(), 6), round(p.z(), 6))


def _ekey(a, b):
    ka, kb = _pkey(a), _pkey(b)
    return (ka, kb) if ka <= kb else (kb, ka)


def rotation(rx: float, ry: float, rz: float):
    """World rotation: X first, then Y, then Z (as 3ds Max)."""
    from PySide6.QtGui import QMatrix4x4
    m = QMatrix4x4()
    m.rotate(rz, _qv(0, 0, 1))
    m.rotate(ry, _qv(0, 1, 0))
    m.rotate(rx, _qv(1, 0, 0))
    return m


def copy_matrix(i, j, k, p: dict, center, ref):
    """The world matrix of copy (i, j, k).

    ``center`` = what the rotation turns about, ``ref`` = the object's own
    reference point (it scales about it, and it is the point that orbits
    when Re-Orient is off)."""
    from PySide6.QtGui import QMatrix4x4
    move, rot, scl = increments(p)
    off = _qv(*[move[a] * i for a in range(3)])
    if p["dim"] >= 2:
        off += _qv(*p["row2"]) * float(j)
    if p["dim"] >= 3:
        off += _qv(*p["row3"]) * float(k)
    r = rotation(rot[0] * i, rot[1] * i, rot[2] * i)
    s = [1.0 + (scl[a] / 100.0 - 1.0) * i for a in range(3)]
    if abs(s[0]) < 1e-6 or abs(s[1]) < 1e-6 or abs(s[2]) < 1e-6:
        s = [v if abs(v) >= 1e-6 else 1e-6 for v in s]
    ref_new = center + r.map(ref - center)
    m = QMatrix4x4()
    m.translate(off + ref_new)
    if p["reorient"]:
        m = m * r
    m.scale(s[0], s[1], s[2])
    m.translate(-ref)
    return m


# ---------------------------------------------------------------------------
# The command (one undo step)
# ---------------------------------------------------------------------------

def make_array_command(scene, p: dict):
    """Build the undoable array command for the CURRENT selection, or
    ``None`` when there is nothing to do."""
    from core.history import Command

    groups, faces, edges = gather_selection(scene)
    if not (groups or faces or edges):
        return None
    if total_in_array(p) <= 1:
        return None

    class ArrayCommand(Command):
        """Builds the copies on its first ``do`` (after an Instance run has
        turned classic groups into components) and replays the very same
        sub-commands on redo."""

        def __init__(self):
            self.cmds: list = []
            self.built = False
            self.copies = 0

        def do(self, scene_):
            if self.built:
                for c in self.cmds:
                    c.do(scene_)
                return
            self.built = True
            try:
                self._build(scene_)
            except Exception:
                for c in reversed(self.cmds):
                    c.undo(scene_)
                self.cmds = []
                raise

        def _run(self, scene_, cmd):
            cmd.do(scene_)
            self.cmds.append(cmd)

        def _build(self, scene_):
            from core.group import copy_group, transformed_attrs, \
                transformed_mesh, carry_axes
            from core.history import (AddEdgeCommand, AddFaceCommand,
                                      GroupToComponentCommand,
                                      InsertGroupCommand)
            from core.mesh import Mesh

            instance = p["type"] == "instance"
            if instance:
                for g in groups:
                    if not g.is_component():
                        self._run(scene_, GroupToComponentCommand(g))

            # Reference points.
            loose_pts = list(_loose_points(faces, edges))
            loose_ref = _bbox_center(loose_pts) if loose_pts else None
            g_refs = {id(g): group_pivot(g) for g in groups}
            if p["center"] == "world":
                common = _qv(0, 0, 0)
            elif p["center"] == "selection":
                pts = list(loose_pts)
                for g in groups:
                    pts.extend(_group_points(g))
                common = _bbox_center(pts) or _qv(0, 0, 0)
            else:
                common = None       # pivot: each object about its own

            def grid():
                n1 = max(1, int(p["count"][0]))
                n2 = max(1, int(p["count"][1])) if p["dim"] >= 2 else 1
                n3 = max(1, int(p["count"][2])) if p["dim"] >= 3 else 1
                for k in range(n3):
                    for j in range(n2):
                        for i in range(n1):
                            if i == j == k == 0:
                                continue      # the original
                            yield i, j, k

            curve_ids: dict = {}
            for idx, (i, j, k) in enumerate(grid()):
                for g in groups:
                    ref = g_refs[id(g)]
                    c = common if common is not None else ref
                    m = copy_matrix(i, j, k, p, c, ref)
                    ng = copy_group(g)
                    if ng.xform is not None:
                        if not instance:
                            ng.make_unique()     # Copy: independent
                    if ng.xform is not None:
                        ng.xform = m * ng.xform
                    else:
                        ng.mesh = transformed_mesh(ng.mesh, m)
                        carry_axes(ng, m)
                    self._run(scene_, InsertGroupCommand(ng))
                if faces or edges:
                    c = common if common is not None else loose_ref
                    m = copy_matrix(i, j, k, p, c, loose_ref)
                    for f in faces:
                        self._run(scene_, AddFaceCommand(
                            [m.map(v) for v in f.vertices],
                            holes=[[m.map(v) for v in h] for h in f.holes]
                            or None,
                            auto=False,
                            attrs=transformed_attrs(f.attrs, m)))
                    for e in edges:
                        curve = getattr(e, "curve", None)
                        key = None if curve is None else (curve, idx)
                        if key is not None and key not in curve_ids:
                            curve_ids[key] = Mesh.next_curve_id()
                        self._run(scene_, AddEdgeCommand(
                            m.map(e.a), m.map(e.b),
                            soft=getattr(e, "soft", False) or None,
                            curve=curve_ids.get(key)))
                self.copies += 1

        def undo(self, scene_):
            for c in reversed(self.cmds):
                c.undo(scene_)

    return ArrayCommand()


def run_array(viewport, p: dict):
    """Execute the array as one undo step; the selection stays on the
    originals (as in 3ds Max). Returns the command or None."""
    scene = viewport.scene
    keep = set(scene.selection)
    cmd = make_array_command(scene, p)
    if cmd is None:
        return None
    viewport.history.execute(cmd)
    scene.selection.clear()
    scene.selection.update(e for e in keep)
    scene.version += 1
    notify = getattr(viewport, "notify_scene_changed", None)
    if notify:
        notify()
    viewport.update()
    return cmd


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def load_params() -> dict:
    p = default_params()
    try:
        from PySide6.QtCore import QSettings
        raw = QSettings().value(SETTINGS_KEY, "")
        if raw:
            saved = json.loads(raw)
            for k, v in saved.items():
                if k in p and type(v) is type(p[k]):
                    p[k] = v
    except Exception:
        pass
    return p


def save_params(p: dict) -> None:
    try:
        from PySide6.QtCore import QSettings
        QSettings().setValue(SETTINGS_KEY, json.dumps(p))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The dialog
# ---------------------------------------------------------------------------

def _unit():
    """(metres per typed unit, unit label) of the document."""
    try:
        from core import units
        code = units.model_unit()
        short = {"in": "in", "in-frac": "in", "ft": "ft", "ft-in": "ft",
                 "ft-in-frac": "ft"}.get(code, code)
        return units.bare_number_scale(), short
    except Exception:
        return 1.0, "m"


def _make_dialog_class():
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox,
                                   QDialog, QDoubleSpinBox, QGridLayout,
                                   QGroupBox, QHBoxLayout, QLabel,
                                   QMessageBox, QPushButton, QRadioButton,
                                   QSpinBox, QVBoxLayout)

    class ArrayDialog(QDialog):
        def __init__(self, viewport, parent=None):
            super().__init__(parent)
            self.viewport = viewport
            self.setWindowTitle(TITLE)
            # Non-modal: orbit, pan and zoom the viewport while the dialog
            # (and the preview) stays open. The objects to array are the
            # ones selected when the dialog opened — clicking around in the
            # viewport meanwhile does not change what gets copied.
            self.setModal(False)
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            self._sel = set(viewport.scene.selection)
            self.p = load_params()
            self.scale_m, self.ulabel = _unit()
            self._preview_cmd = None
            self._busy = False
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.setInterval(150)
            self._timer.timeout.connect(self._refresh_preview)
            self._build_ui()
            self._load_into_ui()

        # ---- UI ----------------------------------------------------------
        def _spin(self, lo, hi, dec, suffix=""):
            s = QDoubleSpinBox(self)
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setSuffix(suffix)
            s.setKeyboardTracking(False)
            s.setMinimumWidth(90)
            s.valueChanged.connect(self._changed)
            return s

        def _build_ui(self):
            lay = QVBoxLayout(self)

            # Array Transformation
            box = QGroupBox("Array Transformation: World Coordinates", self)
            g = QGridLayout(box)
            g.addWidget(QLabel("<b>Incremental</b>"), 0, 1, 1, 3,
                        Qt.AlignCenter)
            g.addWidget(QLabel("<b>Totals</b>"), 0, 6, 1, 3, Qt.AlignCenter)
            for c, t in enumerate("XYZ"):
                g.addWidget(QLabel(t), 1, 1 + c, Qt.AlignCenter)
                g.addWidget(QLabel(t), 1, 6 + c, Qt.AlignCenter)
            self.rows = {}
            u = f" {self.ulabel}"
            specs = [("move", "Move", -1e6, 1e6, 3, u),
                     ("rotate", "Rotate", -36000, 36000, 2, "°"),
                     ("scale", "Scale", -10000, 10000, 2, " %")]
            for r, (key, label, lo, hi, dec, suf) in enumerate(specs, start=2):
                inc = [self._spin(lo, hi, dec, suf) for _ in range(3)]
                tot = [self._spin(lo, hi, dec, suf) for _ in range(3)]
                left = QPushButton("<", self)
                right = QPushButton(">", self)
                for b in (left, right):
                    b.setFixedWidth(26)
                    b.setCheckable(True)
                left.clicked.connect(lambda _c=False, k=key: self._mode(k, "inc"))
                right.clicked.connect(lambda _c=False, k=key: self._mode(k, "tot"))
                g.addWidget(QLabel(label), r, 0)
                for c in range(3):
                    g.addWidget(inc[c], r, 1 + c)
                    g.addWidget(tot[c], r, 6 + c)
                g.addWidget(left, r, 4)
                g.addWidget(right, r, 5)
                g.addWidget(QLabel(label), r, 9)
                self.rows[key] = (inc, tot, left, right)
            self.reorient = QCheckBox("Re-Orient", self)
            self.uniform = QCheckBox("Uniform", self)
            self.reorient.toggled.connect(self._changed)
            self.uniform.toggled.connect(self._changed)
            g.addWidget(self.reorient, 5, 6, 1, 2)
            g.addWidget(self.uniform, 5, 8, 1, 2)
            g.addWidget(QLabel("Center:"), 5, 0)
            self.center = QComboBox(self)
            self.center.addItem("Selection Center", "selection")
            self.center.addItem("Pivot Point Center", "pivot")
            self.center.addItem("World Origin", "world")
            self.center.currentIndexChanged.connect(self._changed)
            g.addWidget(self.center, 5, 1, 1, 4)
            lay.addWidget(box)

            mid = QHBoxLayout()
            # Type of Object
            tbox = QGroupBox("Type of Object", self)
            tl = QVBoxLayout(tbox)
            self.t_copy = QRadioButton("Copy", self)
            self.t_inst = QRadioButton("Instance", self)
            self.t_group = QButtonGroup(self)
            for b in (self.t_copy, self.t_inst):
                self.t_group.addButton(b)
                tl.addWidget(b)
                b.toggled.connect(self._changed)
            tl.addStretch(1)
            mid.addWidget(tbox)

            # Array Dimensions
            dbox = QGroupBox("Array Dimensions", self)
            dl = QGridLayout(dbox)
            dl.addWidget(QLabel("Count"), 0, 1)
            dl.addWidget(QLabel("<b>Incremental Row Offsets</b>"), 0, 2, 1, 3,
                         Qt.AlignCenter)
            for c, t in enumerate("XYZ"):
                dl.addWidget(QLabel(t), 1, 2 + c, Qt.AlignCenter)
            self.d_radio = []
            self.d_count = []
            self.d_off = {2: [], 3: []}
            self.d_group = QButtonGroup(self)
            for r, d in enumerate((1, 2, 3), start=2):
                rb = QRadioButton(f"{d}D", self)
                self.d_group.addButton(rb)
                rb.toggled.connect(self._changed)
                sp = QSpinBox(self)
                sp.setRange(1, 10000)
                sp.setKeyboardTracking(False)
                sp.valueChanged.connect(self._changed)
                dl.addWidget(rb, r, 0)
                dl.addWidget(sp, r, 1)
                self.d_radio.append(rb)
                self.d_count.append(sp)
                if d >= 2:
                    for c in range(3):
                        s = self._spin(-1e6, 1e6, 3, u)
                        dl.addWidget(s, r, 2 + c)
                        self.d_off[d].append(s)
            self.total_lbl = QLabel(self)
            dl.addWidget(QLabel("Total in Array:"), 5, 0, 1, 2)
            dl.addWidget(self.total_lbl, 5, 2)
            mid.addWidget(dbox, 1)
            lay.addLayout(mid)

            # Live-preview banner: impossible to miss while the preview runs.
            self.pv_lbl = QLabel(self)
            self.pv_lbl.setWordWrap(True)
            self.pv_lbl.setVisible(False)
            lay.addWidget(self.pv_lbl)

            # Buttons
            bl = QHBoxLayout()
            self.preview = QPushButton("Preview", self)
            self.preview.setCheckable(True)
            self.preview.setMinimumWidth(130)
            self.preview.toggled.connect(self._preview_toggled)
            reset = QPushButton("Reset All Parameters", self)
            reset.clicked.connect(self._reset)
            ok = QPushButton("OK", self)
            ok.setDefault(True)
            ok.clicked.connect(self.accept)
            cancel = QPushButton("Cancel", self)
            cancel.clicked.connect(self.reject)
            bl.addWidget(self.preview)
            bl.addWidget(reset)
            bl.addStretch(1)
            bl.addWidget(ok)
            bl.addWidget(cancel)
            lay.addLayout(bl)

        # ---- parameters <-> UI -------------------------------------------
        def _conv(self, key):
            """(UI value -> stored value) factor."""
            return self.scale_m if key == "move" else 1.0

        def _load_into_ui(self):
            self._busy = True
            p = self.p
            for key, (inc, tot, left, right) in self.rows.items():
                f = self._conv(key)
                for c in range(3):
                    inc[c].setValue(p[key]["inc"][c] / f)
                    tot[c].setValue(p[key]["tot"][c] / f)
            self.reorient.setChecked(bool(p["reorient"]))
            self.uniform.setChecked(bool(p["uniform"]))
            i = max(0, self.center.findData(p["center"]))
            self.center.setCurrentIndex(i)
            (self.t_inst if p["type"] == "instance" else self.t_copy).setChecked(True)
            self.d_radio[max(0, min(2, int(p["dim"]) - 1))].setChecked(True)
            for c in range(3):
                self.d_count[c].setValue(int(p["count"][c]))
                self.d_off[2][c].setValue(p["row2"][c] / self.scale_m)
                self.d_off[3][c].setValue(p["row3"][c] / self.scale_m)
            self._busy = False
            self._sync()

        def _read_ui(self):
            p = self.p
            for key, (inc, tot, _l, _r) in self.rows.items():
                f = self._conv(key)
                if p[key]["mode"] == "inc":
                    p[key]["inc"] = [s.value() * f for s in inc]
                else:
                    p[key]["tot"] = [s.value() * f for s in tot]
            p["reorient"] = self.reorient.isChecked()
            p["uniform"] = self.uniform.isChecked()
            p["center"] = self.center.currentData()
            p["type"] = "instance" if self.t_inst.isChecked() else "copy"
            for d, rb in enumerate(self.d_radio, start=1):
                if rb.isChecked():
                    p["dim"] = d
            p["count"] = [s.value() for s in self.d_count]
            p["row2"] = [s.value() * self.scale_m for s in self.d_off[2]]
            p["row3"] = [s.value() * self.scale_m for s in self.d_off[3]]

        def _sync(self):
            """Enable the active side of each row, show the computed value
            on the other, the dimensions in use and the total."""
            self._busy = True
            p = self.p
            inc_v = increments(p)
            tot_v = totals_from_increments(p)
            for n, (key, (inc, tot, left, right)) in enumerate(self.rows.items()):
                f = self._conv(key)
                active_inc = p[key]["mode"] == "inc"
                left.setChecked(active_inc)
                right.setChecked(not active_inc)
                uni = key == "scale" and p["uniform"]
                for c in range(3):
                    inc[c].setEnabled(active_inc and not (uni and c > 0))
                    tot[c].setEnabled(not active_inc and not (uni and c > 0))
                    if active_inc:
                        tot[c].setValue(tot_v[n][c] / f)
                    else:
                        inc[c].setValue(inc_v[n][c] / f)
            dim = p["dim"]
            for d in (1, 2, 3):
                self.d_count[d - 1].setEnabled(d <= dim)
                for s in self.d_off.get(d, []):
                    s.setEnabled(d <= dim)
            self.total_lbl.setText(str(total_in_array(p)))
            self._busy = False

        def _mode(self, key, mode):
            self._read_ui()
            p = self.p
            if p[key]["mode"] != mode:
                # Carry the effective value over to the new side.
                n = list(self.rows).index(key)
                if mode == "tot":
                    p[key]["tot"] = list(totals_from_increments(p)[n])
                else:
                    p[key]["inc"] = list(increments(p)[n])
                p[key]["mode"] = mode
            self._load_into_ui()
            self._changed()

        _PV_ON = ("QPushButton { background: #2e9e4f; color: white; "
                  "font-weight: bold; border: 1px solid #1f7a3a; "
                  "border-radius: 3px; padding: 3px 8px; }")
        _BANNER = {
            "live": "background: #1f5f33; color: #e8ffe9;",
            "busy": "background: #7a5a12; color: #fff6e0;",
            "error": "background: #7a1f1f; color: #ffecec;",
        }

        def _banner(self, kind, text):
            self.pv_lbl.setStyleSheet(
                self._BANNER[kind] + " padding: 6px 8px; border-radius: 3px;")
            self.pv_lbl.setText(text)
            self.pv_lbl.setVisible(True)

        def _style_preview(self, on):
            if on:
                self.preview.setText("● Live Preview ON")
                self.preview.setStyleSheet(self._PV_ON)
                self.preview.setToolTip(
                    "The preview follows every change by itself — "
                    "click to switch it off.")
            else:
                self.preview.setText("Preview")
                self.preview.setStyleSheet("")
                self.preview.setToolTip(
                    "Show the array in the model; it then updates by "
                    "itself on every change.")
                self.pv_lbl.setVisible(False)
            if self.isVisible():
                QTimer.singleShot(0, self.adjustSize)

        def _changed(self, *_a):
            if self._busy:
                return
            self._read_ui()
            self._sync()
            if self.preview.isChecked():
                self._banner("busy", "⟳ Updating the preview…")
                self._timer.start()

        def _reset(self):
            self.p = default_params()
            self._load_into_ui()
            self._changed()

        # ---- the objects to array ------------------------------------------
        def _restore_selection(self) -> bool:
            """Put the dialog's objects back into the selection (those that
            still exist). False when none is left."""
            scene = self.viewport.scene
            alive = set(scene.groups) | set(scene.mesh.faces) | set(scene.mesh.edges)
            sel = {e for e in self._sel if e in alive}
            scene.selection.clear()
            scene.selection.update(sel)
            return bool(sel)

        # ---- preview -----------------------------------------------------
        def _undo_preview(self):
            cmd = self._preview_cmd
            self._preview_cmd = None
            if cmd is None:
                return
            stack = getattr(self.viewport.history, "undo_stack", [])
            if stack and stack[-1] is cmd:
                keep = set(self.viewport.scene.selection)
                self.viewport.history.undo()
                self.viewport.scene.selection.clear()
                self.viewport.scene.selection.update(keep)
                self.viewport.update()

        def _too_many(self) -> bool:
            return total_in_array(self.p) > MAX_OBJECTS

        def _refresh_preview(self):
            self._undo_preview()
            if not self.preview.isChecked():
                return
            if self._too_many():
                self._banner(
                    "error", f"Preview paused — Total in Array is "
                    f"{total_in_array(self.p):,}, more than {MAX_OBJECTS:,}. "
                    "Reduce the counts.")
                return
            self._banner("busy", "⟳ Updating the preview…")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            if not self._restore_selection():
                self._banner("error", "The objects to array are gone "
                             "(deleted or undone). Close and select again.")
                return
            try:
                self._preview_cmd = run_array(self.viewport, self.p)
            except Exception as exc:          # never leave half an array
                self._preview_cmd = None
                self._banner("error", f"Preview failed: {exc}")
                return
            if self._preview_cmd is None:
                self._banner("live", "● <b>LIVE PREVIEW</b> — nothing to "
                             "copy yet (Total in Array is 1).")
            else:
                self._banner(
                    "live",
                    f"● <b>LIVE PREVIEW</b> — {self._preview_cmd.copies:,} "
                    f"copies · changes apply instantly")

        def _preview_toggled(self, on):
            self._style_preview(on)
            if on:
                self._refresh_preview()
            else:
                self._timer.stop()
                self._undo_preview()

        # ---- close -------------------------------------------------------
        def accept(self):
            self._read_ui()
            if self._too_many():
                QMessageBox.warning(
                    self, TITLE,
                    f"Total in Array is {total_in_array(self.p)} — more than "
                    f"{MAX_OBJECTS}. Reduce the counts.")
                return
            self._timer.stop()
            self._undo_preview()
            save_params(self.p)
            if not self._restore_selection():
                QMessageBox.warning(self, TITLE, "The objects to array are "
                                    "gone (deleted or undone).")
                return
            try:
                cmd = run_array(self.viewport, self.p)
            except Exception as exc:
                QMessageBox.critical(self, TITLE, f"The array failed:\n{exc}")
                return
            if cmd is not None:
                self.viewport.flash_status(
                    f"Array: {cmd.copies} copies (one undo step)", 4000)
            super().accept()

        def reject(self):
            self._timer.stop()
            self._undo_preview()
            self._read_ui()
            save_params(self.p)
            super().reject()

    return ArrayDialog


_DIALOG_CLASS = None
_OPEN = None


def show_array_dialog(viewport, parent=None) -> None:
    global _DIALOG_CLASS
    if not viewport.scene.selection:
        viewport.flash_status(
            "Array: select the objects to array first.", 5000)
        return
    groups, faces, edges = gather_selection(viewport.scene)
    if not (groups or faces or edges):
        viewport.flash_status(
            "Array: select groups, components or geometry first.", 5000)
        return
    if _DIALOG_CLASS is None:
        _DIALOG_CLASS = _make_dialog_class()
    global _OPEN
    if _OPEN is not None:
        try:
            _OPEN.reject()
        except RuntimeError:            # already closed and deleted
            pass
    dlg = _DIALOG_CLASS(viewport, parent or viewport.window())
    _OPEN = dlg
    dlg.show()
    dlg.raise_()

# ---------------------------------------------------------------------------
# Toolbar (PESI3D): icons drawn in IngeTrazo's own icon style
# ---------------------------------------------------------------------------

def _pesi3d_icons():
    """Icon key → draw(painter, ink, accent) on a 48 px canvas."""
    import math  # noqa: F401
    from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: F401
    from PySide6.QtGui import (QBrush, QColor, QPainterPath, QPen,  # noqa: F401
                               QPolygonF)

    def _a(c, alpha):
        return QColor(c.red(), c.green(), c.blue(), alpha)

    def array_icon(p, ink, acc):
        # Original (accent) and two copies — each moved, turned and scaled
        # a little more, as the Array dialog's 1D row does.
        p.save()
        p.setBrush(_a(acc, 170))
        p.drawRect(QRectF(7, 26, 14, 14))
        p.restore()
        for cx, cy, s, ang in ((25.5, 25.5, 11.0, 15), (36.5, 13.5, 8.0, 30)):
            p.save()
            p.translate(cx, cy)
            p.rotate(ang)
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(-s / 2, -s / 2, s, s))
            p.restore()

    return {"array": array_icon}


def _pesi3d_toolbar(app, title, entries):
    """A toolbar of this plugin's own — one icon per command (PESI3D).

    ``entries`` = (icon key, text, tip, callable). The icons are drawn
    like IngeTrazo's own (views/icons.py: 48 px, ink = the palette's text
    colour, 3 px pen, the orange accent) and redrawn when the theme flips.
    The toolbar moves, floats and hides like the built-in ones (right-click
    on any toolbar); its place is kept by its objectName."""
    try:
        from PySide6.QtCore import QEvent, QObject, QSize, Qt
        from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
        from PySide6.QtWidgets import QApplication, QToolBar
    except Exception:  # noqa: BLE001 — no Qt, no toolbar
        return None
    win = getattr(app, "window", None)
    if win is None:
        return None
    draws = _pesi3d_icons()

    def make_icon(key):
        draw = draws.get(key)
        if draw is None:
            return QIcon()
        qa = QApplication.instance()
        ink = (QColor(qa.palette().windowText().color()) if qa is not None
               else QColor(40, 44, 52))
        pm = QPixmap(48, 48)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(ink, 3.0)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        try:
            draw(p, ink, QColor(243, 115, 41))
        finally:
            p.end()
        return QIcon(pm)

    name = f"pesi3d_{getattr(app, 'key', title)}"
    tb = None
    make = getattr(win, "_new_toolbar", None)     # the host's own builder
    if callable(make):
        try:
            tb = make(title, name)
        except Exception:  # noqa: BLE001
            tb = None
    if tb is None:
        tb = QToolBar(title, win)
        tb.setObjectName(name)
        tb.setMovable(True)
        tb.setFloatable(True)
        try:
            from views.icons import toolbar_icon_px
            px = int(toolbar_icon_px())
        except Exception:  # noqa: BLE001
            px = 24
        tb.setIconSize(QSize(px, px))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        win.addToolBar(Qt.TopToolBarArea, tb)

    actions = []
    for key, text, tip, fn in entries:
        act = QAction(make_icon(key), text, tb)
        act.setToolTip(f"{text}\n{tip}" if tip else text)
        if tip:
            act.setStatusTip(tip)
        act.triggered.connect(lambda _c=False, f=fn: f())
        tb.addAction(act)
        actions.append((act, key))

    class _ThemeWatch(QObject):
        def eventFilter(self, obj, event):  # noqa: N802 — Qt override
            if event.type() in (QEvent.PaletteChange,
                                QEvent.ApplicationPaletteChange,
                                QEvent.StyleChange):
                for a, k in actions:
                    a.setIcon(make_icon(k))
            return False

    watch = _ThemeWatch(tb)
    tb.installEventFilter(watch)
    tb._pesi3d_watch = watch
    _pesi3d_place_later(win)
    return tb


def _pesi3d_place_later(win):
    """A toolbar the saved window layout does not know yet lands at the end
    of the top row, squeezed behind the built-in ones. Once the window is
    laid out, put new PESI3D toolbars on a row of their own under the
    built-in ones — only the first time each one appears; after that the
    user's own arrangement (saved with the window) wins. Every PESI3D
    plugin carries this code; the first one to get here does it for all."""
    if getattr(win, "_pesi3d_place_pending", False):
        return
    win._pesi3d_place_pending = True
    from PySide6.QtCore import QSettings, Qt, QTimer
    from PySide6.QtWidgets import QToolBar

    def place():
        win._pesi3d_place_pending = False
        try:
            st = QSettings()
            key = "plugins/pesi3d/placed_toolbars"
            placed = st.value(key) or []
            if isinstance(placed, str):
                placed = [placed]
            placed = list(placed)
            bars = [t for t in win.findChildren(QToolBar)
                    if t.objectName().startswith("pesi3d_")]
            new = [t for t in bars if t.objectName() not in placed]
            if not new:
                return
            fresh = not placed            # no PESI3D row yet → open one
            for i, t in enumerate(sorted(new, key=lambda t: t.objectName())):
                shown = not t.isHidden()
                win.removeToolBar(t)
                if fresh and i == 0:
                    win.addToolBarBreak(Qt.TopToolBarArea)
                win.addToolBar(Qt.TopToolBarArea, t)
                t.setVisible(shown)
            st.setValue(key, placed + [t.objectName() for t in new])
        except Exception:  # noqa: BLE001 — layout only, never break the app
            pass

    QTimer.singleShot(0, place)


def setup(app) -> None:
    """Extensions ▸ Array…  and right-click ▸ Array… on a selection."""
    app.add_menu_action(
        "Array…", lambda: show_array_dialog(app.viewport, app.window),
        tip="Copies of the selection in 1D, 2D or 3D with move, rotate and "
            "scale per copy (like the 3ds Max Array dialog).")

    def context(menu, selection) -> None:
        if not app.viewport.scene.selection:
            return
        from PySide6.QtCore import QTimer
        menu.addSeparator()
        act = menu.addAction("Array…")
        act.triggered.connect(lambda _c=False: QTimer.singleShot(
            0, lambda: show_array_dialog(app.viewport, app.window)))

    app.add_context_menu(context)

    _pesi3d_toolbar(app, TITLE, [
        ("array", "Array…",
         "Copies of the selection in 1D, 2D or 3D with move, rotate and scale per copy.",
         lambda: show_array_dialog(app.viewport, app.window)),
    ])
