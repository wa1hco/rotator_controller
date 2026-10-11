# Open Rotator Controller: System Design Overview (processor-agnostic)

*Draft 1, Oct 10, 2026. WA1HCO.*

## 0. Baseline and scope

**The baseline is one box in the shack that drives the stock rotator over its existing rotor cable.** The box replaces the manufacturer's control box. The rotator, its motor, brake, position sensor, and the cable up the tower stay the same. Anything that needs electronics on the tower or new cable is listed as a "new idea" with its tradeoffs. None of it is the default.

This document leaves the processor open. Every interface below is defined so that it could run on STM32, Teensy, RP2040, or ESP32, and in a PC build against a simulator.

It builds on existing work:

- **wa1hco/Rotator_Controller** and **Rotator-Controller-V2**, V4 branch: the CDE/Ham-M dual-end pot method (two ADC reads, 60 Hz notch, FIR filter, solving for the pot resistance). Also the V4 board's solid-state AC relays and isolated USB.
- **wa1hco/k3ng_rotator_controller** fork: the PC build, physics simulator (backlash, stiction, stall and stuck-relay faults), GS-232 integration tests, and browser compass.
- **WIMS**: the `RotatorBackend` (read / move_az / stop), `RotatorState` (az, el, target, moving, health, soft limits), the GS-232 helpers, and the per-rotator command serialization rule.
- **StreamDeck**: the seat verbs `rotator.point / bump / stop / park` and the seat-io config (`protocol: yaesu_gs232`, `park_az`, `soft_az`, `poll_ms`).
- **SO4R_Interlock**, **Tiny_Sequencer**, and **wsjtx-inhibit**: the station's existing priority, KEY/PTT, and TX-inhibit patterns.

The reference points are K3NG (very broad features, compile-time `#define` configuration) and Green Heron RT-21. The RT-21 offers PWM speed and ramps, a point-and-shoot knob, offset correction, master/slave linking for stacks, and sensor modes POT/COUNTER/HAMx/T2X/TIC-PST/ORION/SPID/YAESU. It reports no-motion, pot-out-of-range, and counter-range faults.

---

## 1. Modularity

### Options

| Split | Description | Pros | Cons |
|---|---|---|---|
| A. Monolith (K3NG style) | One firmware, features chosen with `#define` | Simple to flash | Hard to test; configuration needs a rebuild; this is the problem we are leaving |
| B. Layered single box | One shack box; firmware split into modules with fixed interfaces; configuration is runtime data | Testable; matches the stock-cable baseline | Display and network options add to the box's BOM |
| C. Box + separate bridge | Shack box is the real-time controller (USB serial plus an optional Ethernet/Wi-Fi module); a PC or Pi service adds web, MQTT, and many-client handling | Keeps safety-critical code small; PC-side features can change fast | Two things to deploy |
| D. Distributed (*new idea*) | Driver/sensor unit on the tower, control head in the shack, linked by RS-485, CAN, or Ethernet | Short motor/sensor runs; digital link is immune to cable resistance and hum; one cable for many rotators | **Needs new cable and tower electronics** (lightning, weather, power at the tower); breaks the baseline |

### Recommendation: B inside the box, with C as an optional add-on

The firmware runs in five layers. Each layer talks to the next through a small interface.

1. **Hardware layer.** ADC, GPIO, PWM, timers, counter input, nonvolatile memory, serial/socket. The PC build swaps in the simulator here.
2. **Axis I/O.** A `PositionSource` (pot single-ended, pot dual-end, pulse counter, absolute encoder, inclinometer) and an `AxisDriver` (AC relays + brake, DC H-bridge PWM, stepper). Rotator profiles (section 6) choose and configure these.
3. **Motion core.** One `Axis` state machine per axis: limits, overlap, route planning, ramps, brake timing, stall/fault checks. It is pure logic with no I/O, so it can be unit-tested.
4. **Command bus.** Every input (front panel, protocol parsers, network, interlocks) becomes one internal command set: `point(az[,el])`, `jog(dir,speed)`, `stop`, `park`, `set_config`, `get_state`. Every output (display, telemetry) subscribes to one `AxisState` record. That record is a superset of WIMS `RotatorState`: az, el, target, moving, direction, speed, health, fault, soft limits, owner.
5. **Front ends.** Protocol plugins (section 4), UI (sections 2 and 3), and integration (section 7).

