# Rotor drive sheet

Azimuth, AC version. The Drive MCU is `drive_mcu`. The pot front end and the VIN_RECT warning are `analog_input`. The power sheet is still later. Pin assignment is in `docs/design/drive-controller.md`.

Nets on this sheet join by name. A label on a pin is the connection. Hierarchical labels are the ones that leave the sheet. `+5V` is a hierarchical label with a power flag, because that supply is on the power sheet, which is not drawn yet. `+3V3` is a hierarchical label. Its power flag is on this sheet, and the Drive sheets share the net. Logic ground is the `GNDPWR` power symbol, and it is flagged too. On the root, `+5V` and `AC_HOT` stay no-connects until the power sheet exists. The other rotor pins are wired to `drive_mcu` and `analog_input`.

Logic ground is `ROTOR_RETURN`, and that hierarchical label is tied to the `GNDPWR` power symbol, so they are one net. CDE terminal 1 lands on it (ADR 0018). Do not put a current shunt in it. The pot measurement uses it as the ADC reference. The parent-sheet pin `ROTOR_RETURN` is that same net, and the root carries it to the Drive sheets.

## Rotor connector

`J1` is a Phoenix MSTBA 2,5/8-G-5,08 header (library order code 1757307, 12 A). The mating plug is the cable half and is not on the board. The header is inside the box. The cable enters through the rear plate and lands here (ADR 0011), so `J1` has no `Panel` fields. The 8 A MC 1,5 header is too close to the motor current; the 12 A MSTBA is the one on the sheet.

CDE HAM-IV / HAM-M / CD-45, terminals 1 to 8, matching the catalog drawing and the text note on the V4 sheet. V4's `J3` is a 10-pin Mate-N-Lok. Those pin numbers are not these terminal numbers.

| J1 | CDE | Role on this sheet |
| --- | --- | --- |
| 1 | common | `GNDPWR`. Motor, brake, and pot wiper. |
| 2 | brake | `BRK_OUT`. Solenoid. Energized releases the wedge. Off, the wedge is engaged. |
| 3 | pot end + | `AZ_POT_3` |
| 4 | winding / cap | `TB4`. Run cap for a CDE rotor. |
| 5 | CW | `CW_OUT`. Through the right limit switch to terminal 8. |
| 6 | CCW | `CCW_OUT`. Through the left limit switch to terminal 4. |
| 7 | pot end − | `AZ_POT_7` |
| 8 | winding / cap | `TB8`. |

Right is CW. Left is CCW. The motor run cap on a CDE rotor is across terminals 4 and 8.

### Yaesu and the other AC rotors

G-450 class, cap on the controller: land motor CW (Yaesu 5) on J1-5, motor CCW (Yaesu 4) on J1-6, motor common (Yaesu 6) and pot ground (Yaesu 3) on J1-1, pot REF (Yaesu 1) on J1-3, pot wiper (Yaesu 2) on J1-7. Open `SJ1` and `SJ2`. Close `SJ3` and `SJ4`. The cap bank then sits across the two drive ends.

G-5500 and HDR-300 keep the cap in the rotor. Leave `SJ1` through `SJ4` open and do not fit `C1` or `C2`. A second cap in parallel with the internal one is the wrong build.

HDR-300 is not a 1:1 map onto this 8-pin block (catalog: 1 CCW, 2 CW, 3 common, 4 brake, 8 pot REF, 9 wiper, 10 pot ground). It needs a cable adapter. The board still supports it by omitting the cap.

`SJ1` and `SJ2` are closed solder jumpers (CDE, the default). `SJ3` and `SJ4` are open. Closing both pairs puts the cap on 4-8 and on the drive ends at the same time. Do not do that.

## Motor run caps

`C1` and `C2` are in parallel on `CAP_A` / `CAP_B`. Pad 1 to pad 1, pad 2 to pad 2, the same pairing as the outline.

| Ref | Part | Footprint | Order |
| --- | --- | --- | --- |
| C1 | KEMET R60EW61005000K, 100 µF, 100 VDC / 63 VAC, flat | `C_Rect_KEMET_R60_P37.5_L41.5_W20_H40_Flat` | Mouser not found. Digi-Key 399-13010-ND. |
| C2 | TDK B32526T1336K000, 33 µF, upright | `C_Rect_TDK_B32526T_P37.5_L41.5_W24_H15_Upright` | Mouser 871-B32526T1336K000, unverified (ADR 0016). |

