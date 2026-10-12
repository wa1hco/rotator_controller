# V4 Board: Replace CPC1966 SSRs with Discrete Opto-Triac + Power-Triac Channels

Change plan for the user's V4 board: KiCad "CDE Rotor Controller V4.1, WA1HCO (c) 2025". The drawing this note was written against uses an STM32F405 and an ADuM3160. The accepted MCU is now an STM32F407VGT6 with a LAN8720A (`mcu-ethernet-lcsc.md`); this note does not redraw that MCU.
Written 2026-10-10. No user files were modified; all work was done on copies in `/workspace/v4x/` and `/workspace/v2tools/`.

Legend:
- **[V]** verified from the board file or a datasheet
- **[E]** engineering estimate
- **[M]** measure on the bench
- **[U]** unverified (check before ordering)

---

## 0. Which files were used

| File | Date / size | Result |
|---|---|---|
| `/workspace/v4/Rotator-Controller-V4.kicad_sch` | Sep 30 2025, 376,824 B | **Byte-identical** (md5 6036…f1) to the copy inside `backup-2026-04-27.zip` |
| `/workspace/v4/Rotator-Controller-V4.kicad_pcb` | Sep 29 2025, 985,738 B | **Byte-identical** (`cmp`) to the copy in the backup zip |
| `backup-2026-04-27.zip` | Newest entries: `.kicad_pro` 2026-04-27 14:33, `Software/.vscode/*` and `.pio/.../idedata.json` 2026-04-27 16:46 | **No newer schematic or PCB.** The April 2026 activity was project settings and firmware IDE files only. |
| GitHub `wa1hco/Rotator-Controller-V2`, branch `Rotator_Controller_V4` | Last commits 2025-09-30 ("More work on schematic / Started software conversion to STM32F405") and 2025-10-09 ("Removed some deleted files") | Consistent with the laptop files. I did not hash-compare the GitHub copy. **[U]** |

**The analysis therefore uses the Sep 30 2025 schematic and the Sep 29 2025 PCB.**
- The PCB pad nets are the authoritative netlist.
- My schematic netlister only resolves 241/375 pins on this file. It falsely merges `+3v3/26VAC/VBUS`, which is a parser artifact; the PCB shows these nets correctly separated.
- Schematic and PCB contain the same reference designators (no sch-only or pcb-only parts).

---

## 1. The current V4 switching circuit (from PCB pad nets) [V]

### 1.1 Power path

```
J3.1 /26VAC ─┬─ U3 (CPC1966) pin3 ── pin4 ── /Left  ── J3.7  (D13 SMAJ90CA to GND)
             ├─ U4 (CPC1966) pin3 ── pin4 ── /Right ── J3.3  (D14 SMAJ90CA to GND)
             ├─ U5 (CPC1966) pin3 ── pin4 ── /Brake ── J3.2  (D15 SMAJ90CA to GND)
             ├─ D12 SMAJ90CA to GND,  C29 0.1µF "200V" 1206 to GND
             └─ D7 ("1N4004" value, 1N4148 symbol, SOD-123F) → /36VDC → C19 120µ "100V" CP_Elec_8x10,
                C26 1µ → U6 NDP6802SF-50 (5 V LDO, SOT-89) → /5V → U7 AP2112K-3.3 → /+3v3
J3.6, J3.10  GND  (rotor common = transformer return = logic ground)
J3.5 /Cap2, J3.9 /Cap1 ─ J2 "Motor Cap" 1×2 2.54 mm pin header (run cap off-board)
J3.4 /Pot+, J3.8 /Pot−  (D16/D17 SMAJ10CA, C31/C32 0.1 "200V" to GND)
```

Additional facts:
- **No fuse** anywhere on the board.
- **No snubbers.**
- **No MOV.**

### 1.2 Drive

Each channel is an MCU net feeding an input resistor and a separate indicator branch:

| SSR | MCU net | CPC1966 input resistor (pin 2) | Indicator branch |
|---|---|---|---|
| U3 | `LeftMCU` | R12 1 kΩ | R11 1 kΩ → D8 "Left" LED |
| U4 | `RightMCU` | R14 1 kΩ | R13 1 kΩ → D9 "Right" LED |
| U5 | `BrakeMCU` | R16 1 kΩ | R15 1 kΩ → D10 "Brake" LED |

