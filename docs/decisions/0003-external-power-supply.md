# ADR 0003: Separate external power supply

- Status: Accepted
- Date: 2026-10-11

## Context

Mains, the 26 VAC rotator transformer, and a DC motor bus do not have
to live in the same enclosure as the MCU.

## Decision

Power supplies stay outside the controller. The box receives low-voltage
power (26 VAC for an AC rotator such as a HAM-IV, and 13.8 V for logic).
Mains wiring stays in the supply. AC switching either turns on at zero
current or uses snubbers for the inductive kick.

## Consequences

The controller enclosure has no mains entry and no transformer. Rear-panel
cables include the low-voltage feeds. Fusing and snubbing of the motor
lines are still the controller's job.
