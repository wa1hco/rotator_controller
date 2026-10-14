#!/usr/bin/env python3
# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Move overlapping schematic text on a KiCad sheet.

Reference, value, and other visible fields, plus net, global, and
hierarchical labels (and sheet pins), are checked against symbol-body
boxes, wires, and other text. An item moves only when its ink box
overlaps one of those. Everything else keeps its exact bytes: position,
rotation, and justification.

Fields and labels Jeff Millar edited in f665ffd are listed in
owner_frozen.json. Those items stay exactly where he put them, even
when they still overlap. The checker reports them and does not fail
the build for his placements.

Symbol bodies come from the embedded lib_symbols. Library coordinates
are Y-up; the sheet file is Y-down. The instance transform matches
KiCad's 0/90/180/270 matrices, including mirror. Text extents use the
schematic stroke-font widths at the field's font size.

Labels stay on the wire or pin they already mark. Only the spin
(the angle and justification KiCad actually draws) changes. A short
stub wire is added only when no spin is clear. Symbols and existing
wires are never moved.

The writer replaces the (at), (justify), and (hide) tokens of the
items it changes. It does not reserialize the sheet, so a field that
does not overlap is byte-identical.

    python3 software/tools/kicad/tidy_schematic.py --check SHEET.kicad_sch
    python3 software/tools/kicad/tidy_schematic.py --dry-run SHEET.kicad_sch
    python3 software/tools/kicad/tidy_schematic.py SHEET.kicad_sch
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path


GRID = 1.27
# Ink boxes closer than this are a touch, not an overlap. Glyph-width
# error on short labels is about 0.15 mm, so a smaller epsilon would
# move text the owner (or a previous pass) already left clear.
EPS = 0.20
# A label is allowed to sit on its own connection point.
ATTACH_R = 0.45
DEFAULT_STROKE = 0.1524
# KiCad text-offset ratio plus the default pen (size/8) for local labels.
LOCAL_OFFSET_RATIO = 0.15 + 0.125
# Hierarchical / global / sheet-pin text starts one glyph-width plus the
# text-offset ratio past the anchor. See SCH_HIERLABEL::GetSchematicTextOffset.
HIER_OFFSET_EXTRA = 0.15
# Stroke font baseline pitch at line-spacing 1, in units of the font height.
INTERLINE = 1.61
# Glyph advance / font size. Fitted from KiCad 9 SVG textLength on these
# sheets (median error 0.05 mm at 1.27 mm). Unknown characters use 0.90.
GLYPH_WIDTH = {
    " ": 0.7249,
    "#": 0.9889,
    "'": 0.7972,
    "(": 1.3150,
    ")": 0.8500,
    "+": 1.3459,
    ",": 0.8500,
    "-": 1.1089,
    ".": 0.4532,
    "/": 0.9540,
    "0": 0.9657,
    "1": 1.0281,
    "2": 1.0270,
    "3": 0.9974,
    "4": 0.9982,
    "5": 1.0297,
    "6": 1.0274,
    "7": 1.0103,
    "8": 1.0256,
    "9": 1.0297,
    ":": 0.7194,
    "=": 1.0714,
    "A": 0.8969,
    "B": 0.9992,
    "C": 1.0420,
    "D": 1.0595,
    "E": 0.9106,
    "F": 0.9182,
    "G": 1.0387,
    "H": 1.0956,
    "I": 0.5179,
    "J": 0.8473,
    "K": 1.0320,
    "L": 0.8024,
    "M": 1.1563,
    "N": 1.0771,
    "O": 1.0602,
    "P": 0.9797,
    "Q": 1.1432,
    "R": 1.0247,
    "S": 0.9467,
    "T": 0.7852,
    "U": 1.1007,
    "V": 0.8257,
    "W": 1.1120,
    "X": 1.0000,
    "Y": 0.8469,
    "Z": 0.9532,
    "_": 0.7840,
    "a": 0.7983,
    "b": 0.9919,
    "c": 0.7730,
    "d": 0.9210,
    "e": 0.7582,
    "f": 0.9413,
    "g": 1.1134,
    "h": 0.9525,
    "i": 0.3223,
    "k": 0.8413,
    "l": 0.5947,
    "m": 1.4618,
    "n": 0.9031,
    "o": 0.9429,
    "p": 0.9508,
    "r": 0.5583,
    "s": 0.9503,
    "t": 0.6481,
    "u": 0.9469,
    "v": 1.0504,
    "w": 1.3929,
    "x": 0.8500,
    "y": 0.8479,
    "z": 0.7906,
}
HIDE_WHEN_OVERLAPPING = {"Footprint", "LCSC", "MPN"}
LABEL_HEADS = {"label", "global_label", "hierarchical_label"}


def _load_frozen(path: Path | None = None) -> set[tuple]:
    """Keys of fields and labels the owner placed. The tool never moves them."""
    source = path if path is not None else Path(__file__).with_name("owner_frozen.json")
    if not source.is_file():
        return set()
    data = json.loads(source.read_text(encoding="utf-8"))
    return {tuple(key) for key in data.get("keys", [])}


# (kind, uuid) or (kind, parent uuid, property name). Loaded once.
FROZEN: set[tuple] = _load_frozen()


# --- s-expression spans -------------------------------------------------

@dataclass
class Form:
    start: int
    end: int
    parts: list = field(default_factory=list)

    @property
    def head(self) -> str:
        if self.parts and isinstance(self.parts[0], str):
            return self.parts[0]
        return ""

    def atoms(self):
        for part in self.parts[1:]:
            if isinstance(part, str):
                yield part

    def child(self, name: str):
        for part in self.parts:
            if isinstance(part, Form) and part.head == name:
                return part
        return None

    def children(self, name: str | None = None):
        for part in self.parts:
            if isinstance(part, Form) and (name is None or part.head == name):
                yield part

    def atom_after(self, name: str) -> str | None:
        """Value atom of a (name value) pair that is a direct child."""
        node = self.child(name)
        if node is None:
            return None
        for part in node.parts[1:]:
            if isinstance(part, str):
                return part
        return None