**Configuration** is a versioned, checksummed settings record stored on the box. Each rotator profile starts from a preset ("HAM-IV", "G-1000DXC", "SPID RAS"...), and you then adjust it. You can edit it from the front panel, over serial (text commands), or as JSON from the web/PC. It can be exported and imported so one file describes a station. No rebuild is needed to change rotator type or protocol. Optional features that don't fit the board (for example a TFT driver on a small MCU) are left out of the build. That is a build-variant choice, not user configuration.

**Multi-axis and multi-rotator.** The core handles N axes. The baseline box is one azimuth axis, or one az + el pair (G-5500/SPID az-el). Stacks are handled one level up (section 7).

---

## 2. Display

| Option | Cost/effort | Readability | Notes |
|---|---|---|---|
| None (headless) | Lowest | Via PC/web only | Fine for remote sites; still needs status LEDs |
| Character LCD 20x4 (+ BigFont) | Low; you already have BigFont | Good, especially big digits | Proven in K3NG and your code; limited graphics |
| 7-segment LED via MAX7221 | Low; used on your 2022 board | Excellent at distance, any light | Numbers only; no menus |
| OLED 128x64 / 2.4" | Low | Good up close; burn-in risk | Good for setup menus |
| TFT 3.5–5" (or Nextion) | Medium | Compass rose, target needle, faults | Nextion is supported in K3NG today but ties you to a vendor; plain SPI TFT + LVGL is more open |
| LED ring (24–72 LEDs) | Low–medium | Can read heading at a glance | Pairs well with a numeric display |
| Web compass | Firmware/bridge work | Any screen, remote | Already exists in the K3NG fork's simulator GUI |

**What it shows:** current az (el), target, direction/moving, the overlap zone (450°/500° rotators), brake state, speed, the selected rotator (multi-rotator box), who is in control (panel/PC/WIMS), and faults ("NO MOTION", "POT OPEN", "COUNTER RANGE", "INTERLOCK"). A setup screen shows raw sensor values (Rtop ohms, counts) for calibration. Your Octave CSV logging becomes a "scope" page.

**Recommendation:** treat the display as a front-end module so the panel can grow. The default panel is a numeric heading display (MAX7221 7-seg or big-digit LCD) plus a status LED row. A TFT is a front-panel option. Every box also serves the web compass once a network path exists, either on the box or through the bridge.

---

## 3. User controls

| Control | Role | Recommendation |
|---|---|---|
| Heading knob (encoder with push) | Point-and-shoot like the RT-21: turn to choose, push or wait to go | **Yes**; the main control. An encoder beats a preset pot (no calibration, unlimited turns) |
| CW / CCW buttons | Manual jog; hold = run with ramp | **Yes**, like the CDE levers. Keep "release = stop" |
| STOP | Large, always active, highest priority | **Yes**. Also a hardware stop input on the rear panel |
| Brake release (AC/CDE) | Manual brake for nudging | Only in a "manual mode"; normally automatic |
| Presets (4–8 buttons or a menu) | EU/JA/W6/park headings, per rotator | Yes, as menu entries; physical buttons optional |
| Joystick | Az/el jog for satellite/EME | Optional module (K3NG has FEATURE_JOYSTICK_CONTROL) |
| Speed pot/encoder | Max speed limit for DC/PWM rotators | Menu setting; knob optional |
| Rotator select | Multi-rotator box | Encoder push-long or a button |
| StreamDeck | `rotator.point/bump/stop/park` | Through WIMS/seat agent and the network API (section 4); no USB HID in the box |
| Web/remote | Same verbs plus configuration | Through the network API, behind authentication |

**Safety interlocks (all of them stop motion and are latched and reported):**

