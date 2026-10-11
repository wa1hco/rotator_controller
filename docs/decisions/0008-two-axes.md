# ADR 0008: Two axes at the sensor and MCU

- Status: Accepted
- Date: 2026-10-11

## Context

Many rotators are azimuth only. Az/el pairs (G-5500, SPID, and others)
need a second sensor and a second motor channel. The MCU and the sensor
front end are cheap compared with pretending the second axis does not
exist.

## Decision

The sensor inputs and the firmware core support two axes. The motor
drive for the second axis can be a module or a conditional assembly, so
an azimuth-only board does not have to be populated with a second power
stage.

Sensor kinds the hardware plan covers are dual-end pot, single-ended pot
with excitation, and pulse/reed counters. The first firmware sensor
implementation is the CDE dual-end pot.

## Consequences

`MotionController` is per axis. Settings and the GS-232 parser start
with azimuth; elevation is a second instance, not a different program.
The imported V4 PCB is still a single-axis CDE board until the respin.