def _tokenize(text: str):
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            yield c, i, i + 1
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            yield text[i:j], i, j
            i = j
            continue
        j = i + 1
        while j < n and not text[j].isspace() and text[j] not in "()":
            j += 1
        yield text[i:j], i, j
        i = j


def _parse_form(tokens, index, text):
    kind, start, _ = tokens[index]
    if kind != "(":
        raise ValueError(f"expected '(' at {start}")
    parts = []
    index += 1
    while index < len(tokens):
        kind, tok_start, tok_end = tokens[index]
        if kind == ")":
            return Form(start, tok_end, parts), index + 1
        if kind == "(":
            child, index = _parse_form(tokens, index, text)
            parts.append(child)
            continue
        if kind.startswith('"') and kind.endswith('"') and len(kind) >= 2:
            raw = kind[1:-1]
            raw = raw.replace("\\\\", "\\").replace('\\"', '"').replace("\\n", "\n")
            parts.append(raw)
        else:
            parts.append(kind)
        index += 1
    raise ValueError("unclosed '('")


def parse_sexpr(text: str) -> Form:
    tokens = list(_tokenize(text))
    if not tokens or tokens[0][0] != "(":
        raise ValueError("schematic is not an s-expression")
    form, index = _parse_form(tokens, 0, text)
    return form


def _num(token: str) -> float:
    return float(token)


def fmt_num(value: float) -> str:
    quantized = round(value, 2)
    rendered = f"{quantized:.2f}".rstrip("0").rstrip(".")
    if rendered in ("", "-0"):
        return "0"
    return rendered


# --- geometry -----------------------------------------------------------

@dataclass
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    def normalized(self) -> "Box":
        return Box(min(self.x0, self.x1), min(self.y0, self.y1),
                   max(self.x0, self.x1), max(self.y0, self.y1))

    def inflate(self, pad: float) -> "Box":
        return Box(self.x0 - pad, self.y0 - pad, self.x1 + pad, self.y1 + pad)

    def union(self, other: "Box") -> "Box":
        return Box(min(self.x0, other.x0), min(self.y0, other.y0),
                   max(self.x1, other.x1), max(self.y1, other.y1))


def boxes_overlap(a: Box, b: Box, eps: float = EPS) -> bool:
    return (min(a.x1, b.x1) - max(a.x0, b.x0)) > eps and (
        min(a.y1, b.y1) - max(a.y0, b.y0)
    ) > eps


def shown_text(raw: str) -> str:
    """Text KiCad draws. '~' is empty. '~{ABC}' and '~A' draw an overbar."""
    if raw == "~":
        return ""
    out = []
    i = 0
    while i < len(raw):
        if raw.startswith("~{", i):
            end = raw.find("}", i + 2)
            if end < 0:
                out.append(raw[i + 1 :])
                break
            out.append(raw[i + 2 : end])
            i = end + 1
            continue
        if raw[i] == "~" and i + 1 < len(raw):
            out.append(raw[i + 1])
            i += 2
            continue
        out.append(raw[i])
        i += 1
    return "".join(out)


def text_width(text: str, size: float) -> float:
    total = 0.0
    for char in text:
        total += GLYPH_WIDTH.get(char, 0.90)
    return total * size


def text_size_of(effects: Form | None) -> tuple[float, float]:
    if effects is None:
        return 1.27, 1.27
    font = effects.child("font")
    if font is None:
        return 1.27, 1.27
    size = font.child("size")
    if size is None or len(size.parts) < 3:
        return 1.27, 1.27
    return _num(size.parts[1]), _num(size.parts[2])


def justify_of(effects: Form | None) -> tuple[str, str]:
    horiz, vert = "center", "center"
    if effects is None:
        return horiz, vert
    node = effects.child("justify")
    if node is None:
        return horiz, vert
    for part in node.atoms():
        if part in ("left", "right", "center"):
            horiz = part
        elif part in ("top", "bottom"):
            vert = part
    return horiz, vert


def is_hidden(effects: Form | None) -> bool:
    if effects is None:
        return False
    hide = effects.child("hide")
    if hide is None:
        return False
    flag = next(hide.atoms(), "yes")
    return flag != "no"


def line_spacing_of(effects: Form | None) -> float:
    if effects is None:
        return 1.0
    font = effects.child("font")
    if font is None:
        return 1.0
    node = font.child("line_spacing")
    if node is None:
        return 1.0
    value = next(node.atoms(), None)
    return float(value) if value is not None else 1.0


def upright_angle(angle: float) -> int:
    """KiCad KeepUpright() collapses 180->0 and 270->90 before spin is set."""
    turned = int(round(angle)) % 360
    if turned == 180:
        return 0
    if turned == 270:
        return 90
    return turned


def spin_of(angle: float, horiz: str) -> str:
    """Spin KiCad draws after load.

    The file angle is uprighted, SetSpinStyle runs, then the effects
    justification overwrites the horizontal align. With justify left,
    angle 180 draws the same way as angle 0 (text to +X), and angle 270
    draws the same way as angle 90 (text toward -Y).
    """
    vertical = upright_angle(angle) == 90
    if vertical:
        return "down" if horiz == "right" else "up"
    return "left" if horiz == "right" else "right"


def spin_file(spin: str) -> tuple[int, str]:
    """Angle and justification KiCad's saver writes for a spin."""
    return {
        "right": (0, "left"),
        "left": (180, "right"),
        "up": (90, "left"),
        "down": (270, "right"),
    }[spin]