Both footprints are the ones from the Hammond outline: lead pitch 37.5 mm, hole 1.3 mm, pad 2.5 mm. The KEMET footprint also has the two non-plated 3.2 mm cable-tie holes. Heights 20.3 mm and 15.0 mm against the 22.9 mm limit. Both parts are fitted for a CDE build and are DNP, by the `Populate` field, when the rotor already has the cap. They are not marked `dnp` in KiCad, because the CDE build wants them stuffed.

## Triac channels

Three copies: CW (`Q5`), CCW (`Q6`), brake (`Q7`). Each one is:

`+5V` — 180 Ω — red LED — MOC3023SM LED — 2N7002 — `GNDPWR`

MOC pin 6 — 100 Ω — triac gate. Gate — 1 kΩ — MT1. MT2 is `AC_BUS`. MT1 is the load (`CW_OUT`, `CCW_OUT`, or `BRK_OUT`). Snubber 68 Ω + 0.1 µF X2 from `AC_BUS` to the load. LTV-814 across the triac for stuck-on sense.

The triacs are BTA16-600SWRG, insulated tab, vertical TO-220, on the 10 × 50 mm bar (ADR 0004, ADR 0010). The footprint is the library vertical TO-220. Leads land about 2.5 mm in front of the bar face, board x about 34.4, 12.7 mm pitch. Do not lay them flat. The Mouser number `511-BTA16-600SW` is from a Findchips distributor listing, not a page opened on mouser.com.

MOC3023SM is onsemi, LCSC C899792, random phase, IFT 5 mA max. SMT wide DIP. Do not use pin 5, and do not substitute the UMW clone. Stock on that C-number was thin when the page was checked. A through-hole MOC3023M from Mouser is the fallback and is not on this sheet.

The opto LED is held on for the whole move. Do not pulse it. A zero-cross opto is the wrong part (ADR 0004).

### LED resistor, about 10 mA from 5 V

Series drop is a red LED plus the MOC3023 LED. Assumed forward voltages 2.0 V and 1.3 V.

`5.0 − 2.0 − 1.3 = 1.7 V`. `1.7 V / 10 mA = 170 Ω`. The sheet uses 180 Ω.

`1.7 / 180 = 9.4 mA`. With the forward voltages spread from about 1.8+1.15 to 2.2+1.5, the current is about 7 to 11 mA. That is above the 5 mA IFT maximum and far below the 60 mA LED absolute maximum. Dissipation in the 180 Ω is about 16 mW. 0603 is enough.

### Gate resistor and snubber

Values are the ones in `docs/design/v4-discrete-triac-change.md`, not new guesses.

Gate 100 Ω. If the opto fires at the crest of the 26 VAC secondary, about 37 V peak, the pulse into the gate is roughly `(37 − 3) / 100 = 340 mA`. The MOC3023 non-repetitive surge rating is 1 A. The 1 kΩ from gate to MT1 diverts about `1.3 V / 1 kΩ = 1.3 mA`, so it does not steal the trigger (IGT of the BTA16-600SW is 10 mA max) and it does hold the gate off when the opto is dark.

Snubber 68 Ω in series with 0.1 µF, across MT2-MT1. Time constant `68 × 0.1 µF = 6.8 µs`. At 60 Hz the capacitor alone draws about `2π × 60 × 0.1 µF × 26 V ≈ 1 mA`. Energy in the capacitor at 37 V is `½ × 0.1 µF × 37² ≈ 68 µJ`, which the 68 Ω absorbs at turn-off. The capacitor is an X2 film part, 15 mm pitch class. It is not an MLCC. The V2 ceramics failed here. The exact Mouser MPN is still open.

## Hardware interlock

All of this is 3.3 V logic. There is no AND gate and no supervisor on this sheet. Direction exclusion and the dead time of at least 500 ms are the Drive's job (ADR 0020). Startup, brownout, and the option bytes are ADR 0021 (Accepted). The voltages and the register values are cited there. Before and after plots of the supervisor removal are `docs/design/img/rotor-drive-supervisor-before.png` and `docs/design/img/rotor-drive-supervisor-after.png`.

CW follows `AZ_CW_EN`. CCW follows `AZ_CCW_EN`. The brake follows `AZ_BRAKE_EN`. Each of those nets is a Drive pin into the gate of Q2, Q3, or Q4, the 2N7002 that switches the MOC3023 LED. The LED current stays on +5 V through 180 Ω. The Drive pin drives the FET gate, about 33 µA into the 100 kΩ pulldown at 3.3 V.

