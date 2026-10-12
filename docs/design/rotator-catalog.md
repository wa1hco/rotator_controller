# Rotator catalog for the WA1HCO open rotator controller

Every entry here becomes a run-time **rotor preset**, stored in `rotor-presets.yaml` (schema_version 1). The user chooses a model, the preset loads typed defaults, and a calibration sweep learns the rest: pot end points or pulse counts, seconds per 360°, and coast.

**Legend**
- **[?]**: unknown, or taken from a search summary, an inference, or sources that disagree. Do not trust it until it is checked on the bench. The YAML `unverified:` list names these fields.
- **[proposed, bench-tune]**: a default chosen for this controller, not a manufacturer figure.
- Source tags such as [HAM4] refer to the Sources list at the end.
- Pin numbers are the rotor and cable terminal numbers used by the stock controller, or by the Green Heron RT-21 Appendix A tables when that is the only source.
- Support levels:
  - **v1**: works with the AC triac board.
  - **v1-2axis**: needs both axes.
  - **v2-dc**: needs the DC H-bridge module.
  - **later**: needs more data or hardware.
  - **alias**: a controller or retrofit that maps onto a rotor preset.
  - **no**: out of scope.

**Green Heron coverage.** The RT-21 manual (Appendix A) has hookup tables for:
- Hy-Gain/CDE: HAM-II through HAM-V, T2X, CD-45, HDR-300.
- Yaesu: G-450/650/800/1000/2800, plus DXA/SDX.
- Prosistel: D and PRO.
- Others: Create, Daiwa, M2/Orion (AC and DC), SPID RAK/BIG-RAK/RAS, TIC Ring Rotor, Alliance HD-73, Rotor Doctor.

Every RT-21 table that bears on our hardware is captured below.


## Summary table

| id | model | axes | family | support | motor | brake | sensor | range | s/360 |
|---|---|---|---|---|---|---|---|---|---|
| cde-ham-m-s3-5 | HAM-M (Series 3, 4, 5) | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | electric_positive_lock | pot_dual_end_grounded_wiper 500 ohm | 360 | 50 |
| cde-ham-ii | HAM-II (CD-44/Ham-2 box) | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | 45-50 [?] |
| cde-ham-iii | HAM-III | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | 45-60 [?] |
| hygain-ham-iv | HAM-IV | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | 45-60 |
| hygain-ham-v | HAM-V (with DCU-1) | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 26 V [?] | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm [?] | 360 | [?] |
| hygain-t2x | T-2X Tailtwister | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | 45-60 [?] |
| hygain-cd-45ii | CD-45-II | az | CDE-AC-nobrake-pot | v1 | ac_split_phase_cap_run 24 V | disc_internal | pot_dual_end_grounded_wiper 500 ohm [?] | 360 | 45-60 |
| cde-cd-44 | CD-44 | az | CDE-AC-brake-pot | v1 | ac_split_phase_cap_run 24 V | [?] | pot_dual_end_grounded_wiper 500 ohm | 360 | [?] |
| hygain-ar-40 | AR-40 (TV/light-duty class; AR-500 not researched) | az | unsupported | no | ? [?] | [?] | ? [?] | 360 | [?] |
| hygain-hdr-300a | HDR-300 / HDR-300A | az | AC-brake-multiturn-pot | v1 | ac_pm_split_capacitor 24 V | solenoid_brake_clutch | pot_multiturn_single_ended 1000 ohm | 400 | [?] |
| yaesu-g-450a | G-450A / G-650A | az | Yaesu-AC-pot | v1 | ac_split_phase_cap_run 24 V [?] | none_gear | pot_single_ended 500 ohm [?] | 450 | 51-63 |
| yaesu-g-5500 | G-5500 (AC, az-el) | az+el | Yaesu-AC-pot | v1-2axis | ac_split_phase_cap_run 24 V | none_gear | pot_single_ended 500 ohm | 450 | 58 |
| yaesu-g-550 | G-550 (elevation) | el | Yaesu-AC-pot | v1-2axis | ac_split_phase_cap_run 24 V | none_gear | pot_single_ended 500 ohm [?] | 180 | [?] |
| kenpro-kr-series | KR-400 / KR-600(RC) / KR-1000 / KR-2000; KR-5400/5600 az-el | az (KR-5x00: az+el) | Yaesu-AC-pot | v1 | ac_split_phase_cap_run 24 V [?] | none_gear | pot_single_ended 500 ohm | [?] | 53-63 |
| daiwa-mr-750 | MR-750 / MR-300 | az | Yaesu-AC-pot | v1 | ac_cap_run [?] | [?] | pot_single_ended | [?] | [?] |
| create-rc5 | RC5-1 / RC5-3 / RC5A-2 / RC5A-3 / RC5B-3 / RC5B-4 (+P variants) | az | Yaesu-AC-pot | v1 | ac_cap_run 28 V [?] | [?] | pot_single_ended [?] | [?] | 60-150 |
| alliance-hd-73 | HD-73 | az | Yaesu-AC-pot | v1 | ac_split_phase_cap_run 20 V [?] | [?] | pot_single_ended_low_ohm 75 ohm | [?] | [60, None] [?] |
| alliance-u-110 | U-110 / U-100 Tenna-Rotor | az | unsupported | no | ac 24 V [?] | [?] | ? [?] | 360 | 60 |
| orion-or-2300 | OR-2300 (original) | az | Yaesu-AC-pot | v1 | ac_cap_run [?] | [?] | pot_single_ended | 360 | [?] |
| prosistel-ac-48v | PST-51 / PST-61 / PST-71 (older 48 VAC, Model A/B/C box) | az | AC48-pot | check | ac_cap_run 48 V | [?] | pot_single_ended 10000 ohm | 440 | 70-130 |
| yaesu-g-dxa | G-800DXA / G-1000DXA / G-2800DXA | az | DC-pot | v2-dc | dc_pm 24 V | none_gear | pot_single_ended 500 ohm | 450 | 40-120 |
| yaesu-g-450adc | G-450ADC / G-450CDC | az | DC-pot | v2-dc | dc_pm 22 V | none_gear | pot_rheostat 500 ohm [?] | 450 | 56 |
| yaesu-g-5500dc | G-5500DC (az-el) | az+el | DC-pot | v2-dc | dc_pm 22 V | none_gear | pot_single_ended [?] | 450 | 60 |
| yaesu-g-800sdx | G-800S / G-800SDX / G-1000SDX | az | DC-pot | later | ? [?] | none_gear | pot_single_ended [?] | 450 [?] | [?] |
| prosistel-d | PST-61D / PST-71D / PST-2051D / PST-110D (D series) | az | DC-pot | v2-dc | dc_pm 24 V | [?] | pot_single_ended | 500 | 90-100 |
| tic-ringrotor | Ring Rotor (1022/1032 etc.) | az (around tower) | DC-pot | v2-dc | dc_pm 13.8 V | none_gear | pot_single_ended 500 ohm | [?] | [?] |
| rotordoctor-rd-1800 | RD-1800 | az | DC-pot | v2-dc | dc_pm [?] | [?] | pot_single_ended | [?] | [?] |
| spid-rak | RAK | az | DC-pulse | v2-dc | dc_pm 24 V | none | reed_pulse 1/deg | 720 [?] | 60-120 |
| spid-big-rak | BIG-RAK | az | DC-pulse | v2-dc | dc_pm [?] | none | reed_pulse 2/deg [?] | [?] | 60-210 [?] |
| spid-ras | RAS / BIG-RAS (az-el); HR variants | az+el | DC-pulse | v2-dc | dc_pm [?] | none | reed_pulse 1/deg [?] | [?] | 60-120 |
| m2-or2800px | OR2800PX (DC) with RC2800PX | az | DC-pulse | v2-dc | dc_pm [?] | none | reed_pulse 11/deg | 360 | 55-270 |
| orion-or2800-ac | OR2800 (older AC) | az | AC-pulse | v1 | ac_cap_run [?] | [?] | reed_pulse [?] | [?] | [?] |
| prosistel-pro | PST-71D PRO / RR55D-PRO (encoder) | az | DC-encoder | later | dc_pm [?] | none | encoder_2bit [?] | [?] | [?] |
| alias-telex-dcu | DCU-1 Pathfinder / DCU-2 / DCU-3 (controllers) | az | CDE-AC-brake-pot | alias | ? [?] | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | [?] |
| alias-rotor-ez | Rotor-EZ (board in CDE/Hy-Gain box) | az | CDE-AC-brake-pot | alias | ? [?] | wedge_solenoid | pot_dual_end_grounded_wiper 500 ohm | 360 | [?] |
| emoto-emotator | Emotator 103/502/747/1102/1103/1105/1200 series (SX/MXX/FX) | az (some az-el) | mixed | later | mixed [?] | mixed | pot_single_ended [?] | [?] | 35-170 |
| generic-ac-pot | AC capacitor-run motor + pot | az|el | generic | v1 | ac_split_phase_cap_run 24 V | optional | pot_any | 360 | [?] |
| generic-dc-pot | DC PM motor + pot | az|el | generic | v2-dc | dc_pm [?] | optional | pot_any | 360 | [?] |
| generic-dc-pulse | DC PM motor + pulse sensor (reed / Hall / encoder) | az|el | generic | v2-dc | dc_pm [?] | optional | pulse_any | 360 | [?] |

## Per-model detail

### CDE (Cornell-Dubilier) HAM-M (Series 3, 4, 5)  (`cde-ham-m-s3-5`)