Pin 1 of each CPC1966 goes to GND.

CPC1966 datasheet (IXYS DS-CPC1966-R04) **[V]**:
- Pin 1 = −LED, pin 2 = +LED, pins 3/4 = AC load. **The polarity on the board is correct.**
- 3 A rms, 600 Vp, SCR outputs with zero-cross turn-on.
- I_F to activate 5 mA max; use >10 mA in noisy environments.
- I_H 44–50 mA.
- Rated load voltage 20–240 Vrms (load-current spec at 120–240 Vrms).
- "Snubber circuits may be required at low power factors."

### 1.3 Interlock, master cutoff, conduction sensing

**None.** The three SSRs are independent, so CW and CCW can both be on, which shorts the run cap and stalls the motor. Nothing disconnects the 26 VAC if an SSR fails shorted, and nothing reports a stuck-on SSR.

The schematic has a "ZCD" text label, but there are no ZCD components.

### 1.4 Layout

- Board outline is 99 × 70 mm (x 95–194, y 55–125). There are **no mounting holes.** **[V]**
- Switching region, top-right quarter, about x 140–180, y 55–72:
  - U3/U4/U5 SIP-4 at (144.4, 65.6 / 69.6 / 61.7)
  - Drive and LED resistors in a column at x ≈ 141
  - TVS D12–D15 at x 167.9
  - J3 Mate-N-Lok 2×5 at (175.2, 60.7)
  - J2 at (174.4, 84)
- Power traces (/26VAC, /Left, /Right, /Brake, /Cap1, /Cap2) are **0.8 mm**. GND and GNDD are poured on both layers.
- On-board notes: "Brake Current ~2 amps / Motor Current ~0.7 amps, no load". These are presumably the user's measurements; nameplate is 5 A brake and 2.25 A motor.
- There are no heatsink or enclosure notes.

### 1.5 Issues found (the K1-style check, and others)

The SSR channels have no NC/NO equivalent: each CPC1966 is a single normally-open switch and its LED polarity is right. Defaults are safe: an unpowered or reset MCU leaves the LEDs off. Ordered by severity:

1. **No CW/CCW interlock.** A firmware bug or a shorted SSR can short the run cap. This is the main safety gap; §4 fixes it.

2. **SSR channels and most MCU I/O are not wired.**
   - `LeftMCU`, `RightMCU` and `BrakeMCU` connect only to R11–R16; no STM32 pin reaches them.
   - Almost every STM32 GPIO is a no-connect, including:
     - the ADC inputs for `Flt_W±`
     - the buttons SW1/SW2 (nets `/CW`, `/CCW`)
     - `AzPre` (RV1)
     - `LED` (D5)
     - **SWD PA13/PA14, so the chip cannot be programmed.**
   - V4 is mid-conversion from Teensy; the board as drawn cannot work.

3. **Three different 3.3 V nets.**
   - `/+3V3` feeds every STM32 VDD (U2.19/32/48/64), FB2→AVCC, and the pot bias R24/R25.
   - `/+3v3` is U7's output, plus U1 side 2 and C33/C34/C7/C9.
   - `/3V3` reaches RV1 only.
   - KiCad labels are case-sensitive, so **the MCU has no supply.** Unify the labels.

4. **USB D+/D− are swapped on the isolated side.**
   - Net `/D+` runs from U1 pin 11 to PA12 (OTG_FS_DP); net `/D−` from U1 pin 10 to PA11.
   - ADuM4160/3160 datasheet: pin 10 = DD+, pin 11 = DD−. **[V]**

5. **ADuM3160 is strapped for low speed.**
   - SPU (U1.5) goes to GNDD and SPD (U1.13) to GND.
   - The datasheet says high = full speed, and both pins must match. **[V]**
   - The STM32 OTG_FS device port is full-speed, so tie SPU→VDD1 and SPD→VDD2.
   - Add 24 Ω series resistors on the DD side (R5/R6 27 Ω already exist on the UD side).

