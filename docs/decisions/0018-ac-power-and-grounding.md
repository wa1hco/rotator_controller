# ADR 0018: Power input and grounding (AC version)

- Status: Accepted
- Date: 2026-10-12

## Context

ADR 0003 put the mains and the rotator transformer outside the box,
and it also brought 13.8 V in for logic. That second feed is dropped.
The CDE pot wiper is the motor and brake return (terminal 1). The
dual-end measurement has to use that same node, because of the pot's
ground and the transients on it. A separate logic ground, an isolated
DC-DC, or a 12 V input would float the ADC off the quantity it is
measuring.

This record is the AC controller only (HAM-IV / T2X class). The
DC-rotor version is a later H-bridge module with its own supply. It
is not a 12 V logic input and it is not specified here.

## Decision

One 26 VAC input. The transformer stays in the external supply. The
rear plate carries it on Anderson Powerpoles, grey and black housings,
the same arrangement as V2. Polarity does not matter on AC. The colors
are the key: this pair is not the shack's red/black 12 VDC pair.
Housings are the Powerpole 15/30/45 series. Contacts have to carry the
motor plus the brake (about 7.3 A intermittent), so 15 A contacts are
enough. Exact Mouser numbers are TBD; buy the V2 pair.

Two ways to put that pair on the plate. Pick one before drilling:

- A pigtail through a gland. The generator default is that option:
  Ø16.3, center 11.00 mm above the board (plate Y = 38.40 at the
  planned X = 17.50). Same opening class as the rotor gland. The
  gland size is unverified.
- A 2-position panel-mount Powerpole bracket. The bracket and its
  cutout are TBD. Do not drill a bracket hole from the gland default.
  When a bracket is chosen, set `PanelCutout` and `PanelZ` and
  regenerate.

There is no 13.8 V connector, no 12 V input, and no isolated DC-DC.
Logic power is derived from the 26 VAC on the rotor-return ground.

**Ground.** Logic ground is the rotor return, CDE terminal 1. The
whole controller floats on that node. The transformer secondary floats
in the supply box and is referenced only at terminal 1. USB stays
isolated by the ADuM4160. Ethernet stays isolated by the MagJack
magnetics. The rotor return meets the chassis through an RF capacitor
in parallel with a TVS. Values are TBD. The rear-plate ground stud is
the chassis bond to station ground. It is not a DC short from logic
ground to the chassis.

**Logic rails.** Half-wave rectifier, bulk capacitor, a non-isolated
buck to 5 V, then an LDO to 3.3 V for the MCU and the analog. The buck
input rating is at least 60 V. Consider a separate filtered 3.3 V, or
a reference, for the ADC VREF pin so buck ripple stays off the pot
measurement. That part is TBD.

### Why not a linear regulator

Estimated 5 V load: STM32F407 about 100 mA, LAN8720A about 50 mA,
LEDs and optos 50–100 mA. Total 200–250 mA.

The half-wave crest is about 37 V (26 × √2 = 36.8 V). Drop one diode
and the bulk rail sits near 36 V at nominal line. A linear drop from
that rail to 5 V is

P = (V_bulk − 5 V) × I

At 36 V and 200 mA that is 6.2 W. At 36 V and 250 mA it is 7.8 W. At
32 V and 220 mA it is 5.9 W. The working figure is **about 6–7 W**
inside the box, on top of the triacs. That is why the V4 5 V LDO was
already over its package budget, and why a linear-only supply is
rejected.

A buck at 85 % making 5 V at 250 mA dissipates about 0.2 W
(1.25 W × (1/0.85 − 1)). An LDO from 5 V to 3.3 V at 150 mA (MCU plus
PHY) dissipates about 0.3 W. LEDs and optos can stay on 5 V. Regulator
heat is about half a watt.

### Bulk capacitor

The cap has to hold the buck up while the ~5 A brake pulls in and the
secondary sags. It does not have to power the board for the whole
move. Once the sagged crest is high enough for the buck, the
transformer is feeding the rail again.

Assumptions, all unverified until measured on a HAM-IV:

| Item | Value |
|---|---|
| Nominal crest on the cap | 36 V (about 37 V peak, minus a diode) |
| Light-load / high-line crest | up to about 48 V (the V4 "/36VDC" note's upper end, not re-measured) |
| Ride-through window | 100 ms (about six cycles at 60 Hz) |
| Allowed droop | 36 V down to 18 V (ΔV = 18 V). 18 V is still above a 60 V buck's minimum |
| 5 V load during the sag | 250 mA |
| Buck efficiency in the droop | 80 % |
| Average bulk voltage during the droop | 27 V |
| Discharge current | I = (5 × 0.250) / (0.80 × 27) = 58 mA. Use **80 mA** so quiescent current and a worse efficiency are covered |

C = I × Δt / ΔV = 0.080 × 0.100 / 18 = **444 µF**.

Start with **470 µF, 63 V**. 63 V is above the 48 V crest. If a
measurement shows the crest above that, use 80 V or 100 V. Normal
half-wave ripple at 80 mA and 60 Hz is I / (f × C) = 2.8 V, which is
fine on a 36 V rail.

If the sag is deeper or longer (200 ms, down to 12 V), the same
formula gives about 670 µF, so the next step is 1000 µF.

The rectifier sees about two peaks in series (cap voltage plus the
opposite half-cycle), about 74 V, and it charges the bulk cap. Use a
1 A, at least 100 V diode. Not a 1N4148. The part number is TBD.

Half-wave DC in the transformer is the logic current, about 60–80 mA,
drawn from one polarity. The brake is about 5 A. The offset is about
1–2 % of that current, so it is acceptable at this load. Do not
half-wave the motor or the brake.

### Buck candidates

LCSC pages below were read on 2026-10-12. Stock was not checked.
Recheck before ordering. C-numbers that were not on a product page are
TBD.

| Part | Input | Current | LCSC | Note |
|---|---|---|---|---|
| TI LM5164DDAR | 6–100 V operating | 1 A | **C477928** | Preferred. 100 V covers a crest above 60 V. Non-isolated. SMT, SO-8 PowerPAD |
| TI LMR36006BRNXR | 4.2–60 V operating, 66 V transient absolute max | 0.6 A | **C1850367** | Meets the 60 V floor. A crest above 60 V continuous is outside its operating range. Non-isolated |
| MPS MP9486 (fixed-5 V option exists) | 100 V class | 1 A class | **TBD** | No C-number confirmed on an LCSC page |

Rejected for this rail: TI LMR51430 (LCSC C5185863 is a real listing,
4.5–36 V). 36 V is below the crest. MPS MP4560 was not confirmed at
≥ 60 V, so it is not a candidate until that rating is checked.

The 3.3 V LDO part is TBD. It is an LCSC part when chosen (ADR 0013).

## Consequences

Unplugging the Powerpoles removes motor power and logic power
together. There is no separate "tower work" logic supply. The bulk
cap covers a short sag, not an unplugged transformer. ROM DFU needs
the 26 VAC feed so the 3.3 V rail is up. USB VBUS powers only the
upstream side of the ADuM4160.

ADR 0003 still keeps mains and the transformer out of the box. Its
13.8 V logic feed is superseded by this record. The sizing arithmetic
is repeated in `docs/design/hardware-requirements.md` section 3.
