# ADR 0004: Discrete triacs instead of CPC1966

- Status: Accepted
- Date: 2026-10-11

## Context

The V4 board as drawn uses three CPC1966 solid-state relays for CW, CCW,
and brake. Those parts are zero-cross switches. On the inductive motor
and brake load they can refuse to re-fire when current zero arrives at
a non-zero voltage. The V2 relay board also showed what happens with
the wrong capacitors across the motor lines.

## Decision

Each AC channel is a random-phase opto-triac driver, an onsemi MOC3023M,
firing a BTA16-600SW power triac (insulated tab, 16 A, 600 V, logic-level
gate), with an RC snubber across the triac (68 Ω and 0.1 µF X2 film).
The same part is used for CW, CCW, and brake. The CPC1966s come off the
board.

## Consequences

The KiCad project in `hardware/controller/` still shows the CPC1966
circuit. The triac swap exists as a design note
(`docs/design/v4-discrete-triac-change.md`) and as uncommitted edits on
the owner's laptop, which will be brought in later. Firmware and the
heatsink plan assume the triacs, not the CPC1966s.
