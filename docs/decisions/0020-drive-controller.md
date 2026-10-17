# ADR 0020: Drive MCU in place of the discrete interlock

- Status: Accepted
- Date: 2026-10-17

## Context

ADR 0005 puts CW/CCW exclusion and the reversal gap in 74LVC gates and an RC hold, with a longer gap in firmware. Those gates are hard to review for every timing edge, and the STM32F407 is also busy with Ethernet, USB, the web UI, and firmware updates. A deadline that lives in that firmware can slip for reasons that have nothing to do with the motor.

The long form, the state diagram, and the state-by-event tables are in `docs/design/drive-controller.md`.

## Decision

Add a second MCU, the Drive. The STM32F407 is the Station. Those names are confirmed.

Deadlines live in the Drive: triac and brake gates, the ARM relay, reversal dead time, the ramp states, soft limits, stall, jam, run timeout, position sensing, and the heartbeat. An AC axis is on or off. Its ramp time is 0, so `RAMP_UP` and `RAMP_DOWN` pass straight through. A real slope belongs to the later DC H-bridge module (ADR 0018). The Drive stores its own copy of the limits, calibration, park heading, and loss policy, and it follows that copy while the Station is off. The Station keeps the web UI, USB, Ethernet, GS-232, Hamlib, Easycom, the operator catalog, logging, schedules, multi-rotator, and updates for both chips.

Commands from the Station are targets on a 3.3 V UART. Both chips share the rotor-return ground (ADR 0018), so the link has no isolator. A late, duplicate, or lost command leaves the Drive on the last accepted target.

The host heartbeat default is 5 seconds, set per rotor, allowed range 2 to 30 seconds. The default loss policy is stop. Hold and complete-the-move remain available per rotor. Idle and parked axes have no heartbeat deadline. The per-axis machine, including dead time, limits, the ramp states, stall, and heartbeat, is the diagram and the tables in the design note.

K1, the ARM relay, stays: one relay on the first board. It is the only way to end a shorted-triac fault. Gate pulldowns cannot open a triac that has failed short. The 5 A inductive rating against about 7.3 A motor-plus-brake overlap stays open.

TR1, the ZMCT103C, stays as drawn. Its 5 A rating against that same overlap current, and saturation, stay open.

The Drive MCU is the STM32G431RBT6, LQFP-64, LCSC C431633, checked on the LCSC page on 2026-10-17. JLC assembly stock was not rechecked.

Residual hardware is ARM_OK only: `ARM_EN AND nRESET` from the TPS3823 forces the triac-driver gates and the relay off while the Drive is in reset, plus pulldowns, plus the brake defaulting to engaged. Direction exclusion and the 500 ms gap live in the Drive state machine. The direction lockout (U2, the direction AND gates, and the hold RC) comes off in a later schematic edit. It is not removed in the change that accepted this record.

This record replaces the combinatorial-gate and RC-hold parts of ADR 0005. The ARM relay, brake-defaults-engaged, stuck-on sensing, and a dead time of at least 500 ms remain. The dead time is enforced by the Drive.

## Consequences

U2, the direction AND gates U4–U9, and the hold RC leave the schematic in a later edit. U10 leaves with them if the ARM_OK clamp already forces the brake driver off. U3's `ARM_OK` function stays. The schematic and the firmware are unchanged by the acceptance of this record.

The state machine is a shared C++17 core, unit-tested on the PC and, later, run against the physics simulator. That code is not in this change.

The CCW hold on the current sheet is open (`HOLD_CCW` is only U2 pin 9 in the 2026-10-17 netlist). The later schematic edit removes that network. It does not repair it.