def lib_to_sheet(lx: float, ly: float, ax: float, ay: float, rot: int, mirror: str | None):
    if mirror == "x":
        ly = -ly
    elif mirror == "y":
        lx = -lx
    turned = rot % 360
    if turned == 0:
        return ax + lx, ay - ly
    if turned == 180:
        return ax - lx, ay + ly
    if turned == 90:
        return ax - ly, ay - lx
    if turned == 270:
        return ax + ly, ay + lx
    raise ValueError(f"unsupported symbol rotation {rot}")


def field_box(x, y, angle, width, height, horiz, vert) -> Box:
    """Axis-aligned ink box of ordinary text (fields, notes, sheet names)."""
    if horiz == "left":
        x0, x1 = 0.0, width
    elif horiz == "right":
        x0, x1 = -width, 0.0
    else:
        x0, x1 = -width / 2.0, width / 2.0
    if vert == "top":
        y0, y1 = 0.0, height
    elif vert == "bottom":
        y0, y1 = -height, 0.0
    else:
        y0, y1 = -height / 2.0, height / 2.0
    corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    turned = int(round(angle)) % 360
    mapped = []
    for dx, dy in corners:
        if turned == 0:
            mapped.append((x + dx, y + dy))
        elif turned == 180:
            mapped.append((x - dx, y - dy))
        elif turned == 90:
            # File angle is CCW in Y-up, which is clockwise on the Y-down sheet.
            mapped.append((x + dy, y - dx))
        elif turned == 270:
            mapped.append((x - dy, y + dx))
        else:
            mapped.append((x + dx, y + dy))
    xs = [p[0] for p in mapped]
    ys = [p[1] for p in mapped]
    return Box(min(xs), min(ys), max(xs), max(ys))


def multiline_box(x, y, angle, raw: str, size_x, size_y, horiz, vert, spacing) -> Box | None:
    shown = shown_text(raw)
    if shown == "":
        return None
    lines = shown.split("\n")
    width = max(text_width(line, size_x) for line in lines)
    if width <= 0:
        return None
    pitch = INTERLINE * size_y * spacing
    height = size_y + (len(lines) - 1) * pitch
    return field_box(x, y, angle, width, height, horiz, vert)


def label_box(x, y, spin: str, width: float, height: float, kind: str) -> Box:
    """Text plus the hierarchical shape, in sheet coordinates."""
    if kind == "label":
        dist = LOCAL_OFFSET_RATIO * height
        if spin == "right":
            box = Box(x, y + dist - height, x + width, y + dist)
        elif spin == "left":
            box = Box(x - width, y + dist - height, x, y + dist)
        elif spin == "up":
            box = Box(x + dist - height, y - width, x + dist, y)
        else:
            box = Box(x + dist - height, y, x + dist, y + width)
        return box
    dist = (1.0 + HIER_OFFSET_EXTRA) * height
    shape = height * (1.6 if kind == "global_label" else 1.0)
    if spin == "right":
        text = Box(x + dist, y - height / 2.0, x + dist + width, y + height / 2.0)
        graphic = Box(x, y - height / 2.0, x + shape, y + height / 2.0)
    elif spin == "left":
        text = Box(x - dist - width, y - height / 2.0, x - dist, y + height / 2.0)
        graphic = Box(x - shape, y - height / 2.0, x, y + height / 2.0)
    elif spin == "up":
        text = Box(x - height / 2.0, y - dist - width, x + height / 2.0, y - dist)
        graphic = Box(x - height / 2.0, y - shape, x + height / 2.0, y)
    else:
        text = Box(x - height / 2.0, y + dist, x + height / 2.0, y + dist + width)
        graphic = Box(x - height / 2.0, y, x + height / 2.0, y + shape)
    return text.union(graphic)


# --- sheet model --------------------------------------------------------

@dataclass
class SymbolBody:
    name: str
    box: Box
    pins: list  # (x, y) connection points in sheet coordinates


@dataclass
class WireSeg:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class TextItem:
    kind: str  # property, label, global_label, hierarchical_label, sheet_pin, text
    name: str
    shown: str
    x: float
    y: float
    angle: float
    horiz: str
    vert: str
    size_x: float
    size_y: float
    spacing: float
    box: Box
    # Spans into the original file. None when the item is not editable.
    at_span: tuple[int, int] | None = None
    justify_span: tuple[int, int] | None = None
    effects_close: int | None = None
    anchor_on_pin: bool = False
    movable: bool = True
    # Set when this pass relocates or rewrites the item.
    new_x: float | None = None
    new_y: float | None = None
    new_angle: float | None = None
    new_horiz: str | None = None
    hide: bool = False
    stub: tuple[float, float, float, float] | None = None
    # (kind, uuid) or ("property"|"sheet_property", parent uuid, name).
    key: tuple | None = None
    # Owner-edited. Kept as an obstacle and never rewritten.
    frozen: bool = False

    def current_box(self) -> Box:
        return self.box

    def place(self, x, y, angle, horiz, vert, spacing=None):
        self.new_x = x
        self.new_y = y
        self.new_angle = angle
        self.new_horiz = horiz
        self.x, self.y, self.angle, self.horiz, self.vert = x, y, angle, horiz, vert
        if spacing is not None:
            self.spacing = spacing
        self.box = self._rebuild_box()

    def _rebuild_box(self) -> Box:
        if self.kind in LABEL_HEADS or self.kind == "sheet_pin":
            kind = "label" if self.kind == "label" else (
                "global_label" if self.kind == "global_label" else "hierarchical_label"
            )
            width = text_width(self.shown, self.size_x)
            return label_box(self.x, self.y, spin_of(self.angle, self.horiz), width, self.size_y, kind)
        rebuilt = multiline_box(
            self.x, self.y, self.angle, self.shown, self.size_x, self.size_y,
            self.horiz, self.vert, self.spacing,
        )
        return rebuilt if rebuilt is not None else self.box