- Hardware STOP input.
- Optional limit switches.
- Motor over-current and stall/no-motion timeout.
- Sensor fault (pot open or out of range, counter stops counting).
- Duty-cycle and thermal limits. CDE transformers are rated at **10% duty**, and Yaesu specifies a **3-minute maximum continuous run**; enforce both in firmware.
- Brake delay checks.
- A "tower work" lockout that disables all motion and needs a local panel action to clear.

---

## 4. PC applications and protocols

### What the apps actually speak (checked)

- **Hamlib rotctld** uses a TCP text protocol, default port 4533: `P az el`, `p`, `S`, `K` (park), `M dir speed`, `_`, plus long `\set_pos` forms. **Gpredict** and many Linux tools use it. Hamlib has backends for GS-232A/B, EasyComm, SPID Rot1/Rot2Prog, DCU-1, Prosistel, Green Heron RT-21, and others.
- **N1MM+** talks to its **N1MM Rotor** program (or to PstRotator) over UDP **port 12040**. The rotor program then talks to the controller in a named protocol (Yaesu, DCU-1, Green Heron, and others).
- **DXView (DXLab)** supports AlfaSpid, Green Heron, Hy-Gain, M-Squared, Prosistel, Yaesu, and others directly over serial, or through N1MM Rotor.
- **PstRotator** speaks almost everything (GS-232A/B az and az-el, DCU-1/DCU-1X, RT-20/21, Prosistel, ERC, Rotor-EZ...). It relays N1MM UDP and is the common bridge for **Log4OM** and similar apps.
- **SPID Rot2Prog** is a 13-byte binary frame (`0x57 ... K 0x20`, K = 0x0F stop / 0x1F status / 0x2F set), 600 baud.
- **WIMS** today uses GS-232 (`Mxxx`, `C`/`C2`, `A`/`S`) through `RotatorBackend`.

### Protocol plugins

| Protocol | Priority | Why |
|---|---|---|
| Yaesu GS-232A/B (az and az-el) | **Tier 1** | Universal; WIMS, N1MM Rotor, DXView, PstRotator, Hamlib all speak it |
| Hamlib rotctld (native TCP) | **Tier 1** (network) | Gpredict and Linux apps with no rotctld process in between; decimal degrees |
| Native JSON API (WebSocket/REST) | **Tier 1** (network) | Full state, faults, config, multi-rotator; maps 1:1 onto WIMS `RotatorState` and the StreamDeck verbs |
| EasyComm I/II | Tier 2 | Satellite software (Gpredict through Hamlib, SatNOGS-style tools), tenths of a degree |
| Hy-Gain DCU-1 | Tier 2 | Many Windows loggers' "Hy-Gain/Rotor-EZ" setting; already in K3NG (FEATURE_DCU_1_EMULATION) |
| SPID Rot2Prog emulation | Tier 3 | SpidSat users and AlfaSpid-only software |
| Prosistel, Green Heron native | Tier 3 / later | Only if users ask; GS-232 covers most of these setups |

Each serial or TCP port is configured to one protocol. One box can expose USB-serial (GS-232) and TCP 4533 (rotctld) and the JSON API at the same time.

### Transport

**USB CDC serial** is the baseline. It works with everything and needs no drivers. Isolated USB is already in the V4 design, and it keeps ground loops out of the shack PC. **Ethernet** is preferred over Wi-Fi in a contest station: it is deterministic, keeps RF out of the 2.4 GHz band, and is easy to configure with a static IP. Wi-Fi is fine for a portable box. If the box has no network hardware, the **bridge service** can run on the shack PC or a Pi. It holds the USB port and offers rotctld, JSON, and MQTT. This is the same pattern as the WIMS host agent that owns a serial port.

### Multi-client arbitration

WIMS already says "serialize commands per rotator; one controller of record." Carry that rule down into the box:

