# ADR 0012: One repository for hardware and software

- Status: Accepted
- Date: 2026-10-11

## Context

The V4 board lived in `wa1hco/Rotator-Controller-V2` on branch
`Rotator_Controller_V4`, next to an older firmware tree. The simulator
lived in the K3NG fork. Design notes lived outside both.

## Decision

This repository is the home of the controller. Hardware is under
`hardware/`. Firmware, the simulator, and host tools are under
`software/`. Design notes and decision records are under `docs/`.
Licenses differ by path: GPL-3.0-only for software, CERN-OHL-S-2.0 for
hardware, CC BY-SA 4.0 for docs.

## Consequences

A change to the triac circuit and a change to the motion state machine
are reviewed in one place. The source repositories are left as they
were; this tree records the commits it was copied from.