6. **The CPC1966s are under-driven.**
   - (3.3 V − 1.2 V) / 1 kΩ ≈ 2.1 mA, against **5 mA max required** and >10 mA recommended. **[V]**
   - Turn-on is unreliable.

7. **The CPC1966 is a poor fit for this load.**
   - It is rated 3 A, below the 5 A brake nameplate.
   - Zero-cross turn-on (5–20 V window) on a cap-run motor and solenoid gives worst-case inductive inrush and possible half-wave misfiring at low power factor.
   - The datasheet specifies load current at 120–240 Vrms.
   - This is why we are changing it.

8. **The logic supply is thermally over budget.**
   - NDP6802SF: 85 V in, 100 mA, **P_D max 1 W**, θJA 44 °C/W. **[V]**
   - From /36VDC (≈33–48 V) to 5 V at a 50–80 mA STM32 + USB-isolator + LED load is (30–43 V) × (0.05–0.08 A) ≈ **1.5–3.4 W.** **[E]**
   - Opto LEDs or a relay coil would make it worse. Replace U6 with a small buck (§5).

9. **D7 is ambiguous.**
   - The value says 1N4004, but the symbol, datasheet link and footprint are 1N4148 / SOD-123F (100 V, 150 mA).
   - A half-wave rectifier with a reservoir cap sees PIV ≈ 2 × Vpk ≈ 74–96 V, which is too close to 100 V, and the inrush into C19 exceeds a 1N4148's rating.
   - Use an S1J/US1J (SMA, 600 V, 1 A) or similar. **[U]**
   - C19 "120 µF 100 V" in an 8×10 mm SMD can: check it exists and that its ripple rating is adequate. **[U]**

10. **J2 "Motor Cap" is a 2.54 mm pin header.** The run cap carries ≈1.8 A rms continuously, so use a latched ≥5 A connector. (Same finding as the V2 review.)

11. **0.8 mm power traces** are ≈2.5–3 A on 1 oz copper at 10 °C rise (IPC-2221). **[E]** The brake path (nameplate 5 A) needs ≥2.5 mm on 1 oz, ≥1.5 mm on 2 oz, or a pour.

12. **Minor:**
    - R4 pin 1 is unconnected, so the "Motor" LED D3 is dead.
    - SW1 and SW2 are both valued "CW".
    - No mounting holes.

---

## 2. Recommended channel design (×3: CW/Right, CCW/Left, Brake)

### 2.1 Parts (datasheet-verified values)

