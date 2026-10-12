# ADR 0009: Hammond 1455N1601 enclosure

- Status: Accepted
- Date: 2026-10-11
- Revised: 2026-10-12. The slot-6 board outline is in the repository.
  The motor run cap that fits this height is ADR 0016. Machining
  drawings are generated from the layout (ADR 0017); the PDFs under
  `panels/preliminary-pre-layout/` are the pre-layout sheets.

## Context

The box has to sink triac heat, hold a board about 100 mm wide, and
present a simple front and rear. A folded sheet-metal box makes the
thermal path and the end plates a custom job.

## Decision

Use a Hammond 1455N1601 extruded aluminum enclosure, 160 × 103 × 53 mm.
The board slides into the side-wall card slots.

- Board: 159 × 99 mm, in slot 6.
- Front end plate: CCW, STOP, and CW, plus six Dialight 551 right-angle
  LED holes. No light pipes and no preset pot.
- Rear end plate: every cable (26 VAC Anderson Powerpoles, M16 rotor
  gland, USB-C, RJ45 MagJack, ground stud). Ethernet is standard
  (ADR 0014). The Powerpole pair is grey and black, as on V2
  (ADR 0018). A panel-mount bracket for that pair is TBD; the other
  option is a pigtail through a gland. The gland, USB-C, and the stud
  are still TBD on the drawing.
- No connectors on the other faces, and no internal wiring harness.
  The rear plate and the PCB connectors are one subassembly.
- Motor run capacitor: KEMET 100 µF flat plus TDK 33 µF upright,
  133 µF, inside the 22.9 mm height limit (ADR 0016).

## Consequences

The board outline is in `hardware/controller/mechanical/outline-1455N1601/`.
End-plate and top-wall drawings are generated from footprint fields
(ADR 0017). The pre-layout sheets are in
`panels/preliminary-pre-layout/`.
Slot heights chained from Hammond typical dimensions are about
±0.6 mm. Test-fit one board in a box before drilling a batch.
The top wall is the heat-sink surface (ADR 0010), because the side
walls are the slot comb and the belly plate is a sliding joint.
