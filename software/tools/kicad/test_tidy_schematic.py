#!/usr/bin/env python3
# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Overlap detection moves only the text that collides."""

import tempfile
import unittest
from pathlib import Path

import tidy_schematic as tidy


SHEET = """\
(kicad_sch
	(version 20250114)
	(generator "eeschema")
	(generator_version "9.0")
	(uuid "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	(paper "A4")
	(lib_symbols
		(symbol "Device:R"
			(symbol "R_0_1"
				(rectangle
					(start -1.016 -2.54)
					(end 1.016 2.54)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
							(hide yes)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
							(hide yes)
						)
					)
				)
			)
		)
	)
	(symbol
		(lib_id "Device:R")
		(at 50.8 50.8 0)
		(unit 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(uuid "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee")
		(property "Reference" "R1"
			(at 50.8 50.8 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" "100"
			(at 50.8 55.88 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" "Resistor_SMD:R_0805"
			(at 50.8 50.8 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "LCSC" "C1234"
			(at 50.8 60.96 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(instances
			(project "t"
				(path "/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
					(reference "R1")
					(unit 1)
				)
			)
		)
	)
	(label "CLEAR_NET"
		(at 10.16 10.16 0)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify left)
		)
		(uuid "cccccccc-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	)
	(label "ON_BODY"
		(at 50.8 46.99 0)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify left)
		)
		(uuid "dddddddd-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	)
	(wire
		(pts
			(xy 40.64 46.99) (xy 50.8 46.99)
		)
		(stroke
			(width 0)
			(type default)
		)
		(uuid "eeeeeeee-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	)
)
"""

CLEAR_VALUE = """\
		(property "Value" "100"
			(at 50.8 55.88 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)"""

CLEAR_LABEL = """\
	(label "CLEAR_NET"
		(at 10.16 10.16 0)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify left)
		)
		(uuid "cccccccc-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	)"""


class SpinTests(unittest.TestCase):
    def test_file_angle_with_left_justify_collapses(self):
        # KiCad uprights 180/270, then the file's justify wins.
        self.assertEqual(tidy.spin_of(0, "left"), "right")
        self.assertEqual(tidy.spin_of(180, "left"), "right")
        self.assertEqual(tidy.spin_of(90, "left"), "up")
        self.assertEqual(tidy.spin_of(270, "left"), "up")
        self.assertEqual(tidy.spin_of(180, "right"), "left")
        self.assertEqual(tidy.spin_of(270, "right"), "down")

    def test_resistor_body_matches_sheet_axes(self):
        _root, model = tidy.load_sheet(SHEET)
        body = model.symbols[0].box
        # Lib rect x ±1.016, y ±2.54, rotation 0, origin (50.8, 50.8),
        # plus half of the 0.254 mm stroke.
        self.assertAlmostEqual(body.x0, 50.8 - 1.016 - 0.127, places=2)
        self.assertAlmostEqual(body.x1, 50.8 + 1.016 + 0.127, places=2)
        self.assertAlmostEqual(body.y0, 50.8 - 2.54 - 0.127, places=2)
        self.assertAlmostEqual(body.y1, 50.8 + 2.54 + 0.127, places=2)

    def test_shown_text_strips_overbar(self):
        self.assertEqual(tidy.shown_text("~"), "")
        self.assertEqual(tidy.shown_text("~{RESET}"), "RESET")
        self.assertEqual(tidy.shown_text("~R"), "R")


class TidyTests(unittest.TestCase):
    def test_only_overlapping_text_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.kicad_sch"
            path.write_text(SHEET, encoding="utf-8")
            before = tidy.main(["--check", str(path)])
            self.assertEqual(before, 1)
            applied = tidy.main([str(path)])
            self.assertEqual(applied, 0)
            updated = path.read_text(encoding="utf-8")
            self.assertIn(CLEAR_VALUE, updated)
            self.assertIn(CLEAR_LABEL, updated)
            self.assertIn("(hide yes)", updated)
            # The clear LCSC field sits below the body and stays visible.
            self.assertIn('(property "LCSC" "C1234"\n\t\t\t(at 50.8 60.96 0)', updated)
            self.assertNotIn('(property "Reference" "R1"\n\t\t\t(at 50.8 50.8 0)', updated)
            self.assertIn('(at 50.8 50.8 0)', updated)  # the symbol itself
            again = path.read_text(encoding="utf-8")
            self.assertEqual(tidy.main([str(path)]), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), again)
            self.assertEqual(tidy.main(["--check", str(path)]), 0)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.kicad_sch"
            path.write_text(SHEET, encoding="utf-8")
            self.assertEqual(tidy.main(["--dry-run", str(path)]), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), SHEET)


if __name__ == "__main__":
    unittest.main()
