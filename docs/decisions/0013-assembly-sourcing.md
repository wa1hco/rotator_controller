# ADR 0013: JLCPCB assembles SMT; the owner hand-solders through-hole

- Status: Accepted
- Date: 2026-10-11

## Context

The controller is a one-off shack box, not a production run. Through-hole
connectors, the MagJack, and the triacs are easier to place, inspect, and
replace by hand. The fine-pitch MCU, PHY, and passives are not.

## Decision

- The owner hand-solders every through-hole part. Those parts are bought
  from Mouser.
- JLCPCB assembles every SMT part. Every SMT part must be in the LCSC
  catalog, so JLCPCB can load it.
- On the KiCad symbols, an SMT part carries an `LCSC` field with the
  LCSC C-number. A through-hole part carries a `Mouser` field with the
  Mouser order number.

## Consequences

A part that is only in a catalog JLCPCB cannot assemble does not go on
the board as SMT. The through-hole MagJack is a Mouser part, not an LCSC
jack that JLCPCB would place. The imported V4 schematic does not have
these fields yet. They are added when the board is re-laid-out. This
record does not change the KiCad files.