def _at_span(node: Form) -> tuple[tuple[int, int], float, float, float] | None:
    at = node.child("at")
    if at is None or len(at.parts) < 3:
        return None
    x = _num(at.parts[1])
    y = _num(at.parts[2])
    angle = _num(at.parts[3]) if len(at.parts) > 3 and isinstance(at.parts[3], str) else 0.0
    return (at.start, at.end), x, y, angle


def _xy_pairs(node: Form) -> list[tuple[float, float]]:
    points = []
    for child in node.children("xy"):
        atoms = list(child.atoms())
        if len(atoms) >= 2:
            points.append((_num(atoms[0]), _num(atoms[1])))
    return points


def _stroke_width(node: Form) -> float:
    stroke = node.child("stroke")
    if stroke is None:
        return DEFAULT_STROKE
    width = stroke.child("width")
    if width is None:
        return DEFAULT_STROKE
    value = next(width.atoms(), "0")
    parsed = _num(value)
    return DEFAULT_STROKE if parsed == 0 else parsed


def _transform_point(pt, origin, rot, mirror):
    return lib_to_sheet(pt[0], pt[1], origin[0], origin[1], rot, mirror)


def _primitive_boxes(graphic: Form, origin, rot, mirror) -> list[Box]:
    boxes = []
    width = _stroke_width(graphic) / 2.0
    head = graphic.head
    if head == "rectangle":
        start = graphic.child("start")
        end = graphic.child("end")
        if start and end:
            a = list(start.atoms())
            b = list(end.atoms())
            corners = [(float(a[0]), float(a[1])), (float(b[0]), float(b[1])),
                       (float(a[0]), float(b[1])), (float(b[0]), float(a[1]))]
            mapped = [_transform_point(p, origin, rot, mirror) for p in corners]
            xs = [p[0] for p in mapped]
            ys = [p[1] for p in mapped]
            boxes.append(Box(min(xs), min(ys), max(xs), max(ys)).inflate(width))
    elif head == "polyline":
        pts = graphic.child("pts")
        if pts:
            mapped = [_transform_point(p, origin, rot, mirror) for p in _xy_pairs(pts)]
            if mapped:
                xs = [p[0] for p in mapped]
                ys = [p[1] for p in mapped]
                boxes.append(Box(min(xs), min(ys), max(xs), max(ys)).inflate(width))
    elif head == "circle":
        center = graphic.child("center")
        radius = graphic.child("radius")
        if center and radius:
            atoms = list(center.atoms())
            cx, cy = _transform_point((float(atoms[0]), float(atoms[1])), origin, rot, mirror)
            rad = float(next(radius.atoms())) + width
            boxes.append(Box(cx - rad, cy - rad, cx + rad, cy + rad))
    elif head == "arc":
        start = graphic.child("start")
        mid = graphic.child("mid")
        end = graphic.child("end")
        if start and mid and end:
            triple = []
            for node in (start, mid, end):
                atoms = list(node.atoms())
                triple.append(_transform_point((float(atoms[0]), float(atoms[1])), origin, rot, mirror))
            xs = [p[0] for p in triple]
            ys = [p[1] for p in triple]
            boxes.append(Box(min(xs), min(ys), max(xs), max(ys)).inflate(width))
    return boxes


def _pin_geometry(pin: Form, origin, rot, mirror, names_hidden: bool, numbers_hidden: bool):
    at = pin.child("at")
    if at is None:
        return None, []
    atoms = list(at.atoms())
    lx, ly, lang = float(atoms[0]), float(atoms[1]), float(atoms[2]) if len(atoms) > 2 else 0.0
    length = float(pin.atom_after("length") or 0)
    # In the library file the pin angle is the direction from the connection
    # point back toward the body (Device:R's top pin sits at +Y with angle 270).
    rad = (int(round(lang)) % 360)
    toward = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}.get(rad, (-1.0, 0.0))
    inner = (lx + toward[0] * length, ly + toward[1] * length)
    tip = _transform_point((lx, ly), origin, rot, mirror)
    tail = _transform_point(inner, origin, rot, mirror)
    stroke = _stroke_width(pin) / 2.0
    segment = Box(min(tip[0], tail[0]), min(tip[1], tail[1]),
                  max(tip[0], tail[0]), max(tip[1], tail[1])).inflate(max(stroke, 0.05))
    return tip, [segment]


def _symbol_graphics(lib_sym: Form, unit: int):
    """Body-style 1 graphics for the common unit and the placed unit."""
    lib_name = lib_sym.parts[1]
    short = lib_name.split(":", 1)[-1]
    wanted = {f"{short}_0_1", f"{short}_{unit}_1"}
    graphics = []
    for child in lib_sym.children("symbol"):
        if len(child.parts) < 2 or child.parts[1] not in wanted:
            continue
        for part in child.parts:
            if isinstance(part, Form) and part.head in (
                "rectangle", "polyline", "circle", "arc", "bezier", "pin",
            ):
                graphics.append(part)
    names_hidden = False
    numbers_hidden = False
    pin_names = lib_sym.child("pin_names")
    if pin_names and pin_names.child("hide"):
        names_hidden = True
    pin_numbers = lib_sym.child("pin_numbers")
    if pin_numbers and pin_numbers.child("hide"):
        numbers_hidden = True
    return graphics, names_hidden, numbers_hidden


def _bind(item: TextItem | None, key: tuple) -> TextItem | None:
    if item is None:
        return None
    item.key = key
    if key in FROZEN:
        item.frozen = True
        item.movable = False
    return item