Aliases: Ham-M, TR-44 Series 3 (box-compatible)  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current 2.25 A; run cap 130 uF, location controller. 130 MFD electrolytic (non-polar), 10 % duty
- **Brake:** electric_positive_lock; 24 V, 3.5 A. Positive lock into one of 96 segments (3.75 deg spacing); continuous-duty solenoid; stock box has no delay (lever)
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: ends on 3 and 7, wiper = terminal 1 common. Excitation: stock ~13 VDC.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor, in CW/CCW motor feeds.
- **Speed:** 50 s (approx. 50 s per 360 deg). Duty: motor 10 % duty (transformer thermal cutout).
- **Cable:** 8 conductors; connector screw terminal strip; 2 x #18 (1, 2) + 6 x #22 to ~120 ft.
  - Pinout [?]: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Ham-M SERIES 1 and 2 (and TR-44 S1/S2) are wired differently; a later control on them 'will destroy the rotor pot instantly' (NORM). Preset must warn; check 500 ohm across 3-7 and cap across 4-8 first.
- **Gotcha:** Open, non-sealed wirewound pot gets noisy (RT-21 note).
- **Notes:** Pinout assumed identical to later 8-wire CDE family for Series 3-5, per NORM interchangeability statement.
- **Sources:** [HAMM], [NORM], [WA1HCO]  Unverified fields: cable.pinout

### CDE HAM-II (CD-44/Ham-2 box)  (`cde-ham-ii`)

Aliases: Ham-2  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap [?], location controller. NORM: most CDE run caps are 108-155 uF bipolar
- **Brake:** wedge_solenoid [?]; 24 V, [?]. Same rotor as Ham-M; new 3-lever control box (1973)
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: ends 3 and 7, wiper 1. Excitation: stock ~13 VDC.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor motor feeds.
- **Speed:** 45-50 s [?] (45-50 s at 60 Hz).
- **Cable:** 8 conductors; connector screw terminal strip.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Same rotor as Ham-M Series 5 (NORM).
- **Sources:** [NORM], [SRCH]  Unverified fields: motor.current_a, speed, brake.type

### CDE HAM-III  (`cde-ham-iii`)

Aliases: Ham-3, CD-44/Ham-3  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap [?], location controller.
- **Brake:** wedge_solenoid; 24 V [?], [?]. 1977: new motor with internal brake, redesigned wedge and housing (NORM)
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: ends 3 and 7, wiper 1. Excitation: stock ~13 VDC.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor motor feeds.
- **Speed:** 45-60 s [?] (45-60 s at 60 Hz).
- **Cable:** 8 conductors; connector screw terminal strip.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Sources:** [NORM], [SRCH]  Unverified fields: speed, brake.volts

### CDE / Telex / Hy-Gain (MFJ) HAM-IV  (`hygain-ham-iv`)

Aliases: Ham-4, HAM-IVX (220 V box)  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current 2.25 A; run cap 130-156 uF, location controller. 130-156 MFD motor-start cap (P/N 5151500/5151501); power transformer 120/26 VAC 10 % duty, thermal switch. Manual: move cap to tower for runs >300 ft. N0AX: 120-140 uF. WA1HCO doc: 130-156 uF 50 VAC
- **Brake:** wedge_solenoid; 24 V, 5.0 A, coil 0.75 ohm. Wedge brake; RT-21: brake sets in 6-degree increments
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: ends 3 (+) and 7 (-), wiper = 1 (common); wiper-to-3 is 0 ohm at full CCW. Excitation: stock ~13 VDC across 3-7; DCU-3: 8-9 VDC open, 0-4.5 VDC on 3-1.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor: terminal 5 -> right limit -> 8; terminal 6 -> left limit -> 4.
- **Speed:** 45-60 s (45-60 s at 60 Hz). Duty: transformer 10 % duty; thermal switch trips after 4-5 min continuous, resets in ~10 min (T2X manual, same box design).
- **Cable:** 8 conductors; connector terminal strip (older); 8-pin Cinch-Jones on box; AMP pigtail at rotor.; max cable R: 1-2 <= 0.8 ohm, others <= 2.0 ohm.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Terminal 1 carries motor + brake return AND is the pot wiper reference: 60 Hz ripple on the pot reading (why the dual-end + notch design exists).
- **Gotcha:** An open limit switch at end of travel looks like 'no current'; not a fault at the end stop.
- **Gotcha:** RT-21: open pot gets noisy; some users add 30-100 uF from POS to GND at the controller.
- **Notes:** DCU-3 resistance table: brake 1-2 0.75 ohm; half winding 1-8 and 1-4 2.5 ohm; whole motor 4-8 4.5 ohm; pot 3-7 500 ohm (+ cable).
- **Sources:** [HAM4], [DCU3], [RT21], [N0AX], [WA1HCO], [T2X]

### Telex / Hy-Gain HAM-V (with DCU-1)  (`hygain-ham-v`)

Aliases: HAM-VX  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 26 V [?]; current [?]; run cap 130-156 uF, location controller. 130-156 MFD (P/N 5151501); may be moved to tower for >300 ft so only 6 wires run
- **Brake:** wedge_solenoid; [?], [?]; engage after stop 8 s. DCU-1: brake engages 8 s after motor power is removed, even on STOP; immediately on AC loss
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm [?]. Wiring: same 8-wire scheme as HAM-IV (DCU-1/3 interchangeable). Excitation: [?].
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor; DCU-1 EPC calibration finds both limit switches.
- **Speed:** [?].
- **Cable:** 8 conductors; connector weatherproof 8-pin AMP at rotor, gold contacts; RF beads on pot lines.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** DCU-1: release brake, momentary reverse a few degrees, then run to target; half speed (half-cycle pulses) for the last 5 deg; brake held 8 s after stop. No-motion stop after 8 s. Do not reverse during rotation.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Ships with the digital DCU-1; DCU-1, DCU-2 and DCU-3 share one serial command set (DCU-3 manual).
- **Notes:** Manual describes '26 volt operation'; motor current not given.
- **Sources:** [HAM5], [DCU3]  Unverified fields: motor.volts, sensor.ohms

### CDE / Telex / Hy-Gain (MFJ) T-2X Tailtwister  (`hygain-t2x`)

Aliases: T2X, T-2XX (220 V), T-2XD3 (with DCU-3)  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap 130-156 uF, location controller. C-2, 130-156 MFD motor start (P/N 5151500)
- **Brake:** wedge_solenoid; 24 V, [?]. Heavier wedge and housing than HAM-IV (NORM). Known 'brake stick'. Manual: 'allow a few seconds for the rotator to coast down' before re-engaging
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: ends 3 and 7, wiper 1; ~13 VDC across 3-7 in stock box. Excitation: stock ~13 VDC.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor motor feeds; RT-21 T2X option keeps 5 deg away from them.
- **Speed:** 45-60 s [?] (45-60 s). Duty: thermal switch in transformer trips after 4-5 min continuous; auto reset ~10 min.
- **Cable:** 8 conductors; connector 8-pin Cinch on control box, weatherproof AMP at rotor; see manual Table 1.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box. Brake-stick relief: before a motion, run briefly in the opposite direction to unload the wedge (RT-21 T2X option; DCU-1/DCU-3 do the same).
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Stock box test: ~30 VAC on 1-2 (brake), 1-5, 1-6; ~13 VDC on 3-7.
- **Gotcha:** Brake stick: soft limits must leave room to back off before the limit switch.
- **Notes:** A search summary claims motor 24 VAC 5.0 A and brake 24 VAC 5.0 A; not confirmed in an opened source.
- **Sources:** [T2X], [T2XS], [RT21], [NORM], [SRCH]  Unverified fields: motor.current_a, brake.current_a, speed

### Telex / Hy-Gain (MFJ) CD-45-II  (`hygain-cd-45ii`)

Aliases: CD-45IIX, CD-45  
Family **CDE-AC-nobrake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current 2.25 A; run cap 130-156 uF, location controller. Control box shares the HAM-IV/CD-45-II parts list; 120/26 VAC transformer, 10 % duty
- **Brake:** disc_internal; [?], [?]. 'Automatic disc type'; terminal 2 unused in rotor (7 wires suffice)
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm [?]. Wiring: CDE 8-wire scheme, terminal 2 unused. Excitation: stock ~13 VDC.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor.
- **Speed:** 45-60 s (45-60 s at 60 Hz). Duty: transformer 10 % duty, thermal switch.
- **Cable:** 7 conductors; connector terminal strip; Cinch 8-pin plug + AMP parts in kit; max: terminal 1 1.0 ohm; 3-8 2.5 ohm.
  - Pinout [?]: 1=common: motor windings, brake, pot wiper (heavy wire); 2=not used (no solenoid brake); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** As CDE without brake output: stop, wait for coast, then reverse.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Brake output disabled (terminal 2 open).
- **Sources:** [CD45], [REZ]  Unverified fields: cable.pinout, sensor.ohms

### CDE CD-44  (`cde-cd-44`)

Aliases: TR-44 Series 3 (box-compatible)  
Family **CDE-AC-brake-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap [?], location controller.
- **Brake:** [?]; [?], [?]. Brake type not confirmed (wedge vs disc)
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: 8-wire, interchangeable with Ham-2/3/4/T2X boxes (NORM). Excitation: [?].
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor.
- **Speed:** [?].
- **Cable:** 8 conductors; connector terminal strip; 2 x #18 + 6 x #22 to ~120 ft.
  - Pinout [?]: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, wait, run; on stop remove motor drive, keep brake released for coast-down (stock DCU-1 8 s fixed, DCU-3 0-8 s default 3 s, Rotor-EZ 5 s), then engage brake. Never reverse while turning (DCU-1 manual: reversing hangs the system with brake released); stop, coast, then reverse. Run cap is across terminals 4-8 in the control box.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Verify 500 ohm across 3-7 and cap across 4-8 before connecting (NORM).
