# Rotator Controller Feature Survey and Hardware-Driven Plan

*Draft 1, Oct 10, 2026. WA1HCO. Companion to `system-overview.md`.*

**Baseline:** one shack box drives the rotator over its existing rotor cable. The processor is not chosen yet, so compute and peripheral needs are stated as requirements. The question "full replacement of the stock control box vs. working alongside it" is still **open**. Section 3.3 shows how each answer changes the hardware.

Legend: **●** has it (documented). **○** partial, optional add-on, or via companion software. **–** not documented / not offered. **?** unverified. Source numbers [n] refer to section 5.

---

## 1. Products surveyed

| Short name | What it is | Type |
|---|---|---|
| **K3NG** | K3NG Arduino rotator controller (open source, GPL-3.0) [1][2] | Open firmware, DIY hardware |
| **RT-21** | Green Heron RT-21 universal controller (plus Az-El and Prop-Pitch "RT-21pp" variants) [3][4][5][6] | Commercial full replacement |
| **ERC-M** | DF9GR Easy-Rotor-Control, 1–2 axis interface [7][8] | Commercial interface (alongside stock box, or with "rotorcards") |
| **ARS** | EA4TX ARS-USB, plus ARSCU Yaesu-DC / Prosistel control units [9][10] | Commercial interface (alongside) or replacement (ARSCU) |
| **DCU-3** | Hy-Gain DCU-3 digital controller for HAM-IV/T2X [11] | Stock-brand digital replacement |
| **Yaesu** | G-1000/2800DXC stock box + GS-232B computer interface [12][13] | Stock box + add-on interface |
| **SPID** | Rot2Prog and MD-01/02/03 controllers [14][15][16] | Stock digital controllers (pulse sensors) |
| **M2** | RC2800PX / RC2800PRKX2SU for OR-2800 [17][18] | Stock digital controller (pulse sensor) |
| **Pst** | PstRotator / PstRotatorAz PC software [19][20] | PC software |
| **SatNOGS** | SatNOGS rotator controller + firmware (open) [21][22] | Open firmware/hardware (sat az-el) |
| **ESP32-open** | Rot32 (ESP32, rotctld over Wi-Fi, web UI) [23]; WiFiRotorCtl (OH1KH, rotctld over Wi-Fi) [24] | Open hobby projects |
| **wa1hco** | Your Rotator_Controller / V4 board + K3NG fork simulator | Your prior work |

---

## 2. Feature matrix with classification

**Class key:**
- **A** drives the hardware design (state the hardware impact).
- **B** firmware-only, cheap to add later.
- **C** belongs on the PC/bridge, not in the box.
- **D** skip / low value.

To keep the tables readable, products with nothing in a row are left out of that row's "who has it" column. Where a product is not mentioned, its documentation shows no such feature, or I could not confirm one.