def _make_text_item(kind, name, raw, node, at_info, effects, movable) -> TextItem | None:
    span, x, y, angle = at_info
    size_x, size_y = text_size_of(effects)
    horiz, vert = justify_of(effects)
    spacing = line_spacing_of(effects)
    shown = shown_text(raw)
    if shown.strip() == "":
        return None
    if kind in LABEL_HEADS or kind == "sheet_pin":
        label_kind = {
            "label": "label",
            "global_label": "global_label",
            "sheet_pin": "hierarchical_label",
            "hierarchical_label": "hierarchical_label",
        }[kind]
        box = label_box(x, y, spin_of(angle, horiz), text_width(shown, size_x), size_y, label_kind)
    else:
        box = multiline_box(x, y, angle, raw, size_x, size_y, horiz, vert, spacing)
        if box is None:
            return None
    justify = effects.child("justify") if effects is not None else None
    return TextItem(
        kind=kind,
        name=name,
        shown=shown,
        x=x,
        y=y,
        angle=angle,
        horiz=horiz,
        vert=vert,
        size_x=size_x,
        size_y=size_y,
        spacing=spacing,
        box=box,
        at_span=span if movable else None,
        justify_span=(justify.start, justify.end) if justify is not None and movable else None,
        effects_close=(effects.end - 1) if effects is not None and movable else None,
        movable=movable,
    )


@dataclass
class SheetModel:
    symbols: list
    wires: list
    texts: list


def load_sheet(text: str) -> tuple[Form, SheetModel]:
    root = parse_sexpr(text)
    libraries = {}
    lib_root = root.child("lib_symbols")
    if lib_root is not None:
        for sym in lib_root.children("symbol"):
            if len(sym.parts) >= 2 and isinstance(sym.parts[1], str):
                libraries[sym.parts[1]] = sym

    symbols: list[SymbolBody] = []
    wires: list[WireSeg] = []
    texts: list[TextItem] = []

    for node in root.children():
        head = node.head
        if head == "symbol" and node.child("lib_id"):
            lib_id = node.parts[1] if False else node.atom_after("lib_id")
            # atom_after looks at child forms. lib_id's value is its atom.
            lib_node = node.child("lib_id")
            lib_id = next(lib_node.atoms()) if lib_node else ""
            at = _at_span(node)
            if at is None:
                continue
            _, ax, ay, arot = at
            mirror_node = node.child("mirror")
            mirror = next(mirror_node.atoms(), None) if mirror_node else None
            unit_node = node.child("unit")
            unit = int(next(unit_node.atoms())) if unit_node and next(unit_node.atoms(), None) else 1
            # next() consumes; re-read
            if unit_node:
                unit = int(list(unit_node.atoms())[0])
            lib = libraries.get(lib_id)
            boxes = []
            pins = []
            if lib is not None:
                graphics, names_hidden, numbers_hidden = _symbol_graphics(lib, unit)
                for graphic in graphics:
                    if graphic.head == "pin":
                        tip, _pin_boxes = _pin_geometry(
                            graphic, (ax, ay), int(round(arot)), mirror,
                            names_hidden, numbers_hidden,
                        )
                        if tip is not None:
                            pins.append(tip)
                        # Pin leads are the connection, not the body. Text may
                        # sit on the pin tip; it overlaps only when it enters
                        # the graphic body.
                    else:
                        boxes.extend(_primitive_boxes(graphic, (ax, ay), int(round(arot)), mirror))
            if not boxes:
                boxes.append(Box(ax - 1.27, ay - 1.27, ax + 1.27, ay + 1.27))
            body = boxes[0]
            for extra in boxes[1:]:
                body = body.union(extra)
            ref = ""
            for prop in node.children("property"):
                if len(prop.parts) >= 2 and prop.parts[1] == "Reference":
                    ref = prop.parts[2] if len(prop.parts) > 2 else ""
            symbols.append(SymbolBody(ref or lib_id, body, pins))
            sym_uuid = node.atom_after("uuid") or ""
            for prop in node.children("property"):
                if len(prop.parts) < 3:
                    continue
                pname = prop.parts[1]
                raw = prop.parts[2] if isinstance(prop.parts[2], str) else ""
                effects = prop.child("effects")
                if is_hidden(effects):
                    continue
                at_info = _at_span(prop)
                if at_info is None:
                    continue
                item = _bind(
                    _make_text_item("property", pname, raw, prop, at_info, effects, True),
                    ("property", sym_uuid, pname),
                )
                if item is not None:
                    texts.append(item)
        elif head in LABEL_HEADS:
            raw = node.parts[1] if len(node.parts) > 1 and isinstance(node.parts[1], str) else ""
            at_info = _at_span(node)
            if at_info is None:
                continue
            item = _bind(
                _make_text_item(head, head, raw, node, at_info, node.child("effects"), True),
                (head, node.atom_after("uuid") or ""),
            )
            if item is not None:
                texts.append(item)
        elif head == "text":
            raw = node.parts[1] if len(node.parts) > 1 and isinstance(node.parts[1], str) else ""
            at_info = _at_span(node)
            if at_info is None:
                continue
            item = _bind(
                _make_text_item("text", "text", raw, node, at_info, node.child("effects"), True),
                ("text", node.atom_after("uuid") or ""),
            )
            if item is not None:
                texts.append(item)
        elif head == "wire":
            pts = node.child("pts")
            if pts is None:
                continue
            pairs = _xy_pairs(pts)
            if len(pairs) >= 2:
                wires.append(WireSeg(pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1]))
        elif head == "sheet":
            at = node.child("at")
            size = node.child("size")
            if at and size:
                ax, ay = (float(v) for v in list(at.atoms())[:2])
                w, h = (float(v) for v in list(size.atoms())[:2])
                symbols.append(SymbolBody("sheet", Box(ax, ay, ax + w, ay + h), []))
            sheet_uuid = node.atom_after("uuid") or ""
            for prop in node.children("property"):
                if len(prop.parts) < 3:
                    continue
                effects = prop.child("effects")
                if is_hidden(effects):
                    continue
                at_info = _at_span(prop)
                if at_info is None:
                    continue
                item = _bind(
                    _make_text_item(
                        "property", prop.parts[1], prop.parts[2], prop, at_info, effects, True,
                    ),
                    ("sheet_property", sheet_uuid, prop.parts[1]),
                )
                if item is not None:
                    texts.append(item)
            for pin in node.children("pin"):
                raw = pin.parts[1] if len(pin.parts) > 1 and isinstance(pin.parts[1], str) else ""
                at_info = _at_span(pin)
                if at_info is None:
                    continue
                item = _bind(
                    _make_text_item(
                        "sheet_pin", "pin", raw, pin, at_info, pin.child("effects"), True,
                    ),
                    ("sheet_pin", pin.atom_after("uuid") or ""),
                )
                if item is not None:
                    # The pin's connection is the anchor, on the sheet edge.
                    symbols[-1].pins.append((item.x, item.y))
                    texts.append(item)
    _mark_attached(texts, symbols)
    return root, SheetModel(symbols, wires, texts)