- **Notes:** Discontinued 1981; parts via Norm's Rotor Service.
- **Sources:** [NORM], [SRCH]  Unverified fields: brake.type, cable.pinout

### Telex / Hy-Gain (MFJ) AR-40 (TV/light-duty class; AR-500 not researched)  (`hygain-ar-40`)

Aliases: AR-40X  
Family **unsupported**, support **no**, axes az

- **Motor:** [?]; [?]; current [?]; run cap [?], location [?]. Control unit max output 18 VAC
- **Brake:** [?]; [?], [?].
- **Sensor:** [?] [?]. Wiring: 5-wire cable; knob + START button auto-seek box. Excitation: [?].
- **Travel:** 360 deg, overlap 0 deg; limits: CW/CCW end-of-rotation adjustments in control box.
- **Speed:** [?].
- **Cable:** 5 conductors; connector screw terminals 1-5; #22 to 75 ft.
  - Pinout: [?]
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** [?]
- **Gotcha:** Auto-seek TV-class rotator; sensing scheme not in the manual text. Unsupported until a schematic is checked.
- **Sources:** [AR40]  Unverified fields: motor, sensor

### Telex / Hy-Gain HDR-300 / HDR-300A  (`hygain-hdr-300a`)

Aliases: HDR-300AX  
Family **AC-brake-multiturn-pot**, support **v1**, axes az

- **Motor:** ac_pm_split_capacitor; 24 V; current [?]; run cap [?], location rotor. Motor, capacitor, limit switches and pot are inside the rotor; 1/10 HP; thermal breaker in motor
- **Brake:** solenoid_brake_clutch; [?], [?]. 'Low voltage' solenoid brake/clutch on motor shaft, slips above 7500 in-lb. Stock: manual FREE/LOCK switch; coast before locking
- **Sensor:** pot_multiturn_single_ended, 1000 ohm, 3-turn. Wiring: 3-turn wirewound pot: REF pin 8, wiper pin 9, ground pin 10. Excitation: 5 VDC; 0.833-2.500 VDC over 0-360 deg.
- **Travel:** 400 deg, overlap 40 deg; limits: ~20 deg overtravel each way, -20 to +380 deg.
- **Speed:** [?] (Not stated in manual). Duty: Thermal breaker in motor.
- **Cable:** 7 conductors; connector 8-pin at rotor, 10-pin at console; 3 large wires (pins 1,2,3) <= 0.5 ohm each; 4 small (4,8,9,10).
  - Pinout: 1=motor CCW (RT-21 A.9); 2=motor CW; 3=ground / motor common; 4=brake; 8=pot REF (+5 V); 9=pot wiper; 10=pot ground
- **Sequencing / coast:** Release brake (FREE), run, stop, coast, then LOCK. Delay value not specified by Hy-Gain.
- **Soft-start / PWM:** AC: RT-21 uses AC MOTOR mode, MIN SPEED 10 (no PWM).
- **Gotcha:** Only 1/3 of the pot span is used (1.667 V of 5 V for 360 deg); calibrate span, consider ADC gain/offset.
- **Gotcha:** Brake/clutch slips if locked while still turning.
- **Sources:** [HDR], [RT21]  Unverified fields: brake.volts

### Yaesu G-450A / G-650A  (`yaesu-g-450a`)