- Every command carries a **source** (panel, usb, tcp:N, wims, interlock). The latest `point` wins, except that **STOP from anyone always wins**.
- A **local panel action takes control** for N seconds, and remote `point` commands are refused with a reason during that time. This stops a logger from yanking the antenna while an operator is turning the knob.
- An optional **owner lock**: a client can claim a rotator (for example WIMS during a run). Other clients can still read state; their writes are refused with a reason.
- All state is broadcast to every subscriber, so the panel, WIMS, and the web view always agree.

---

## 5. Motor control

### Drive types

| Drive | Rotators | Over stock cable | Control |
|---|---|---|---|
| **AC cap-run motor + solenoid wedge brake** | Hy-Gain HAM-IV/V, T2X, HDR-300, CDE | Motor 24 VAC 2.25 A, cap-start/cap-run (cap lives in the control box); brake solenoid 24 VAC 5 A; 8 wires; transformer 26 VAC, 10% duty | Relays or solid-state relays (V4: CPC1966) for CW, CCW, brake. **No speed control.** The sequence is brake release → delay → motor → coast → brake. |
| **AC motor, no brake** | Older Yaesu G-450A/G-650, some G-5500 | 24 VAC class (verify per model) | Relays/SSR; coast timing |
| **DC brushed, variable voltage** | Yaesu G-450ADC (~20 VDC), G-1000/2800DXC (11–24 VDC), G-5500DC (22 VDC), Prosistel D (24 VDC), M2 OR-2800 (27 VDC), SPID RAS (12–24 VDC) | Two motor wires; polarity sets direction | H-bridge with PWM. Soft start/stop, speed limit, slowdown near the target. Current sensing comes for free. |
| **Stepper** | Homebrew, small satellite az-el | New design | Step/dir driver with acceleration profile; open loop needs homing |

### Core behaviors

All of these live in the `Axis` core. Each one is a profile parameter.

- **Ramps.** On DC drives: ramp up, cruise, then slow down inside an approach window (RT-21 "precision ramp", K3NG slow start/slow down). On AC drives: bang-bang control plus **predicted coast**. Learn the coast distance and stop early, which your simulator's backlash/stiction model can tune.
- **Brake timing.** Configurable delays: brake release → motor; motor off → brake engage. The CDE wedge must not engage while the rotator is still moving. The CDE wedge has 75 teeth 4.8° apart, so the final heading lands within the brake's tooth spacing. Report it honestly rather than chase it.
- **Direction-reversal dwell.** A minimum stop time before reversing. This protects gears and AC motor caps.
- **Overlap and route planning.** For 450° (Yaesu) and 500° (Prosistel 70°+360°+70°) rotators, pick the shorter route that stays inside the limits. Optionally keep a preferred side, and "unwind" when idle. Also support north-center and south-center, and any starting point (K3NG and RT-21 both do).
- **Soft limits.** For side mounts and feedline wrap. TIC/Prosistel-style "use the middle 88% of the pot" protection where the rotator has no mechanical limit switches.
- **Stall/no-motion detection.** The position must change by X° within T seconds of drive on. It catches a seized rotator, broken cable, frozen brake, or blown cap, and it is the first fault the RT-21 reports.
- **Current sensing.** On DC, read H-bridge current for over-current, jam detection, and mechanical health trends. On AC, a current transformer or shunt in the transformer secondary detects a missing or open motor and a stuck relay. That is cheap insurance.
- **Duty-cycle tracking.** Per-transformer and per-motor run-time budgets (10%, 3-minute limits).
- **Offset.** A mast-slip offset, like RT-21 OFFSET and DXView's per-antenna offset.

**Recommendation:** two driver families in one box design. (1) **AC relay/SSR + brake** for the CDE/Hy-Gain baseline, which your hardware already does. (2) **DC H-bridge with PWM and current sense** for Yaesu DC, Prosistel, M2, and SPID. They can be two output boards or a populate-option, behind the same `AxisDriver` interface. The stepper is a software driver for homebrew use only.

---

## 6. Rotator types supported

The stock cable decides what the box can sense. "Needs" means what the shack box must provide over that cable.

