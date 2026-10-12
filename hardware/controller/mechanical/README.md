# Enclosure drawings

Hammond 1455N1601, 160 × 103 × 53 mm. The board is 159 × 99 mm and
sits in slot 6. Decisions: [ADR 0009](../../../docs/decisions/0009-hammond-enclosure.md),
[ADR 0010](../../../docs/decisions/0010-triac-heatsink-bar.md),
[ADR 0016](../../../docs/decisions/0016-motor-run-capacitor.md),
[ADR 0017](../../../docs/decisions/0017-enclosure-machining-drawings.md).
The dimension notes are
[outline-1455N1601/README.md](outline-1455N1601/README.md).

Heights taken from Hammond typical dimensions are about ±0.6 mm.
Test-fit one board in a box before drilling a batch.

## Board outline

[outline-1455N1601/](outline-1455N1601/)

| File | What |
|---|---|
| [RotatorController-1455N1601-outline.kicad_pcb](outline-1455N1601/RotatorController-1455N1601-outline.kicad_pcb) | Edge.Cuts, slot keep-outs, triac-bar zone, motor-cap zone, end-plate plane markers, height-limit notes. Not the V4 board. The front and rear panel sheets are not on this board. |
| [`.kicad_pro`](outline-1455N1601/RotatorController-1455N1601-outline.kicad_pro) / [`.kicad_dru`](outline-1455N1601/RotatorController-1455N1601-outline.kicad_dru) | KiCad 9 project and JLCPCB rule file |
| [outline.png](outline-1455N1601/outline.png) | Top view and end view |
| [README](outline-1455N1601/README.md) | Dimensions, sources, and what is still unverified |

The long edges have a 2.5 mm copper keep-out and a 3.5 mm component-body
line. The triac bar is 10 × 50 mm at board x 21.9–31.9. Two top-wall
holes, Ø3.4, sit at enclosure x = 29 from the rear-plate inner face,
y = ±20 from the centerline.

Open the outline, not the V4 project, when checking the mechanical
board:

```bash
kicad hardware/controller/mechanical/outline-1455N1601/RotatorController-1455N1601-outline.kicad_pro
```

## Machining drawings

Panel holes are generated from the layout. They are not drawn on the
PCB. The script is
[`software/tools/enclosure/gen_machining.py`](../../../software/tools/enclosure/gen_machining.py).
It parses the `.kicad_pcb` (no KiCad GUI) and writes, per plate, a 1:1
PDF, a 1:1 SVG, and a PNG preview. Print the PDF or SVG at 100 %. Each
sheet has a 50 mm check bar, ordinate dimensions from the lower-left
datum, a hole table, and a title block with the board git SHA and the
date.

```bash
python3 software/tools/enclosure/gen_machining.py \
  path/to/board.kicad_pcb \
  -o /tmp/enclosure-drawings
```

`--slot` defaults to 6, which puts the PCB top face at Y = 27.40 mm
on the end plate. `--allow-empty` exits 0 when the board has no
`Panel` fields and no bar mounting holes, which is how CI treats the
V4 board until those fields exist.

### Footprint fields

Add these as footprint properties in pcbnew. The anchor of the
footprint is the hole centre. Board x/y are millimetres from the
Edge.Cuts minimum corner (rear-left on the outline).

| Property | Example | Meaning |
|---|---|---|
| `Panel` | `front`, `rear`, or `top` | Which plate this part cuts |
| `PanelCutout` | `circle:6.5`, `rect:17.02x14.60`, `rrect:13.6x6.5:r1` | Opening. Optional when the footprint matches a default |
| `PanelZ` | `3.40` | Centre height above the board, mm. Optional when a default applies |
| `PanelName` | `CCW button` | Hole-table name. Optional; the reference is used otherwise |

End-plate Y = 27.40 + `PanelZ` for slot 6. From outside, the front
plate has board y = 0 on the right, and the rear plate has board y = 0
on the left. The four Hammond plate screws (Ø4.19, countersunk) are
drawn on every end plate as existing holes. Do not re-drill them.

Defaults when `PanelCutout` or `PanelZ` is omitted:

| Part | Cutout | PanelZ |
|---|---|---|
| NKK BB button | Ø6.5 | 3.40 |
| Dialight 551 LED | Ø4.0 | 5.08 |
| USB-C (GT-USB-7010ASV) | 13.60 × 6.50 R1 | 1.68 |
| RJ45 (Pulse J0011) | 17.02 × 14.60 R0.25 | 7.05 |
| M16 gland | Ø16.3 | 11.00 |
| Ground stud | Ø4.3 | 15.10 |
| 26 VAC Powerpoles | Ø16.3 gland (bracket TBD) | 11.00 |

The top-wall template uses the `np_thru_hole` pads of a footprint
named `AL_BAR…`, or any footprint with `Panel` = `top`. The wall
drill is Ø3.4 unless `PanelCutout` overrides it. Datum X is the
rear-plate inner face (board x + 2.10 mm). Datum Y is the outside
edge on the board y = 0 side, so the outline bar holes land at
(29.00, 31.50) and (29.00, 71.50), which is centreline ±20.

A fixture at
[`software/tools/enclosure/testdata/panel-regression.kicad_pcb`](../../../software/tools/enclosure/testdata/panel-regression.kicad_pcb)
places placeholders at today's positions. The test checks the
generated hole table against the outline README within 0.05 mm.

```bash
python3 -m unittest discover -s software/tools/enclosure -p 'test_*.py'
```

## Preliminary sheets (pre-layout)

[panels/preliminary-pre-layout/](panels/preliminary-pre-layout/).
These are the hand drawings from before any layout carried `Panel`
fields. Print at 100 %. They are the hole table the generator is
tested against. Replace them with a generator run once the real
board has those fields. Do not drill a batch from these alone.

| File | What |
|---|---|
| [front-panel-1455N1601.pdf](panels/preliminary-pre-layout/front-panel-1455N1601.pdf) | Front plate, 1:1, pre-layout |
| [front-panel-1455N1601.svg](panels/preliminary-pre-layout/front-panel-1455N1601.svg) | Same drawing |
| [front-panel-1455N1601.png](panels/preliminary-pre-layout/front-panel-1455N1601.png) | Screen copy |
| [rear-panel-1455N1601.pdf](panels/preliminary-pre-layout/rear-panel-1455N1601.pdf) | Rear plate, 1:1, pre-layout |
| [rear-panel-1455N1601.svg](panels/preliminary-pre-layout/rear-panel-1455N1601.svg) | Same drawing |
| [rear-panel-1455N1601.png](panels/preliminary-pre-layout/rear-panel-1455N1601.png) | Screen copy |

Front plate: CCW, STOP, and CW (Ø6.5) and six Dialight 551 right-angle
LED holes (Ø4.0). No light pipes. LED functions are still TBD.

Rear plate: 26 VAC Anderson Powerpoles (grey + black), M16 rotor
gland, USB-C, RJ45, and a ground stud. The drawable Powerpole default
is a pigtail gland, Ø16.3 at 11.00 mm above the board (ADR 0018). A
2-position panel-mount bracket is the other option; its cutout is
TBD. The gland, USB-C, and the stud are still marked TBD on the
drawing. The pre-layout PDF still shows the withdrawn 22.00 × 12.50
terminal-block opening.