| Function | Part | Key ratings | Why |
|---|---|---|---|
| Opto triac driver | **onsemi MOC3023M** (DIP-6; MOC3023SM for SMD) | Random phase; VDRM 400 V; **I_FT 5 mA max** (most sensitive grade); recommended I_F between I_FT and 60 mA; I_TSM 1 A (100 µs, 120 pps); V_TM ≤3 V @ 100 mA; static dv/dt 1000 V/µs (listed without min/typ in my source **[U]**); 4170 Vrms isolation **[V]** | Random phase is required for inductive loads. A zero-cross opto (MOC3043/3063) or the CPC1966 would refuse to re-fire when current zero is reached at a non-zero voltage. The 5 mA grade gives margin from a 3.3/5 V supply. |
| Power triac | **BTA16-600SW** (ST; Littelfuse BTA16-600SW3G is equivalent), **insulated TO-220AB** | 16 A rms; 600 V; **I_GT 10 mA max** (Q1–Q3; 2 mA min); V_GT ≤1.3 V; I_TSM 168–170 A; V_TM ≤1.55 V @ 22.5 A; Littelfuse spec (dI/dt)c ≥2 A/ms unsnubbed @110 °C and dV/dt ≥250 V/µs; **tab isolated 2500 Vrms** **[V]**. ST V_TO 0.85 V / R_d 25 mΩ and Rth(j-c) ≈2.1 °C/W **[U]**, taken from the ST family datasheet and not re-read. | 3-quadrant logic-level "snubberless" triac. Low I_GT fires easily from 26 VAC. The 16 A rating gives inrush margin for the brake solenoid and run-cap transients. The insulated tab can bolt straight to a grounded chassis. One part number for all three channels. |
| Alternative triac | BTA08-600SW (8 A insulated, I_GT 10 mA; ST: (dI/dt)c 5.4 A/ms @ (dV/dt)c 0.1 V/µs, 2.8 A/ms @ 10 V/µs; V_TO 0.85 V, R_d 50 mΩ) **[V]** | — | Fine for CW/CCW (2.25 A). Usable for the brake, but runs warmer and has less surge margin. Not worth a second part number. |
| Load snubber across MT2–MT1 | **68 Ω 1206 (or 0.5 W MELF) + 0.1 µF X2 film, 275 VAC** (e.g. KEMET R46 / Vishay MKP338-2 class, 10 or 15 mm pitch) **[U MPN]** | — | Limits commutation (dV/dt)c and absorbs cable and limit-switch transients. X2 film is self-healing and will not crack like the MLCCs that failed on V2. |
| Gate series R_G (MT2 side, before the opto) | **100 Ω, 1206** | — | See the calculation below. |
| Gate–MT1 R_GK | **1 kΩ 0603** (fit, DNP option) | — | Noise immunity for a 10 mA-sensitive gate. Diverts only 1.3 mA. |
| Opto LED drive | **2N7002 low-side + 330 Ω from +5 V**, channel indicator LED in series | — | See below. |
| Conduction sense across each triac | **LTV-814S** (AC-input phototransistor; also H11AA1/TLP620) + **2 × 7.5 kΩ 1206 in series** (15 kΩ, splits dissipation) + 10 kΩ pull-up to 3.3 V | — | §4.3. LTV-814 CTR ≥20 % @ ±1 mA **[U]**. |

### 2.2 Gate-resistor calculation for 26 VAC [E]

The triac fires when the instantaneous voltage across it reaches:

V_fire = V_TM(opto) + V_GT + (I_GT + V_GT/R_GK) × R_G

Worst case (cold, low line):
- I_GT ≈ 2 × 10 mA = 20 mA at −20 °C **[E]** (typical temperature curve)
- V_GT 1.3 V
- V_TM(opto) ≈ 3 V
- R_GK = 1 kΩ, so it adds 1.3 mA

With **R_G = 100 Ω**: V_fire = 3 + 1.3 + 21.3 mA × 100 Ω ≈ **6.4 V**.
- At low line (23.4 Vrms, 33 Vpk) that is sin⁻¹(6.4/33) ≈ **11° ≈ 0.5 ms** after voltage zero.
- At 25 °C it is ≈5.4 V, about 9°.
- This only affects the first half-cycle. After that, an inductive load's current zero arrives while the line voltage is already large, so the triac re-fires immediately.

Opto surge limit: the LED can switch on at the line peak, worst case 48 V at high line with no load. I_peak = 48 V / 100 Ω = **0.48 A < 1 A I_TSM.** OK.
- R_G must stay ≥ 48 Ω.
- Don't go above about 220 Ω, or cold, low-line firing drifts past ~20°.

Latching: with a slowly rising inductive current, the opto keeps supplying gate current as long as the LED is lit, so the triac retries until the load current exceeds I_L. Hold the LED on continuously; do not pulse it.

### 2.3 Opto LED drive [E]

Circuit: +5 V → 330 Ω → indicator LED (0402 red, ~2.0 V) → MOC3023 LED (1.15–1.5 V) → 2N7002 drain. The 2N7002 gate comes from the interlock logic and has a 100 kΩ pull-down.

- I_F ≈ (5 − 2.0 − 1.25 − 0.05) / 330 ≈ **5.2 mA.** That is too close to I_FT, so either drop the series indicator or use **150 Ω**.
- **Chosen: R = 150 Ω with the indicator LED in series: I_F ≈ 11 mA typ, ≥ 8 mA worst case.** That is 2× I_FT, with margin for LED aging and temperature.
- The existing D8/D9/D10 become these series indicators, so they show real drive current. R11/R13/R15 are deleted, and R12/R14/R16 become 150 Ω.
- If you drop the indicator instead: 330 Ω gives ≈ 10.5 mA.

