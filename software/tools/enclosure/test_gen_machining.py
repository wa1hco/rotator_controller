"""Hole-table regression for the enclosure machining generator.

The fixture places placeholder footprints at board coordinates that the
slot-6 transform must map onto the 2026-10-11 Hammond 1455N1601 end-panel
table (outline README). Centres and opening sizes have to agree within
0.05 mm. Plate screws are the existing Hammond holes on that same table.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_machining as gm

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "testdata" / "panel-regression.kicad_pcb"
OUTLINE = (
    HERE.parents[2]
    / "hardware"
    / "controller"
    / "mechanical"
    / "outline-1455N1601"
    / "RotatorController-1455N1601-outline.kicad_pcb"
)
V4 = HERE.parents[2] / "hardware" / "controller" / "Rotator-Controller-V4.kicad_pcb"

TOL = 0.05

# name, x, y, kind, w, h, r
FRONT = [
    ("LED_PWR", 11.50, 32.48, "circle", 4.0, 4.0, 0.0),
    ("LED_LINK", 18.50, 32.48, "circle", 4.0, 4.0, 0.0),
    ("SW_CCW", 29.50, 30.80, "circle", 6.5, 6.5, 0.0),
    ("LED_CCW", 40.50, 32.48, "circle", 4.0, 4.0, 0.0),
    ("SW_STOP", 51.50, 30.80, "circle", 6.5, 6.5, 0.0),
    ("LED_CW", 62.50, 32.48, "circle", 4.0, 4.0, 0.0),
    ("SW_CW", 73.50, 30.80, "circle", 6.5, 6.5, 0.0),
    ("LED_BRAKE", 84.50, 32.48, "circle", 4.0, 4.0, 0.0),
    ("LED_FAULT", 91.50, 32.48, "circle", 4.0, 4.0, 0.0),
]
REAR = [
    ("J_POWER", 17.50, 38.40, "circle", 16.3, 16.3, 0.0),
    ("J_GLAND", 43.50, 38.40, "circle", 16.3, 16.3, 0.0),
    ("J_USB", 69.50, 29.08, "rrect", 13.60, 6.50, 1.0),
    ("J_GND", 69.50, 42.50, "circle", 4.3, 4.3, 0.0),
    ("J_RJ45", 87.50, 34.45, "rrect", 17.02, 14.60, 0.25),
]
SCREWS = [
    (3.99, 4.00),
    (99.01, 4.00),
    (3.99, 49.00),
    (99.01, 49.00),
]
TOP = [
    (29.00, 31.50),
    (29.00, 71.50),
]


def _plate(job, ident):
    matches = [plate for plate in job.plates if plate.ident == ident]
    if len(matches) != 1:
        raise AssertionError(f"{ident}: found {len(matches)} plates")
    return matches[0]


def _close(got, exp, label):
    if abs(got - exp) > TOL:
        raise AssertionError(f"{label}: {got} vs {exp} (tol {TOL} mm)")


class HoleTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.job = gm.collect_job(FIXTURE, revision="test", date="2026-10-12")

    def test_slot6_board_top_is_27_40(self):
        self.assertEqual(gm.board_top_y_mm(6), 27.40)
        self.assertEqual(self.job.board_top_y, 27.40)

    def test_front_matches_published_table(self):
        self._check_machined(_plate(self.job, "front"), FRONT)

    def test_rear_matches_published_table(self):
        self._check_machined(_plate(self.job, "rear"), REAR)

    def test_plate_screws(self):
        for ident in ("front", "rear"):
            screws = [h for h in _plate(self.job, ident).holes if h.existing]
            got = sorted((h.x, h.y) for h in screws)
            exp = sorted(SCREWS)
            self.assertEqual(len(got), len(exp), ident)
            for (gx, gy), (ex, ey) in zip(got, exp):
                _close(gx, ex, f"{ident} screw x")
                _close(gy, ey, f"{ident} screw y")
                self.assertEqual(screws[0].cutout.w, gm.SCREW_DIAMETER_MM)

    def test_top_wall_from_bar_pads(self):
        holes = [h for h in _plate(self.job, "top").holes if not h.existing]
        self.assertEqual(len(holes), 2)
        got = sorted((h.x, h.y) for h in holes)
        for (gx, gy), (ex, ey) in zip(got, TOP):
            _close(gx, ex, "top x")
            _close(gy, ey, "top y")
        for hole in holes:
            _close(hole.cutout.w, 3.4, "top drill")

    def _check_machined(self, plate, expected):
        machined = [h for h in plate.holes if not h.existing]
        by_name = {h.name: h for h in machined}
        self.assertEqual(set(by_name), {row[0] for row in expected})
        for name, x, y, kind, w, h, r in expected:
            hole = by_name[name]
            _close(hole.x, x, f"{name} x")
            _close(hole.y, y, f"{name} y")
            self.assertEqual(hole.cutout.kind, kind, name)
            _close(hole.cutout.w, w, f"{name} w")
            _close(hole.cutout.h, h, f"{name} h")
            _close(hole.cutout.r, r, f"{name} r")


class DefaultAndTransformTest(unittest.TestCase):
    def test_defaults_match_published_openings(self):
        cases = [
            ("Button_NKK_BB15AH", "BB15AH-FA", "SW1", "circle:6.5", 3.40),
            ("LED_Dialight_551", "551-0207F", "D1", "circle:4.0", 5.08),
            ("USB_C_GT-USB-7010ASV", "GT-USB-7010ASV", "J1", "rrect:13.60x6.50:r1", 1.68),
            ("RJ45_Pulse_J0011", "J0011D01BNL", "J2", "rrect:17.02x14.60:r0.25", 7.05),
            ("Gland_M16", "M16", "J3", "circle:16.3", 11.00),
            ("GND_STUD_M4", "M4", "J4", "circle:4.3", 15.10),
            ("Terminal_Power_In", "POWER", "J5", "circle:16.3", 11.00),
        ]
        for name, value, ref, spec, panel_z in cases:
            found = gm.lookup_default(name, value, ref)
            self.assertIsNotNone(found, name)
            self.assertEqual(found[0], spec, name)
            self.assertEqual(found[1], panel_z, name)

    def test_explicit_fields_override_defaults(self):
        board = _write_board(
            """
            (footprint "Button_NKK_BB15AH"
              (layer "F.Cu")
              (at 10 0)
              (property "Reference" "SW1")
              (property "Value" "BB15AH-FA")
              (property "Panel" "front")
              (property "PanelCutout" "circle:9")
              (property "PanelZ" "1.00")
            )
            """
        )
        job = gm.collect_job(board, revision="t", date="2026-10-12")
        hole = [h for h in _plate(job, "front").holes if not h.existing][0]
        _close(hole.cutout.w, 9.0, "override dia")
        _close(hole.y, 27.40 + 1.00, "override z")
        # board y = 0 is the right side: X = 101
        _close(hole.x, 101.0, "front y0")

    def test_rear_y0_is_left_side(self):
        board = _write_board(
            """
            (footprint "Gland_M16"
              (layer "F.Cu")
              (at 10 0)
              (property "Reference" "J3")
              (property "Panel" "rear")
              (property "PanelZ" "11")
            )
            """
        )
        job = gm.collect_job(board, revision="t", date="2026-10-12")
        hole = [h for h in _plate(job, "rear").holes if not h.existing][0]
        _close(hole.x, 2.0, "rear y0")
        _close(hole.cutout.w, 16.3, "default gland")

    def test_rotated_bar_pad(self):
        # 90° CCW on a Y-down board: local (0, -20) -> local (-20, 0)
        # footprint (26.9, 49.5) -> board (6.9, 49.5)
        # enclosure (9.0, 51.5)
        board = _write_board(
            """
            (footprint "AL_BAR_10x50"
              (layer "F.Cu")
              (at 26.9 49.5 90)
              (property "Reference" "HS1")
              (pad "" np_thru_hole circle (at 0 -20) (size 3.2 3.2) (drill 3.2))
            )
            """
        )
        job = gm.collect_job(board, revision="t", date="2026-10-12")
        hole = _plate(job, "top").holes[0]
        _close(hole.x, 9.0, "rot x")
        _close(hole.y, 51.5, "rot y")

    def test_user_cutout_spellings(self):
        circle = gm.parse_cutout("circle:6.5")
        rect = gm.parse_cutout("rect:17.02x14.60")
        rounded = gm.parse_cutout("rrect:13.6x6.5:r1")
        self.assertEqual(circle.kind, "circle")
        _close(circle.w, 6.5, "circle")
        self.assertEqual(rect.kind, "rect")
        _close(rect.w, 17.02, "rect w")
        _close(rect.h, 14.60, "rect h")
        self.assertEqual(rounded.kind, "rrect")
        _close(rounded.w, 13.6, "rrect w")
        _close(rounded.h, 6.5, "rrect h")
        _close(rounded.r, 1.0, "rrect r")


class OutputAndEmptyTest(unittest.TestCase):
    def test_render_contains_ordinate_and_title(self):
        job = gm.collect_job(FIXTURE, revision="abc123def456", date="2026-10-12")
        with tempfile.TemporaryDirectory() as tmp:
            written = gm.write_outputs(job, Path(tmp))
            names = {path.name for path in written}
            for stem in ("front-panel", "rear-panel", "top-wall"):
                for suffix in (".pdf", ".svg", ".png"):
                    self.assertIn(stem + suffix, names)
            svg = (Path(tmp) / "front-panel.svg").read_text(encoding="utf-8")
            self.assertIn("29.50", svg)
            self.assertIn("30.80", svg)
            self.assertIn("abc123def456", svg)
            self.assertIn("2026-10-12", svg)
            pdf = (Path(tmp) / "front-panel.pdf").read_bytes()
            self.assertTrue(pdf.startswith(b"%PDF"))
            png = (Path(tmp) / "front-panel.png").read_bytes()
            self.assertTrue(png.startswith(b"\x89PNG"))
            payload = json.loads((Path(tmp) / "holes.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["git"], "abc123def456")
            self.assertEqual(payload["board_top_y_mm"], 27.40)

    def test_allow_empty_exits_zero(self):
        board = _write_board(
            """
            (footprint "R_0805"
              (layer "F.Cu")
              (at 10 10)
              (property "Reference" "R1")
              (property "Value" "10k")
            )
            """
        )
        rc = gm.main([str(board), "-o", str(board.parent / "out"), "--allow-empty", "--rev", "t", "--date", "2026-10-12"])
        self.assertEqual(rc, 0)
        self.assertFalse((board.parent / "out").exists())

    def test_missing_panel_fields_is_an_error_without_allow_empty(self):
        board = _write_board('(footprint "R_0805" (layer "F.Cu") (at 1 1) (property "Reference" "R1"))')
        rc = gm.main([str(board), "-o", str(board.parent / "out"), "--rev", "t"])
        self.assertEqual(rc, 2)

    def test_outline_bar_and_no_panel_sheets(self):
        job = gm.collect_job(OUTLINE, revision="outline", date="2026-10-12")
        idents = {plate.ident for plate in job.plates}
        self.assertNotIn("front", idents)
        self.assertNotIn("rear", idents)
        self.assertIn("top", idents)
        holes = sorted((h.x, h.y) for h in _plate(job, "top").holes)
        self.assertEqual(len(holes), 2)
        for (gx, gy), (ex, ey) in zip(holes, TOP):
            _close(gx, ex, "outline top")

    def test_v4_has_no_panel_fields(self):
        if not V4.is_file():
            self.skipTest("V4 board not in this tree")
        job = gm.collect_job(V4, revision="v4", date="2026-10-12")
        self.assertTrue(job.is_empty())


def _write_board(body: str) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / "board.kicad_pcb"
    path.write_text(
        "(kicad_pcb (version 20241229) (generator \"test\") "
        "(gr_rect (start 0 0) (end 159 99) (layer \"Edge.Cuts\") (stroke (width 0.1))) "
        + body
        + ")",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
