# ADR 0007: USB required, Ethernet optional

- Status: Accepted
- Date: 2026-10-11

## Context

Logging and control programs already speak GS-232 over a serial port.
A network connection is useful at a remote site and is not required to
turn a rotator.

## Decision

Isolated USB serial is required. Ethernet (an RJ45 on the rear panel)
is optional and may be left off a given board. The firmware sees both
as the same byte-link interface.

## Consequences

The V4 board's ADuM USB isolation stays. An Ethernet PHY or module is
not allowed to become a boot dependency. GS-232 over USB is the first
protocol path; a network listener can use the same parser.