Supply load: at most 2 channels are on at once (one direction plus the brake), so ≈ 22 mA from +5 V. That is one more reason to replace U6 with a buck.

### 2.4 Dissipation and heatsinking [E]

Triac loss: P = V_TO × I_avg + R_d × I_rms², with I_avg = 0.9 × I_rms. BTA16: V_TO 0.85 V, R_d 25 mΩ **[U]**.

| Channel | I_rms | P per triac |
|---|---|---|
| Brake, nameplate | 5 A | 3.8 + 0.6 = **4.5 W** |
| Brake, board note "~2 A" | 2 A | **1.6 W** |
| Motor, nameplate | 2.25 A | 1.7 + 0.13 = **1.85 W** |
| Motor, no load | 0.7 A | **0.55 W** |

Duty cycle:
- The brake triac conducts for the whole rotation, and a full 360° on a HAM-IV takes about 60 s.
- Rotator duty is about 10 % by spec, but a long contest session can mean repeated 30–60 s runs.
- Design for the **worst continuous case: brake 4.5 W + one motor triac 1.85 W = 6.4 W.**

Free-air TO-220 is about 60 °C/W, so 4.5 W would rise 270 °C. **A heatsink is required.**

Sizing, for Tj ≤ 100 °C at 40 °C ambient:
- Brake junction above sink: 4.5 W × (2.1 °C/W junction-to-case + ~0.3 °C/W grease) ≈ 11 °C.
- That leaves a ≤ ~49 °C sink rise at 6.4 W, so **R_th(sink–air) ≤ ~7.5 °C/W.**
- Options:
  - Bolt all three insulated BTA tabs (grease, no pad) to an aluminum enclosure wall (≥2 mm thick; a ~100 × 70 mm wall area is roughly 5–7 °C/W **[E]**).
  - Or use a common bar or extrusion of ≤5 °C/W.
- The tabs are isolated (2500 Vrms), so the bar can be chassis or ground.
- At the measured currents (2 A / 0.7 A, about 2.2 W total), the margin is large.

### 2.5 Transient protection with triacs

The triacs turn off at **current zero**, so the switch itself no longer produces an inductive kick. That kick was what destroyed the V2 capacitors and was the main SMAJ stress in the V2 review. What remains is rotor-end limit-switch arcing, cable pickup and lightning.

| Node | Part | Change |
|---|---|---|
| D12 (26VAC bus) | SMAJ90CA | **Keep.** Line peak ≤ 48 V is well under VBR ≥ 100 V. Optional: add a 14 mm MOV (e.g. 14D560K, 35 VAC / 45 VDC max continuous) at the 26 VAC input ahead of the master relay for surge energy **[U]**. |
| D13, D14 (Left/Right) | SMAJ90CA | **Keep at ≥ 90 V standoff.** These nodes carry the idle-winding voltage (est. 37–90 Vpk **[M]**). Upgrade to SMCJ90CA (1500 W, 10.3 A) if there is room. |
| D15 (Brake) | SMAJ90CA | Keep. Could drop to SMCJ58CA (VC 93.6 V @ 16.5 A) **[V]**, but it is no longer critical. |
| C29 (0.1 µF "200V" MLCC on 26VAC) | — | Replace with 0.1 µF X2 film, or delete; the snubbers already load the bus. |
| Opto and triac | — | Off-state stress is at most the 146 V clamp, against MOC3023 400 V and BTA16 600 V. Large margin. |

### 2.6 Fusing

Add **F1: 5×20 mm PCB fuse clip pair (or a TR5 / Littelfuse 0154-style holder), T6.3 A 250 V slow-blow** in the 26 VAC hot, at the J3 input, ahead of the MOV and master relay **[E]**.
- Brake plus motor at nameplate is about 7.25 A, but measured is about 2 + 1–2 A. Raise to T8A if solenoid inrush blows T6.3A **[M]**.
- The fuse also protects against a shorted triac with a failed master relay.
- It does not replace the transformer's primary fuse.

---

## 3. One channel, schematic and KiCad-style netlist