def _mark_attached(texts, symbols):
    for item in texts:
        if item.kind not in LABEL_HEADS and item.kind != "sheet_pin":
            continue
        for sym in symbols:
            for px, py in sym.pins:
                if abs(px - item.x) <= 0.05 and abs(py - item.y) <= 0.05:
                    item.anchor_on_pin = True
                    break


# --- overlap and placement ----------------------------------------------

def _segment_overlaps_box(seg: WireSeg, box: Box, ignore=None) -> bool:
    """True when the wire centerline crosses the box away from ignore."""
    x0, y0, x1, y1 = seg.x0, seg.y0, seg.x1, seg.y1
    dx = x1 - x0
    dy = y1 - y0
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-9:
        return False
    # Clip the segment against the expanded box by sampling the entry interval.
    # Parametric Liang-Barsky.
    p = [-dx, dx, -dy, dy]
    q = [x0 - box.x0, box.x1 - x0, y0 - box.y0, box.y1 - y0]
    u0, u1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-12:
            if qi < 0:
                return False
            continue
        t = qi / pi
        if pi < 0:
            if t > u1:
                return False
            if t > u0:
                u0 = t
        else:
            if t < u0:
                return False
            if t < u1:
                u1 = t
    if u1 - u0 <= 1e-6:
        return False
    if ignore is None:
        return True
    ix, iy, radius = ignore
    # Any point of the clipped segment farther than radius from the anchor counts.
    for u in (u0, u1, (u0 + u1) / 2.0):
        px = x0 + u * dx
        py = y0 + u * dy
        if (px - ix) ** 2 + (py - iy) ** 2 > radius * radius:
            return True
    return False


def item_overlaps(item: TextItem, model: SheetModel, texts: list[TextItem]) -> list[str]:
    reasons = []
    box = item.box
    ignore = (item.x, item.y, ATTACH_R) if item.kind in LABEL_HEADS or item.kind == "sheet_pin" else None
    for sym in model.symbols:
        if ignore is not None and item.anchor_on_pin:
            # Touching the pin end is the connection, not an overlap. The body
            # still counts: text that runs back along the pin into the graphic
            # fails the epsilon test below.
            pass
        if boxes_overlap(box, sym.box):
            # Ignore a label whose box only covers the pin tip of the symbol
            # it is attached to. Shrink the test by requiring the overlap to
            # reach past the attach radius from the anchor.
            if ignore is not None and item.anchor_on_pin:
                ox0 = max(box.x0, sym.box.x0)
                oy0 = max(box.y0, sym.box.y0)
                ox1 = min(box.x1, sym.box.x1)
                oy1 = min(box.y1, sym.box.y1)
                # If every corner of the overlap is inside the attach radius,
                # this is the connection point.
                corners = [(ox0, oy0), (ox1, oy0), (ox0, oy1), (ox1, oy1)]
                if all((cx - item.x) ** 2 + (cy - item.y) ** 2 <= ATTACH_R ** 2 for cx, cy in corners):
                    continue
            reasons.append(f"symbol {sym.name}")
    for seg in model.wires:
        if _segment_overlaps_box(seg, box, ignore):
            reasons.append("wire")
            break
    for other in texts:
        if other is item:
            continue
        if boxes_overlap(box, other.box):
            reasons.append(f"{other.kind} {other.shown.split(chr(10))[0][:24]}")
            break
    return reasons


def overlapping_items(model: SheetModel) -> list[tuple[TextItem, list[str]]]:
    found = []
    for item in model.texts:
        # Hidden fields are not drawn. Owner placements stay in the report.
        if not item.movable and not item.frozen:
            continue
        reasons = item_overlaps(item, model, model.texts)
        if reasons:
            found.append((item, reasons))
    return found


def _near(a, b) -> bool:
    return abs(a - b) <= 0.05


def _away_spin(item: TextItem, model: SheetModel) -> str:
    """Spin that points from the nearest symbol center toward this anchor."""
    best = None
    best_d = 1e18
    for sym in model.symbols:
        cx = (sym.box.x0 + sym.box.x1) / 2.0
        cy = (sym.box.y0 + sym.box.y1) / 2.0
        # Prefer a symbol this label is actually attached to.
        attached = any(_near(px, item.x) and _near(py, item.y) for px, py in sym.pins)
        dist = (cx - item.x) ** 2 + (cy - item.y) ** 2
        if attached:
            dist *= 0.01
        if dist < best_d:
            best_d = dist
            best = (cx, cy)
    if best is None:
        return "right"
    cx, cy = best
    dx = item.x - cx
    dy = item.y - cy
    if abs(dx) >= abs(dy):
        return "right" if dx >= 0 else "left"
    return "down" if dy >= 0 else "up"


def _label_candidates(item: TextItem, model: SheetModel):
    away = _away_spin(item, model)
    order = ["right", "left", "up", "down"]
    # Try the outward spin first, then the others, current spin last.
    ordered = [away] + [spin for spin in order if spin != away]
    for spin in ordered:
        angle, horiz = spin_file(spin)
        yield item.x, item.y, angle, horiz, None


def _snap(value: float) -> float:
    return round(value / GRID) * GRID