| Rotator | Motor | Position sensor | Box needs (stock cable) |
|---|---|---|---|
| Hy-Gain HAM-IV/V, CD-45II | 24 VAC cap-run, 2.25 A | 500 Ω pot (wires 3–7, wiper common) | 26 VAC transformer, run cap, 3 relays/SSRs, **dual-end pot reading** (your method cancels wiper/cable resistance), notch+FIR filtering |
| Hy-Gain T2X, HDR-300 | AC + wedge brake | 500 Ω pot | Same as HAM; HDR-300 motor/brake currents differ (verify) |
| Yaesu G-450ADC / G-450CDC | DC ~20 V | Pot, 450° | H-bridge, pot reference/ADC, 450° overlap |
| Yaesu G-800 / G-1000DXC / G-2800DXC | DC 11–24 V variable | Pot, 450° | H-bridge PWM, overlap, 3-minute duty limit |
| Yaesu G-5500 / G-5500DC (az-el) | AC (orig.) / DC 22 V | Pots, az 450°, el 180° | Two axes; AC or DC driver; el limits |
| Prosistel PST-61/71/110 D | DC 24 V | 10 kΩ pot, 5 V excitation, 500° | H-bridge, 5 V pot reference, TIC-PST middle-range protection |
| M2 Orion OR-2800 | DC 27 V, ~3.2 A | Reed-switch pulses, 3960/360° (open loop) | H-bridge, pulse counter, **counts stored across power loss**, re-calibration routine |
| Alfa SPID RAS/RAK/BIG-RAK | DC 12–24 V | Reed/magnetic pulses, 1 pulse/° typical (0.5/0.25 settings) | H-bridge, pulse counter, saved counts, homing |
| Create RC5 / ERC | AC/DC by model (verify) | Pot | Profile only once verified |
| TIC Ring Rotor | Varies | Pot | TIC-PST mode |
| Homebrew / slew drive | DC or stepper | Encoder (AS5045/HH-12), pot, IMU | Generic profile |

**Pulse-counter rotators** (SPID, Orion) need special care. Position is relative, so the count must be saved in nonvolatile memory on every stop and at power-fail detect. The box also needs a "set heading" calibration command and a range-error check, which the RT-21 reports as a COUNTER RANGE fault.

### Support tiers

- **Tier 1 (first hardware):** Hy-Gain/CDE HAM-IV/T2X with your dual-end pot method. This is your station, your board, your proven method, and Green Heron's most expensive gap.
- **Tier 2:** Yaesu DC (G-450ADC, G-1000/2800DXC) and generic pot + DC. One H-bridge board covers the largest installed base.
- **Tier 3:** Pulse-counter rotators (SPID, M2 Orion), Prosistel, G-5500 az-el.
- **Tier 4:** Steppers, encoders, IMU sensors, remote sensor units.

### New ideas (beyond the stock-cable baseline)

| Idea | Benefit | Cost/tradeoff |
|---|---|---|
| Absolute encoder (AS5045/AS5600) at the rotator, read over RS-485 | 0.1° resolution, no pot wear, survives power loss | Tower electronics, new or added cable pairs, lightning exposure |
| Tower-mounted H-bridge/relay unit plus digital link | Short high-current runs; one cable serves several rotators | New cable, power at the tower, weatherproofing, harder to service |
| Hall/IMU heading sensor on the mast | Independent check on mast slip | Magnetic noise near steel; needs calibration |
| Current-signature monitoring over time | Spot bearing/grease/cap failure early | Data storage and analysis only; no cable change (good candidate for early adoption) |

---

## 7. Station integration

