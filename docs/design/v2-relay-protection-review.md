# V2 Rotator Controller: Relay / Motor-Line Protection Review

Scope: the Teensy V2 board (mechanical G5LE relays, CDE/Hy-Gain HAM-IV/T2X, 26 VAC). Review date 2026-10-10.
I checked every capacitor and TVS/varistor on the 26VAC, brake, motor (Left/Right), run-cap and pot nets against the voltages the cap-run motor actually produces.

Legend: **[V]** verified from schematic, PCB or datasheet · **[E]** engineering estimate · **[M]** must be measured on the bench.

## 0. Sources examined

| Version | File | Notes |
|---|---|---|
| **A: 2022 Eagle "v2"** | `wa1hco/Rotator_Controller_Board/Rotator Control Teensy 26VAC v2.sch` (OSHPark Mar/Apr 2022) | This is the board that burned the 0.1 µF caps (see §2). |
| **B: KiCad backup 2025-04-21** | `Rotator-Controller-V2/.../backup-2025-04-21.zip` (sch + pcb) | Already has all of the SMAJ90CA TVSs. |
| **C: KiCad current** | `RotatorController.kicad_sch` | Run cap moved off-board via J4. |

How I checked:
- Nets were extracted with my own S-expression and XML netlister (`/workspace/v2tools/net.py`, `cur.json`, `old.json`).
- I cross-checked version B's PCB pad nets for K1–K3, J2/J3, C1, C10–C12, D3, D14 and D16; they match its schematic. **[V]**
- `RotatorController.csv` (the BOM) is stale and matches neither B nor C exactly.
- **No capacitor in any version carries an MPN, dielectric or voltage field beyond the Value text.** Wherever this review says "200 V", that number comes from the Value string only. The dielectric is unknown and probably X7R. **[unverified]**

## 1. Relay and contact wiring

Omron G5LE-1 terminals per the datasheet: 1 = COM, 3 = NC, 4 = NO, 2/5 = coil. **[V]**

| Ver | Relay | COM | Contact used → net | Function |
|---|---|---|---|---|
| A | K1 | 26VAC | NO ("S") → BRAKE | brake release |
| A | K2 | 26VAC | NO → K3 COM | motor on |
| A | K3 | from K2 | NO → RIGHT, NC ("O") → LEFT | direction |
| B/C | K3 | 26VAC | **pin 4 (NO)** → Brake | brake release |
| B/C | K1 | 26VAC | **pin 3 (NC)** → K2 COM (N31); pin 4 unconnected | motor on |
| B/C | K2 | N31 | pin 4 (NO) → Right, pin 3 (NC) → Left | direction |

**FLAG: K1 in B/C is wired on its NC contact.**
- K3 uses pin 4 (NO) for its switched output, but K1 uses pin 3. Under Omron numbering that is NC, so a de-energized K1 would put 26 VAC on K2 COM and on Left (K2 at rest). The rotator would turn CCW whenever the board is unpowered or the Teensy is in reset, with the brake engaged.
- Firmware `rotator_pins_HCO_board_V3.h` says MotorPin is "high to run motor". That is inconsistent with an NC connection.
- The Eagle board (A) used NO for motor-on.
- Either the KiCad symbol or footprint numbering differs from Omron's, or this is a wiring error. **Check before building C:** the KiCad footprint's pad 3/4 positions vs. the physical relay, or a continuity test on a built B board.

Other topology notes:
- **Good:** the direction relay is an SPDT changeover in every version. Left and Right can never both be driven, so the relays cannot short the run cap. Keep this property in any SSR redesign; the hardware interlock in hardware-requirements.md is there for this reason.
- **Board ground = rotor terminal 1 = transformer return.** All "to GND" parts below therefore sit directly across a motor winding or the brake coil.

## 2. Inventory and diff

### Version A (Eagle 2022): the version that burned caps [V]

All caps are `.1` C1206 with no voltage or dielectric given. The assembly BOM lists 16× ".1 C1206" with no rating.

| Ref | Net (to GND = rotor common) | What it actually sits across |
|---|---|---|
| **C1** | BRAKE | **Brake solenoid** (only a capacitive path when K1 opens) |
| **C3** | RIGHT | CW winding (through limit switch); idle winding when running CCW |
| **C4** | LEFT | CCW winding; idle winding when running CW |
| **C8** | CAP1 | Winding end / run cap; in parallel with C4 through the limit switch |
| **C9** | CAP2 | Same, in parallel with C3 |
| C10 | 26VAC | Transformer secondary |
| C5 | rotor "N/C" pin | Unused conductor |
| C6, C7 | WIPER−/+ | Pot ends |
| C19 | CAP1–CAP2 | 100 µF run cap, KEMET R60EW6100 film (on board) |
| Z1 | 26VAC | 1206 varistor, voltage unspecified |
| Z2, Z3 | WIPER−/+ | 1206 varistors, voltage unspecified |