### 2.1 Motion / motor control

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| AC motor CW/CCW relay drive (CDE/Hy-Gain, Yaesu AC) | K3NG ●, RT-21 ● (18–36 VAC @5 A), ERC-M ○ (open-collector + rotorcard), ARS ○, DCU-3 ●, wa1hco ● | **A** | 2 relays/SSRs per axis rated for motor current (HAM-IV motor 24 VAC 2.25 A [25]); TVS/snubbers; run capacitor if full replacement |
| Brake / wedge solenoid drive + delay | K3NG ●, RT-21 ● (0–6 s), ERC-M ● (AUX relay), DCU-3 ● (0–8 s), wa1hco ● | **A** | 3rd relay/SSR ≥ brake current (HAM-IV brake solenoid 24 VAC 5 A [25]). Delay logic is B |
| DC brushed motor drive, reversing | K3NG ○ (external), RT-21 ● (12–48 VDC @5 A), RT-21pp ● (24–28 V, 10 A), ARSCU ●, SPID ●, M2 ●, SatNOGS ● (MC33926) | **A** | H-bridge 12–48 V, ≥5 A continuous (10 A for prop-pitch class); DC supply sized to match |
| PWM speed control | K3NG ●, RT-21 ● (10–100 %), SPID MD ● (max power), M2 ● (S1–S9), Yaesu ● (speed pot, GS-232B X1–X4) | **A** (DC) / **D** (AC cap-run) | PWM-capable H-bridge with current sense. Not meaningful for AC cap-run motors |
| Soft start / ramp / slow down near target | K3NG ●, RT-21 ● (10 ramp settings), SPID MD ●, M2 ●, ERC-M ○ (overshoot correction) | **B** (needs A's PWM) | Firmware once PWM exists. High value: reduces tower/rotator stress |
| Coast compensation (AC) | DCU-3 ● (0–10°), ERC-M ○ (overshoot corr.) | **B** | Learn the coast distance; your simulator can tune it |
| Reversal delay / dwell | RT-21 ● (0–6 s) | **B** | Cheap; protects gears and caps |
| Stepper drive | K3NG ●, SatNOGS ● | **A** if included | Step/dir driver header. Value low for HF/VHF baseline → **D** for v1 |
| Prop-pitch / high-current 3-wire DC | RT-21pp ● | **A** | 10 A+ stage, heavier relays. **D** for v1; maybe later |
| Counter-rotation (rotator above rotator) | RT-21 ● | **B/C** | Two axes plus logic. Niche → later |

### 2.2 Position sensing

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Single-ended pot (voltage) | K3NG ●, RT-21 ● (150 Ω–10 kΩ), ERC-M ●, ARS ● (10-bit, op-amp conditioner + trimmer), Yaesu ●, wa1hco ● | **A** | Pot excitation source, scaling/conditioning per pot range, ADC ≥12-bit, input filtering |
| **Dual-end pot, grounded wiper (cable/wiper-resistance cancellation)** | wa1hco ● (unique) | **A** | 2 ADC channels per axis, bias resistors, twin-T 60 Hz notch, clamps (V3 3.6 V zeners). Key differentiator for CDE |
| Multi-turn pot (Prosistel 10 kΩ, 5 V excitation) | RT-21 ● (TIC-PST), ARSCU-Prosistel ● | **A** | Selectable excitation (5 V vs low-current CDE bias); range jumper/switch |
| Pulse counter (reed/Hall) | RT-21 ● (up to 64 pulses/°), SPID ● (1/0.5/0.25°/pulse), M2 ● (3960/360°), K3NG ● (pulse input); ARS – (explicitly not supported) | **A** | 2 debounced, protected counter inputs with pull-up supply (M2 reed ~11.3 VDC while moving [17]). Needs power-fail detect + nonvolatile count storage |
| Absolute/incremental encoders (AS5045/HH-12, quadrature) | K3NG ●, RT-21 ○ (special order), SatNOGS ● (AS5601 I2C) | **A** (header only) | SPI/I2C/quad header. New-cable idea; put the header on the board, no front end |
| IMU / compass / inclinometer | K3NG ● (HMC5883L, LSM303, ADXL345…), ARS ○ (inclinometer), Rot32 ● (LSM303) | **A** (header only) | I2C header. Low value for baseline |
| Calibration: 2-point, multi-point table | K3NG ● (correction tables), ERC-M ● (az every 30°, el every 5°), RT-21 ● (auto-cal), wa1hco ● | **B** | Pure firmware. High value |
| Offset (mast slip, alt antennas) | RT-21 ● (+2 alt offsets), ERC-M ●, DXView ○ | **B** | Cheap, high value |
| Higher resolution (0.1°) | RT-21 ● (1/3° pot, 1/10° pulse), ERC-M ○, K3NG ○ | **A** (ADC quality) | 12-bit + oversampling minimum; option for 16–24-bit external ADC |

### 2.3 Safety / protection

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| No-motion / stall detection | RT-21 ●, K3NG ●, SatNOGS ● (motor error) | **B** | Firmware with position. Highest value |
| Motor current sensing / over-current | SatNOGS ● (load measurement), SPID MD ○ (max power) | **A** | Shunt/Hall sensor + ADC channel per axis (DC). Current transformer/shunt in AC secondary (AC) |
| Pot out-of-range / open pot | RT-21 ● (TIC-PST) | **B** (needs A front end that rails cleanly) | Bias so an open pot reads out of range, not mid-scale |
| Counter range error | RT-21 ● | **B** | — |
| Soft limits / side-mount limits / ≤720° | RT-21 ●, K3NG ●, ERC-M ●, SPID MD ● | **B** | Cheap, high value |
| Limit switch inputs | K3NG ● (limit sense), SatNOGS ● (endstops) | **A** | 2 inputs per axis (optional) |
| TVS on all external terminals | RT-21 ● (industrial TVS), wa1hco ● (SMAJ90CA) | **A** | Mandatory on rotor terminals, comms, and I/O |
| Duty-cycle / thermal limit (CDE 10 %, Yaesu 3 min) | — (not documented on controllers) | **B** | Cheap; protects transformers and motors |
| Watchdog | ARS ●, SatNOGS ● | **B** | MCU watchdog; trivial |
| E-stop / external stop input | K3NG ○ (button) | **A** | 1 opto-isolated input, fail-safe wiring |
| Command timeout | K3NG ● | **B** | — |

### 2.4 User controls

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| CW/CCW buttons | K3NG ●, RT-21 ●, DCU-3 ●, M2 ●, wa1hco ● | **A** | GPIO + front-panel connector |
| Point-and-shoot knob | RT-21 ● (pot, 340°), DCU-3 ●, K3NG ● (preset pot/encoder), wa1hco ● (preset pot) | **A** | Encoder + push (2–3 GPIO) preferred over pot (frees an ADC) |
| Presets | DCU-3 ● (6), M2 ● (10/axis), K3NG ○, Pst ● | **B** | Firmware, after the knob/menu exists |
| Joystick | K3NG ● | **A** (connector) | 2 ADC + button. Optional header |
| Speed pot | K3NG ●, Yaesu ● | **A** small | 1 ADC; could be a menu setting instead → **D** |
| Park / autopark | K3NG ●, SatNOGS ● | **B** | — |
| StreamDeck / web | ESP32-open ○, Pst ● (web server) | **C** | Through the network API |

### 2.5 Display

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Character LCD / backlit | K3NG ●, RT-21 ● (FSTN, 8 brightness levels, auto-dim), DCU-3 ●, wa1hco ● | **A** | I2C/SPI or parallel connector; backlight PWM |
| Nextion / TFT | K3NG ● (Nextion) | **A** | UART or SPI connector; 5 V/3V3 power budget |
| 7-segment LED (MAX7221) | wa1hco ● (2022 board) | **A** | SPI connector |
| Web compass / embedded web server | RT-21 ○ (LAN/Wi-Fi option, v4.13), Rot32 ●, Pst ● (on PC), wa1hco ○ (simulator GUI) | **A** if on box (network HW); **C** if bridge | See comms |

### 2.6 PC / network interfaces and protocols

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| USB virtual COM | K3NG ●, RT-21 ●, ERC-M ● (FTDI), ARS ●, DCU-3 ●, SPID ●, M2 ○ (PRKX2SU), wa1hco ● | **A** | USB device port; **isolation** (ADuM4160 on V4) recommended |
| RS-232 DB-9 | RT-21 ● (also master/slave link), ERC-M ○, DCU-3 ●, Yaesu GS-232B ●, SPID MD ● (×2), M2 ● | **A** | Level shifter + DB-9; useful for legacy and daisy-chaining |
| Ethernet / Wi-Fi on box | RT-21 ○ (add-in card), SPID MD-02 ● (Ethernet, TCP 23), ERC-M ○ (LAN option), K3NG ○ (Ethernet shield), Rot32/WiFiRotorCtl ● (Wi-Fi) | **A** | Chosen path: MCU MAC + LAN8720A + MagJack. A W5500-class SPI module was considered and dropped |
| RS-485 | SatNOGS ● (UART or RS-485), SPID MD ○ (expansion) | **A** (header) | Transceiver footprint. Useful for "new idea" tower units |
| GS-232A/B | K3NG ●, ERC-M ●, ARS ● (A), Yaesu ●, SPID MD ●, wa1hco ● | **B** | Tier 1 |
| DCU-1 | K3NG ●, RT-21 ● (all DCU-1 programs), ERC-M ●, SPID MD ● (HyGain) | **B** | Tier 1–2; very cheap |
| EasyComm | K3NG ●, SatNOGS ● (easycomm 3) | **B** | Tier 2 |
| rotctld TCP | Rot32 ●, WiFiRotorCtl ● | **B** (needs network) | Tier 1 once there is network |
| Rot2Prog | SPID ● | **B** | Tier 3 |
| N1MM UDP rotor protocol (port 12040) | Pst ●, N1MM Rotor ● | **C** | Bridge/WIMS side |
| Remote control over IP | RT-21 ○ (GH Everyware), Pst ●, ARS ○ (ARSVCOM), SPID MD ● | **C** (+ A if on-box network) | — |
| Firmware update over USB | RT-21 ● (v3+) | **A** small | Bootloader path over USB; required |

### 2.7 Multi-rotator / az-el

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Az-el (2 axes) | K3NG ●, RT-21 Az-El ●, ERC-M ●, ARS ●, SPID ●, M2 ○ (PRKX2SU), SatNOGS ●, Pst ● | **A** | 2nd axis worth of drive + sensor + connector |
| Dual-azimuth (2 az axes) | ERC-M ● (VE2DX ext.), SPID MD ● | **A** | Same as above. Valuable for contest stacks |
| Master/slave / stacks | RT-21 ● (over RS-232), Pst ● (instances), K3NG ○ (remote unit) | **B/C** | Prefer network/bridge coordination |
| Remote sensor unit | K3NG ● (master/remote) | **A** (new cable) | "New idea" only |

### 2.8 Tracking

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Moon/sun tracking | K3NG ● (needs RTC/GPS), Pst ● | **C** | On box needs RTC/GPS → keep on PC |
| Satellite tracking | K3NG ● (P13), RT-21 ○ (GH Tracker), Pst ● | **C** | — |
| Timed tracking buffer | GS-232B ● (≤3800 positions), K3NG ● | **B/D** | GS-232B compatibility only |
| GPS / RTC | K3NG ● | **D** for box | — |

### 2.9 Station integration

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Ancillary/aux outputs (pin control) | K3NG ● (ancillary pins), ERC-M ● (6 open-collector), Pst ○ (relay boards) | **A** | 2–4 open-collector/relay outputs ("rotating", overlap, aux) |
| TX-inhibit / rotate-inhibit input | — | **A** | 1–2 opto inputs (ties to SO4R_Interlock / sequencer) |
| SteppIR/UltraBeam/band tracking | Pst ● (Az) | **C** | — |
| Band data input | — | **C** | Get it over the network from N1MM/WIMS instead of BCD lines |
| MQTT / REST | — (none of the products) | **B** (needs network) | Differentiator |

### 2.10 Configuration / calibration / diagnostics

| Feature | Who has it | Class | Hardware implication / value |
|---|---|---|---|
| Config without rebuild (menu/utility) | RT-21 ● (SETUP utility, save/restore), ERC-M ● (Service Tool, save/load), SPID ●, K3NG – (compile-time, partial EEPROM) | **B** | Needs enough nonvolatile storage |
| Rotator-type presets | RT-21 ● (POT/COUNTER/HAMx/T2X/TIC-PST/ORION/SPID/YAESU) | **B** | High value |
| Jumper-selected motor voltage/feedback | RT-21 ● | **A** | Shows the HW variance a universal box must absorb |
| Status/error registers | SatNOGS ● (GS/GE) | **B** | — |
| Raw-sensor/debug logging | K3NG ●, RT-21 ○ (debug mode), wa1hco ● (CSV + Octave) | **B** | — |
| Supply/voltage monitoring | — | **A** small | 1–2 ADC dividers (motor supply, logic) |

---

## 3. Focused plan

### 3.1 Hardware-driving decisions to lock first (ranked)

1. **Which motor-drive families are on the v1 board.** AC relay + brake only, or AC + DC H-bridge. This sets the power stage, supply, heat, connectors, and enclosure. *Recommendation:* the logic board carries both interfaces. Power stages are **swappable modules**: AC (3 relays/SSRs) and DC (H-bridge + current sense). Ship v1 with the AC module.
2. **Full replacement vs. alongside the stock box** (section 3.3). This decides whether mains, a transformer, and a run capacitor live in your box. *Recommendation:* design for full replacement and leave the alongside path open through the same logic board (a "no power module" variant with open-collector outputs).
3. **Sensor front ends included.** Dual-end pot (CDE) + single-ended pot with selectable excitation (Yaesu/Prosistel), plus pulse counter inputs. *Recommendation:* include all three on the board, even if pulse firmware waits until v2/later. Changing a board later costs much more than populating a few parts now.
4. **Axes per box.** 1 or 2. *Recommendation:* the logic board supports 2 axes (az-el or dual-az, as in ERC-M and SPID MD-02). The first enclosure populates 1.
5. **On-box network or bridge.** *Updated 2026-10-11:* Ethernet is standard, not optional. The MCU is an STM32F407VGT6 with a LAN8720A (see `mcu-ethernet-lcsc.md`). USB stays required. The W5500-on-SPI option is dropped. RS-232 stays an optional population.
6. **Front-panel interface.** *Recommendation:* a ribbon/connector to a separate panel board (I2C/SPI display, encoder, 4–6 buttons, LEDs), so the panel style can change without respinning the main board.
7. **Station I/O count:** E-stop and inhibit inputs, aux outputs (see the list below).

### 3.2 Hardware requirements (processor-agnostic)

**Per axis (×2 on the logic board):**

- **Position analog:**
  - 2 ADC channels (dual-end pot top/bottom).
  - Switchable configuration: dual-end CDE bias (330 Ω to 3.3 V, as now) ↔ single-ended excitation (≈5 V, for 500 Ω–10 kΩ pots; RT-21 range 150 Ω–10 kΩ).
  - Twin-T 60 Hz notch + RC anti-alias.
  - Clamp to the ADC rail, plus SMAJ-class TVS at the terminal.
- **Pulse input:** 1 counter input with selectable pull-up (≈12 V for M2 reed [17]), Schmitt trigger + RC debounce, opto or comparator. Rates are low: 64 pulses/° max (RT-21) at a few °/s is a few hundred Hz. Unverified: M2 per-pulse timing.
- **Current sense:** 1 ADC channel (shunt or Hall amplifier) on the DC module; an optional current-transformer/shunt sense on the AC module.
- **Drive interface to the power module:** CW, CCW, BRAKE/AUX enables, 1 PWM, fault-in. Use logic-level signals so modules can change.
- **Limit inputs:** 2 optional (CW/CCW limit), opto/RC.

**Power modules:**

- **AC module (v1):**
  - 3 SSR/relay channels for 24–30 VAC: motor CW, CCW ≥ 3 A; brake ≥ 5 A.
  - Unverified: whether the CPC1966 on V4 is rated for the 5 A brake current. Check its datasheet, or use G5LE-class relays for the brake.
  - Snubbers/MOVs, a fuse, and run-capacitor terminals (full-replacement case).
- **DC module (v2):** H-bridge 12–48 V, ≥5 A continuous (RT-21 class); PWM ≈20 kHz; current sense; brake/coast mode; fuse; TVS. A 10 A variant is a later option (RT-21pp class).

**Common:**

- **ADC totals:**
  - Required: 4 position + 2 current + 2 supply monitors (motor rail, logic/pot excitation) = **8 channels**.
  - Optional: +2 (preset pot or joystick).
  - At least 12-bit. Sample at ≥500 Hz per channel to keep the existing FIR/notch scheme (2 ms ISR). A footprint for an external 16–24-bit ΔΣ ADC (SPI/I2C) gives a 0.1° path.
- **Nonvolatile storage:** settings plus pulse-count checkpoints. FRAM recommended for write endurance, plus **power-fail detect** (comparator on the unregulated rail with enough hold-up to save counts).
- **Comms:**
  - USB device, **galvanically isolated** (as V4).
  - RS-232 DB-9 (level shifter).
  - Ethernet is standard: STM32F407 MAC + LAN8720A + MagJack (not a W5500, and not an unpopulated footprint). See `mcu-ethernet-lcsc.md`.
  - RS-485 transceiver footprint (for "new idea" tower units / daisy-chain).
- **Station I/O:**
  - 3 opto-isolated inputs: E-stop, rotate-inhibit (from SO4R_Interlock/sequencer), spare.
  - 3 open-collector outputs (≥ 60 V/300 mA, like the SO4R PTT spec): rotating, overlap/fault, aux.
  - Pluggable terminal block.
- **Front-panel connector:** I2C + SPI + 8–10 GPIO + 5 V/3V3 + backlight PWM, on one ribbon.
- **Expansion header:** I2C, SPI, UART, 2 GPIO (encoders, IMU, inclinometer, extra ADC).
- **Grounding/isolation:** separate motor-power return from logic; isolated USB; a single star point.
  - The CDE pot is referenced to the rotor common (terminal 1), which also carries brake/motor current [25]. Plan the pot front end around a moving reference with large 60 Hz ripple, as your notch + biasing already does.

**Compute/peripheral requirements (no part chosen):**

- **Motion + filtering only:** a small Cortex-M with FPU class is ample. Needs 8+ ADC channels or an external ADC, 2 hardware counters/capture inputs, 2+ PWM, USB device, 2–3 UARTs, I2C, SPI, and a watchdog. Interrupt-driven 500 Hz sampling of 8 channels is light.
- **Adding on-box Ethernet + web server + rotctld + JSON:** an MCU with an Ethernet MAC, or a separate network coprocessor (Ethernet module / ESP32-class). Plan for hundreds of KB of RAM and ≥1 MB of flash for TCP/IP + web assets. *Estimate, not measured.*
- **Firmware update over USB without opening the box** (bootloader).

### 3.3 Full replacement vs. alongside the stock box

| Aspect | **Full replacement** (like RT-21, DCU-3, ARSCU) | **Alongside stock box** (like ERC-M, ARS-USB in parallel) |
|---|---|---|
| Power stage | Your AC/DC modules, transformer (CDE: 26 VAC; HAM-IV transformer is rated **10 % duty** [25]) or DC supply 12–48 V | **None.** Drive the stock box's controls via relay/open-collector contacts (ERC-M uses 6 open-collector outputs [8]) |
| Mains | IEC inlet, fuse, transformer, safety spacing and a safety review in your box | None (12–14 V DC in, like ERC-M/ARS) |
| Run capacitor (AC cap-run) | In your box (cap lives in the stock control unit for HAM-IV [25]) | Stays in the stock box |
| Position sensing | You own the pot circuit, so **dual-end method is possible** | You read the stock box's meter/pot voltage in parallel (high-impedance tap). **Dual-end method generally not possible**, because the stock box biases the pot. Yaesu DXC has an external-control output (G-5500DC: 0–4.5 V position output [26]) |
| Speed control / ramps | Possible on DC (PWM) | Only what the stock box exposes (Yaesu speed input / GS-232B X1–X4); none on CDE |
| Brake timing | Yours | CDE: you must parallel the brake lever contact inside the stock box (modification); Yaesu: stock box handles it |
| Rotator coverage | Broad, with modules | Limited to boxes with a remote connector, or invasive wiring (ERC "rotorcards" exist for this) |
| Cost/effort | Higher BOM, heavier enclosure | Low BOM, small box, quick win |
| Failure modes | You own all protection | Stock box remains a fallback |

**Recommendation:** make the **logic board identical** for both paths.

- **Full replacement** = logic board + AC or DC power module + supply.
- **Alongside** = logic board + an "interface module" (relay/open-collector contacts + high-impedance position tap). For CDE this loses the dual-end advantage, which is your best feature. So full replacement is the stronger CDE product, while alongside is a cheap entry for Yaesu DXC owners.

### 3.4 Phased roadmap

**v1: "Better than DCU-3/RT-21 for a HAM-IV/T2X"** (hardware: logic board rev A + AC module + panel board)

- Az only, CDE HAM-IV/T2X, full replacement:
  - dual-end pot with notch + FIR
  - relays/SSR + brake with release/engage delays
  - reversal dwell; coast compensation (learned)
  - no-motion/stall detection, duty-cycle limit, soft limits
  - E-stop input, watchdog, open-pot detection
- 2-point + table calibration, offset (+ 2 alt offsets), 6–10 presets, park.
- Panel: encoder point-and-shoot, CW/CCW, STOP, numeric display (MAX7221 or big-digit LCD).
- Isolated USB: **GS-232A/B, DCU-1**, plus a JSON-lines native protocol. Text setup commands with config export/import.
- Rotate-inhibit input, "rotating" output.
- Simulator-backed CI (from the K3NG fork) for the motion core.
- Board **includes but may leave unpopulated:** 2nd axis, pulse inputs, Ethernet footprint, DC-module connector, RS-232, RS-485.

**v2: "Universal pot rotators + network"**

- DC module: Yaesu G-450ADC/G-1000/2800DXC, Prosistel, generic 12–48 V. PWM ramps, current-sense over-current/jam detection, 450°/500° overlap routing.
- 2nd axis: G-5500 az-el, dual-az.
- On-box Ethernet: rotctld (TCP 4533), JSON/WebSocket, web compass. EasyComm.
- WIMS `native_json` backend; StreamDeck verbs; owner/lock arbitration.
- Alongside-stock-box interface module (Yaesu DXC first).

**Later**

- Pulse-counter rotators (SPID, M2 Orion) with FRAM checkpoints + power-fail save; Rot2Prog emulation.
- MQTT, wind auto-park, master/slave and counter-rotate (network-coordinated).
- TFT panel option, joystick, encoder/IMU/inclinometer support, stepper (SatNOGS-style).
- 10 A prop-pitch module, current-signature health trending.
- New-cable ideas (RS-485 tower sensor/driver).

**Off the box, always (class C):** moon/sun/satellite tracking, logger and N1MM UDP, band-following, SteppIR, remote-over-internet. These go to WIMS, PstRotator, Gpredict, or the bridge.

**Skip (class D):** speed pot (use a menu), on-box GPS/RTC, timed-tracking buffer beyond GS-232B compatibility, stepper in v1, Nextion lock-in.

---

## 4. Unverified items to check before layout

- CPC1966 (V4) AC SSR current rating vs. HAM-IV brake 5 A / motor 2.25 A, and inrush. Check the datasheet.
- HAM-IV/T2X run-capacitor value and voltage; T2X/HDR-300 motor/brake currents (only HAM-IV specs confirmed [25]).
- Original (AC) G-5500 and older Yaesu "DXA" motor types (DC confirmed only for DXC, G-450ADC, G-5500DC [12][26][27]).
- Create RC5 motor type and pot value.
- M2 reed pulse rate at full speed (affects debounce RC).
- Whether DCU-3 speaks DCU-1 protocol (likely, not confirmed).

---

## 5. Sources

1. K3NG rotator controller repo and README feature list: https://github.com/k3ng/k3ng_rotator_controller (feature flags checked in `rotator_features.h`, e.g. FEATURE_DCU_1_EMULATION, FEATURE_ETHERNET, FEATURE_NEXTION_DISPLAY, FEATURE_STEPPER_MOTOR, FEATURE_SATELLITE_TRACKING)
2. K3NG wiki: https://github.com/k3ng/k3ng_rotator_controller/wiki
3. Green Heron RT-21 product page (features, specs): https://www.greenheronengineering.com/product/rotator-controller-rt-21/
4. RT-21 manual (sensor options POT/COUNTER/HAMx/T2X/TIC-PST/ORION/SPID/YAESU): https://www.greenheronengineering.com/wp-content/uploads/2019/08/RT-21_Manual_current.pdf
5. RT-21 Az-El manual: https://www.greenheronengineering.com/wp-content/uploads/2022/11/RT-21-Az-El-Version-2-Manual.pdf
6. RT-21 Prop Pitch: https://www.greenheronengineering.com/product/rotator-controller-prop-pitch/ ; RT-21 v4 LAN/Wi-Fi option: https://www.greenheronengineering.com/wp-content/uploads/2022/11/Version-4-rev-4.pdf
7. ERC software guide: https://www.schmidt-alba.de/eshop/Software-Guide:_:15.html
8. ERC-M product/kit pages: https://www.schmidt-alba.de/eshop/EASY-ROTOR-CONTROL:::1.html ; https://comtekradio.com.au/erc-m-usb-kit/
9. ARS-USB FAQ: https://ea4tx.com/en/faqs/ars-usb-faqs/
10. ARS-USB hardware: https://ea4tx.com/en/products-page/ars-usb/ars-hardware/
11. Hy-Gain DCU-3 manual: https://www.wimo.com/media/akeneo_connector/media_files/D/C/DCU_3_Manual_v2_00f1.pdf
12. Yaesu G-1000DXC/G-2800DXC manual: https://www.rigpix.com/rotators/yaesu_g1000dxc-2800dxc_manual.pdf
13. Yaesu GS-232B manual: http://www.radiomanual.info/schemi/YAESU_ACC/Yaesu_GS-232B_user_2004.pdf
14. SPID RAS / Rot2Prog: http://spid.net.pl/en/ras-2/ ; http://spid.net.pl/en/rot2prog-2/
15. Rot2Prog protocol: http://ryeng.name/blog/3
16. SPID MD-01/02/03 manual: https://www.wimo.com/media/akeneo_connector/media_files/S/P/SPID_MD_0x_MANUAL__Version2022_10_27_ENG_76ad.pdf
17. M2 RC2800PX-AZ manual: https://www.m2inc.com/content/PDF%20MANUALS/RC2800%20SERIES/RC2800PXB-AZMAN04-W.pdf
18. M2 RC2800PRKX2SU manual: https://www.m2inc.com/content/PDF%20MANUALS/RC2800%20SERIES/RC2800PRKX2SUMAN01.pdf
19. PstRotator site: https://www.pstrotator.com/
20. PstRotatorAz manual: https://pstrotator.com/ANT/PstRotatorAz%20User%20Manual.pdf
21. SatNOGS Rotator Controller wiki: https://wiki.satnogs.org/SatNOGS_Rotator_Controller
22. SatNOGS rotator firmware README: https://gitlab.com/librespacefoundation/satnogs/satnogs-rotator-firmware/blob/master/README.md
23. Rot32 (ESP32): https://github.com/evanwurden/Rot32
24. WiFiRotorCtl (OH1KH): https://github.com/OH1KH/WiFiRotorCtl
25. Hy-Gain HAM-IV manual (motor 24 VAC 2.25 A, brake 24 VAC 5 A, 26 VAC 10 % duty transformer, 8-wire): http://www.radiomanual.info/schemi/ACC_rotator/Hy-gain_HAM-IV_HAM-IVx_user.pdf
26. Yaesu G-5500DC manual (JP; 22 VDC motor, 0–4.5 V position output): https://connect.yaesu.com/indivisual/wp-content/uploads/2024/11/G-5500DC_OM_JPN_EBB70X001_2405A-ES.pdf
27. Yaesu G-450ADC/CDC manual (~20 VDC motor): https://yaesu.com/Files/4CB6273C-1018-01AF-FA4D504B591F641A/G-450ADC_CDC_OM_ENG_EBB86X200_1907V-AS.pdf
