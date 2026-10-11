# ADR 0011: TE CPC rotor connector

- Status: Accepted
- Date: 2026-10-11

## Context

The station already has a rotor-cable connector standard, written up by
Steve Schultz WB8WGY and used by Dave Cipolle W1SZ and others: TE
Connectivity CPC connectors, wired 1:1 to the HAM-IV terminal strip.

## Decision

Use TE CPC Series 1, shell size 13, 9 contacts.

| End | Part | Role |
|---|---|---|
| Rotor chassis | 206705-1 | Square-flange receptacle, pin contacts |
| Controller pigtail | 206708-1 | Plug, socket contacts |

Pins 1–8 are wired 1:1 with the rotor terminals. Pin 9 is unused. The
controller end is female (socket contacts) so a live plug does not
expose pins. Shell 13 has no panel-mount female, so the controller uses
a short pigtail from the rear plate to the 206708-1 plug, terminated
inside on a pluggable terminal block.

## Consequences

The rear panel does not carry a CPC flange. It carries the pigtail
entry, a shield lug, and the other cables. Trailer reverse-sex shell 17
parts (211769-1 / 211768-1) are for the tower-trailer wall, not the
controller face.