**There is no TVS or snubber on BRAKE, LEFT, RIGHT or CAP1/2.** The only clamp anywhere near the motor is the unspecified chip varistor Z1, and it sits on the supply side.

"Across relay terminals" in practice means each relay output had a 0.1 µF cap to the transformer return. When the contact opens, that cap ends up in series with the open contact across the line, and it is the only thing absorbing the load's stored energy.

### Version B (2025-04 backup) → Version C (current)

| Ref | Value text | Pkg | Net(s) | B | C | Across a contact? |
|---|---|---|---|---|---|---|
| D3 | SMAJ90CA | SMA | 26VAC–GND | ✓ | ✓ | No (supply) |
| D16 | SMAJ90CA | SMA | Brake–GND | ✓ | ✓ | No; across the brake coil |
| D17 | SMAJ90CA | SMA | Right–GND | ✓ | ✓ | No; across the CW winding |
| D18 | SMAJ90CA | SMA | Left–GND | ✓ | ✓ | No; across the CCW winding |
| D14 / D15 | SMAJ90CA | SMA | Wiper+ / Wiper−–GND | ✓ | ✓ | No (pot ends) |
| C1 | 0.1 200V | 1206 | 26VAC–GND | ✓ | ✓ | No |
| C11 / C12 | 0.1 200V | 1206 | Wiper+ / Wiper−–GND | ✓ | ✓ | No |
| C2–C9 | 0.1 2% | 1206 | Twin-T 60 Hz notch (pot ADC path) | ✓ | ✓ | No |
| C10 (B) | 100 µF MKS4 film | THT 37.5 mm | Cap1–Cap2 (run cap on board) | ✓ | — | — |
| J4 (C) | "Motor Cap" | **2.54 mm pin header** | Cap1/Cap2 → external run cap | — | ✓ | — |
| C10 (C) | 0.1 | 1206 | +5V | — | ✓ | logic |
| C13 / C14 (C) | 0.1 / **"120u" in 1206** | 1206 | 5V_Serial (USB VBUS) | — | ✓ | logic |
| D1, D9 (C) / BAS40-04 (B) | ADC clamps | SOT-23 | after notch | ✓ | ✓ | logic |