`R2G`, `R3G`, and `R4G` are 100 kΩ from those gates to `GNDPWR`. `R50`, `R51`, and `R52` are another 100 kΩ on `AZ_CW_EN`, `AZ_CCW_EN`, and `AZ_BRAKE_EN`. A high-Z pin, which is how a non-debug GPIO comes out of reset, leaves the opto FET off.

The relay FET follows `ARM_EN`. `R53` and `R40` both pulldown that net, 100 kΩ to `GNDPWR`. Low or high-Z leaves Q1 off, so K1 stays open and the brake stays engaged.

The 74LVC14, the direction AND gates, the hold network, the ARM_OK AND gates (U3, U6, U9, U10 and C3, C6, C9, C10), and the TPS3823 clamp (U1, C21, R41, R42, Q8, Q9, R54, R55, R56) are not on this sheet. The Drive keeps both direction outputs off for at least 500 ms before a reversal.

### Brake defaults to engaged

`AZ_BRAKE_EN` high means release. Low, or a high-Z pin with `R4G` and `R52`, leaves the solenoid open and the wedge engaged. A hardware IWDG reset returns the pin to analog and the pulldown re-engages the wedge. STOP is a software command from the Station. While the core is running it drops this gate. A stuck core is the hardware IWDG.

## ARM relay

`K1` is an Omron G5LE-1A4-DC5, SPST-NO, in series with the 26 VAC hot after the fuse. The symbol on the sheet is the SPDT drawing, because that is the KiCad symbol and the matching footprint. On the SPST-NO part, pin 4 (NC) is absent. Confirm this against the Omron bottom-view figure before stuffing:

| Pin | Function | Net |
| --- | --- | --- |
| 1 | COM, moving contact | `AC_FUSED` |
| 3 | NO, the contact that remains on the SPST part | `AC_BUS` |
| 2 and 5 | coil | `N_COIL` and `+5V` |
| 4 | NC, not present on G5LE-1A | no-connect |

Coil off, the rotator is dark. A swapped NO/NC would run the motor whenever the controller is unpowered. That was a V2 bug. Normal motion does not make or break load current in this contact. The triacs do that. The relay opens on a fault.

Datasheet ratings used here, from the Omron G5LE sheet: standard type, 10 A at 120 VAC general purpose, 5 A at 120 VAC inductive (cos φ = 0.4). Coil 5 V, 62.5 Ω, 80 mA, 400 mW. Height 19 mm, under the 22.9 mm limit. Simultaneous motor plus brake is about 7.3 A intermittent, which is over the 5 A inductive rating. The high-capacity G5LE-1A-E (16 A NO) is the part to look at if that overlap is real. The accepted design note specified G5LE-1A4-DC5, so this sheet does not silently change it. Mouser `653-G5LE-1A4-DC5` was seen on distributor listings, not confirmed on a live Mouser page.

The coil transistor is an AO3400A (LCSC C20917, AOS, SOT-23, about 5.7 A, 48 mΩ at 2.5 V). The symbol is the 2N7002 drawing because the pinout is the same G-S-D. A 2N7002 at 3.3 V gate is a poor switch for 80 mA. `Q2`, `Q3`, and `Q4` (LCSC C8545, JSCJ) only switch the opto LEDs. Flyback is a 1N4148W across the coil, cathode at +5 V. Gate pulldown 100 kΩ on `ARM_EN` (R40 and R53).

## Outputs against the supply

The cited thresholds are in ADR 0021. On this sheet the behavior is:

| Supply | Triac gates (Q2 Q3 Q4) | Relay (Q1) | Brake wedge | K1 contact |
| --- | --- | --- | --- | --- |
| VDD below POR / VBOR0, pin high-Z, +5 V may still be up. Pin state is not guaranteed. | Pulldown holds the 2N7002 off. VGS(th) minimum is 1 V. | R40 and R53 hold Q1 off while `ARM_EN` is high-Z. Q1's VGS(th) minimum is 0.65 V, so a pin that is not high-Z can begin to conduct above that. | Engaged if the brake triac is off. | Open while the gate is high-Z. |
| Gate net driven high by something other than the MCU (a short, or a bootloader pin). | The 100 kΩ pulldown loses. The triac can fire. | The same short can close K1. | Follows the brake gate. | Can close. |
| VDD under VBOR4 (about 2.8 V). BOR holds reset. Pins are analog. | Pulldowns hold the FETs off. | Pulldowns hold Q1 off. | Engaged. | Open. |
| VDD up, core running, option bytes and IWDG not yet checked. | Still the reset pulldowns until firmware drives them. Firmware pets the IWDG inside the power-on window, about 0.5 s, then shortens it to about 100 ms. | Same. | Engaged. | Open until firmware raises `ARM_EN`. |
| Running, VIN_RECT early warning. | Firmware drives CW and CCW low and the brake gate low. | Firmware drives `ARM_EN` low. | Engaged. | Opens. |
| IWDG timeout. A stuck Drive. | Pins return to analog. Pulldowns hold the FETs off. | Same. | Engaged. | Open. |
| STOP command from the Station, core running. | Firmware drives the direction gates low and the brake gate low. | Firmware drives `ARM_EN` low. | Engaged. | Open. |

A divided VIN_RECT into a Drive comparator is the early warning. It is not drawn on this sheet. The PVD watches the 3.3 V rail. The VIN_RECT warning is the comparator.

## 26 VAC inlet

Grey and black Powerpoles on a pigtail, the V2 keying, so the connector cannot be mistaken for a red/black 12 V pair (ADR 0018). Polarity does not matter electrically. Housings are 15 A contacts, 15/30/45 series. Mouser numbers are still TBD. `J2` is the board end of the pigtail, a 2-position Phoenix MKDS screw terminal. Its `Panel` / `PanelZ` / `PanelCutout` fields describe the gland (rear, z = 11.00, circle 16.3), not a hole under the terminal. `MK1` is a no-pad marker, `Panel_Gland_M16`, so the machining script can draw the gland wherever the marker is placed at layout, without drilling the board. The Powerpole bracket cutout is still TBD. Do not drill a bracket from the gland circle.

`AC_HOT` — fuse `F1` — `AC_FUSED`. The fuse is a T6.3 A 250 V slow-blow 5×20 cartridge in Keystone 3512 class clips, ahead of the MOV and the relay. Nameplate motor plus brake is about 7.3 A and intermittent. If the brake inrush opens T6.3 A, the next step is T8 A, which is the number already in the triac-change note. Clip and cartridge Mouser numbers are TBD.

`RV1` is across `AC_FUSED` to `GNDPWR`, after the fuse. It is a 35 VAC continuous disc, for example a 14D560K (56 V varistor, about 35 VAC working), not a mains MOV. Footprint is the nearest library 15.5 mm disc. Mouser MPN TBD.

`D1` is a half-wave diode from `AC_FUSED` to `VIN_RECT`, before the ARM contact, so the logic stays up when the relay opens. Crest is `26 × √2 ≈ 37 V`. Reverse voltage is about two crests, 74 V, so the diode is a 1 A, at least 200 V SMA (S1M or US1M), not a 1N4148. LCSC number TBD. The bulk capacitor and the buck are on the power sheet. Do not half-wave the motor or the brake.

`D2` is an SMAJ90CA from `AC_FUSED` to `GNDPWR`, after the fuse and before the relay. `D1`, the power-supply tap, is on that same fused node, so the logic supply and the clamp both see the line while the relay is open.

## Protection

FOSAN SMAJ90CA, LCSC C5353147, SMA, 90 V standoff, 146 V clamp. This is not the Littelfuse part. JSCJ also lists an SMAJ90CA under a different C-number; the sheet uses C5353147.

| Ref | Where |
| --- | --- |
| D3 | `CW_OUT` to `GNDPWR` |
| D4 | `CCW_OUT` to `GNDPWR` |
| D5 | `BRK_OUT` to `GNDPWR` |
| D2 | `AC_FUSED` to `GNDPWR` |
| D6, D7 | pot ends `AZ_POT_3` and `AZ_POT_7` |

The line crest, about 37 V and not more than about 48 V with a high secondary, is under the 90 V standoff, so the parts do not conduct on a normal cycle. `D6` and `D7` are cable-fault clamps. They do not protect a 3.3 V ADC. That clamp belongs on the processor sheet.

The chassis RF capacitor and TVS from `GNDPWR` are ADR 0018 and are not on this sheet.

## Zero-cross sense

