# Enclosure drawings

Hammond 1455N1601, 160 × 103 × 53 mm. The board is 159 × 99 mm and
sits in slot 6. Decisions: [ADR 0009](../../../docs/decisions/0009-hammond-enclosure.md),
[ADR 0010](../../../docs/decisions/0010-triac-heatsink-bar.md),
[ADR 0016](../../../docs/decisions/0016-motor-run-capacitor.md).
The dimension notes are
[outline-1455N1601/README.md](outline-1455N1601/README.md).

Heights taken from Hammond typical dimensions are about ±0.6 mm.
Test-fit one board in a box before drilling a batch.

## Board outline

[outline-1455N1601/](outline-1455N1601/)

| File | What |
|---|---|
| [RotatorController-1455N1601-outline.kicad_pcb](outline-1455N1601/RotatorController-1455N1601-outline.kicad_pcb) | Edge.Cuts, slot keep-outs, triac-bar zone, motor-cap zone, end-panel marks. Not the V4 board. |
| [`.kicad_pro`](outline-1455N1601/RotatorController-1455N1601-outline.kicad_pro) / [`.kicad_dru`](outline-1455N1601/RotatorController-1455N1601-outline.kicad_dru) | KiCad 9 project and JLCPCB rule file |
| [outline.png](outline-1455N1601/outline.png) | Top view and end view |
| [README](outline-1455N1601/README.md) | Dimensions, sources, and what is still unverified |

The long edges have a 2.5 mm copper keep-out and a 3.5 mm component-body
line. The triac bar is 10 × 50 mm at board x 21.9–31.9. Two top-wall
holes, Ø3.4, sit at enclosure x = 29 from the rear-plate inner face,
y = ±20 from the centerline.

## End panels

[panels/](panels/). Print the PDF or SVG at 100 %. Each sheet has a
50 mm check bar.

| File | What |
|---|---|
| [front-panel-1455N1601.pdf](panels/front-panel-1455N1601.pdf) | Front plate, 1:1 |
| [front-panel-1455N1601.svg](panels/front-panel-1455N1601.svg) | Same drawing |
| [front-panel-1455N1601.png](panels/front-panel-1455N1601.png) | Screen copy |
| [rear-panel-1455N1601.pdf](panels/rear-panel-1455N1601.pdf) | Rear plate, 1:1 |
| [rear-panel-1455N1601.svg](panels/rear-panel-1455N1601.svg) | Same drawing |
| [rear-panel-1455N1601.png](panels/rear-panel-1455N1601.png) | Screen copy |

Front plate: CCW, STOP, and CW (Ø6.5) and six Dialight 551 right-angle
LED holes (Ø4.0). No light pipes. LED functions are still TBD.

Rear plate: power inlet, M16 rotor gland, USB-C, RJ45, and a ground
stud. Power, the gland, USB-C, and the stud are still marked TBD on
the drawing.

Open the outline, not the V4 project, when checking these drawings:

```bash
kicad hardware/controller/mechanical/outline-1455N1601/RotatorController-1455N1601-outline.kicad_pro
```