- **Contest/logging software heading.** N1MM+ → N1MM Rotor/PstRotator → GS-232; DXView/Log4OM → GS-232 or PstRotator. **WIMS click-to-point** works today through `yaesu_gs232`. Later, WIMS adds a `native_json` backend to get health, fault, and owner data that GS-232 cannot carry.
- **StreamDeck.** Verbs go seat → WIMS → rotator. Add `rotator.bump` (±N°) and an optional `rotator.select` to the native API, so the deck never needs a protocol of its own.
- **Multi-rotator and stacks.** One box can drive two axes. Stacks (master/slave, like RT-21 linking) are better coordinated at the **network/bridge layer**: a group points both rotators, and the **slowest one gates "on target."** Stack antenna selection (WIMS `antenna_stacks`, `upper/lower/both`) stays in the seat agent. The rotator only publishes "aligned/not aligned."
- **Band decoder and antenna switching.** Use N1MM radio info over UDP or a band-data input to choose a **rotator profile per band** (which rotator the knob controls, per-band preset headings, per-antenna offset like DXView's Ant2 offset). The box does not switch RF; it only reports and follows.
- **SO2R/SO4R and the interlock.** Your SO4R_Interlock assigns radio priority and gates PTT/relays. The rotator does not need to stop TX. Instead, offer an **optional "inhibit rotation while TX" input**, driven by the interlock or the Tiny_Sequencer CTS/TX-ready line. That prevents RF-induced pot jitter and keeps the beam stable during EME/meteor-scatter transmit periods. Also offer an optional **"rotating" output**, which WIMS or the wsjtx-inhibit path can use to hold WSJT-X TX while a beam turns off target. Both default off.
- **Satellite/EME tracking.** Gpredict/SatPC32/PstRotator drive the box through rotctld/EasyComm/GS-232. The box needs fine target updates, a small deadband, speed control on DC, and el limits. K3NG's built-in moon/sun/satellite tracking is better kept on the PC. A box-resident moon/sun track is a nice-to-have later.
- **Weather/wind safety.** A wind-speed input (anemometer or MQTT topic) can trigger **auto-park/weathervane** to a chosen heading and lock out motion above a threshold. Combine with K3NG-style autopark after idle.
- **Networking and telemetry.** **MQTT** (state topic per rotator, command topic with source-tagged commands) for home automation and dashboards. **REST/WebSocket** JSON for WIMS and the web UI. **mDNS** names (`rot-144.local`) to match the WIMS seat-io ids. Only allow authenticated writes on the network.
- **How WIMS fits.** WIMS is the station brain. It picks the station, computes the bearing (`geo.delta_az`), and maps the antenna to its rotator and instance. The controller is a **reliable actuator** that reports truth (position, health, faults, owner). Keep pointing decisions in WIMS and motion safety in the box.

---

## 8. Open questions (ranked)

1. **Which rotators must version 1 support?** Recommendation: HAM-IV/T2X only (AC + brake + dual-end pot), with the Yaesu DC H-bridge as the second board. This sets the power stage, transformer, and enclosure.
2. **What is the shack box?** A complete replacement for the stock control box (your own transformer, run cap, brake drive), or a "smart insert" that keeps the stock transformer? This affects safety rating, cost, and what is mains-side.
3. **Is network on the box, or through a bridge?** Ethernet/Wi-Fi on the controller, or USB-only with a PC/Pi service? This decides where rotctld, JSON, MQTT, and the web UI live.
4. **Panel style.** Headless + web, numeric display + knob (RT-21 style), or a TFT compass? This decides the enclosure and front-panel BOM.
5. **Multi-rotator scope.** One rotator per box (simple, matches CDE wiring) or a box that drives 2–4 rotators with a selector (a contest station like yours)? Stacks would be coordinated in WIMS either way.
6. **Arbitration policy.** How long the panel holds control, whether WIMS can lock a rotator, and whether STOP from the deck is final.
7. **TX-related interlocks.** Do you want rotation-inhibit-on-TX or TX-hold-while-rotating at all, and is it the SO4R interlock or WIMS that drives it?
8. **License and project shape.** GPL-3.0 firmware (compatible with K3NG, which is now GPL-3.0; your Rotator_Controller still carries the older CC BY-NC-SA notice). Open hardware (CERN-OHL or CC BY-SA, matching your board repos). A new repo vs. continuing in the K3NG fork.
9. **New-cable ideas.** Is an absolute encoder or tower electronics ever on the table for your own towers, or strictly a contributor option?