`U17`, LITEON LTV-814S-TA1, LCSC C125118, across `AC_FUSED` (before the relay, so the sense still works with the ARM open). Two 7.5 kΩ 1206 in series, 15 kΩ total. The LTV-814 input is bidirectional, so both half-cycles conduct and a 60 Hz line produces pulses at 120 Hz.

Peak LED current `37 V / 15 kΩ ≈ 2.5 mA`. Dissipation `(26 V)² / 15 kΩ ≈ 45 mW` for the pair, about 22 mW each. Emitter at `GNDPWR`, collector `ZC_SENSE` with 10 kΩ to 3.3 V. `ZC_SENSE` is high near the zero crossing and low while the opto is lit. The edge the firmware wants is the high gap, not a low pulse.

The SMDIP-4_W7.62 land is the library guess for the Lite-On gullwing. Check it against the Lite-On drawing before the board is ordered.

## Current sense

A shunt in `GNDPWR` would move the pot reference (ADR 0018). The sense is a current transformer on the fused hot instead.

`TR1` is a Zeming ZMCT103C, 1000:1, through-hole. One turn of `AC_FUSED` goes through the bore. That primary is not a pad. LCSC C94571 is the catalog page that was checked. The part is through-hole, so the symbol has a Mouser field (TBD) and no LCSC field. JLCPCB would otherwise try to place it.

Burden `R20` is 100 Ω, 0805. At the 5 A rating, secondary current is 5 mA and the burden voltage is `5 mA × 100 Ω = 0.50 V rms`, 0.71 V peak.

Bias is 10 kΩ / 10 kΩ from 3.3 V, 1.65 V, with 100 nF to `GNDPWR`. The ADC net `I_SENSE` is the other end of the secondary through 1 kΩ. At 5 A the pin sits at `1.65 ± 0.71 V`. Two BAT54s clamp it to 3.3 V and to `GNDPWR`.

Nameplate motor plus brake, about 7.3 A, is past the 5 A rating. If the CT stayed linear, 7.3 A would be 0.73 V rms and 1.03 V peak, still inside 0 to 3.3 V (`1.65 ± 1.03`). Saturation, not the ADC window, is the open question. Stall detection can use a lower threshold than the overlap current. The overlap is short.

## Hierarchical labels

| Label | Direction | Meaning |
| --- | --- | --- |
| `+5V`, `+3V3` | in | From the power sheet. |
| `ROTOR_RETURN` | both | Logic ground, tied to `GNDPWR`. CDE terminal 1. Parent-sheet pin. |
| `AC_HOT` | both | Powerpole hot, before the fuse. |
| `VIN_RECT` | out | Half-wave raw dc into the power sheet. |
| `AZ_CW_EN`, `AZ_CCW_EN`, `AZ_BRAKE_EN`, `ARM_EN` | in | MCU requests. Brake high releases. `ARM_EN` is the relay FET gate. |
| `ZC_SENSE` | out | High in the zero-cross gap. |
| `I_SENSE` | out | CT, biased at 1.65 V. |
| `AZ_CW_SNS`, `AZ_CCW_SNS`, `AZ_BRAKE_SNS` | out | Low while that triac is on. Stuck-on is armed, not gated, and no pulse for 20 ms. |
| `AZ_POT_3`, `AZ_POT_7` | both | Pot ends. The wiper is terminal 1, on `GNDPWR`. |

## Bill of materials

LCSC numbers were checked on the product page on 2026-10-12. Stock is not a promise. "TBD" means the number was not verified and must not be invented. Through-hole parts are Mouser. SMT parts are LCSC.

### SMT, LCSC verified

| Qty | Ref | MPN | LCSC |
| --- | --- | --- | --- |
| 3 | Q2 Q3 Q4 | JSCJ 2N7002, SOT-23 | C8545 |
| 1 | Q1 | AOS AO3400A, SOT-23 | C20917 |
| 3 | U11 U12 U13 | onsemi MOC3023SM | C899792 |
| 4 | U14 U15 U16 U17 | LITEON LTV-814S-TA1 | C125118 |
| 6 | D2–D7 | FOSAN SMAJ90CA (not Littelfuse) | C5353147 |

### SMT, LCSC still TBD

No C-number is filled in for these. Do not guess one.

