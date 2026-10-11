# ADR 0010: Triacs on a bar clamped to the top wall

- Status: Accepted
- Date: 2026-10-11

## Context

Three BTA16-600SW triacs need a thermal path into the extrusion. The
side walls are not flat. A bar that hangs from the lid and is only
soldered to the board stresses the leads. A D²PAK island on the belly
plate is a weak and electrically hot path.

## Decision

The three insulated-tab triacs are soldered to the PCB and bolted to
one 6061 aluminum bar, 10 mm thick by 50 mm long. The bar is screwed to
the PCB from below, so the board, bar, and triacs are one rigid piece
and the leads do not carry the bar.

Two M3 screws through the top wall pull the bar up. A 1.0 mm Bergquist
GAP PAD TGP 3000 (or TGP 3000ULM) on top of the bar is clamped to about
0.65 mm and takes up the height tolerance. Bar height H is cut from one
measurement of the real box (`H = D_k − 0.65 mm`) and then reused.

The tabs are internally insulated, so the bar and the box sit at chassis
potential.

## Consequences

A single run is capped at 120 s in firmware, because steady-state
heating only matters for a stuck or continuous fault. The bar drawing
and the top-wall hole pattern are not in the repo yet; the dimensions
are in `docs/design/triac-thermal-packaging.md`. A 1 inch aluminum angle
is the documented cheaper alternative, not the chosen design.
