# ADR 0005: Direction interlock, ARM relay, and firmware dead time

- Status: Accepted
- Date: 2026-10-11

## Context

CW and CCW both on shorts the run capacitor and stalls the motor. A
shorted triac has to be taken off the 26 VAC bus. The triac also stays
latched until current zero, so a direction reversal needs a gap.

## Decision

Hardware gating, not firmware alone, enforces mutual exclusion:

- `CW_GATE` requires CW requested, CCW not requested, ARM, and the
  opposite-direction hold timer clear. CCW is the mirror of that.
- An RC hold blocks the opposite direction for roughly 70–110 ms after
  a gate drops.
- An ARM master relay (Omron G5LE or equivalent) is in series with the
  triac bus. Normal motion does not make or break load current with
  that relay. It opens on a fault.

Firmware still waits before reversing: at least 500 ms with both
direction outputs off, and it coasts to a stop before reversing. The
firmware gap is longer than the hardware gap. The hardware gap is the
backstop when firmware asserts both or crashes.

## Consequences

The motion state machine has an explicit dead-time state, and the triac
driver never turns CW and CCW on together. ARM is a separate output.
Stuck-on sensing across each triac is part of the same hardware plan.