```
            F1 T6.3A      K10 (G5LE NO, master)
J3.1 /26VAC_IN ──[F1]──┬──o/ o────────────┬─────────────────────────────── /26VAC  (bus to all 3 channels)
                       │  (coil: +5V─K10─Q13 drain, D30 flyback; Q13 gate = ARM)
                  RV10 MOV(opt)           │
                       │                  ├── D12 SMAJ90CA ── GND
                      GND                 │
                                          │            ┌──────────── R32 68Ω ─── C40 0.1µF X2 ───────┐
                                          │            │                                             │
                                          ├────────────┤ MT2   Q10 BTA16-600SW (insulated tab)   MT1 ├──── /Right ── J3.3
                                          │            └───────────────────┬─────────────────────────┘     │
                                          │                                G                              D14 SMAJ90CA
                                          │                                │                                │
                                          └── R30 100Ω ── U10.6 (MOC3023)  │                               GND
                                                          U10.4 ───────────┤
                                                                           └── R31 1k ── /Right (MT1)
          +5V ── R50 150Ω ── D9 "Right" LED ── U10.1(A) ; U10.2(K) ── Q20 2N7002 D ; Q20 S ── GND
                                                                       Q20 G ── CW_GATE (from interlock), R51 100k ── GND
   Sense:  /26VAC ── R40 7.5k ── R41 7.5k ── U13 LTV-814 LED pair ── /Right
           U13 C ── R43 10k ── +3V3 ;  U13 C ── RIGHT_SENSE (MCU GPIO, EXTI) ; U13 E ── GND
```

Netlist, Right/CW channel (Left/CCW and Brake are identical: Q11/Q12, U11/U12, etc.). Refdes are placeholders.

```
NET /26VAC_IN : J3.1, F1.1
NET /26VAC_F  : F1.2, K10.COM, RV10.1(opt)
NET /26VAC    : K10.NO, D12.A2, Q10.MT2, Q11.MT2, Q12.MT2, R30.1, R33.1, R36.1,
                C40.1(via R32), C41.., C42.., R40.1, R44.1, R48.1
NET /Right    : Q10.MT1, R31.2, C40.2, D14.A2, J3.3, R41.2(→U13.K/A pair)
NET N_R_G1    : R30.2, U10.6
NET N_R_GATE  : U10.4, Q10.G, R31.1
NET N_R_SN    : R32.2, C40.1        (R32.1 on /26VAC)
NET N_R_LED1  : R50.2, D9.A         (R50.1 on +5V)
NET N_R_LED2  : D9.K, U10.1
NET N_R_DRV   : U10.2, Q20.D
NET CW_GATE   : Q20.G, R51.1, IC_AND.Y1, (hold RC: R60.1)
NET N_R_SENS  : R40.2, R41.1
NET RIGHT_SNS : U13.C, R43.2, MCU.PBx
NET ARM       : MCU.PBy, R70(100k→GND), IC_AND.inputs, Q13.G
NET GND       : Q20.S, U13.E, R51.2, D12.A1, D14.A1, J3.6, J3.10, ...
```

Pinout notes:
- MOC3023M: 1 = anode, 2 = cathode, 4 = MT, 6 = MT; 3/5 = NC (do not use pin 5).
- BTA16 TO-220AB: 1 = A1/MT1, 2 = A2/MT2, 3 = G.
- **Check both pinouts against the datasheet figure when you make the footprint.** [U]

---

## 4. Interlock, sensing and master cutoff (hobby-PCB simple)

### 4.1 Hardware interlock with enforced dead time

MCU outputs: `CW_REQ`, `CCW_REQ`, `BRK_REQ` and `ARM`, each with a 100 kΩ pull-down so reset or boot states are safe.

```
CW_GATE  = CW_REQ  · /CCW_REQ · ARM · OK_CW        (74LVC21 dual 4-input AND, gate A)
CCW_GATE = CCW_REQ · /CW_REQ  · ARM · OK_CCW       (74LVC21 gate B)
BRK_GATE = BRK_REQ · ARM                           (74LVC1G08)
/CW_REQ, /CCW_REQ                                  (74LVC14 Schmitt inverters)
OK_CW    = NOT(HOLD_CCW),  OK_CCW = NOT(HOLD_CW)   (74LVC14)
HOLD_x   : x_GATE → 1 kΩ → BAT54 → node[1 µF X7R ∥ 100 kΩ to GND] → 74LVC14 input
```