Diff summary:
- Every TVS was already present in B; it is not a C-only addition.
- A → B/C removed the caps on BRAKE, LEFT, RIGHT and CAP1/2 (A's C1, C3, C4, C8, C9). It added SMAJ90CA D16/D17/D18 on those nets and D3 on 26VAC.
- B → C moved the run cap off-board (C10 film → J4 header), changed the connectors (2-pin + 8-pin Mate-N-Lok → one 2×5 J2) and swapped the ADC clamps.
- **No capacitor sits on a relay output or contact in B or C.** So "fewer 0.1 µF caps" is accurate, and the remaining ones are not in the failure path.

## 3. Voltages the parts must survive

| Condition | Peak | Basis |
|---|---|---|
| 26 VAC nominal | 36.8 V | √2 × 26 **[V]** |
| +10% high line | 40.4 V | **[E]** |
| Light load / no-load transformer rise (+10–20%) | 44–48 V | **[E][M]**: small 10%-duty transformers regulate poorly |
| **Idle winding to common** (D17/D18 node, A's C3/C4/C8/C9) | ≈37 V balanced, up to ~70–90 V at light load or stall-transition | **[E][M]**: the aux winding of a cap-run motor rises above line off the balance point |
| **Across the open K2 contact** | = run-cap voltage ≈ √2 × line in balance ≈ 52 Vpk; higher when unbalanced | **[E]** |
| Brake coil kick on open, unclamped | I·√(L/C) | see below |

Why the open K2 contact voltage equals the run-cap voltage: the HAM-IV run cap connects the two winding ends. One end is at hot (the driven terminal) and the other is the idle terminal, which is the open contact's other side. **[V] topology, [E] magnitude.**

Kick estimates **[E]; all inductances need measurement [M]:**
- **Brake:** 24 VAC / 5 A with R ≈ 0.75 Ω gives X ≈ 4.7 Ω, so L ≈ 12 mH (plunger in; varies). Peak current ≈ 7 A, so ½LI² ≈ 0.3 J.
  - Version A, with only C1 = 0.1 µF: V ≈ 7 × √(0.012/1e-7) ≈ **2.4 kV** ideal. In practice the contact arc clips this, but it still lands at hundreds of volts, repeated on every bounce.
  - **This alone explains the burned caps: almost certainly A's C1 on BRAKE, then C3/C4/C8/C9.**
- **Motor:** when K1 opens, the winding current has a low-impedance loop through the 100–140 µF run cap and the other winding, so the motor kick is much softer than the brake kick. A's 0.1 µF caps still took the arc's fast edges plus the continuous idle-winding voltage. Most 1206 0.1 µF MLCCs are 25–50 V parts, so ~52–90 Vpk continuous on C3/C4/C8/C9 exceeds their rating with no transient needed at all. **[E]: the actual parts fitted are unknown.**
- **Reversal:** if K2 changes over while K1 is closed, a run cap charged to ~±52 V is slammed against the line. The step reaches ~90 V into whatever capacitance sits on the nodes, and an MLCC can crack under it. **[E]**

## 4. TVS evaluation (B/C)

Datasheet values **[V]**:
- **SMAJ90CA** (Littelfuse): bidirectional, VRWM 90 V, VBR 100–111 V @ 1 mA, VC 146 V @ IPP 2.7 A (10/1000 µs), 400 W, rep-rate 0.01%.
- **SMCJ90CA:** same voltages, 1500 W, IPP 10.3–10.6 A.
- **SMCJ58CA:** VRWM 58 V, VBR 64.4–71.2 V, VC 93.6 V @ 16.5 A, 1500 W.

| Ref | Steady-state margin | Transient duty | Verdict |
|---|---|---|---|
| **D3** (26VAC) | 48 Vpk worst vs VBR(min) 100 V: large margin, never conducts on line | Only line surges | **Adequate.** SMCJ58CA would clamp lower and absorb ~4× the energy, which protects C1 better. Optional. |
| **D16** (Brake) | Brake node only ever sees line (≤48 Vpk), so 90 V standoff is more than needed | Brake kick up to ~7 A / ~0.3 J **[E]**, vs 2.7 A IPP and ~0.55 J single 10/1000 µs pulse; repeats on every stop and bounce, against a 0.01% duty rating | **Marginal / overstressed in worst case.** Change to **SMCJ58CA**: clamps at ≤94 V, which also halves the stress on K3's contact, and is rated 16 A. Better still, add an RC snubber or MOV (§6). |
| **D17 / D18** (Right / Left) | Must stay off at the idle-winding peak. Estimated 37–90 V vs VBR(min) 100 V: **probably OK but thin if the light-load idle peak approaches 90 V** | Motor kick is partly absorbed by the run-cap loop; SMA energy is likely adequate **[E]** | **Adequate pending measurement [M].** Scope Left/Right to GND at light load. If the idle peak exceeds ~80 V, go to SMCJ100CA/110CA (VBR min 111/122 V). Otherwise upgrade to **SMCJ90CA** for energy margin. Do **not** lower these to 58 V: they would then conduct on the idle winding every cycle. |
| **D14 / D15** (pot ends) | Fine; never conduct normally | Only coupled or fault energy | **Harmless but ineffective for the ADC.** A 146 V clamp does not protect a 3.3 V input; D1/D9 plus the series R do. Keep them as cable-fault and lightning protection. |

All parts are bidirectional (CA), which is correct for AC. **[V]**

The 0.01% rep-rate rating means these SMA parts are rated for occasional surges, not for absorbing a relay kick every operation. That is why the snubber in §6 should take the repetitive energy and the TVS should become a backstop.

## 5. Capacitor evaluation (B/C)

| Ref | Rating vs stress | Verdict |
|---|---|---|
| **C1** 0.1 µF "200V" 1206, 26VAC–GND | ≤48 Vpk normally; D3 limits a transient to ≤146 V @ 2.7 A. 200 V clears that, but only if the fitted part really is 200 V. | **Adequate if a 200 V part is fitted [unverified].** Risks: X7R DC-bias loss is irrelevant here, but 1206 MLCCs crack from board flex near the heavy Mate-N-Lok and from surge. Prefer a 0.1 µF X2 275 VAC film, or a 1206/1210 Y2/X1 safety-rated MLCC. |
| **C11 / C12** 0.1 µF "200V", pot ends | Pot lines only see motor voltage under a cable fault (D14/D15 cap that at ~146 V) | **Adequate.** |
| C2–C9 0.1 µF 2% | Behind the series resistors | Fine; not in the motor path. |
| Run cap (external via **J4**) | Carries ≈ V_cap·ωC ≈ 37 V × 377 × 130 µF ≈ **1.8 A rms** continuously, more at stall **[E]** | **J4 is underrated.** A 2.54 mm header/socket is ~3 A at best and has no latch. A fretting or loose pin opens the run cap (the motor won't start, or hums) or arcs. Use a 2-pin Mate-N-Lok, a screw terminal ≥5 A, or keep the cap on board as in B. |
| C14 "120u" in 1206 on 5V_Serial | Value/footprint mismatch. If J1 is an upstream USB device port, >10 µF exceeds USB inrush limits. | **Out of scope; fix the value/footprint.** |

No remaining cap is across a relay contact or a motor/brake node, so the original failure mechanism is gone in B/C. **[V]**

## 6. Recommended changes (for a V2 respin; the SSR design carries these forward)

1. **Resolve the K1 pin 3/4 question first** (§1). Wire motor-on to NO so an unpowered or reset board cannot drive the motor.
2. **Brake (D16 node):** replace SMAJ90CA with **SMCJ58CA**.
   - Add an RC snubber across the brake coil (Brake–GND, i.e. J2.2–J2.6/10): **47–100 Ω, 1–2 W + 0.1–0.22 µF X2 275 VAC film** (e.g. KEMET R46/R463 or Vishay MKP X2 class; part selection **[unverified]**).
   - Fully absorbing 0.3 J in a cap would need ~60 µF, so the snubber damps the ring and the TVS/contact take the remainder.
   - Optionally add a 14 mm MOV rated 40–50 VAC in parallel for energy. **[E]: tune on the bench.**
3. **Motor (D17/D18):**
   - Measure the idle peak, then use **SMCJ90CA**, or SMCJ100CA/110CA if the idle peak is >80 V.
   - Add one RC snubber **across K1's contact** (26VAC ↔ N31), or across each motor terminal to common: 47–100 Ω + 0.1 µF X2 film.
   - Note an X2 snubber across an open contact leaks ~3–4 mA at 26 V/60 Hz. That is harmless to the motor, but put it across the motor-on contact (K1) rather than the direction contacts.
4. **Firmware sequencing:** never change K2 under load. Use the order K1 off → wait ≥40 ms (run cap discharges through the windings) → K2 change → K1 on. Release the brake before motor-on and set it after motor-off plus a coast delay. Verify this against the current K3NG/HCO code. **[unverified]**
5. **RF bypass:**
   - Do not put caps from relay outputs to the AC return.
   - If RF on the rotor cable is a problem, use **1–4.7 nF Y2-rated** caps from each rotor line to **chassis** at J2, plus a ferrite or common-mode choke on the cable.
   - Chassis must be a separate copper area bonded to the enclosure, not GND/AC return.
6. **Run-cap connector:** replace J4's 2.54 mm header with a ≥5 A latched connector, or return the run cap to the board.
7. **Grounding:** GND (rotor common/AC return) is tied to the USB shield and ground in C (J1). The PC ground then becomes the transformer return reference, so ground-loop current and any transformer fault reach the PC. Add USB isolation (ADuM4160/ADuM3160, already chosen in the V4 branch) or isolate the 26 VAC side.
8. **BOM hygiene:** put MPN, voltage and dielectric fields on every cap and TVS. The current files cannot prove what was fitted.

## 7. Bench measurements to close the [M] items

Use a scope with a differential or isolated probe, referenced to rotor terminal 1.
1. Left and Right to GND while running each direction, at light load (rotator unloaded on the bench) and loaded: gives the idle-winding peak.
2. Voltage across the run cap.
3. Brake–GND at K3 opening, with and without a snubber: gives the kick peak and duration (current probe on the brake lead for energy).
4. K1 contact voltage at opening.
5. Transformer secondary no-load vs. motor+brake load.

Use the results to pick the D17/D18 voltage and to tune the snubber R/C.

## 8. Unverified items (summary)

- Actual fitted cap voltage and dielectric (all versions).
- Version A's cap voltage. Its 1206 caps were probably 50 V class, but that is unverified.
- Z1–Z3 varistor voltage.
- Brake and winding inductance.
- Idle-winding peak.
- Transformer regulation.
- KiCad G5LE symbol/footprint pad 3/4 mapping vs. the physical relay.
- Firmware relay sequencing.
- J1's USB role.
- Specific X2 snubber MPNs.