def _field_candidates(item: TextItem, model: SheetModel):
    host = None
    host_d = 1e18
    for sym in model.symbols:
        cx = (sym.box.x0 + sym.box.x1) / 2.0
        cy = (sym.box.y0 + sym.box.y1) / 2.0
        dist = (cx - item.x) ** 2 + (cy - item.y) ** 2
        if dist < host_d:
            host_d = dist
            host = sym
    seeds = [(item.x, item.y)]
    if host is not None:
        body = host.box
        cx = (body.x0 + body.x1) / 2.0
        cy = (body.y0 + body.y1) / 2.0
        half_w = text_width(item.shown, item.size_x) / 2.0
        half_h = item.size_y / 2.0
        gap = GRID
        seeds.extend([
            (cx, body.y0 - gap - half_h),
            (cx, body.y1 + gap + half_h),
            (body.x0 - gap - half_w, cy),
            (body.x1 + gap + half_w, cy),
        ])
        for step in range(1, 10):
            delta = step * GRID
            for ox, oy in (
                (0, -delta), (0, delta), (-delta, 0), (delta, 0),
                (-delta, -delta), (delta, -delta), (-delta, delta), (delta, delta),
            ):
                seeds.append((cx + ox, cy + oy))
    seen = set()
    # Keep the current angle first, then 0, then 90.
    angles = []
    for angle in (int(round(item.angle)) % 360, 0, 90):
        if angle not in angles:
            angles.append(angle)
    for sx, sy in seeds:
        gx, gy = _snap(sx), _snap(sy)
        key = (round(gx, 2), round(gy, 2))
        if key in seen:
            continue
        seen.add(key)
        for angle in angles:
            yield gx, gy, angle, item.horiz, item.vert


def _try_place(item: TextItem, x, y, angle, horiz, vert, model: SheetModel) -> bool:
    saved = (item.x, item.y, item.angle, item.horiz, item.vert, item.box)
    item.x, item.y, item.angle, item.horiz, item.vert = x, y, angle, horiz, vert
    item.box = item._rebuild_box()
    clear = not item_overlaps(item, model, model.texts)
    if not clear:
        item.x, item.y, item.angle, item.horiz, item.vert, item.box = saved
    return clear


def _commit_place(item: TextItem, x, y, angle, horiz, vert, stub=None):
    item.new_x = x
    item.new_y = y
    item.new_angle = float(angle)
    item.new_horiz = horiz
    item.stub = stub
    item.x, item.y, item.angle, item.horiz = x, y, float(angle), horiz
    item.box = item._rebuild_box()


def place_item(item: TextItem, model: SheetModel) -> bool:
    if item.frozen:
        return False
    if item.kind == "property" and item.name in HIDE_WHEN_OVERLAPPING:
        item.hide = True
        # A hidden field is not drawn and is not an obstacle.
        item.box = Box(item.x, item.y, item.x, item.y)
        item.movable = False
        return True
    if item.kind in LABEL_HEADS or item.kind == "sheet_pin":
        for x, y, angle, horiz, _vert in _label_candidates(item, model):
            if angle == int(round(item.angle)) % 360 and horiz == item.horiz:
                continue
            if _try_place(item, x, y, angle, horiz, item.vert, model):
                _commit_place(item, x, y, angle, horiz, item.vert)
                return True
        for length in (GRID, 2 * GRID, 3 * GRID, 4 * GRID):
            for dx, dy in ((length, 0), (-length, 0), (0, length), (0, -length)):
                nx, ny = item.x + dx, item.y + dy
                # The original anchor stays; only a successful spin is kept.
                origin = (item.x, item.y)
                for _x, _y, angle, horiz, _vert in _label_candidates(item, model):
                    stub = WireSeg(origin[0], origin[1], nx, ny)
                    model.wires.append(stub)
                    placed = _try_place(item, nx, ny, angle, horiz, item.vert, model)
                    if placed:
                        _commit_place(
                            item, nx, ny, angle, horiz, item.vert,
                            stub=(origin[0], origin[1], nx, ny),
                        )
                        return True
                    model.wires.pop()
        return False
    ranked = []
    origin_x, origin_y = item.x, item.y
    for x, y, angle, horiz, vert in _field_candidates(item, model):
        if _near(x, origin_x) and _near(y, origin_y) and int(round(angle)) % 360 == int(round(item.angle)) % 360:
            continue
        dist = (x - origin_x) ** 2 + (y - origin_y) ** 2
        ranked.append((dist, 0 if int(angle) % 180 == int(round(item.angle)) % 180 else 1, x, y, angle, horiz, vert))
    ranked.sort()
    for _dist, _turn, x, y, angle, horiz, vert in ranked:
        if _try_place(item, x, y, angle, horiz, vert, model):
            _commit_place(item, x, y, angle, horiz, vert)
            return True
    return False


def tidy(model: SheetModel) -> tuple[list[TextItem], list[tuple[TextItem, list[str]]]]:
    """Move overlapping items. Returns (changed, leftovers)."""
    changed: list[TextItem] = []
    for _pass in range(8):
        pending = overlapping_items(model)
        if not pending:
            break
        progress = False
        for item, _reasons in pending:
            if item.hide or not item.movable:
                continue
            if not item_overlaps(item, model, model.texts):
                continue
            if place_item(item, model):
                changed.append(item)
                progress = True
        if not progress:
            break
    leftovers = overlapping_items(model)
    # changed may list an item twice if a later pass moved it again; keep the last.
    unique = []
    seen = set()
    for item in reversed(changed):
        if id(item) in seen:
            continue
        seen.add(id(item))
        unique.append(item)
    unique.reverse()
    return unique, leftovers


# --- write --------------------------------------------------------------

def _justify_text(horiz: str, vert: str) -> str:
    parts = []
    if horiz != "center":
        parts.append(horiz)
    if vert != "center":
        parts.append(vert)
    if not parts:
        return ""
    return "(justify " + " ".join(parts) + ")"