| Qty | Value | Size | Refs |
| --- | --- | --- | --- |
| 3 | 180 Ω | 0603 | R70 R80 R90 |
| 1 | 100 Ω | 0805 | R20 burden |
| 3 | 100 Ω | 0603 | R71 R81 R91 |
| 4 | 1 kΩ | 0603 | R23 R72 R82 R92 |
| 8 | 7.5 kΩ | 1206 | R30 R31 R74 R75 R84 R85 R94 R95 |
| 3 | 68 Ω | 1206 | R73 R83 R93 |
| 6 | 10 kΩ | 0603 | R21 R22 R32 R76 R86 R96 |
| 8 | 100 kΩ | 0603 | R40 R50 R51 R52 R53 R2G R3G R4G |
| 3 | 100 nF | 0603 | C20 C22 C23 |
| 3 | red LED | 0603 | D70 D71 D72 |
| 2 | BAT54 | SOD-123 | D20 D21 |
| 1 | 1N4148W | SOD-123 | D8 |
| 1 | S1M or US1M, ≥ 200 V | SMA | D1 |

### Through-hole, Mouser

| Qty | Ref | MPN | Mouser | Status |
| --- | --- | --- | --- | --- |
| 3 | Q5 Q6 Q7 | ST BTA16-600SWRG | 511-BTA16-600SW | Findchips listing, not a live Mouser page |
| 1 | K1 | Omron G5LE-1A4-DC5 | 653-G5LE-1A4-DC5 | Distributor listings, not a live Mouser page |
| 1 | C1 | KEMET R60EW61005000K | TBD | Digi-Key 399-13010-ND |
| 1 | C2 | TDK B32526T1336K000 | 871-B32526T1336K000 | Unverified, ADR 0016 |
| 1 | J1 | Phoenix 1757307 | TBD | Library order code, 12 A |
| 1 | J2 | pigtail landing, MKDS 2-pos | TBD | Powerpole housings also TBD |
| 1 | F1 | T6.3 A 250 V 5×20, Keystone 3512 class clips | TBD | |
| 1 | RV1 | 35 VAC disc, 14D560K class | TBD | |
| 3 | C70 C71 C72 | 0.1 µF X2, 15 mm, 275 VAC class | TBD | |
| 1 | TR1 | Zeming ZMCT103C | TBD | TH. LCSC page C94571. No LCSC field on the symbol. |
| 4 | SJ1–SJ4 | solder jumpers, copper | none | Not an orderable part |

`MK1` is not in the bill of materials.

## Open questions

1. Powerpole housing and contact Mouser numbers, and the rear-plate bracket cutout. The gland is the circle 16.3 at PanelZ 11.00. Do not derive a bracket hole from that circle.
2. Phoenix 1757307 Mouser number, and the mating MSTB plug MPN for the cable.
3. KEMET R60EW61005000K has no Mouser number yet. TDK `871-B32526T1336K000` is unverified.
4. Fuse clip and cartridge Mouser numbers. Whether T6.3 A survives brake inrush, or the fuse should be T8 A.
5. MOV MPN. X2 0.1 µF MPN. S1M / US1M, BAT54, 1N4148W, red LED, and the passives, all LCSC TBD.
6. MOC3023SM land (SMDIP-6_W9.53) against onsemi 646BY, and LTV-814S against SMDIP-4_W7.62. MOC3023SM stock was thin; a through-hole MOC3023M from Mouser may be the real buy.
7. SMAJ90CA on the sheet is FOSAN C5353147, not Littelfuse.
8. ZMCT103C is through-hole and was confirmed on LCSC, not on Mouser. The 5 A rating against a 7.3 A motor-plus-brake overlap, and whether stall detection still works if the CT saturates.
9. G5LE-1A4 inductive rating is 5 A. The overlap is about 7.3 A. G5LE-1A-E is the 16 A alternative. This sheet keeps the part the design note named. Confirm pin 3 is NO on the figure before stuffing.
10. HDR-300 cable adapter. Elevation is a second copy of this sheet, not drawn.
11. Chassis RF capacitor and TVS from `GNDPWR` (ADR 0018) still belong on a later sheet. The pot clamp is on `analog_input`.
12. The VIN_RECT divider is on `analog_input` (39.0 kΩ over 1.00 kΩ, no capacitor, into PA1). STOP is a Station command. The Drive has no STOP pin. A stuck Drive is the hardware IWDG. Removing power is the power switch or the AC feed. TR1's conditioning stays on this sheet. Moving it needs approval.
13. Vertical TO-220 footprint versus the bar lead row is a placement note. The footprint itself is the library part, not a custom lead bend.
