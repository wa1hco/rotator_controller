# Enclosure and heatsink drawings

Placeholder for fabrication drawings that are not in the repository yet.

Decisions these drawings have to match are in
`docs/decisions/0009-hammond-enclosure.md`,
`docs/decisions/0010-triac-heatsink-bar.md`, and
`docs/design/triac-thermal-packaging.md`.

## Hammond 1455N1601 drill templates

Enclosure: Hammond 1455N1601, 160 × 103 × 53 mm extruded aluminum.
The PCB slides into the side-wall slots. Only the belly plate and the
two end plates are removable.

- **Front end plate:** buttons and LEDs only. PCB-mounted actuators and
  light pipes pass through the plate. No connectors.
- **Rear end plate:** every cable. Rotor pigtail, 13.8 V, 26 VAC, USB-C,
  and the Ethernet MagJack (through-hole, standard on every board).
  No connectors on the other faces, and no internal wiring harness.

Needed here later:

- Front-plate hole template (STOP, CW, CCW, LED light pipes) with the
  end-plate screw pattern (4 × #6 on 95.02 × 45.00 mm).
- Rear-plate hole template for the cable entries and the chassis ground lug.
- Edge keepout: 3.5 mm on both long edges of a board about 99.3 mm wide.

## Triac heatsink bar

Three insulated-tab BTA16-600SW triacs (CW, CCW, brake) soldered to the
PCB and bolted to one 6061 aluminum bar, 10 mm thick × 50 mm long × H
tall. The bar is screwed to the PCB from below (2 × M3). Two M3 button-head
screws through the top wall clamp the bar up through a 1.0 mm gap pad.

Needed here later:

- Bar drawing: stock size, H, tap depths, triac-tab holes at 12.7 mm
  pitch, and the two PCB screws.
- Top-wall hole pattern: x = 29 mm from the rear plate's inner face,
  y = ±20 mm from the board centerline, Ø3.4 mm.
- Note that H is cut from one measurement of the actual box
  (`H = D_k − 0.65 mm`) and then reused. Do not treat an example H as
  final until `D_k` is measured.
