# ADR 0003: Separate external power supply

- Status: Accepted
- Date: 2026-10-11
- Revised: 2026-10-12. The separate 13.8 V logic feed is superseded by
  ADR 0018. Mains and the transformer still stay outside the box.

## Context

Mains, the 26 VAC rotator transformer, and a DC motor bus do not have
to live in the same enclosure as the MCU.

## Decision

Power supplies stay outside the controller. Mains wiring stays in the
supply. For the AC version the box receives one low-voltage feed, 26 VAC,
and makes its own logic rails from that (ADR 0018). There is no separate
DC logic supply and no 12 V input. A later DC-rotor H-bridge brings its
own supply; that is not this box. AC switching either turns on at zero
current or uses snubbers for the inductive kick.

## Consequences

The controller enclosure has no mains entry and no transformer. The
rear panel has the 26 VAC Powerpoles, not a 13.8 V connector. Fusing
and snubbing of the motor lines are still the controller's job.