def render_edits(text: str, changed: list[TextItem]) -> str:
    edits = []
    for item in changed:
        if item.hide:
            if item.effects_close is None:
                continue
            # Insert before the effects closing paren, matching the file's tabs.
            edits.append((item.effects_close, item.effects_close, "\n\t\t\t\t(hide yes)\n\t\t\t"))
            continue
        if item.at_span is None or item.new_x is None:
            continue
        angle = int(round(item.new_angle if item.new_angle is not None else item.angle)) % 360
        new_at = f"(at {fmt_num(item.new_x)} {fmt_num(item.new_y)} {angle})"
        # Keep a 0-angle token's style only when we actually change something.
        old = text[item.at_span[0]:item.at_span[1]]
        if old != new_at:
            edits.append((item.at_span[0], item.at_span[1], new_at))
        new_horiz = item.new_horiz if item.new_horiz is not None else item.horiz
        new_vert = item.vert
        want = _justify_text(new_horiz, new_vert)
        have = text[item.justify_span[0]:item.justify_span[1]] if item.justify_span else ""
        if want != have:
            if item.justify_span is not None:
                if want:
                    edits.append((item.justify_span[0], item.justify_span[1], want))
                else:
                    edits.append((item.justify_span[0], item.justify_span[1], ""))
            elif want and item.effects_close is not None:
                edits.append((item.effects_close, item.effects_close, "\n\t\t\t" + want))
        if item.stub is not None:
            x0, y0, x1, y1 = item.stub
            wire = (
                f"\n\t(wire\n\t\t(pts\n\t\t\t(xy {fmt_num(x0)} {fmt_num(y0)}) "
                f"(xy {fmt_num(x1)} {fmt_num(y1)})\n\t\t)\n"
                f"\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
                f'\t\t(uuid "{uuid.uuid4()}")\n\t)'
            )
            # Insert just after the label form. at_span sits inside it, so the
            # insert position is the caller's end of the label. TextItem does
            # not store that; use effects_close's form by inserting at the
            # justify/at edit only, and append wires at a sentinel.
            edits.append(("stub", wire))
    stubs = [edit[1] for edit in edits if edit[0] == "stub"]
    spans = [edit for edit in edits if edit[0] != "stub"]
    spans.sort(key=lambda edit: edit[0], reverse=True)
    out = text
    for start, end, repl in spans:
        out = out[:start] + repl + out[end:]
    if stubs:
        # Before the file's final closing parenthesis.
        close = out.rfind(")")
        out = out[:close] + "".join(stubs) + "\n" + out[close:]
    return out


def _split_overlaps(rows):
    """Owner placements are reported; only other overlaps fail the check."""
    owner = [(item, reasons) for item, reasons in rows if item.frozen]
    other = [(item, reasons) for item, reasons in rows if not item.frozen]
    return owner, other


def _print_overlap(prefix: str, item: TextItem, reasons: list[str]) -> None:
    shown = item.shown.split("\n")[0][:40]
    print(
        f"  {prefix}{item.kind} {item.name} {shown!r} "
        f"at {fmt_num(item.x)},{fmt_num(item.y)} overlaps {', '.join(reasons)}"
    )


def describe(item: TextItem) -> str:
    label = item.shown.split("\n")[0]
    if len(label) > 32:
        label = label[:29] + "..."
    if item.hide:
        return f"HIDE {item.kind} {item.name} {label!r} at {fmt_num(item.x)},{fmt_num(item.y)}"
    dest = ""
    if item.new_x is not None:
        dest = (
            f" -> {fmt_num(item.new_x)},{fmt_num(item.new_y)}"
            f" angle {int(round(item.new_angle or 0))} justify {item.new_horiz}"
        )
        if item.stub is not None:
            dest += " +stub"
    return f"MOVE {item.kind} {item.name} {label!r}{dest}"


def process_path(path: str, mode: str) -> dict:
    original = Path(path).read_text(encoding="utf-8")
    _root, model = load_sheet(original)
    before = overlapping_items(model)
    changed: list[TextItem] = []
    leftovers = before
    updated = original
    if mode != "check":
        # Reload so placement mutates a fresh model. before was on this model;
        # tidy() mutates it in place, which is what we want.
        changed, leftovers = tidy(model)
        if mode == "apply" and changed:
            updated = render_edits(original, changed)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(updated)
    return {
        "path": path,
        "before": before,
        "changed": changed,
        "leftovers": leftovers,
        "original": original,
        "updated": updated,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="De-overlap KiCad schematic text.")
    parser.add_argument("sheets", nargs="+", help="KiCad schematic sheets")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="list overlaps and exit 1 if any remain")
    group.add_argument("--dry-run", action="store_true", help="print the moves without writing")
    args = parser.parse_args(argv)
    mode = "check" if args.check else "dry-run" if args.dry_run else "apply"
    exit_code = 0
    for path in args.sheets:
        result = process_path(path, mode)
        name = path
        if mode == "check":
            owner, other = _split_overlaps(result["before"])
            print(f"{name}: {len(other)} overlap(s), {len(owner)} owner placement(s) left overlapping")
            for item, reasons in other:
                _print_overlap("", item, reasons)
            for item, reasons in owner:
                _print_overlap("OWNER ", item, reasons)
            if other:
                exit_code = 1
            continue
        owner, other = _split_overlaps(result["leftovers"])
        print(f"{name}: moved {sum(1 for item in result['changed'] if not item.hide)}, "
              f"hid {sum(1 for item in result['changed'] if item.hide)}, "
              f"leftover {len(other)}, owner leftover {len(owner)}")
        for item in result["changed"]:
            print("  " + describe(item))
        for item, reasons in other:
            _print_overlap("LEFTOVER ", item, reasons)
        for item, reasons in owner:
            _print_overlap("OWNER LEFTOVER ", item, reasons)
        if other:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
