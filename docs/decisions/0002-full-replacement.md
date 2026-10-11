# ADR 0002: Full replacement of the stock controller

- Status: Accepted
- Date: 2026-10-11

## Context

A rotator controller can sit beside the manufacturer's box and only
pretend to be a button, or it can take the rotor cable and do the
manufacturer's job.

## Decision

This box replaces the stock controller. The rotator, its motor, brake,
position sensor, and the cable up the tower stay as they are. The shack
box drives that cable directly. Electronics on the tower, and a new
cable, are out of scope for the baseline.

## Consequences

The board has to switch the motor and brake, read the sensor, and
survive the voltages on that cable. It is not an interface pod for an
intact CDE or Yaesu control box.
