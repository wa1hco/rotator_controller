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

    def test_owner_frozen_field_stays_byte_identical(self):
        key = ("property", "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee", "Reference")
        tidy.FROZEN.add(key)
        reference = """\
		(property "Reference" "R1"
			(at 50.8 50.8 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)"""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "sheet.kicad_sch"
                path.write_text(SHEET, encoding="utf-8")
                self.assertEqual(tidy.main([str(path)]), 0)
                updated = path.read_text(encoding="utf-8")
                self.assertIn(reference, updated)
                self.assertIn("(hide yes)", updated)
                _root, model = tidy.load_sheet(updated)
                frozen_ref = next(item for item in model.texts if item.frozen)
                self.assertEqual(frozen_ref.name, "Reference")
                self.assertTrue(tidy.item_overlaps(frozen_ref, model, model.texts))
                self.assertEqual(tidy.main(["--check", str(path)]), 0)
        finally:
            tidy.FROZEN.discard(key)

    def test_off_page_freeze_is_lifted(self):
        # A4 is 297 x 210 mm. x=400 is outside the border; x=50.8 is on the page.
        key = ("property", "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee", "Reference")
        tidy.FROZEN.add(key)
        try:
            sheet = SHEET.replace("(at 50.8 50.8 0)", "(at 400 50.8 0)")
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "sheet.kicad_sch"
                path.write_text(sheet, encoding="utf-8")
                _root, model = tidy.load_sheet(sheet)
                self.assertTrue(model.symbols[0].off_page)
                reference = next(item for item in model.texts if item.name == "Reference")
                self.assertTrue(reference.off_page)
                self.assertFalse(reference.frozen)
                self.assertEqual(tidy.main([str(path)]), 0)
                updated = path.read_text(encoding="utf-8")
                self.assertIn('(lib_id "Device:R")\n\t\t(at 400 50.8 0)', updated)
                self.assertNotIn('(property "Reference" "R1"\n\t\t\t(at 400 50.8 0)', updated)
                self.assertEqual(tidy.main(["--check", str(path)]), 0)
        finally:
            tidy.FROZEN.discard(key)

    def test_usledger_page_box(self):
        root = tidy.parse_sexpr('(kicad_sch (paper "USLedger"))')
        box = tidy.page_box(root)
        self.assertEqual((box.x0, box.y0, box.x1, box.y1), (0.0, 0.0, 431.8, 279.4))

    def test_sheet_pin_ignores_its_own_wire(self):
        # The pin name is drawn back along the wire that ends on the pin.
        # A wire that only crosses the name is still an overlap.
        sheet = """\
(kicad_sch
	(version 20250114)
	(generator "eeschema")
	(uuid "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	(paper "A3")
	(sheet
		(at 100 20)
		(size 40 30)
		(uuid "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee")
		(property "Sheetname" "drive"
			(at 120 18 0)
			(effects (font (size 1.27 1.27)))
		)
		(pin "ARM_EN" input
			(at 100 30 180)
			(effects (font (size 1.27 1.27)) (justify right))
			(uuid "cccccccc-bbbb-4ccc-8ddd-eeeeeeeeeeee")
		)
	)
	(wire
		(pts (xy 70 30) (xy 100 30))
		(stroke (width 0) (type default))
		(uuid "dddddddd-bbbb-4ccc-8ddd-eeeeeeeeeeee")
	)
)
"""
        crossed = sheet.replace(
            "(xy 70 30) (xy 100 30)",
            "(xy 70 30) (xy 110 30)",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "root.kicad_sch"
            path.write_text(sheet, encoding="utf-8")
            self.assertEqual(tidy.main(["--check", str(path)]), 0)
            path.write_text(crossed, encoding="utf-8")
            self.assertEqual(tidy.main(["--check", str(path)]), 1)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.kicad_sch"
            path.write_text(SHEET, encoding="utf-8")
            self.assertEqual(tidy.main(["--dry-run", str(path)]), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), SHEET)


if __name__ == "__main__":
    unittest.main()