Aliases: G-450XL (24 VAC, 5-cond), G-400 / G-400RC (same RT-21 table)  
Family **Yaesu-AC-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 24 V [?]; current [?]; run cap 100 uF 60 VAC, location controller. G-450A service-manual parts list: 100 uF 60 VAC (Q9000477); WA1HCO doc: G-400 100 uF 60 VAC. Controller draws 0.5 A from 100-120 VAC
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm [?]. Wiring: 3-wire: 1 REF, 2 wiper, 3 ground. Excitation: [?].
- **Travel:** 450 deg, overlap 90 deg; limits: end stops; OVERLAP LED past 360 deg; stops at ~90 deg (450 total).
- **Speed:** 51-63 s (63 s at 50 Hz, 51 s at 60 Hz). Duty: 3 min continuous (5 min absolute), then rest.
- **Cable:** 6 conductors; connector 7-pin round at rotor (pin 7 unused) / 6-pin rectangular at controller; 6 x 0.5 mm2 (#20) minimum.
  - Pinout: 1=pot REF (+); 2=pot wiper (POS); 3=pot ground; 4=motor CCW / cap; 5=motor CW / cap; 6=motor common
- **Sequencing / coast:** No brake. Manual: do not suddenly reverse rotation -> stop, dwell, reverse.
- **Soft-start / PWM:** AC cap-run: none in stock. RT-21: AC MOTOR mode, MIN SPEED 10.
- **Gotcha:** G-400RC / G-450XL: no REF on pin 1; pot used as variable resistor (RT-21 J6 2-3).
- **Gotcha:** G-600, G-600RC, G-2000RC need RT-21 factory modifications - not covered here.
- **Notes:** 24 VAC confirmed for G-450XL; RT-21 uses its 24 VAC tap for G-450A/650A.
- **Sources:** [G450A], [RT21], [G450SM], [G450XL], [WA1HCO]  Unverified fields: sensor.ohms, motor.volts

### Yaesu G-5500 (AC, az-el)  (`yaesu-g-5500`)

Family **Yaesu-AC-pot**, support **v1-2axis**, axes az+el

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap 100 uF, location rotor. 100 uF phase cap inside the motor housing ('unlike other versions')
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm. Wiring: 3-wire per axis; 500 ohm 360 deg pots. Excitation: [?].
- **Travel:** 450 deg, overlap 90 deg; limits: az: end stops; el: 0-180 deg.
- **Speed:** 58 s (az 58 s/360 deg, el 67 s/180 deg (approx., 60 Hz)). Duty: 5 min intermittent, then >= 15 min rest.
- **Cable:** 6 conductors; connector 7-pin metal connector per rotator; 8-pin DIN external control.
  - Pinout [?]: 1=pot REF (+); 2=pot wiper (POS); 3=pot ground; 4=motor CCW / cap; 5=motor CW / cap; 6=motor common
- **Sequencing / coast:** No brake. Stock box turns right/up if both buttons pressed; our interlock forbids both.
- **Soft-start / PWM:** AC: none.
- **Gotcha:** Cap is in the rotor: do NOT add a second run cap in the controller.
- **Gotcha:** Ext. control DIN: pin 6 az 2-4.5 VDC (0-450 deg), pin 1 el 2-4.5 VDC (0-180 deg), pins 2/4/3/5 to pin 8 = R/L/D/U (alongside-mode option).
- **Notes:** Rotor pinout assumed same as G-450A family (cap across 4-5).
- **Sources:** [G5500], [AMSATC], [AMSATP]  Unverified fields: cable.pinout

### Yaesu G-550 (elevation)  (`yaesu-g-550`)

Family **Yaesu-AC-pot**, support **v1-2axis**, axes el

- **Motor:** ac_split_phase_cap_run; 24 V; current [?]; run cap [?], location [?]. 30 VA consumption
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm [?]. Wiring: 500 ohm, 360 deg continuous pot. Excitation: [?].
- **Travel:** 180 deg, overlap 0 deg; limits: 0-180 deg.
- **Speed:** [?] (~67 s per 180 deg at 60 Hz).
- **Cable:** 6 conductors; connector [?]; #20 or larger.
  - Pinout: [?]
- **Sequencing / coast:** No brake; stop before reverse.
- **Soft-start / PWM:** AC: none.
- **Notes:** Manual seen only via search excerpt.
- **Sources:** [G550], [AMSATP]  Unverified fields: sensor.ohms, speed

### Kenpro KR-400 / KR-600(RC) / KR-1000 / KR-2000; KR-5400/5600 az-el  (`kenpro-kr-series`)

Aliases: Kenpro (later Yaesu G-series)  
Family **Yaesu-AC-pot**, support **v1**, axes az (KR-5x00: az+el)

- **Motor:** ac_split_phase_cap_run; 24 V [?]; current [?]; run cap [?], location [?].
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm. Wiring: VR5 gear-driven pot in rotor; 500 ohm on schematic; one unit measured 41-650 ohm. Excitation: [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** 53-63 s (KR-600RC: 53 s at 60 Hz, 63 s at 50 Hz).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** No brake; stop before reverse.
- **Soft-start / PWM:** AC: none.
- **Gotcha:** Measured pot can exceed nominal 500 ohm; calibration must not assume 500.
- **Notes:** Assumed electrically similar to early Yaesu G-400/G-600; confirm pinout per model.
- **Sources:** [KR600], [KRMUS]  Unverified fields: motor.volts, travel, cable

### Daiwa MR-750 / MR-300  (`daiwa-mr-750`)

Aliases: Diawa (RT-21 spelling)  
Family **Yaesu-AC-pot**, support **v1**, axes az

- **Motor:** ac_cap_run; [?]; current [?]; run cap [?], location [?]. Stock box picked motor voltage with terminal 7/8/9 (higher taps for long runs); RT-21 uses its 24 VAC or 36 VAC tap
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: 1 REF, 2 wiper, 3 ground. Excitation: [?].
- **Travel:** [?], overlap [?]; limits: 'slight over-travel' (RT-21).
- **Speed:** [?].
- **Cable:** [?] conductors; connector terminal strip.
  - Pinout: 1=pot REF; 2=pot wiper; 3=ground; 5=motor CCW; 6=motor CW; 7/8/9=motor common, increasing voltage taps
- **Sequencing / coast:** Stop before reverse.
- **Soft-start / PWM:** AC: RT-21 AC MOTOR mode, no PWM.
- **Gotcha:** Motor tap selection maps to our transformer choice (24 vs 36 VAC).
- **Sources:** [RT21]  Unverified fields: motor.volts

### Create (CD Corp, Japan) RC5-1 / RC5-3 / RC5A-2 / RC5A-3 / RC5B-3 / RC5B-4 (+P variants)  (`create-rc5`)

Aliases: Create RC5 series  
Family **Yaesu-AC-pot**, support **v1**, axes az

- **Motor:** ac_cap_run; 28 V [?]; current [?]; run cap [?], location [?]. Power 90 VA (RC5-1/3), 150 VA (RC5A), 200 VA (RC5B); RT-21 uses its 24 VAC tap
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: 4 REF, 5 wiper, 6 ground; 7 = stock indicator (unused by RT-21). Excitation: [?].
- **Travel:** [?], overlap [?]; limits: 'slight over-travel' (RT-21).
- **Speed:** 60-150 s (RC5-3/RC5A: 75-110 s (50 Hz) / 60-95 s (60 Hz); RC5B: 95-150 / 80-125 s; variable in stock box).
- **Cable:** 7 conductors; connector [?].
  - Pinout: 1=motor common (GND); 2=motor CW; 3=motor CCW; 4=pot REF; 5=pot wiper; 6=ground; 7=stock indicator (not used)
- **Sequencing / coast:** Create specifies a reversal time: 0 s (RC5-1), 1 s (RC5-3), 2 s (RC5A), 3 s (RC5B).
- **Soft-start / PWM:** Stock boxes have 'speed control circuits' on an AC motor (method not documented). RT-21: AC MOTOR mode, MIN SPEED 10.
- **Gotcha:** Pot value unverified: a 5 kohm 'RC-Poti' replacement is sold by UKW-Berichte; confirm before fixing excitation.
- **Gotcha:** RC5-1DC variant: 12-15 VDC, 5-core (belongs in DC-pot).
- **Sources:** [CREATE], [RT21], [KUR02C]  Unverified fields: motor.volts, sensor.ohms

### Alliance HD-73  (`alliance-hd-73`)

Aliases: HD-73-1  
Family **Yaesu-AC-pot**, support **v1**, axes az

- **Motor:** ac_split_phase_cap_run; 20 V [?]; current [?]; run cap 155 uF [?] 50 VAC, location controller. Reversible capacitor split-phase motor with center-tapped winding
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended_low_ohm, 75 ohm. Wiring: 2 wiper, 4 and 5 pot ends; RT-21 inserts 75-100 ohm in series with REF (terminal 5). Excitation: [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** [60, None] s [?] (Dual speed: 1 RPM (60 s/360) plus slower 'pinpoint' speed).
- **Cable:** 6 conductors; connector 6-screw terminal strip both ends; #20 stranded to 125 ft.
  - Pinout: 1=motor winding end (CW) + cap; 2=pot wiper; 3=winding center tap (common); 4=pot end (ground); 5=pot end (REF); 6=motor winding end (CCW) + cap
- **Sequencing / coast:** Stop before reverse.
- **Soft-start / PWM:** AC: RT-21 AC MOTOR mode. Stock dual-speed method not documented.
- **Gotcha:** 75 ohm pot: excitation must be current-limited (5 V across 75 ohm = 67 mA).
- **Gotcha:** Cap goes across winding ends 1-6, the same nodes as the drive outputs.
- **Notes:** Alliance stopped production in 1994 (NORM).
- **Sources:** [HD73P], [RT21], [HD73M], [NORM]  Unverified fields: motor.volts, motor.cap_uf, motor.cap_vac, speed

### Alliance U-110 / U-100 Tenna-Rotor  (`alliance-u-110`)

Family **unsupported**, support **no**, axes az

- **Motor:** ac; 24 V [?]; current [?]; run cap [?], location [?].
- **Brake:** [?]; [?], [?].
- **Sensor:** [?] [?]. Wiring: 4-conductor cable, fully automatic dial. Excitation: [?].
- **Travel:** 360 deg, overlap 0 deg; limits: [?].
- **Speed:** 60 s (1 RPM).
- **Cable:** 4 conductors; connector screw terminals 1-4.
  - Pinout: [?]
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** [?]
- **Gotcha:** TV rotator; sensing scheme unknown with only 4 wires. Not a target.
- **Sources:** [U110]  Unverified fields: sensor, motor

### Orion (pre-M2) OR-2300 (original)  (`orion-or-2300`)

Family **Yaesu-AC-pot**, support **v1**, axes az

- **Motor:** ac_cap_run; [?]; current [?]; run cap [?], location [?].
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: 4 REF, 5 wiper, 6 ground. Excitation: [?].
- **Travel:** 360 deg, overlap [?]; limits: CCW mechanical limit at 180 deg from center.
- **Speed:** [?].
- **Cable:** 6 conductors; connector [?].
  - Pinout: 1=motor ground; 2=motor CCW; 3=motor CW; 4=pot REF; 5=pot wiper; 6=ground
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** AC: RT-21 AC MOTOR mode.
- **Sources:** [RT21]  Unverified fields: motor.volts

### Prosistel PST-51 / PST-61 / PST-71 (older 48 VAC, Model A/B/C box)  (`prosistel-ac-48v`)

Family **AC48-pot**, support **check**, axes az

- **Motor:** ac_cap_run; 48 V; current [?]; run cap [?], location controller. 'High starting torque 48 VAC capacitance motor'; 110 W (51/61), 190 W (71); caps on control-box PCB; stock box switches each line with opto-triacs
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, 10000 ohm. Wiring: +12 V and -12 V across pot (pins 4/3), wiper P on pin 1. Excitation: +/-12 VDC (bipolar).
- **Travel:** 440 deg, overlap 80 deg [?]; limits: none in rotor; electronic limits (comparator) in box.
- **Speed:** 70-130 s (PST 51: 70 s, PST 61: 100 s, PST 71: 130 s).
- **Cable:** 7 conductors; connector 8-pin, 7 used; 3 heavier wires for motor.
  - Pinout: 1=pot wiper (P); 2=motor CCW (F2); 3=-12 VDC to pot; 4=+12 VDC to pot; 5=motor common (F1); 6=n/c; 7=motor CW (F3); 8=ground
- **Sequencing / coast:** Stop before reverse.
- **Soft-start / PWM:** AC: none.
- **Gotcha:** 48 VAC motor: needs a 48 VAC transformer; peak line plus cap voltage may exceed the SMAJ90CA 90 V standoff.
- **Gotcha:** Bipolar pot excitation: a passive pot can be driven 0/+V instead, but calibration then differs from stock.
- **Notes:** Overlap inferred from 440 deg total range.
- **Sources:** [PST01]  Unverified fields: travel.overlap_deg

### Yaesu G-800DXA / G-1000DXA / G-2800DXA  (`yaesu-g-dxa`)

Aliases: G-800DXC/G-1000DXC/G-2800DXC (older, same rotor scheme), G-800SA (DC)  
Family **DC-pot**, support **v2-dc**, axes az

- **Motor:** dc_pm; 24 V (range 11-24 V); current [?]; run cap [?], location [?]. Variable DC, ~11-24 V (K9YC). Motor 8.75 ohm -> ~2.7 A stall-limited at 24 V [estimate]
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm. Wiring: 1 REF, 2 wiper, 3 cold end bonded to rotor chassis. Excitation: [?].
- **Travel:** 450 deg, overlap 90 deg; limits: in motor leads (pins 4-5); 450 +/-3 deg.
- **Speed:** 40-120 s (800/1000DXA: 100-40 s; 2800DXA: 120-50 s (variable)). Duty: 3 min continuous / 5 min absolute.
- **Cable:** 6 conductors; connector 6-pin (rotor) / round at controller.
  - Pinout: 1=pot high end (REF); 2=pot wiper; 3=pot cold end, bonded to rotor chassis; 4=motor (through limit switch); 5=motor (through limit switch); 6=n/c
- **Sequencing / coast:** No brake. 2800DXA stock does automatic slow start/stop. Ramp DC down before reversing.
- **Soft-start / PWM:** DC: PWM fully supported (RT-21 1.2 kHz, ramps). RT-21 sets CW limit +90 for overlap.
- **Gotcha:** Pot cold end is chassis: rotor chassis/tower ground ties to the pot reference - grounding noise.
- **Gotcha:** Do not apply AC drive (DC PM motor).
- **Sources:** [DXA], [K9YC], [DXC], [RT21]  Unverified fields: motor.current_a

### Yaesu G-450ADC / G-450CDC  (`yaesu-g-450adc`)

Family **DC-pot**, support **v2-dc**, axes az

- **Motor:** dc_pm; 22 V (range 20-22 V); current [?]; run cap [?], location [?]. ~20 VDC (manual text) / 22 V (spec table); controller fuse 3 A
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_rheostat, 500 ohm [?]. Wiring: Round connector pins 1, 6, 7 unused: pot used as 2-terminal variable resistor. Excitation: current source / pull-up.
- **Travel:** 450 deg, overlap 90 deg; limits: mechanical.
- **Speed:** 56 s (~56 s/360 deg).
- **Cable:** 4 [?] conductors; connector round at rotor.
  - Pinout: [?]
- **Sequencing / coast:** Ramp down before reversing.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** Rheostat sensor: measure resistance (current source or divider with known R), not a ratio.
- **Sources:** [G450ADC], [WRC]  Unverified fields: sensor.wiring, sensor.ohms, cable.conductors

### Yaesu G-5500DC (az-el)  (`yaesu-g-5500dc`)

Family **DC-pot**, support **v2-dc**, axes az+el

- **Motor:** dc_pm; 22 V; current [?]; run cap [?], location [?].
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: Ext. control outputs 2-4.5 VDC az and el, 10 kohm. Excitation: [?].
- **Travel:** 450 deg, overlap 90 deg; limits: az 450 deg, el 180 deg.
- **Speed:** 60 s (az ~60 s/360, el ~65 s/180).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** Ramp down before reversing.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** Rotor-side pinout not confirmed (manual is Japanese).
- **Sources:** [G5500DC]  Unverified fields: sensor.ohms, cable

### Yaesu G-800S / G-800SDX / G-1000SDX  (`yaesu-g-800sdx`)

Family **DC-pot**, support **later**, axes az

- **Motor:** [?]; [?]; current [?]; run cap [?], location [?]. SDX = DC variable-speed (per name); no text manual found
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, ohms [?] [?]. Wiring: [?]. Excitation: [?].
- **Travel:** 450 deg [?], overlap 90 deg [?]; limits: [?].
- **Speed:** [?].
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** [?]
- **Gotcha:** Manual found only as an image scan.
- **Notes:** Use generic-dc-pot preset until verified.
- **Sources:** [DXC]  Unverified fields: motor, sensor, travel

### Prosistel PST-61D / PST-71D / PST-2051D / PST-110D (D series)  (`prosistel-d`)

Aliases: PST-71D Big Boy  
Family **DC-pot**, support **v2-dc**, axes az

- **Motor:** dc_pm; 24 V (range 12-42 V [?]); current [?]; run cap [?], location [?]. PST-71D 24 VDC; PST-61D 12 VDC [summary]; RT-21 taps 18 V (61D, 2051D), 28 V (newer 71D), 42 V (older 71D)
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: 3 wiper, 4 REF, 5 ground. Excitation: RT-21 table: wiper reads 5.01 V CCW limit / 5.40 V center / 5.79 V CW limit; must lie 4.7-6.3 V [?].
- **Travel:** 500 deg, overlap 140 deg; limits: NONE - 70 + 360 + 70 deg, soft limits only (prosistel.biz).
- **Speed:** 90-100 s (~90-100 s per 360 at nominal voltage).
- **Cable:** 5 conductors; connector [?]; 2 x 1 mm2 (motor) + 3 x 0.5 mm2.
  - Pinout: 1=motor CW; 2=motor CCW; 3=pot wiper; 4=pot REF; 5=ground
- **Sequencing / coast:** Ramp up/down [proposed]. Soft limits mandatory.
- **Soft-start / PWM:** DC: PWM OK (RT-21 supports).
- **Gotcha:** No limit switches: a calibration sweep must NOT drive to a mechanical stop; operator sets ends.
- **Gotcha:** Narrow 0.78 V wiper window around ~5.4 V: needs offset/gain or a high-resolution ADC.
- **Gotcha:** Wrong motor voltage tap overheats or underpowers (RT-21 table by model/age).
- **Notes:** Excitation voltage used to produce the ~5.4 V reading is not stated in the table I read.
- **Sources:** [RT21], [PST71], [PST61S]  Unverified fields: motor.volts_range, sensor.excitation

### TIC General Ring Rotor (1022/1032 etc.)  (`tic-ringrotor`)

Family **DC-pot**, support **v2-dc**, axes az (around tower)

- **Motor:** dc_pm; 13.8 V; current [?]; run cap [?], location [?]. RT-21 uses 13.8 V tap
- **Brake:** none_gear; [?], [?].
- **Sensor:** pot_single_ended, 500 ohm. Wiring: 4 CW end, 5 wiper, 6 CCW end; 250 ohm at center. Excitation: [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** [?].
- **Cable:** [?] conductors; connector [?].
  - Pinout: 2=motor; 3=motor; 4=pot CW end; 5=pot wiper; 6=pot CCW end
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** DC: PWM OK.
- **Sources:** [RT21]  Unverified fields: travel

### Rotor Doctor RD-1800  (`rotordoctor-rd-1800`)

Family **DC-pot**, support **v2-dc**, axes az

- **Motor:** dc_pm; [?]; current [?]; run cap [?], location [?].
- **Brake:** [?]; [?], [?].
- **Sensor:** pot_single_ended, ohms [?]. Wiring: 7 REF, 4 wiper, 3 ground. Excitation: [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** [?].
- **Cable:** [?] conductors; connector [?].
  - Pinout: 1=motor CW; 2=motor CCW; 3=ground; 4=pot wiper; 7=pot REF
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** DC: PWM OK.
- **Sources:** [RT21]  Unverified fields: motor

### SPID / Alfa Radio (AlfaSpid) RAK  (`spid-rak`)

Aliases: Alfa Spid RAK  
Family **DC-pulse**, support **v2-dc**, axes az

- **Motor:** dc_pm; 24 V (range 12-24 V); current [?]; run cap [?], location [?].
- **Brake:** none; [?], [?]. No electrical brake; holding mechanism not verified in sources
- **Sensor:** reed_pulse, 1 pulses/deg. Wiring: 2-wire reed (impulse) pair. Excitation: pull-up from controller.
- **Travel:** 720 deg [?], overlap 360 deg; limits: NONE (RT-21: no limit switches); soft limits only.
- **Speed:** 60-120 s (120 / 90 / 60 s per 360 at 12 / 18 / 24 V).
- **Cable:** 4 conductors; connector screw terminals / 4-pin DIN (Rot2Prog).
  - Pinout: 1=motor; 2=motor; 3=impulse; 4=impulse
- **Sequencing / coast:** Count pulses through coast; store count in FRAM; ramp down. No home: position is lost if count is lost -> recal against a mark.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** Relative sensor: must persist count across power loss (FRAM + power-fail).
- **Gotcha:** RF induces false pulses: shielded cable + debounce (SPID MD).
- **Gotcha:** No limit switches: soft limits and stall (no-pulse) timeout mandatory.
- **Sources:** [ALFA], [RT21], [SPIDMD]  Unverified fields: travel.range_deg

### SPID / Alfa Radio BIG-RAK  (`spid-big-rak`)

Family **DC-pulse**, support **v2-dc**, axes az

- **Motor:** dc_pm; [?] (range 12-24 V); current [?]; run cap [?], location [?]. Controller 12-18 V, 3-5 A (RF Hamdesign)
- **Brake:** none; [?], [?]. No electrical brake; holding mechanism not verified in sources
- **Sensor:** reed_pulse, 2 [?] pulses/deg. Wiring: 2-wire reed. Excitation: pull-up.
- **Travel:** [?], overlap [?]; limits: NONE.
- **Speed:** 60-210 s [?] (Alfa sheet: 120/90/60 s; RF Hamdesign: 210/140/100 s (conflict)).
- **Cable:** 4 conductors; connector 4-pin DIN.
  - Pinout: [?]
- **Sequencing / coast:** As RAK.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** Specs conflict between sources (range 720 vs 360, speed); resolve on the bench.
- **Sources:** [ALFA], [BIGRAK], [SPIDMD]  Unverified fields: sensor.pulses_per_deg, travel.range_deg, speed

### SPID / Alfa Radio RAS / BIG-RAS (az-el); HR variants  (`spid-ras`)

Aliases: RAS/HR, BIG-RAS/HR  
Family **DC-pulse**, support **v2-dc**, axes az+el

- **Motor:** dc_pm; [?] (range 13.8-24 V); current 3.0 A; run cap [?], location [?]. 2-3 A, up to 3-5 A in wind (RAS manual). BIG-RAS/HR: 24-30 V up to 12 A (SPID MD)
- **Brake:** none; [?], [?]. No electrical brake; holding mechanism not verified in sources
- **Sensor:** reed_pulse, 1 [?] pulses/deg. Wiring: per axis 2-wire impulse; HR versions: two Hall sensors (quadrature-like). Excitation: pull-up; Hall needs supply.
- **Travel:** [?], overlap [?]; limits: NONE; Rot2Prog allows 180 deg over-travel each side of 360.
- **Speed:** 60-120 s (az 120/60 s, el 80/40 s (12/24 V)).
- **Cable:** 8 conductors; connector [?].
  - Pinout: 1=az motor; 2=az motor; 3=az impulse; 4=az impulse; 5=el motor; 6=el motor; 7=el impulse; 8=el impulse
- **Sequencing / coast:** Stop if no pulses arrive (stall). Count through coast.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** HR gear constants (MD fw>=2.0): RAS/HR 0.031250, BIG-RAS/HR 0.023438 deg per count; non-HR 0.5 or 1.0 - exact semantics [?].
- **Gotcha:** BIG-RAS current up to 12 A exceeds the planned 5 A DC module.
- **Sources:** [RAS], [SPIDMD], [ALFA]  Unverified fields: sensor.pulses_per_deg

### M2 Antenna Systems OR2800PX (DC) with RC2800PX  (`m2-or2800px`)

Aliases: Orion 2800 DC  
Family **DC-pulse**, support **v2-dc**, axes az

- **Motor:** dc_pm; [?] (range 28-42 V); current 3.2 A; run cap [?], location [?]. Motor 28-42 VDC (OR2800 spec); RC2800 output 27 VDC 3.2 A; bench ~45 V open / 30-35 V loaded
- **Brake:** none; [?], [?]. No electrical brake [?]
- **Sensor:** reed_pulse, 11 pulses/deg. Wiring: reed on terminals 5 (+) and 6 (return); ~11.3 V open, ~5 mA closed. Excitation: ~12 V wetting.
- **Travel:** 360 deg, overlap 0 deg; limits: CW/CCW limit switches; 0-360 +/-14 deg.
- **Speed:** 55-270 s (variable with ramp).
- **Cable:** 4 conductors; connector terminal strip.
  - Pinout: 1=motor CCW; 2=motor CW; 5=reed +; 6=reed return
- **Sequencing / coast:** Ramp up/down (stock); count through coast.
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** 3960 pulses per 360 deg typical (11/deg), some units 4015 - calibrate ppd.
- **Gotcha:** ~45 V open-circuit supply exceeds 42 V; check DC module rating.
- **Sources:** [M2RC], [M2OR]

### Orion (pre-M2) OR2800 (older AC)  (`orion-or2800-ac`)

Family **AC-pulse**, support **v1**, axes az

- **Motor:** ac_cap_run; [?]; current [?]; run cap [?], location [?].
- **Brake:** [?]; [?], [?].
- **Sensor:** reed_pulse, pulses/deg [?]. Wiring: 5 POS, 6 GND. Excitation: pull-up.
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** [?].
- **Cable:** 6 conductors; connector [?].
  - Pinout: 1=motor GND; 2=motor CCW; 3=motor CW; 5=pulse POS; 6=pulse GND
- **Sequencing / coast:** Count through coast.
- **Soft-start / PWM:** AC: none.
- **Sources:** [RT21]  Unverified fields: sensor.pulses_per_deg

### Prosistel PST-71D PRO / RR55D-PRO (encoder)  (`prosistel-pro`)

Family **DC-encoder**, support **later**, axes az

- **Motor:** dc_pm; [?]; current [?]; run cap [?], location [?].
- **Brake:** none; [?], [?]. No electrical brake [?]
- **Sensor:** encoder_2bit, pulses/deg [?] [?]. Wiring: 3 V+, 4 GND, 5 sensor out. Excitation: powered [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** [?].
- **Cable:** 5 conductors; connector [?].
  - Pinout: 3=encoder V+; 4=GND; 5=sensor out
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** DC: PWM OK.
- **Gotcha:** RT-21 divide ratio 23750 (71D PRO) / 16000 (RR55D-PRO); counts per degree derive from that.
- **Sources:** [RT21]  Unverified fields: sensor

### Telex / Hy-Gain DCU-1 Pathfinder / DCU-2 / DCU-3 (controllers)  (`alias-telex-dcu`)

Aliases: T-2XD3, HAM-IVD3  
Maps to presets: hygain-ham-iv, hygain-ham-v, hygain-t2x, hygain-cd-45ii  
Family **CDE-AC-brake-pot**, support **alias**, axes az

- **Motor:** [?]; [?]; current [?]; run cap [?], location [?].
- **Brake:** wedge_solenoid; [?], [?]; engage after stop 0-8 s. DCU-1: fixed 8 s; DCU-3: 0-8 s, default 3 s
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: CDE 8-wire. Excitation: DCU-3: 8-9 VDC open.
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor.
- **Speed:** [?].
- **Cable:** 8 conductors; connector Cinch 8-pin / terminal strip.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Copy DCU behaviour: short reverse at start, coast setting 0-10 deg (DCU-3), half-speed last 5 deg (DCU-1), no-motion stop 8 s.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** These are controllers, not rotors: a user replacing one picks the rotor preset; DCU timings are the defaults to copy.
- **Sources:** [DCU3], [HAM5]

### Idiom Press Rotor-EZ (board in CDE/Hy-Gain box)  (`alias-rotor-ez`)

Maps to presets: hygain-ham-iv, hygain-t2x, hygain-cd-45ii, cde-ham-ii, cde-ham-iii  
Family **CDE-AC-brake-pot**, support **alias**, axes az

- **Motor:** [?]; [?]; current [?]; run cap [?], location [?].
- **Brake:** wedge_solenoid; [?], [?]; engage after stop 5 s. Fixed 5 s brake delay
- **Sensor:** pot_dual_end_grounded_wiper, 500 ohm. Wiring: uses stock box pot circuit. Excitation: [?].
- **Travel:** 360 deg, overlap 0 deg; limits: in rotor.
- **Speed:** [?].
- **Cable:** 8 conductors; connector Jones plug numbering 7 5 3 1 / 8 6 4 2.
  - Pinout: 1=common: motor windings, brake, pot wiper (heavy wire); 2=brake solenoid (heavy wire); 3=pot end (+, ~13 VDC in stock box); 4=motor winding end / run cap; 5=CW drive (via right limit sw. to 8); 6=CCW drive (via left limit sw. to 4); 7=pot end (-); 8=motor winding end / run cap
- **Sequencing / coast:** Release brake, run, 5 s brake delay.
- **Soft-start / PWM:** Not recommended. RT-21 found HAMx/T2X the least responsive to its low-frequency AC PWM and ships AC rotors at MIN SPEED=10 (no PWM). DCU-1 uses half-cycle motor pulses over the last 5 deg as a creep mode; triac half-cycle/cycle skipping can mimic this.
- **Gotcha:** Board-in-box add-on; not a rotor. Use the rotor preset.
- **Sources:** [REZ]

### EMOTO (Emotator, Japan) Emotator 103/502/747/1102/1103/1105/1200 series (SX/MXX/FX)  (`emoto-emotator`)

Family **mixed**, support **later**, axes az (some az-el)

- **Motor:** mixed; [?]; current [?]; run cap [?], location [?]. Many AC models 100 VAC (out of scope), some 24 VAC; DC models 12 or 24 V
- **Brake:** mixed; [?], [?]. Varies by model
- **Sensor:** pot_single_ended, ohms [?] [?]. Wiring: [?]. Excitation: [?].
- **Travel:** [?], overlap [?]; limits: [?].
- **Speed:** 35-170 s (AC 47-110 s, DC 35-170 s).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** [?]
- **Soft-start / PWM:** [?]
- **Gotcha:** Spec table columns are merged in the source; per-model numbers not extracted.
- **Gotcha:** 100 VAC motors are not supported by the 20-36 VAC triac stage.
- **Notes:** Per-model verification needed before any preset is published.
- **Sources:** [EMO]  Unverified fields: motor, sensor, travel

### Generic AC capacitor-run motor + pot  (`generic-ac-pot`)

Family **generic**, support **v1**, axes az|el

- **Motor:** ac_split_phase_cap_run; 24 V (range 20-36 V); current [?]; run cap [?], location user. User sets cap location (none / board / rotor)
- **Brake:** optional; 24 V, [?]. Brake output optional
- **Sensor:** pot_any, ohms [?]. Wiring: dual-end grounded wiper | single-ended | rheostat. Excitation: selectable.
- **Travel:** 360 deg, overlap 0 deg; limits: user.
- **Speed:** [?] (learned by calibration sweep). Duty: user (default 3 min).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** Defaults [proposed, bench-tune]: brake release 0.5 s before run, coast delay 3 s, reverse dwell 2 s, stall timeout 8 s.
- **Soft-start / PWM:** AC: none / half-cycle creep.
- **Sources:** [RT21], [DCU3]

### Generic DC PM motor + pot  (`generic-dc-pot`)

Family **generic**, support **v2-dc**, axes az|el

- **Motor:** dc_pm; [?] (range 12-48 V); current [?]; run cap [?], location [?]. DC module 12-48 V, 5 A
- **Brake:** optional; [?], [?].
- **Sensor:** pot_any, ohms [?]. Wiring: single-ended | rheostat. Excitation: selectable.
- **Travel:** 360 deg, overlap 0 deg; limits: user.
- **Speed:** [?] (learned).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** Ramp up/down [proposed: 1 s ramps].
- **Soft-start / PWM:** DC PWM (~1.2 kHz like RT-21, or ultrasonic).
- **Sources:** [RT21]

### Generic DC PM motor + pulse sensor (reed / Hall / encoder)  (`generic-dc-pulse`)

Family **generic**, support **v2-dc**, axes az|el

- **Motor:** dc_pm; [?] (range 12-48 V); current [?]; run cap [?], location [?].
- **Brake:** optional; [?], [?].
- **Sensor:** pulse_any, pulses/deg [?]. Wiring: 1 or 2 channels. Excitation: 5 / 12 V pull-up.
- **Travel:** 360 deg, overlap 0 deg; limits: user; soft limits required if none.
- **Speed:** [?] (learned).
- **Cable:** [?] conductors; connector [?].
  - Pinout: [?]
- **Sequencing / coast:** Ramp; count through coast; FRAM persist.
- **Soft-start / PWM:** DC PWM.
- **Sources:** [RT21], [SPIDMD]


## Preset families and the settings each one exposes

All presets share these settings:
- `axis` (az/el); `range_deg`; `overlap_deg`; `soft_limit_ccw` and `soft_limit_cw`
- `stall_timeout_s`, default 8 s, the same as the DCU-1/DCU-3 no-motion stop
- `reverse_dwell_s`; `coast_deg`, learned
- `s_per_360`, learned, since speed differs between 50 and 60 Hz
- `max_run_s`, the duty limit; `cal_points`

Each family adds the settings below.

1. **CDE-AC-brake-pot**
   - Members: Ham-M S3–5, Ham-II, Ham-III, HAM-IV, HAM-V, T2X, CD-44. The aliases Rotor-EZ and DCU-1/2/3 load these presets.
   - Settings:
     - `brake_release_lead_s`
     - `brake_engage_delay_s`: 0–8 s, default 3 (DCU-3); DCU-1 uses 8 and Rotor-EZ uses 5
     - `prestart_reverse_ms`: the T2X brake-stick bump, off by default for the others
     - `creep_zone_deg`: default 5 (DCU-1), with `creep_mode` = half-cycle triac
     - `limit_margin_deg`: 5 for T2X (RT-21)
     - `run_cap_location`: board on 4–8
     - `pot_mode` = dual-end grounded wiper (500 Ω)
     - `ac_notch` = on
   - Ham-M Series 1/2 is **not** a preset. The UI must show the 3–7 = 500 Ω / 4–8 = cap check.
2. **CDE-AC-nobrake-pot**
   - Member: CD-45-II.
   - Same as family 1 with the brake output disabled.
3. **Yaesu-AC-pot**
   - Members: G-450A/650A/G-400/G-450XL, G-5500 (2 axes), G-550 (el), Kenpro KR, Daiwa, Create RC5, Alliance HD-73, Orion OR-2300.
   - Settings:
     - `pot_mode`: single-ended or rheostat. Rheostat covers G-400RC and G-450XL.
     - `pot_ohms`: 500 typical; HD-73 is 75 (low-ohm, current-limited).
     - `run_cap_location`: board (across the CW/CCW ends) or rotor (G-5500).
     - `motor_vac_tap`: 24 by default; 36 for long Daiwa runs.
     - `reverse_dwell_s`: Create specifies 0/1/2/3 s.
     - `overlap_deg` = 90 for 450° Yaesu.
     - No brake.
4. **AC-brake-multiturn-pot**
   - Member: HDR-300/300A.
   - Settings:
     - `pot_mode` single-ended 1 kΩ 3-turn; `pot_span_fraction` = 1/3
     - `range` −20° to 380°
     - `brake_engage_delay_s`
     - `run_cap_location` = rotor (no board cap)
5. **AC48-pot**
   - Member: old Prosistel PST-51/61/71.
   - Settings:
     - `motor_vac` = 48
     - `pot_excitation`: bipolar ±12 V emulated, or unipolar re-excitation
     - `soft limits` (no limit switches in the rotor)
   - Hardware check needed first (see below).
6. **DC-pot**
   - Members: Yaesu DXA/DXC/G-450ADC/G-5500DC/SDX, Prosistel D, TIC Ring Rotor, Rotor Doctor.
   - Settings:
     - `motor_vdc`
     - `pwm_min_pct`, `pwm_max_pct`, `ramp_up_s`, `ramp_down_s`
     - `pot_mode`: single-ended or rheostat (G-450ADC)
     - `pot_window_v`: Prosistel D, 4.7–6.3 V
     - `soft_limits_required`: Prosistel D
     - `current_limit_a`
7. **DC-pulse**
   - Members: SPID RAK/BIG-RAK/RAS, M2 OR2800PX.
   - Settings:
     - `pulses_per_deg` (1, 2, or 11 for M2, which is 3960 per 360°, with some units at 4015); `pulse_channels` 1/2 (HR Hall)
     - `pullup_v`: 5 or 12
     - `debounce_us`
     - `count_through_coast`
     - `fram_persist`
     - `no_pulse_stall_s`
     - `home_reference`: none, limit switch (M2), or manual mark (SPID)
     - `soft_limits_required`: SPID
     - The ramps and current limit from family 6
8. **AC-pulse**
   - Member: Orion OR2800 (AC).
   - Settings: the AC settings of family 3 plus the pulse settings of family 7.
9. **DC-encoder**
   - Member: Prosistel PRO.
   - Settings: `encoder_divide_ratio` (23750 or 16000), plus the DC settings.
10. **generic**
    - Presets: generic-ac-pot, generic-dc-pot, generic-dc-pulse.
    - Every setting is exposed, with defaults [proposed, bench-tune]:
      - brake lead 0.5 s
      - coast/brake delay 3 s
      - reverse dwell 2 s
      - stall timeout 8 s
      - DC ramps 1 s
11. **unsupported / later**
    - Unsupported: AR-40 and U-110 (TV class, sensing unknown).
    - Later: EMOTO (many are 100 VAC), G-800SDX (no data).

## Hardware implications for the V4/F407 board

1. **Pot front end needs three modes, chosen per axis in software:**
   - CDE dual-end grounded wiper (500 Ω, wiper on the motor/brake common, with 60 Hz ripple).
   - Single-ended (150 Ω–10 kΩ).
   - Rheostat (G-400RC, G-450XL, G-450ADC). Rheostat mode needs a known current source or a reference resistor.
   - A 75 Ω pot (HD-73) needs current-limited excitation, about 20–30 mA at most, and must not be put straight across 5 V (67 mA). Add a series resistor footprint (RT-21 uses 75–100 Ω).
2. **ADC dynamic range.**
   - HDR-300 uses only a third of its 3-turn pot (0.83–2.5 V).
   - Prosistel D spans only about 0.78 V around 5.4 V.
   - Provide a programmable offset/gain stage, or an external 16–24-bit ADC, and allow excitation above 3.3 V (5 V and possibly 8–13 V) on the pot REF output.
3. **Bipolar excitation.** Old Prosistel pots use ±12 V. A unipolar REF works for the passive pot, so no −12 V rail is needed; note this in the docs.
4. **Pulse inputs.**
   - Two channels per axis: SPID HR has two Hall sensors, Prosistel PRO has an encoder.
   - Pull-up selectable between 5 V and 12 V, about 5 mA wetting current for reeds (M2 runs about 11.3 V / 5 mA).
   - RC filter, hysteresis, and ESD/RF protection, because SPID reports RF-induced false pulses.
   - Rates stay under 1 kHz, about 72 Hz for M2, so timer capture or EXTI is enough.
   - Keep FRAM, power-fail detection, and counting through coast-down.
5. **AC drive.**
   - Transformer and tap range of 20–36 VAC: HD-73 20, Yaesu/Kenpro 24, CDE 26–30, Create 28, Daiwa up to 36.
   - Old Prosistel at 48 VAC exceeds the plan: the SMAJ90CA's 90 V standoff can be reached by the cap-phase winding voltage. Mark it unsupported or use a higher-rated TVS/triac snubber option.
6. **Run-cap topology must be configurable.**
   - CDE: cap on 4–8, with drive on 5/6 through the rotor limit switches.
   - Yaesu/HD-73: cap across the two drive ends.
   - G-5500 and HDR-300: the cap is in the rotor, so the board cap must be absent.
   - Use a jumper or relay, and keep the cap terminals separate from the drive terminals.
   - Sizes range from 100 to 156 µF; voltage rating 50–60 VAC at least, 100 VAC for margin.
7. **Direction interlock.** Turning on CW and CCW together shorts the run cap through the triacs. Add a hardware interlock (the stock G-5500 box defaults to right/up). Firmware must enforce stop → coast → reverse dwell.
8. **No PWM on AC motors.** RT-21 ships AC rotors with no PWM, and the CDE rotors respond worst to it. Offer half-cycle or cycle-skipping creep (as DCU-1 does over the last 5°) instead of soft-start.
9. **Brake output** is needed only for the CDE family (24–30 VAC, 3.5–5 A steady, low-ohm coil of 0.75 Ω DCU-3 measured, with inrush) and for the HDR-300 (voltage [?]). It needs its own triac or relay with a fault-safe default of brake engaged.
10. **DC module.**
    - Supply span 12–48 V: SPID 12–24, Yaesu 11–24, Prosistel up to 42, M2 28–42, with about 45 V open circuit.
    - 5 A covers most rotors.
    - BIG-RAS/HR (up to 12 A) and the SPID MD's 20 A outputs exceed it: document this, or plan a 10–15 A option.
11. **Soft limits.** SPID and Prosistel D have no limit switches, so the calibration sweep must not hunt for a mechanical stop on them. The operator sets the end points instead.
12. **Ground and common.**
    - On the CDE rotors, terminal 1 is shared by the motor, brake and pot.
    - On the Yaesu DXA, the pot cold end is tied to the chassis.
    - The pot ground return must therefore be star-routed and filtered (60 Hz notch).
13. **Cable gauge checks.** Optionally add a resistance check during calibration (HAM-IV: terminals 1–2 at most 0.8 Ω; HDR: at most 0.5 Ω).


## Sources

- **[HAM4]** Hy-Gain HAM-IV / HAM-IVX instruction manual (spec table, troubleshooting). <http://www.radiomanual.info/schemi/ACC_rotator/Hy-gain_HAM-IV_HAM-IVx_user.pdf>
- **[DCU3]** Hy-Gain DCU-3 manual v2 (brake/coast delays, pin voltages, resistance table). <https://www.wimo.com/media/akeneo_connector/media_files/D/C/DCU_3_Manual_v2_00f1.pdf>
- **[RT21]** Green Heron RT-21 manual v3.5, Appendix A.1-A.15 and B (per-rotor hookup tables). <https://www.greenheronengineering.com/wp-content/uploads/2019/08/RT-21_Manual_current.pdf>
- **[RT21P]** Green Heron RT-21 product page (supported rotor list, feedback ranges). <https://www.greenheronengineering.com/product/rotator-controller-rt-21/>
- **[T2X]** Hy-Gain T-2X/T-2XX Tailtwister instruction manual. <https://www.qsl.net/4/4x6on/RADIO%20MANUALS/HY-%20GAIN/HY-GAIN--T-2XX-Tailtwister-Rotator.pdf>
- **[T2XS]** Norm's Rotor Service T2X spec page. <http://rotorservice.com/T2X%20specs.htm>
- **[CD45]** Hy-Gain CD-45-II instruction manual. <https://qrzcq.com/pub/RADIO_MANUALS/ROTATORS/HY-GAIN-CD-45-II-ROTATOR-Op-Manual+sch.pdf>
- **[HAM5]** Hy-Gain HAM-V / HAM-VX with DCU-1 Pathfinder manual. <https://static.dxengineering.com/global/images/instructions/hgn-ham-vii.pdf>
- **[HAMM]** CDE HAM-M owner's manual (Issue E 2/72), spec table p.2 (read from scan). <https://pestingers.net/pdfs/other-radios/rotors/cdr-ham-m_man.pdf>
- **[NORM]** Norm's Rotor Service FAQ (Ham-series history, interchangeability, Ham-M S1/S2 wiring warning, cap range). <http://rotorservice.com/faqs.htm>
- **[N0AX]** N0AX, How to Check Rotators from the Ground (terminal 1 common, 120-140 uF). <https://www.onallbands.com/how-to-check-rotators-from-the-ground/>
- **[HDR]** Hy-Gain HDR-300A/AX instruction manual. <https://www.qsl.net/4/4x6on/RADIO%20MANUALS/HY-%20GAIN/HY-GAIN--HDR-300AX-ROTATOR.pdf>
- **[AR40]** Hy-Gain AR-40/AR-40X instruction manual. <https://qrzcq.com/pub/RADIO_MANUALS/HY_GAIN/HY-GAIN--AR-40X-ROTATOR.pdf>
- **[G450A]** Yaesu G-450A/G-650A user manual. <https://radiomanual.info/schemi/ACC_rotator/Yaesu_G-450A_G-650A_user.pdf>
- **[G450XL]** Yaesu G-450XL user manual (24 VAC motor; seen via search excerpt only). <http://www.radiomanual.info/schemi/ACC_rotator/Yaesu_G-450XL_user.pdf>
- **[G450SM]** Yaesu G-450A service manual parts list (100 uF 60 VAC cap; search excerpt only). <https://manualmachine.com/yaesu/g450a/7758382-service-manual/>
- **[DXA]** Yaesu G-800DXA/G-1000DXA/G-2800DXA user manual. <https://www.yaesu.com/Files/4CB6273C-1018-01AF-FA4D504B591F641A/G-800DXA_1000DXA_2800DXA_OM_ENG_EAA67X101_2102B-BS.pdf>
- **[K9YC]** K9YC, TowerTalk 'Yaesu G-1000DXA Rotator Measurements' (pinout, 8.75 ohm motor, 500 ohm pot). <http://lists.contesting.com/pipermail/towertalk/2010-June/118053.html>
- **[DXC]** Yaesu G-1000DXC/G-2800DXC manual. <https://www.rigpix.com/rotators/yaesu_g1000dxc-2800dxc_manual.pdf>
- **[G450ADC]** Yaesu G-450ADC/CDC user manual. <https://yaesu.com/Files/4CB6273C-1018-01AF-FA4D504B591F641A/G-450ADC_CDC_OM_ENG_EBB86X200_1907V-AS.pdf>
- **[G5500]** Yaesu G-5500 instruction manual. <https://qsl.net/4/4x6on/RADIO%20MANUALS/YAESU/YAESU--G-5500-ROTATOR-User-Manual.pdf>
- **[G5500DC]** Yaesu G-5500DC user manual (Japanese). <https://connect.yaesu.com/indivisual/wp-content/uploads/2024/11/G-5500DC_OM_JPN_EBB70X001_2405A-ES.pdf>
- **[G550]** Yaesu G-550 manual (search excerpt only). <http://alex-ua.com/images/upload/YAESU/yaesu_g550_eng.pdf>
- **[AMSATC]** WA4SCA, AMSAT-BB 'Yaesu G5500 rotor trouble' (100 uF cap in motor housing). <https://mail.amsat.org/archives/pipermail/amsat-bb/2009-May/018821.html>
- **[AMSATP]** AMSAT-BB 'G-5500 azimuth and elevation resistor pots' (500 ohm, 360 deg). <https://mail.amsat.org/archives/pipermail/amsat-bb/2009-October/023347.html>
- **[WRC]** G-series Wi-Fi Rotor Controller manual (G-450ADC/G-1000A pot wired as rheostat). <https://device.report/manual/18025534>
- **[SPIDMD]** SPID MD-01/02/03 manual 2022-10-27 (gear ratios, sensor types, motor supply). <https://www.wimo.com/media/akeneo_connector/media_files/S/P/SPID_MD_0x_MANUAL__Version2022_10_27_ENG_76ad.pdf>
- **[RAS]** AlfaSpid RAS + Rot2Prog manual 2008 (wiring, speed, current, overtravel). <https://www.wimo.com/media/manuals/SPID/25082_Satelliten-Rotor-Satellite-Rotator_Manual.pdf>
- **[ALFA]** Alfa Radio RAK/BIG-RAK/RAS/BIG-RAS specification sheet 2008. <https://www.wimo.com/media/akeneo_connector/media_files/2/5/25080_25082_RAK_RAS_specifications_b1fe.pdf>
- **[BIGRAK]** RF HAMDESIGN / SPID BIG-RAK specification sheet. <https://www.rfhamdesign.com/downloads/spid-bigrak-specifications.pdf>
- **[M2RC]** M2 RC2800PX-AZ controller manual (27 VDC 3.2 A, terminal strip, divide ratios). <https://www.m2inc.com/content/PDF%20MANUALS/RC2800%20SERIES/RC2800PXB-AZMAN04-W.pdf>
- **[M2OR]** M2 OR2800PX positioner manual (specs, reed test voltages). <https://www.m2inc.com/content/PDF%20MANUALS/OR2800%20SERIES/OR2800PXMAN02-W.pdf>
- **[PST01]** Prosistel manual rev 2001-12A (Array Solutions): 48 VAC models, +/-12 V 10 k pot, pinout. <https://www.arraysolutions.com/pdfs/Prosistel%20Manual%20rev%202001_12A.pdf>
- **[PST71]** Prosistel PST-71D product page. <https://www.prosistel.biz/public/home-e/pst71/71e.html>
- **[PST61S]** Prosistel PST-61/71/110 user manual (PST-61D 12 VDC, ~90 s; search excerpt only). <https://www.arraysolutions.com/pdfs/Prosistel%20PST-61%20-%20PST-71%20and%20PST-110%20User%20Manual.pdf>
- **[CREATE]** Create (CD Corp) RC5-x series specification sheet. <https://www.cd-corp.com/eng/ama/rtt/rc5_eng.pdf>
- **[KUR02C]** DUORO/kur02 Create rotator page (28 VAC motor; search excerpt only). <https://www.kur02.com.au/index.php?id=35&Itemid=112&option=com_content&view=article>
- **[HD73P]** WC1M, TowerTalk 'HD-73 rotator' (pinout, 75 ohm pot from manual schematic). <http://lists.contesting.com/_towertalk/1999-06/msg00055.html>
- **[HD73M]** Alliance HD-73 owner's manual (20 VAC, 155 uF 50 VAC; search excerpt only, page blocked). <https://manualzz.com/doc/8212742/alliance-hd-73-antenna-rotator-owner-s-manual>
- **[U110]** Alliance U-110 manual (search excerpt only). <http://n3ujj.com/manuals/U-110%20Manual.pdf>
- **[KR600]** GM3WOJ, Kenpro KR-600RC notes (500 ohm VR5, measured 41-650 ohm). <https://www.qsl.net/gm3woj/kr600rc.htm>
- **[KRMUS]** Radiomuseum Kenpro KR-600RC (24 VAC split-phase, 53/63 s; search excerpt only). <https://www.radiomuseum.org/r/kenpro_antenna_rotator_kr_600rc.html>
- **[REZ]** Idiom Press Rotor-EZ install (new-style CD-45II/HAM-IV/T-2X boxes); Ham Supply product page (fixed 5 s brake delay). <https://www.hamsupply.com/wp-content/uploads/2015/11/26-rotor-ez-telex-install.pdf>
- **[EMO]** DUORO/kur02 EMOTATOR specification and comparison table (2020). <https://kur02.com.au/index.php?option=com_content&view=article&id=33&Itemid=130>
- **[K3NG]** K3NG wiki: 250 Basic Rotation Control Pins / 270 Rotation Speed Control. <https://github.com/k3ng/k3ng_rotator_controller/wiki/250-Basic-Rotation-Control-Pins>
- **[WA1HCO]** WA1HCO, 'Rotor and Controller Schematics.docx' (Rotator-Controller-V2 repo, V4 branch). <https://github.com/wa1hco/Rotator-Controller-V2>
- **[SRCH]** Search-engine summaries of manualzz copies of CDE Ham-II / Ham-III / CD-44 manuals (not opened directly). <https://manualzz.com/doc/6343459/cornell-dubilier-ham-iii-antenna-system-user-manual>