How it works:
- The **cross-REQ terms** block both directions if firmware asserts both, with no RC race.
- The **HOLD RC** charges in about 1 ms when a direction is gated. After that gate drops, the RC keeps the opposite direction blocked for t ≈ 100 kΩ × 1 µF × ln(3.0 V / V_T−).
  - With the 74LVC14 V_T− ≈ 1.0–1.5 V at 3.3 V **[U]**, t ≈ **70–110 ms.**
  - That is ≥ 40 ms even at −20 % on C. It covers the triac latching until current zero (≤ 8.3 ms) and run-cap and winding decay.
- This is three logic packages plus a few passives, all 3.3 V from `/+3V3`.
- Firmware should still apply its own reversal delay (≥ 500 ms, and a coast stop before reversing); the hardware is the backstop.

### 4.2 Master cutoff relay

**K10: Omron G5LE-1A4 DC5** (SPST-NO, 10 A, 5 V coil ≈ 80 mA **[U]**), or reuse the G5LE-14 from V2 on its NO contact.
- Placed in series between F1 and the triac bus.
- Driven by `ARM` through Q13 (AO3400 or similar logic-level N-FET), with a 1N4148W flyback diode.

Sequence:
1. ARM → wait 50 ms → self-test (§4.3) → gate.
2. Un-gate → wait ≥ 150 ms → disarm.

So in normal use the relay never makes or breaks load current. It only breaks current on a fault.

Optional watchdog: drive Q13's gate through a charge pump (100 nF + 2 × BAT54) from a GPIO that firmware toggles at ≥ 1 kHz. If the code hangs, ARM drops on its own **[E]**.

### 4.3 Conduction sense: stuck-on detection

Each LTV-814 LED pair sits **across its triac** (MT2–MT1) through 15 kΩ.

| Triac state | Voltage across triac | Opto output |
|---|---|---|
| Blocking (off), idle | Line | Pulses at 120 Hz (LED lit) |
| Blocking (off), opposite direction running | Run-cap voltage, ≈ 37–64 Vrms **[E]** | Pulses at 120 Hz (LED lit) |
| Conducting | ≈ 1 V | Output stays high (dark) |

LED current: I_LED ≈ 37 Vpk / 15 kΩ ≈ 2.5 mA peak. Worst-case resistor dissipation is (64 Vrms)² / 15 kΩ ≈ 0.27 W, split over two 1206 parts.

Firmware rule: **"armed AND not gated AND no pulse in 20 ms" = stuck-on**, so drop ARM and report a fault.
- When disarmed the bus is dead, so all sense lines read "dark". Only evaluate the sense lines while armed.
- The 50 ms pre-gate self-test catches a shorted triac before any motion. The cost is a brief twitch of that load during the test window.
- **Bonus:** these pulses are a free line zero-cross reference, which covers the "ZCD" note on the schematic.

Leakage note: the sense path (~2.5 mA) and the snubber (~1 mA) pass a few mA through the load when it is off. That is harmless for the motor and brake.

---

## 5. Board impact

### Remove
- U3, U4, U5 (CPC1966 SIP-4)
- R11, R13, R15
- C29 (optional)
- J2 pin header: replace it with a latched connector

### Re-value or reuse
- R12, R14, R16 → 150 Ω (opto LED drive)
- D8, D9, D10 become series indicators on the opto LED string
- Keep D12–D15 TVS, J3 and all pot circuitry

### Add (for three channels)
- 3 × BTA16-600SW TO-220 (vertical, row along the top board edge, tabs out to the enclosure wall or a shared bar)
- 3 × MOC3023M
- 3 × (R_G 100 Ω, R_GK 1 kΩ, R_s 68 Ω, C_s 0.1 µF X2)
- 3 × 2N7002 + 100 kΩ
- 3 × LTV-814S + 2 × 7.5 kΩ + 10 kΩ
- 74LVC21, 74LVC14, 74LVC1G08, plus 2 × (1 kΩ, BAT54, 1 µF, 100 kΩ)
- K10 G5LE + AO3400 + 1N4148W
- F1 5×20 clips
- Optional RV10 MOV
- **Replace U6** with a 60 V-input buck to 5 V at ≥ 300 mA, e.g. TI LMR36006 or LMR51430-class **[U part choice]**. Keep U7.

