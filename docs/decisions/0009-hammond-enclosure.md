# ADR 0009: Hammond 1455N1601 enclosure

- Status: Accepted
- Date: 2026-10-11

## Context

The box has to sink triac heat, hold a board about 100 mm wide, and
present a simple front and rear. A folded sheet-metal box makes the
thermal path and the end plates a custom job.

## Decision

Use a Hammond 1455N1601 extruded aluminum enclosure, 160 × 103 × 53 mm.
The board slides into the side-wall card slots.

- Front end plate: buttons and LEDs only.
- Rear end plate: every cable (rotor pigtail, 13.8 V, 26 VAC, USB-C,
  optional Ethernet).
- No connectors on the other faces, and no internal wiring harness.
  The rear plate and the PCB connectors are one subassembly.

## Consequences

Drill templates for the two end plates belong in
`hardware/controller/mechanical/` and are not drawn yet. The top wall is
the heat-sink surface (ADR 0010), because the side walls are the slot
comb and the belly plate is a sliding joint.
