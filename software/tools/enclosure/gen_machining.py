#!/usr/bin/env python3
"""Enclosure machining drawings from a KiCad board.

Reads a .kicad_pcb, finds footprints whose ``Panel`` property is
``front``, ``rear``, or ``top``, and writes a 1:1 drill drawing for each
plate that has features. No KiCad GUI and no pcbnew module: the board
file is parsed as s-expressions.

End-plate coordinates (outside view, datum = lower-left, X right, Y up):

- Plate is 103 x 53 mm. The board (default 99 mm across) is centred, so
  each side margin is (103 - board width) / 2 = 2 mm.
- Front, seen from outside: board y = 0 is the right side.
  plate X = (plate width + board width) / 2 - board y.
- Rear, seen from outside: board y = 0 is the left side.
  plate X = (plate width - board width) / 2 + board y.
- plate Y = board-top Y + PanelZ. Board-top Y defaults to 27.40 mm
  (slot 6). ``PanelZ`` is the optical or mechanical centre height above
  the board, in millimetres.
- Board x/y are millimetres from the Edge.Cuts minimum corner (rear-left
  on the outline board).

Top-wall holes come from ``np_thru_hole`` pads on a footprint with
``Panel`` = ``top`` (or a footprint whose name contains ``AL_BAR``).
Datum X is the rear-plate inner face (board x + the 2.10 mm end gap).
Datum Y is the outside edge on the board y = 0 side. The clearance
drill defaults to 3.4 mm unless ``PanelCutout`` is set.

``PanelCutout`` accepts ``circle:6.5``, ``rect:17.02x14.60``, and
``rrect:13.6x6.5:r1``. Known buttons, LEDs, USB-C, RJ45, the gland,
the ground stud, and the power inlet have defaults for cutout and
``PanelZ`` when those properties are omitted.

Print the PDF or SVG at 100 %. The sheet is A4 landscape and the plate
is drawn at 1:1. A 50 mm bar is on every sheet.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# Hammond 1455N1601 figures used to place holes. Sources and the
# ±0.6 mm caution are in hardware/controller/mechanical/outline-1455N1601/README.md.
PLATE_WIDTH_MM = 103.0
PLATE_HEIGHT_MM = 53.0
INNER_HEIGHT_MM = 49.62
SLOT1_UPPER_BELOW_INNER_MM = 6.41
SLOT_PITCH_MM = 3.50
PLATE_GAP_MM = 2.10
TOP_WALL_DRILL_MM = 3.4
SCREW_DIAMETER_MM = 4.19
SCREW_X_MM = (3.99, 99.01)
SCREW_Y_MM = (4.00, 49.00)

# First match wins. Patterns are tokens, or substrings when the pattern
# is at least 4 characters (so "bb15" hits BB15AH, and "led" does not hit
# an unrelated word).
DEFAULT_CUTOUTS: tuple[tuple[str, tuple[str, ...], str, float], ...] = (
    ("usb-c", ("usb-c", "usbc", "gt-usb", "type-c"), "rrect:13.60x6.50:r1", 1.68),
    ("rj45", ("rj45", "magjack", "j0011", "j403"), "rrect:17.02x14.60:r0.25", 7.05),
    ("gland", ("gland", "m16"), "circle:16.3", 11.00),
    ("stud", ("stud", "gnd"), "circle:4.3", 15.10),
    ("power", ("power", "inlet", "terminal"), "rrect:22.00x12.50:r0.5", 6.00),
    ("led", ("led", "dialight", "551", "cbi"), "circle:4.0", 5.08),
    ("button", ("button", "bb15", "nkk"), "circle:6.5", 3.40),
)

_CIRCLE = re.compile(r"^circle:([0-9]*\.?[0-9]+)$", re.IGNORECASE)
_RECT = re.compile(r"^rect:([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$", re.IGNORECASE)
_RRECT = re.compile(
    r"^rrect:([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+):r([0-9]*\.?[0-9]+)$",
    re.IGNORECASE,
)


class MachiningError(Exception):
    """The board could not be turned into a drawing."""


def qmm(value: float) -> float:
    """Round a millimetre value to 0.01 mm (half up)."""
    cleaned = round(float(value), 6)
    return float(Decimal(str(cleaned)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def board_top_y_mm(slot: int, plate_height: float = PLATE_HEIGHT_MM, inner_height: float = INNER_HEIGHT_MM) -> float:
    """PCB top-face Y on the end plate for a Hammond slot number.

    Slot k upper face is 6.41 + 3.50*(k-1) mm below the inner top.
    The board is lifted to that face. Top and bottom walls split
    (plate height - inner height).
    """
    if slot < 1:
        raise MachiningError(f"slot must be >= 1, got {slot}")
    plate = Decimal(str(plate_height))
    inner = Decimal(str(inner_height))
    top_wall = (plate - inner) / 2
    inner_top = plate - top_wall
    below = Decimal(str(SLOT1_UPPER_BELOW_INNER_MM)) + Decimal(str(SLOT_PITCH_MM)) * (slot - 1)
    return qmm(float(inner_top - below))


# --- s-expressions -------------------------------------------------------

def tokenize(text: str):
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == "(":
            yield ("lparen", "(")
            i += 1
            continue
        if c == ")":
            yield ("rparen", ")")
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                if text[j] == "\\":
                    if j + 1 >= n:
                        break
                    buf.append(text[j + 1])
                    j += 2
                    continue
                if text[j] == '"':
                    break
                buf.append(text[j])
                j += 1
            yield ("str", "".join(buf))
            i = j + 1
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in "()":
            j += 1
        yield ("atom", text[i:j])
        i = j


def parse_sexpr(text: str):
    tokens = list(tokenize(text))
    if not tokens:
        raise MachiningError("empty board file")

    def rec(idx: int):
        kind, val = tokens[idx]
        if kind != "lparen":
            return val, idx + 1
        node: list = []
        idx += 1
        if idx >= len(tokens):
            raise MachiningError("unclosed '(' in board file")
        while tokens[idx][0] != "rparen":
            child, idx = rec(idx)
            node.append(child)
            if idx >= len(tokens):
                raise MachiningError("unclosed '(' in board file")
        return node, idx + 1

    node, idx = rec(0)
    return node


def _is(node, head: str) -> bool:
    return isinstance(node, list) and bool(node) and node[0] == head


def _direct(node, head: str):
    if not isinstance(node, list):
        return
    for child in node:
        if _is(child, head):
            yield child


def _layer(node) -> str | None:
    for child in _direct(node, "layer"):
        if len(child) > 1:
            return str(child[1])
    return None


def _xy_points(node, out: list[tuple[float, float]]):
    if not isinstance(node, list) or not node:
        return
    if node[0] in ("xy", "start", "end", "center") and len(node) >= 3:
        try:
            out.append((float(node[1]), float(node[2])))
        except (TypeError, ValueError):
            pass
    for child in node:
        if isinstance(child, list):
            _xy_points(child, out)


def _at(node) -> tuple[float, float, float] | None:
    for child in _direct(node, "at"):
        if len(child) < 3:
            continue
        try:
            rot = float(child[3]) if len(child) > 3 else 0.0
            return float(child[1]), float(child[2]), rot
        except (TypeError, ValueError):
            return None
    return None


def _properties(fp) -> dict[str, str]:
    found: dict[str, str] = {}
    for child in _direct(fp, "property"):
        if len(child) >= 3 and isinstance(child[1], str):
            found[child[1]] = str(child[2])
    return found


def _prop(props: dict[str, str], key: str) -> str | None:
    for name, value in props.items():
        if name.casefold() == key.casefold():
            return value
    return None


# --- cutouts and geometry ------------------------------------------------

@dataclass(frozen=True)
class Cutout:
    kind: str  # circle, rect, rrect
    w: float
    h: float
    r: float = 0.0

    def label(self) -> str:
        if self.kind == "circle":
            return f"Ø{self.w:.2f}"
        base = f"{self.w:.2f} × {self.h:.2f}"
        if self.kind == "rrect" and self.r:
            return f"{base} R{self.r:.2f}"
        return base


def parse_cutout(spec: str) -> Cutout:
    text = spec.strip().replace(" ", "")
    match = _CIRCLE.match(text)
    if match:
        d = float(match.group(1))
        return Cutout("circle", d, d, 0.0)
    match = _RRECT.match(text)
    if match:
        return Cutout("rrect", float(match.group(1)), float(match.group(2)), float(match.group(3)))
    match = _RECT.match(text)
    if match:
        return Cutout("rect", float(match.group(1)), float(match.group(2)), 0.0)
    raise MachiningError(
        f"bad PanelCutout {spec!r}; use circle:6.5, rect:17.02x14.60, or rrect:13.6x6.5:r1"
    )


def _tokens(text: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", text.casefold()) if part}


def lookup_default(name: str, value: str, reference: str):
    """Return (cutout spec, PanelZ mm) or None."""
    fields = (name or "", value or "", reference or "")
    blob = " ".join(fields).casefold()
    tokens: set[str] = set()
    for field_text in fields:
        tokens |= _tokens(field_text)
    for _ident, patterns, spec, panel_z in DEFAULT_CUTOUTS:
        for pattern in patterns:
            folded = pattern.casefold()
            if folded in tokens or (len(folded) >= 4 and folded in blob):
                return spec, panel_z
    return None


def kicad_rotate(lx: float, ly: float, degrees: float) -> tuple[float, float]:
    """Rotate a footprint-local point into board axes.

    KiCad Y increases downward and a positive footprint rotation is
    counterclockwise on that screen. θ = 90° sends local +X toward
    decreasing Y.
    """
    theta = math.radians(degrees)
    c = math.cos(theta)
    s = math.sin(theta)
    return (lx * c + ly * s, -lx * s + ly * c)


@dataclass
class Hole:
    name: str
    x: float
    y: float
    cutout: Cutout
    note: str
    existing: bool = False
    panel_z: float | None = None

    def as_dict(self) -> dict:
        row = {
            "name": self.name,
            "x_mm": self.x,
            "y_mm": self.y,
            "cutout": self.cutout.label(),
            "kind": self.cutout.kind,
            "w_mm": qmm(self.cutout.w),
            "h_mm": qmm(self.cutout.h),
            "r_mm": qmm(self.cutout.r),
            "note": self.note,
            "existing": self.existing,
        }
        if self.panel_z is not None:
            row["panel_z_mm"] = self.panel_z
        return row


@dataclass
class Plate:
    ident: str
    title: str
    width: float
    height: float
    holes: list[Hole] = field(default_factory=list)
    datum: str = ""


@dataclass
class Job:
    board: Path
    revision: str
    date: str
    slot: int
    board_top_y: float
    board_length: float
    board_width: float
    plates: list[Plate]

    def is_empty(self) -> bool:
        return not any(plate.holes for plate in self.plates)


def _edge_bbox(pcb) -> tuple[float, float, float, float] | None:
    pts: list[tuple[float, float]] = []
    for item in pcb[1:]:
        if not isinstance(item, list) or not item:
            continue
        if item[0] not in ("gr_line", "gr_rect", "gr_circle", "gr_arc", "gr_poly", "gr_curve"):
            continue
        if _layer(item) != "Edge.Cuts":
            continue
        _xy_points(item, pts)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _resolve_panel(name: str, props: dict[str, str]) -> tuple[Cutout, float]:
    reference = _prop(props, "Reference") or name
    value = _prop(props, "Value") or ""
    default = lookup_default(name, value, reference)
    raw_cut = _prop(props, "PanelCutout")
    raw_z = _prop(props, "PanelZ")
    if raw_cut:
        cutout = parse_cutout(raw_cut)
    elif default:
        cutout = parse_cutout(default[0])
    else:
        raise MachiningError(
            f"{reference} ({name}) has Panel set but no PanelCutout and no default cutout"
        )
    if raw_z is not None and raw_z != "":
        try:
            panel_z = qmm(float(raw_z))
        except ValueError as exc:
            raise MachiningError(f"{reference} has PanelZ {raw_z!r}, expected millimetres") from exc
    elif default:
        panel_z = qmm(default[1])
    else:
        raise MachiningError(
            f"{reference} ({name}) has Panel set but no PanelZ and no default height"
        )
    return cutout, panel_z


def _plate_screws() -> list[Hole]:
    holes = []
    n = 1
    for y in SCREW_Y_MM:
        for x in SCREW_X_MM:
            holes.append(
                Hole(
                    name=f"Plate screw {n}",
                    x=qmm(x),
                    y=qmm(y),
                    cutout=Cutout("circle", SCREW_DIAMETER_MM, SCREW_DIAMETER_MM, 0.0),
                    note="existing Hammond, csk, do not re-drill",
                    existing=True,
                )
            )
            n += 1
    return holes


def _front_x(board_y: float, plate_w: float, board_w: float) -> float:
    return qmm((plate_w + board_w) / 2.0 - board_y)


def _rear_x(board_y: float, plate_w: float, board_w: float) -> float:
    return qmm((plate_w - board_w) / 2.0 + board_y)


def _feature_name(props: dict[str, str], fallback: str) -> str:
    named = _prop(props, "PanelName")
    if named:
        return named
    reference = _prop(props, "Reference")
    if reference and reference != "~":
        return reference
    return fallback


def collect_job(
    board: Path,
    *,
    slot: int = 6,
    board_top_y: float | None = None,
    plate_width: float = PLATE_WIDTH_MM,
    plate_height: float = PLATE_HEIGHT_MM,
    plate_gap: float = PLATE_GAP_MM,
    top_drill: float = TOP_WALL_DRILL_MM,
    revision: str | None = None,
    date: str | None = None,
) -> Job:
    text = board.read_text(encoding="utf-8")
    pcb = parse_sexpr(text)
    if not _is(pcb, "kicad_pcb"):
        raise MachiningError(f"{board} is not a kicad_pcb")
    bbox = _edge_bbox(pcb)
    if bbox is None:
        origin_x = origin_y = 0.0
        board_length = 159.0
        board_width = 99.0
    else:
        origin_x, origin_y, max_x, max_y = bbox
        board_length = qmm(max_x - origin_x)
        board_width = qmm(max_y - origin_y)
    top_y = qmm(board_top_y) if board_top_y is not None else board_top_y_mm(slot, plate_height)
    margin_note = (plate_width - board_width) / 2.0

    front: list[Hole] = []
    rear: list[Hole] = []
    top_holes: list[Hole] = []

    for item in pcb[1:]:
        if not _is(item, "footprint"):
            continue
        name = str(item[1]) if len(item) > 1 else ""
        props = _properties(item)
        panel = (_prop(props, "Panel") or "").strip().casefold()
        at = _at(item)
        if at is None:
            continue
        fp_x, fp_y, fp_rot = at

        if panel in ("front", "rear"):
            cutout, panel_z = _resolve_panel(name, props)
            board_y = fp_y - origin_y
            plate_x = _front_x(board_y, plate_width, board_width) if panel == "front" else _rear_x(board_y, plate_width, board_width)
            plate_y = qmm(top_y + panel_z)
            hole = Hole(
                name=_feature_name(props, name),
                x=plate_x,
                y=plate_y,
                cutout=cutout,
                note=f"centre +{panel_z:.2f} mm above PCB",
                panel_z=panel_z,
            )
            (front if panel == "front" else rear).append(hole)
            continue

        is_top = panel in ("top", "topwall", "top-wall") or (not panel and "al_bar" in name.casefold())
        if not is_top:
            if panel:
                raise MachiningError(
                    f"{_feature_name(props, name)} has Panel={panel!r}; use front, rear, or top"
                )
            continue

        raw_cut = _prop(props, "PanelCutout")
        cutout = parse_cutout(raw_cut) if raw_cut else Cutout("circle", top_drill, top_drill, 0.0)
        pads = []
        for pad in _direct(item, "pad"):
            kind = str(pad[2]) if len(pad) > 2 else ""
            if kind != "np_thru_hole":
                continue
            local = _at(pad)
            if local is None:
                continue
            lx, ly = kicad_rotate(local[0], local[1], fp_rot)
            pads.append((fp_x + lx, fp_y + ly))
        if not pads:
            pads.append((fp_x, fp_y))
        ref = _feature_name(props, name)
        indexed = []
        for kx, ky in pads:
            board_x = kx - origin_x
            board_y = ky - origin_y
            indexed.append(
                (
                    qmm(board_x + plate_gap),
                    qmm(board_y + (plate_width - board_width) / 2.0),
                )
            )
        for n, (ex, ey) in enumerate(sorted(indexed, key=lambda row: (row[1], row[0])), start=1):
            label = ref if len(indexed) == 1 else f"{ref}-{n}"
            top_holes.append(
                Hole(
                    name=label,
                    x=ex,
                    y=ey,
                    cutout=cutout,
                    note="top-wall clearance drill",
                )
            )

    def _sort(holes: list[Hole]) -> list[Hole]:
        machined = sorted((h for h in holes if not h.existing), key=lambda h: (h.x, h.y, h.name))
        existing = sorted((h for h in holes if h.existing), key=lambda h: (h.y, h.x, h.name))
        return machined + existing

    plates: list[Plate] = []
    if front:
        plates.append(
            Plate(
                ident="front",
                title="FRONT PANEL",
                width=plate_width,
                height=plate_height,
                holes=_sort(front + _plate_screws()),
                datum="lower-left corner, outside view, X right, Y up. Board y = 0 is the right side.",
            )
        )
    if rear:
        plates.append(
            Plate(
                ident="rear",
                title="REAR PANEL",
                width=plate_width,
                height=plate_height,
                holes=_sort(rear + _plate_screws()),
                datum="lower-left corner, outside view, X right, Y up. Board y = 0 is the left side.",
            )
        )
    if top_holes:
        span = qmm(board_length + 2.0 * plate_gap)
        plates.append(
            Plate(
                ident="top",
                title="TOP WALL",
                width=span,
                height=plate_width,
                holes=_sort(top_holes),
                datum=(
                    "lower-left of the top wall: X from the rear-plate inner face toward the front, "
                    f"Y from the outside edge on the board y = 0 side. "
                    f"Span {span:.2f} mm is plate-inner-face to plate-inner-face "
                    f"(board {board_length:.2f} mm + {plate_gap:.2f} mm each end), "
                    f"not the 160 mm extrusion outside. Side margin {margin_note:.2f} mm."
                ),
            )
        )

    rev = revision if revision is not None else _git_revision(board)
    stamp = date if date is not None else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Job(
        board=board,
        revision=rev,
        date=stamp,
        slot=slot,
        board_top_y=top_y,
        board_length=board_length,
        board_width=board_width,
        plates=plates,
    )


def _git_revision(board: Path) -> str:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=board.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    short = sha[:12]
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--", str(board)],
            cwd=board.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty = ""
    if dirty:
        short += "-dirty"
    return short


def job_json(job: Job) -> dict:
    return {
        "board": str(job.board),
        "git": job.revision,
        "date": job.date,
        "slot": job.slot,
        "board_top_y_mm": job.board_top_y,
        "board_length_mm": job.board_length,
        "board_width_mm": job.board_width,
        "plates": [
            {
                "id": plate.ident,
                "title": plate.title,
                "width_mm": plate.width,
                "height_mm": plate.height,
                "datum": plate.datum,
                "holes": [hole.as_dict() for hole in plate.holes],
            }
            for plate in job.plates
        ],
    }


# --- drawing -------------------------------------------------------------

def _import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Polygon, Rectangle
    except ImportError as exc:
        raise MachiningError(
            "matplotlib is required to write PDF, SVG, and PNG drawings. Install it with pip install matplotlib."
        ) from exc
    return plt, Circle, Polygon, Rectangle


def _stagger(values: list[float], minimum: float) -> list[tuple[float, int]]:
    assigned: list[tuple[float, int]] = []
    for value in sorted(values):
        lane = 0
        while any(abs(value - other) < minimum and other_lane == lane for other, other_lane in assigned):
            lane += 1
        assigned.append((value, lane))
    return assigned


def _rrect_points(cx: float, cy: float, w: float, h: float, r: float) -> list[tuple[float, float]]:
    """Polygon approximation of a rounded rectangle, centred."""
    r = min(r, w / 2.0, h / 2.0)
    if r <= 0:
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    steps = 6
    x0, y0 = cx - w / 2 + r, cy - h / 2 + r
    x1, y1 = cx + w / 2 - r, cy + h / 2 - r
    corners = (
        (x1, y0, -math.pi / 2, 0),
        (x1, y1, 0, math.pi / 2),
        (x0, y1, math.pi / 2, math.pi),
        (x0, y0, math.pi, 3 * math.pi / 2),
    )
    pts: list[tuple[float, float]] = []
    for ox, oy, a0, a1 in corners:
        for step in range(steps + 1):
            ang = a0 + (a1 - a0) * step / steps
            pts.append((ox + r * math.cos(ang), oy + r * math.sin(ang)))
    return pts


def render_plate(job: Job, plate: Plate, stem: Path) -> None:
    """Write stem.pdf, stem.svg, and stem.png. The plate outline is 1:1 on A4 landscape."""
    plt, Circle, Polygon, Rectangle = _import_matplotlib()
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42

    page_w, page_h = 297.0, 210.0
    fig = plt.figure(figsize=(page_w / 25.4, page_h / 25.4))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, page_w)
    ax.set_ylim(0, page_h)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    wide = plate.width > 140
    ox = 36.0 if wide else 46.0
    oy = 58.0 if wide else 86.0
    _draw_sheet(ax, job, plate, ox, oy, page_w, page_h, Circle, Polygon, Rectangle)

    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), format="pdf")
    fig.savefig(stem.with_suffix(".svg"), format="svg")
    fig.savefig(stem.with_suffix(".png"), format="png", dpi=120)
    plt.close(fig)


def _draw_sheet(ax, job: Job, plate: Plate, ox: float, oy: float, page_w: float, page_h: float, Circle, Polygon, Rectangle):
    ax.add_patch(Rectangle((6, 6), page_w - 12, page_h - 12, fill=False, linewidth=0.8, edgecolor="black"))

    ax.text(12, page_h - 12, "ROTATOR CONTROLLER  ·  Hammond 1455N1601", fontsize=11, fontweight="bold", ha="left", va="top", color="black")
    ax.text(12, page_h - 18, f"{plate.title}    1:1    millimetres", fontsize=9, ha="left", va="top")
    ax.text(
        page_w - 12,
        page_h - 12,
        f"{job.date}    git {job.revision}",
        fontsize=8,
        ha="right",
        va="top",
        family="monospace",
    )
    ax.text(page_w - 12, page_h - 18, str(job.board), fontsize=6.5, ha="right", va="top", color="#333333")

    ax.add_patch(Rectangle((ox, oy), plate.width, plate.height, fill=False, linewidth=1.1, edgecolor="black"))
    ax.plot([ox - 1.2, ox - 1.2], [oy, oy + plate.height], color="black", linewidth=0.4)
    ax.plot([ox, ox + plate.width], [oy - 1.2, oy - 1.2], color="black", linewidth=0.4)
    ax.plot(ox, oy, marker="s", color="black", markersize=3.5)
    ax.text(ox - 1.5, oy - 4.2, "0", fontsize=7, ha="right", va="top")
    ax.text(ox + 1.5, oy - 4.2, "DATUM", fontsize=6, ha="left", va="top")

    ax.text(ox + plate.width / 2, oy + plate.height + 3.2, f"{plate.width:.2f} × {plate.height:.2f}", fontsize=7, ha="center", va="bottom")

    numbers: list[tuple[Hole, str]] = []
    machined_i = 0
    screw_i = 0
    for hole in plate.holes:
        if hole.existing:
            screw_i += 1
            numbers.append((hole, f"M{screw_i}"))
        else:
            machined_i += 1
            numbers.append((hole, str(machined_i)))

    for hole, tag in numbers:
        cx, cy = ox + hole.x, oy + hole.y
        _draw_opening(ax, cx, cy, hole, Circle, Polygon, Rectangle)
        reach = max(hole.cutout.w, hole.cutout.h) / 2.0 + 1.6
        lx, ly = cx + reach * 0.7, cy + reach * 0.7
        if lx > ox + plate.width - 1:
            lx = cx - reach * 0.7
        if ly > oy + plate.height - 1:
            ly = cy - reach * 0.7
        ax.annotate(
            tag,
            xy=(cx, cy),
            xytext=(lx, ly),
            fontsize=6,
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "-", "lw": 0.3, "color": "#444444"} if reach > 3.5 else None,
            color="black",
        )

    xs = sorted({hole.x for hole in plate.holes})
    ys = sorted({hole.y for hole in plate.holes})
    for value, lane in _stagger(xs, 8.0):
        tick_y = oy - 8.0 - lane * 7.5
        ax.plot([ox + value, ox + value], [oy, tick_y], color="#444444", linewidth=0.35)
        ax.text(ox + value, tick_y - 0.6, f"{value:.2f}", fontsize=6, rotation=90, ha="center", va="top", family="monospace")
    for value, lane in _stagger(ys, 4.5):
        tick_x = ox - 8.0 - lane * 12.0
        ax.plot([ox, tick_x], [oy + value, oy + value], color="#444444", linewidth=0.35)
        ax.text(tick_x - 0.8, oy + value, f"{value:.2f}", fontsize=6, ha="right", va="center", family="monospace")

    table_x = ox + plate.width + 14.0
    if table_x > page_w - 70:
        table_x = 12.0
        table_top = oy - 28.0
    else:
        table_top = page_h - 28.0
    _draw_table(ax, table_x, table_top, numbers, page_w)

    ax.plot([12, 62], [14, 14], color="black", linewidth=1.0)
    ax.plot([12, 12], [12.5, 15.5], color="black", linewidth=0.8)
    ax.plot([62, 62], [12.5, 15.5], color="black", linewidth=0.8)
    ax.text(37, 16.2, "50 mm at 1:1 — do not scale to fit", fontsize=6.5, ha="center", va="bottom")

    notes = [
        plate.datum,
        (
            f"Slot {job.slot}. PCB top face at Y = {job.board_top_y:.2f} on an end plate. "
            "Feature Y = that height + PanelZ."
        ),
        "Heights chained from Hammond typical dimensions are about ±0.6 mm. Test-fit one board before drilling a batch.",
        "Ordinate dimensions are from the datum. Existing plate screws are Hammond holes; do not re-drill them.",
    ]
    _draw_wrapped(ax, 70, 18, page_w - 12, notes)


def _draw_wrapped(ax, x: float, y: float, right: float, notes: list[str]) -> None:
    width = max(40.0, right - x)
    chars = max(40, int(width / 1.35))
    for note in notes:
        for line in _wrap_text(note, chars):
            ax.text(x, y, line, fontsize=6, ha="left", va="bottom", color="#222222")
            y += 3.2


def _wrap_text(text: str, chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) > chars and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def _draw_opening(ax, cx, cy, hole: Hole, Circle, Polygon, Rectangle):
    color = "#555555" if hole.existing else "black"
    style = (0, (1.2, 0.8)) if hole.existing else "solid"
    cut = hole.cutout
    if cut.kind == "circle":
        ax.add_patch(Circle((cx, cy), cut.w / 2.0, fill=False, linewidth=0.7, edgecolor=color, linestyle=style))
    elif cut.kind == "rrect" and cut.r > 0:
        pts = _rrect_points(cx, cy, cut.w, cut.h, cut.r)
        ax.add_patch(Polygon(pts, closed=True, fill=False, linewidth=0.7, edgecolor=color, linestyle=style))
    else:
        ax.add_patch(
            Rectangle((cx - cut.w / 2, cy - cut.h / 2), cut.w, cut.h, fill=False, linewidth=0.7, edgecolor=color, linestyle=style)
        )
    arm = min(1.6, cut.w * 0.35, cut.h * 0.35)
    ax.plot([cx - arm, cx + arm], [cy, cy], color=color, linewidth=0.3)
    ax.plot([cx, cx], [cy - arm, cy + arm], color=color, linewidth=0.3)


def _draw_table(ax, x: float, top: float, rows: list[tuple[Hole, str]], page_w: float):
    headers = ("#", "Feature", "X", "Y", "Opening", "Notes")
    # Column widths sized to the remaining page.
    usable = max(40.0, page_w - 8 - x)
    widths = (8.0, 28.0, 14.0, 14.0, 32.0, max(20.0, usable - 96.0))
    row_h = 4.0
    y = top
    cursor = x
    for header, width in zip(headers, widths):
        ax.text(cursor + 0.4, y, header, fontsize=6.5, fontweight="bold", ha="left", va="top")
        cursor += width
    y -= row_h - 1.2
    ax.plot([x, x + sum(widths)], [y + 3.2, y + 3.2], color="black", linewidth=0.4)
    for hole, tag in rows:
        cursor = x
        values = (tag, hole.name, f"{hole.x:.2f}", f"{hole.y:.2f}", hole.cutout.label(), hole.note)
        for value, width in zip(values, widths):
            ax.text(cursor + 0.4, y, value, fontsize=6, ha="left", va="top", family="monospace" if value[:1].isdigit() or value.startswith("Ø") or value.startswith("+") else None)
            cursor += width
        y -= row_h
        if y < 28:
            break


def write_outputs(job: Job, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    payload = job_json(job)
    json_path = out_dir / "holes.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    written.append(json_path)
    names = {"front": "front-panel", "rear": "rear-panel", "top": "top-wall"}
    for plate in job.plates:
        if not plate.holes:
            continue
        stem = out_dir / names[plate.ident]
        render_plate(job, plate, stem)
        for suffix in (".pdf", ".svg", ".png"):
            written.append(stem.with_suffix(suffix))
    return written


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate 1:1 enclosure machining drawings from Panel fields on a KiCad board.",
    )
    parser.add_argument("board", type=Path, help="path to a .kicad_pcb")
    parser.add_argument("-o", "--output", type=Path, required=True, help="directory for PDF, SVG, PNG, and holes.json")
    parser.add_argument("--slot", type=int, default=6, help="Hammond slot number (default 6)")
    parser.add_argument(
        "--board-top-y",
        type=float,
        default=None,
        help="override the PCB top-face Y on the end plate, millimetres (default: computed for --slot, 27.40 for slot 6)",
    )
    parser.add_argument("--allow-empty", action="store_true", help="exit 0 when no footprint has a Panel field and no bar holes were found")
    parser.add_argument("--rev", default=None, help="revision string for the title block (default: git HEAD, with -dirty)")
    parser.add_argument("--date", default=None, help="date for the title block (default: UTC today, YYYY-MM-DD)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    if not args.board.is_file():
        print(f"board not found: {args.board}", file=sys.stderr)
        return 1
    try:
        job = collect_job(
            args.board,
            slot=args.slot,
            board_top_y=args.board_top_y,
            revision=args.rev,
            date=args.date,
        )
        if job.is_empty():
            message = (
                f"{args.board}: no footprints carry Panel fields and no triac-bar mounting holes were found"
            )
            if args.allow_empty:
                print(message)
                return 0
            print(message, file=sys.stderr)
            return 2
        written = write_outputs(job, args.output)
    except MachiningError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