### Net names to keep
`/26VAC` (becomes the post-relay bus), `/Left`, `/Right`, `/Brake`, `/Cap1`, `/Cap2`, `GND`, `/36VDC`, `/5V`, plus a unified `/+3V3`.

Rename `LeftMCU`/`RightMCU`/`BrakeMCU` to `CCW_REQ`/`CW_REQ`/`BRK_REQ`, and add `ARM`, `CW_GATE`, `CCW_GATE`, `BRK_GATE`, `*_SNS` and `/26VAC_IN`.

Mapping: Right = CW and Left = CCW, per the schematic note "5 Motor Right / 6 Motor Left" **[V]**.

### Placement
- Triacs, snubbers and the MOC parts go along the top edge, x ≈ 110–165, y 55–65. Three TO-220s at 12.7 mm pitch need about 40 mm.
- Move the TVS row next to J3.
- Put K10 and F1 between J3.1 and the triac row.
- Interlock logic goes near the MCU's former SSR-drive area, x ≈ 125–140, y 65–75.
- Run the AC power nets as **≥ 2.5 mm traces or pours** (1 oz), keeping the brake loop (/26VAC → Q12 → /Brake → J3.2) short.
- **Add 4 × M3 mounting holes**, and fix the board edge to the enclosure wall that carries the triac tabs.

### Creepage
- All AC is ≤ 48 Vpk. IPC-2221 B2 (≤ 50 V, external, uncoated) needs only about 0.6 mm.
- Use **≥ 1 mm between AC power nets** and **≥ 2 mm from AC nets to logic copper** for robustness.
- The opto isolation is functional, not a safety barrier: logic GND is the transformer return. The real isolation barrier stays the ADuM3160 at USB.

### Size
Fits the existing 99 × 70 mm outline if the TO-220s stand on the edge. Grow the board about 10 mm in y if they need to lie flat.

### BOM delta, rough per board (2026 distributor pricing, 1-off) [E][U]

| Change | Cost |
|---|---|
| Remove 3 × CPC1966 | −$13 to −$15 |
| 3 × BTA16-600SW | +$4–6 |
| 3 × MOC3023M | +$2 |
| 3 × X2 0.1 µF | +$1.5 |
| 3 × LTV-814S | +$1.5 |
| Logic ICs | +$1.5 |
| Passives | +$2 |
| G5LE + FET | +$2 |
| Fuse + clips | +$1.5 |
| Buck converter | +$3–4 |
| Heatsink bar (or $0 using the enclosure wall) | +$3–6 |

**Net ≈ +$5 to +$15 per board,** with about 35 more placements.

---

## 6. Firmware changes that go with this

- Arm/disarm and self-test sequence (§4.2, §4.3).
- Brake: release (BRK on) → wait ~250 ms → motor on. Motor off → coast delay (several seconds for HAM-IV per CDE practice **[U]**) → brake set.
- Reversal: motor off → coast → reverse. The hardware hold blocks anything under ~70–110 ms anyway.
- Stuck-on detection: drop ARM, latch a fault, report it to the PC.

---

## 7. Unverified / to measure

- ST BTA16 V_TO / R_d / Rth(j-c): family values, not re-read.
- MOC3023 static dv/dt: min vs typ.
- LTV-814 CTR at 1–2.5 mA.
- 74LVC14 V_T− at 3.3 V.
- G5LE-1A4 DC5 coil current.
- MOV and X2-cap MPNs.
- Buck part choice.
- C19 availability; the D7 replacement.
- TO-220 and MOC pinouts against the footprint drawings.
- Brake inrush current (fuse choice).
- Idle-winding peak (D13/D14 voltage).
- Heatsink thermal resistance of the actual enclosure.
- The GitHub copy of the V4 files (not hash-compared).
