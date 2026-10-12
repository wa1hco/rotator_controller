# ADR 0007: USB and Ethernet both required

- Status: Accepted
- Date: 2026-10-11
- Revised: 2026-10-11. The first wording of this record made Ethernet
  optional. That is superseded by ADR 0014.

## Context

Logging and control programs already speak GS-232 over a serial port.
The box also has to sit on the station network without a USB host in
the middle. An SPI Ethernet controller was the earlier way to get that
on a small MCU. The chosen MCU has a MAC, and the 64-pin part the V4
drawing uses does not.

## Decision

Isolated USB and Ethernet are both required. Ethernet is not a
populate-option, and the W5500-on-SPI path is not the design. The
firmware still sees each transport as the same byte-link interface.

The parts, the 25 MHz PHY clock, and the MagJack are in ADR 0014.

## Consequences

The rear panel always has USB and an RJ45. The imported V4 drawing is
still the F405 board and does not yet show the PHY. GS-232 over USB is
the first protocol path; a network listener uses the same parser.
GS-232 and the text console share those ports by grammar (ADR 0015).
The core does not gain a TCP stack in the skeleton.
