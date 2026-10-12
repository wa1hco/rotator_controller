# ADR 0017: Enclosure machining drawings come from the layout

- Status: Accepted
- Date: 2026-10-12

## Context

The Hammond 1455N1601 end-plate sheets were drawn by hand on the
outline board's User.Drawings layer, next to the board (ADR 0009).
That drawing cannot follow a part when the layout moves it. A hole
that is 0.5 mm off on the board is then 0.5 mm off in the plate, and
nobody notices until the box is drilled.

The outline board is the mechanical reference: Edge.Cuts, the slot
keep-outs, the end-plate plane markers, the height-limit notes, the
triac bar, and the motor caps. It is not the place to keep a second
copy of the panel.

## Decision

Machining drawings are generated from footprint positions on the
`.kicad_pcb`. The script is
`software/tools/enclosure/gen_machining.py`. It does not need the
KiCad GUI.

A footprint is on a plate when it has a property `Panel` = `front`,
`rear`, or `top`.

- `PanelCutout` is optional: `circle:6.5`, `rect:17.02x14.60`, or
  `rrect:13.6x6.5:r1`. Buttons, Dialight 551 LEDs, USB-C, RJ45, the
  M16 gland, the ground stud, and the 26 VAC Powerpole feed have
  defaults.
- `PanelZ` is the optical or mechanical centre height above the
  board, in millimetres. The same parts have defaults (button 3.40,
  LED 5.08, USB-C 1.68, RJ45 7.05, gland 11.00, stud 15.10). The
  Powerpole default is the pigtail gland, Ø16.3 at 11.00 mm
  (ADR 0018). A panel-mount bracket is TBD and is not that default.
- The footprint anchor is the hole centre in the board plane. Board
  coordinates are millimetres from the Edge.Cuts minimum corner
  (rear-left).
- End-plate Y = board-top Y + `PanelZ`. Board-top Y is 27.40 mm for
  slot 6, and `--slot` recomputes it. Front, from outside, has board
  y = 0 on the right. Rear has board y = 0 on the left.
- Top-wall holes are the `np_thru_hole` pads of a footprint with
  `Panel` = `top`, or of a footprint whose name contains `AL_BAR`.
  The clearance drill is 3.4 mm unless `PanelCutout` says otherwise.
  Datum X is the rear-plate inner face. Datum Y is the outside edge
  on the board y = 0 side.

Each plate is a 1:1 A4 PDF and SVG (ordinate dimensions from the
lower-left datum, a hole table, a 50 mm check bar, and a title block
with the board git SHA and the date), plus a PNG preview. Print at
100 %.

The hand-drawn sheets are kept as
`hardware/controller/mechanical/panels/preliminary-pre-layout/`.
They are the pre-layout hole table. A fixture board with footprints
at those positions must regenerate that table within 0.05 mm.

The outline board no longer carries the front and rear panel sheets.
Edge.Cuts, the slot keep-outs, the end-plate plane markers, the
height-limit notes, the bar, and the motor caps stay.

CI runs the generator on the outline board and on the V4 board. If a
board has no `Panel` fields and no bar mounting holes, the job exits 0
and uploads nothing for that board.

## Consequences

Add `Panel` (and `PanelZ` / `PanelCutout` when the default is wrong)
when a connector, button, or LED is placed. Regenerate the drawings
from that board. Do not draw the plates back onto User.Drawings.

Heights chained from Hammond typical dimensions are still about
±0.6 mm (ADR 0009). Test-fit one board in a box before drilling a
batch. The preliminary PDFs are not a substitute for a drawing made
from the real layout.
