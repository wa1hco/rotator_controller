# ADR 0016: Motor run capacitor, 100 µF plus 33 µF

- Status: Accepted
- Date: 2026-10-12

## Context

A CDE HAM-IV or T2X wants 130–156 µF in the controller, across
terminals 4 and 8. The V2 board used one 100 µF part. That is about
23 % under the bottom of the range. The Hammond 1455N1601 in slot 6
leaves 22.9 mm above the board (ADR 0009). A single 150 µF film cap
in this voltage class is taller than that.

The parts check and the placement coordinates are in
`hardware/controller/mechanical/outline-1455N1601/README.md`. Prices
there were read on 2026-10-11. Mouser stock was not confirmed live.
The pair was first drawn on the top. On 2026-10-20 both caps moved
to the bottom: the top is crowded, and slot 6 has 23.1 mm under the
board (17.2 mm within 8.5 mm of the long edges).

## Decision

Two metallized-polyester caps in parallel, 133 µF nominal. Each is
100 VDC / 63 VAC. The motor is about 26–30 VAC, so the cap sees
roughly 37–44 VAC. Both are through-hole. The owner hand-solders them
(ADR 0013).

| Ref | Part | Mount | Height |
|---|---|---|---|
| C_MOTOR1 | KEMET R60EW61005000K, 100 µF. Digi-Key 399-13010-ND. Proven on V2 | Bottom, lying flat. Leads bent up into the board. Soldered from the top | 20.3 mm (bottom limit 23.1; body starts at y 8.6, outside the 8.5 mm / 17.2 strip) |
| C_MOTOR2 | TDK B32526T1336K000, 33 µF. Digi-Key 495-4582-ND. Mouser 871-B32526T1336K000, unverified | Bottom, upright. The 6 mm leads are too short to lay it flat. They go straight up; solder from the top | 15.0 mm (under 17.2 and under 23.1) |

Pad 1 ties to pad 1 and pad 2 to pad 2. ±10 % on each part gives
about 120–146 µF.

Rejected the same day: two 100 µF (200 µF, too much phase shift), a
47 µF laid flat (body too tall or leads too short), two 68 µF (too
tall, or not stocked), a 150 µF single part (taller than 22.9 mm),
and a CBB60 motor-run can (about 45 × 92 mm).

Rotors that carry their own cap (G-5500, HDR-300) leave both parts
off. The catalog still wants the placement to be configurable.

## Consequences

The outline board reserves x 47.25–122.5, y 8.1–50.9 for this pair,
on the bottom, on the same edge as the power inlet and in front of
the triac bar. The heat bar stays on the top. SMT stays on the top.
The V4 KiCad project is not edited. The next layout copies these
footprints onto B.Cu, with B.Fab and B.CrtYd. Symbols get a `Mouser`
field once that order number is confirmed. The KEMET Mouser number
was not found on 2026-10-11.
