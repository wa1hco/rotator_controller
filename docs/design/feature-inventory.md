# Feature inventory

*2026-10-12. WA1HCO. Companion to `configuration.md` and `feature-survey.md`.*

`feature-survey.md` asks what hardware each feature needs. This note
asks a different question: for the PC preference pages and the console
schema, is the feature a stored **setting**, an **operate** action, or
an **install** action, and is it in this project?

Sources, checked for this note:

| Tag | Document |
|---|---|
| K3NG | [`rotator_features.h`](https://github.com/k3ng/k3ng_rotator_controller/blob/master/k3ng_rotator_controller/rotator_features.h) and [`rotator_settings.h`](https://github.com/k3ng/k3ng_rotator_controller/blob/master/k3ng_rotator_controller/rotator_settings.h) on `master` |
| RT-21 | Green Heron RT-21 User Manual 3.5 and the version 4 addendum |
| ERC | ERC-M specification and the ERC-M USB kit page (DF9GR / Schmidt-Alba) |
| DCU-3 | Hy-Gain DCU-3 manual v2 |
| GS-232B | Yaesu GS-232B operating manual |

An **In** row names the setting and the GUI page. **Advanced** rows
are on that page behind the Advanced disclosure, so the first screen
stays the rotator, the travel, the brake, and the park heading.
**Operate** and **Install** rows are milestones in
`software/gui/README.md` and `rotatorctl.phases`. An **Out** row says
why, usually an ADR or the stock-cable baseline in `system-overview.md`.

## Summary

**In as settings now** (schema, simulator, and a GUI page): azimuth and
az/el, north/south center, overlap and soft limits, pot and pulse
sensors, encoder names for a later board, ADC averaging, limit-switch
enable, reversal delay, brake delay, coast, AC creep, DC PWM ramp,
stall current, no-motion jam, run timeout, go-to window, board drive
kind, park, auto-park idle time, six heading memories, two-point and
multi-point calibration, heading offset, log level, admin lock, and
the GS-232, rotctld, Easycom, and DCU-1 port choices.

**In as operate, phase 2:** heading display, go-to, jog, STOP, park and
auto-park, preset recall, enforcement of the limits above, the
calibration sweep, the rest of GS-232B, the three extra protocols, a
live log, and a multi-rotator dashboard. The front panel is STOP, CW,
and CCW.

**In as install, phase 3:** USB DFU, field upgrade into the inactive
slot, rollback status, and the version report.

**Out of this box:** on-box moon, sun, and satellite tracking; RTC and
GPS; a grid locator; the GS-232 timed-position buffer; a remote
master/slave unit; an LCD, OLED, or knob; a compass or accelerometer
on the tower; stepper and prop-pitch drives; a second azimuth on the
same board; Rot2Prog and N1MM UDP inside the controller; K3NG
compile-time `#define`s as the way to configure.

## Axes and travel

| Feature | Sources | Class | This project |
|---|---|---|---|
| Azimuth | All five sources. K3NG runs azimuth with elevation commented out | Settings | **In.** `az.present`. Axes page. A push leaves the controller's own flag alone |
| Azimuth and elevation | K3NG `FEATURE_ELEVATION_CONTROL`. RT-21 Az-El manual. ERC-M is a two-axis interface. GS-232B `W` and `C2`. ADR 0008 | Settings | **In.** `el.present`, and the same `el.*` names as azimuth. Axes page |
| Two azimuths on one box | ERC-M dual-azimuth extension | Settings | **Out.** ADR 0008 uses the two axes as azimuth and elevation. A stack is several controllers, which the phase 2 dashboard coordinates |
| North or south center | K3NG `AZIMUTH_STARTING_POINT_EEPROM_INITIALIZE` (180). RT-21 OFFSET 180 is north-center, 0 is south-center. DCU-3 NORTHSTOP. GS-232B `Z` | Settings | **In.** `az.center` is `north` or `south`. Limits page. `north` puts the stops at south, the usual 450 degree overlap. GS-232B `Z` will write this in phase 2 |
| Overlap and rotation range | K3NG `AZIMUTH_ROTATION_CAPABILITY_EEPROM_INITIALIZE` (450). GS-232B `P36` / `P45`. ERC-M overlap up to 180 degrees. RT-21 soft limits may sit 180 degrees past the normal ends | Settings | **In.** `az.travel_min_deg`, `az.travel_max_deg`, `az.overlap_deg`, and the elevation copies. Limits page |

## Position sensors

| Feature | Sources | Class | This project |
|---|---|---|---|
| Potentiometer | K3NG `FEATURE_AZ_POSITION_POTENTIOMETER`. RT-21 POT, 150 ohm to 10 kohm. ERC-M feedback voltage. DCU-3 and Yaesu pots. ADR 0008 | Settings | **In.** `az.sensor` / `el.sensor`: `single_ended_pot`, `dual_end_pot`, `rheostat`. Axes page. Dual-end grounded-wiper is this project's CDE method and the first firmware driver |
| Pulse and reed | K3NG `FEATURE_AZ_POSITION_PULSE_INPUT`, `OPTION_EL_PULSE_DEBOUNCE`, `EL_POSITION_PULSE_DEBOUNCE` (500 ms), `AZ_POSITION_PULSE_DEG_PER_PULSE`. RT-21 counter mode | Settings | **In.** Sensor value `pulse`. `az.pulse_deg` and `az.pulse_debounce_ms` (elevation too) under Advanced on Axes. ADR 0008 includes the pulse input |
| Incremental encoder | K3NG `FEATURE_AZ_POSITION_INCREMENTAL_ENCODER`, `AZ_POSITION_INCREMENTAL_ENCODER_PULSES_PER_REV` | Settings | **In, as a name.** Sensor value `incremental_encoder`. The v1 front end is pot and pulse. A later board file with the encoder header uses the same setting |
| HH-12 / AS5045 | K3NG `FEATURE_AZ_POSITION_HH12_AS5045_SSI` and `FEATURE_AZ_POSITION_HH12_AS5045_SSI_RELATIVE` | Settings | **In, as a name.** Sensor value `hh12_as5045`. Same later-board rule as the incremental encoder. The relative form is how a more-than-360 degree turn is counted |
| I2C compass and accelerometer | K3NG `FEATURE_AZ_POSITION_HMC5883L`, `FEATURE_AZ_POSITION_DFROBOT_QMC5883`, `FEATURE_AZ_POSITION_POLOLU_LSM303`, `FEATURE_AZ_POSITION_ADAFRUIT_LSM303`, `FEATURE_EL_POSITION_ADXL345_USING_ADAFRUIT_LIB`, `FEATURE_EL_POSITION_MEMSIC_2125` | Settings | **Out.** Those parts are not on the stock rotor cable. The baseline box drives the rotator that is already on the tower (`system-overview.md`). A declination table for a magnetometer goes out with the sensor |
| ADC averaging | K3NG `AZIMUTH_SMOOTHING_FACTOR`. A pot reading on RT-21 and ERC is filtered in the product | Settings | **In.** `az.adc_samples` and `el.adc_samples`, default 8, under Advanced on Axes |
| Open pot or pot out of range | RT-21 status "Pot out-of-range" | Operate | **In, as a fault the pot driver reports.** No extra setting. The dual-end bias is what makes an open pot leave the legal range. Phase 2 status shows it |

## Limits, ramps, brake, stall

| Feature | Sources | Class | This project |
|---|---|---|---|
| Soft limits | RT-21 CCW LIMIT and CW LIMIT. K3NG `OPTION_AZ_MANUAL_ROTATE_LIMITS` and `AZ_MANUAL_ROTATE_CCW_LIMIT`. ERC-M programmable end stops | Settings | **In.** The travel ends are the soft limits. The motion core enforces them in phase 2 |
| Limit switches | K3NG `FEATURE_LIMIT_SENSE` | Settings | **In.** `az.limit_switch` and `el.limit_switch`, default false, under Advanced on Axes. The hardware plan has optional inputs |
| Reversal delay | RT-21 DELAYS, up to 6 seconds. ERC-M delay before the rotator starts | Settings | **In.** `safety.dead_time_ms`. Limits page. The hardware interlock is separate |
| Brake delay | K3NG `AZ_BRAKE_DELAY` (3000 ms). RT-21 DELAYS. DCU-3 BRAKE DELAY 0–8 s, default 3. ERC-M AUX brake | Settings | **In.** `az.brake_delay_s` and `el.brake_delay_s`. Axes page |
| Coast and overshoot | DCU-3 COAST SET, 0–10 degrees. ERC-M overshoot correction. K3NG `FEATURE_AUTOCORRECT` | Settings | **In.** `az.coast_deg` and `el.coast_deg`. Limits page. 0 keeps the motor on until the target |
| AC creep near the target | DCU-1 half-cycle pulses over the last few degrees. The rotator catalog records that RT-21 ships AC rotors with PWM off | Settings | **In.** `az.creep_deg` and `el.creep_deg`, under Advanced on Limits. This is the AC slow-down. `ramp_s` stays 0 on an AC motor |
| PWM slow start and slow stop | K3NG `AZ_SLOWSTART_DEFAULT`, `AZ_SLOW_START_UP_TIME`, `SLOW_DOWN_BEFORE_TARGET_AZ`. RT-21 RAMP 0–9 and MIN/MAX SPEED | Settings | **In, for a DC drive.** `az.ramp_s`, `az.slowdown_deg`, and the elevation copies, under Advanced on Limits. Phase 2 applies them when `sys.drive` is `dc_hbridge` |
| Stall current | This project's current-sense plan in `feature-survey.md` | Settings | **In.** `safety.stall_a`. Limits page |
| Jam / no-motion | K3NG `FEATURE_AZ_ROTATION_STALL_DETECTION`, `STALL_CHECK_FREQUENCY_MS_AZ`, `STALL_CHECK_DEGREES_THRESHOLD_AZ`. RT-21 "ERROR, NO MOTION". ERC-M security stop if the rotor does not move. DCU-1 no-motion stop | Settings | **In.** `safety.stall_timeout_s` (default 8) on Limits. `safety.stall_deg` (default 2) under Advanced |
| Run timeout | K3NG `OPERATION_TIMEOUT` (120000 ms). Yaesu's continuous-run limit is the same kind of cap | Settings | **In.** `safety.max_run_s`. Limits page |
| Go-to window | K3NG `AZIMUTH_TOLERANCE`. ERC-M tolerance for tracking mode | Settings | **In.** `az.tolerance_deg` and `el.tolerance_deg`, under Advanced on Limits |
| Relay or triac CW/CCW | K3NG relay outputs. RT-21 relay or SSR drive. ADR 0004 uses discrete triacs on the AC board | Settings | **In, read-only.** `sys.drive` is `triac`, `relay`, or `dc_hbridge`. Axes page. The board file sets it. The operator does not |
| Stepper drive | K3NG `FEATURE_STEPPER_MOTOR` | Settings | **Out.** The stock rotators this box replaces are AC cap-run or, later, a DC motor. `feature-survey.md` leaves steppers out of v1 |
| Prop-pitch and counter-rotation | RT-21pp. RT-21 counter-rotation | Settings | **Out.** A different power stage and a niche mechanical setup. Not the v1 AC board |

## Park and memories

| Feature | Sources | Class | This project |
|---|---|---|---|
| Park heading | K3NG `FEATURE_PARK` | Settings | **In.** `az.park_deg`, `el.park_deg`, `park.brake`. Park page |
| Park command | K3NG `FEATURE_PARK`. Hamlib `K` | Operate | **In, phase 2.** The button runs the stored heading |
| Timed or auto-park | K3NG `FEATURE_AUTOPARK` | Settings and operate | **In.** `park.idle_min`, 0 leaves the antenna where it stopped. Park page. Phase 2 runs the move when the idle time elapses |
| Preset heading memories | DCU-3, six programmable headings. K3NG preset pot and `FEATURE_AZ_PRESET_ENCODER` store a target a different way | Settings and operate | **In.** `preset.1` through `preset.6`, each `.az` and `.el`, under Advanced on Park. Phase 2 recalls them. These are bearings, separate from the rotor-model presets |
| Display sleep | DCU-3 SLEEP DELAY blanks the LCD | Settings | **Out.** ADR 0006 is headless. There is no panel LCD to sleep |

## Calibration and heading correction

| Feature | Sources | Class | This project |
|---|---|---|---|
| Two-point calibration | K3NG `ANALOG_AZ_FULL_CCW_EEPROM_INITIALIZE` and `ANALOG_AZ_FULL_CW_EEPROM_INITIALIZE`. GS-232B `O` and `F` (`O2` / `F2` for elevation). ERC-M three-step calibrate. DCU-3 LEFT STOP and RIGHT STOP. RT-21 calibrate | Settings and operate | **In.** `az.cal.cw_end`, `az.cal.ccw_end`, and the elevation copies. Calibration page. The sweep button is phase 2 and stays disabled until then |
| Multi-point calibration | K3NG `FEATURE_AZIMUTH_CORRECTION` and `AZIMUTH_CALIBRATION_FROM_ARRAY` / `TO_ARRAY`. ERC-M extended calibration, azimuth about every 30 degrees and elevation every 5 or 15 degrees depending on the ERC-M page | Settings and operate | **In.** `az.cal.map` and `el.cal.map`, under Advanced on Calibration. `none` uses the two end readings. Otherwise at least two `raw:heading` pairs, commas, no spaces. The wizard writes the map in phase 2 |
| Beam heading offset | DCU-3 OFFSET, 0 to 360. ERC-M antenna offset. RT-21 OFFSET is also the center control, which this schema splits into `az.center` | Settings | **In.** `az.offset_deg` and `el.offset_deg`. Calibration page. Mast slip, a second antenna on the mast, or a declination number the operator wants added |
| Magnetic declination as its own table | K3NG LSM303 min/max arrays, used with the compass features | Settings | **Out as a separate table.** The compass sensors are out. An operator who wants a fixed correction types it into `offset_deg` |

## Tracking and time

| Feature | Sources | Class | This project |
|---|---|---|---|
| Moon tracking | K3NG `FEATURE_MOON_TRACKING`, `DEFAULT_LATITUDE`, `DEFAULT_LONGITUDE` | Operate | **Out of the box.** `system-overview.md` keeps moon, sun, and satellite tracking on the PC. The box accepts the next go-to |
| Sun tracking | K3NG `FEATURE_SUN_TRACKING` | Operate | **Out of the box.** Same as moon tracking |
| Satellite tracking | K3NG `FEATURE_SATELLITE_TRACKING`. RT-21 relies on an external tracker for this | Operate | **Out of the box.** Gpredict, SatPC32, or PstRotator send headings |
| RTC | K3NG `FEATURE_CLOCK`, `FEATURE_RTC_DS1307`, `FEATURE_RTC_PCF8583` | Settings | **Out.** A clock is there to feed on-box tracking |
| GPS | K3NG `FEATURE_GPS`, `OPTION_GPS_USE_TINY_GPS_LIBRARY` | Settings | **Out.** Same reason as the RTC. The PC tracker has its own time |
| Grid locator | K3NG maidenhead display options and the latitude/longitude pair | Settings | **Out.** The grid is an input to the PC tracker, not a controller setting |
| GS-232 timed buffer | GS-232B `M` with a time and a list of angles, then `T` (up to 3800 azimuths, or 1900 az/el pairs). K3NG `FEATURE_TIMED_BUFFER` | Operate | **Out.** The host sends the next heading when it is time. The box does not store a track |

## Protocols

| Feature | Sources | Class | This project |
|---|---|---|---|
| GS-232A/B on the shared port | K3NG `FEATURE_YAESU_EMULATION` and `OPTION_GS_232B_EMULATION`. ERC-M GS-232A/B. RT-21 serial control. GS-232B manual. ADR 0015 | Settings and operate | **In.** `ports.tcp` and `ports.gs232_query` (`C` or `C2`). Console page. Phase 1 parses `M`, `C` / `C2`, and `A` / `S`. Phase 2 adds `W`, `X1`–`X4`, `O` / `F`, `P36` / `P45`, `Z`, and the jog letters. There is no mode switch |
| Hamlib rotctld | ADR 0001 (rotctld comes later). `system-overview.md` tier 1. Not a K3NG feature flag; K3NG is usually behind a host rotctld | Settings and operate | **In.** `ports.rotctld`, default 0, under Advanced on Console. Phase 2 binds that port and speaks rotctld. 0 leaves it off. It does not share tokens with the console |
| Easycom | K3NG `FEATURE_EASYCOM_EMULATION`. `system-overview.md` tier 2 | Settings and operate | **In.** `ports.easycom`, default 0, under Advanced on Console. Phase 2 speaks it |
| DCU-1 | K3NG `FEATURE_DCU_1_EMULATION` (azimuth). ERC-M and RT-21 speak DCU-1. DCU-3 uses that command family (`AP1`, `AM1`) | Settings and operate | **In.** `ports.dcu1`, default 0, under Advanced on Console. Phase 2 speaks it |
| Rot2Prog | SPID controllers. `system-overview.md` tier 3 | Operate | **Out.** GS-232 covers the loggers this box aims at. A binary SPID frame can be added if a station asks |
| N1MM UDP port 12040 | PstRotator and N1MM Rotor, in `feature-survey.md` | Operate | **Out of the box.** That port belongs to the PC bridge or WIMS |

## Panel, display, and a remote unit

| Feature | Sources | Class | This project |
|---|---|---|---|
| STOP, CW, CCW | ADR 0006. DCU-3 and RT-21 have the same three actions on a richer panel | Operate | **In, phase 2.** The buttons are direct motion inputs. STOP is already reserved on the PC window. They are not settings |
| Point-and-shoot knob | RT-21 front-panel knob. DCU-3 encoder. K3NG `FEATURE_AZ_PRESET_ENCODER` | Operate | **Out.** ADR 0006: no knob. Heading entry is on the host |
| LCD, OLED, Nextion | K3NG `FEATURE_4_BIT_LCD_DISPLAY`, the I2C LCD flags, and `FEATURE_NEXTION_DISPLAY`. RT-21 FSTN display. DCU-3 LCD | Operate | **Out of the baseline.** ADR 0006. A later front end can subscribe to the same state. Display layout, language, and splash flags in K3NG go out with the panel |
| Joystick and extra button boards | K3NG `FEATURE_JOYSTICK_CONTROL`, `FEATURE_ADAFRUIT_BUTTONS` | Operate | **Out.** The panel is STOP, CW, and CCW |
| Remote master/slave link | K3NG `FEATURE_REMOTE_UNIT_SLAVE`, `FEATURE_MASTER_WITH_SERIAL_SLAVE`, `FEATURE_MASTER_WITH_ETHERNET_SLAVE`. RT-21 master/slave over RS-232 | Operate | **Out.** The baseline is one shack box on the existing rotor cable. Several rotators are several controllers, shown together on the phase 2 dashboard |
| Heading display on the host | RT-21 and DCU-3 show the heading on their panels. ADR 0015 puts a compass on the web UI | Operate | **In, phase 2.** PC GUI and the on-box web status page. `ui.display_range`, `ui.cardinal_labels`, and `ui.speed_display` are the settings, on the Display page |

## Network, logging, and install

| Feature | Sources | Class | This project |
|---|---|---|---|
| Ethernet and USB | ADR 0007, ADR 0014. RT-21 USB, and LAN/Wi-Fi in the version 4 addendum. K3NG `FEATURE_ETHERNET` | Settings | **In.** `net.hostname`, `net.dhcp`, `net.address`, `net.mdns`. Network page |
| Log level and a debug view | K3NG serial debug. RT-21 debug mode. ADR 0015 live log page | Settings and operate | **In.** `ui.log_level` (`error`, `warn`, `info`, `debug`) and `ui.console_echo`. Console page. The live log view is phase 2 |
| Password or admin lock | The web UI is on the LAN (ADR 0015, ADR 0007). K3NG's feature header has no password. The RT-21 v3.5 manual and the v4 addendum used here document LAN/Wi-Fi and do not document an admin password | Settings | **In.** `net.admin_lock` and `net.admin_password`, under Advanced on Network. The lock covers the web UI and console verbs. GS-232 lines on the shared port stay open so a logger keeps working |
| First install and field upgrade | RT-21 firmware update over USB from v3, and `BUn` / `B2n` bootloader commands in the v4 addendum. ADR 0015 A/B slots | Install | **In, phase 3.** USB DFU for the first image, field upgrade into the inactive slot, rollback status, and the version report (`sys.firmware` is already readable) |
| Configure by recompiling | K3NG `rotator_features.h` `#define`s. ADR 0001 and ADR 0015 | Settings | **Out as a method.** Every feature in this table that is in scope is compiled in. The operator changes a setting and saves it |

## Where each in-scope setting lives

The simulator serves this list from `default_schema()`. A preset writes
axis and safety defaults from the catalog and leaves calibration,
memories, and the network lock alone.

| Page | On the page | Under Advanced |
|---|---|---|
| Axes | `sys.drive`, presence, sensor, brake, brake delay | Pulse debounce, degrees per pulse, ADC samples, limit switches |
| Limits | Travel, overlap, `az.center`, coast, speed, dead time, max run, stall current, stall timeout | Creep, PWM ramp, slowdown, go-to window, stall degrees |
| Park | Park headings, brake on arrival, idle minutes | `preset.1` … `preset.6` azimuth and elevation |
| Calibration | Heading offset, CW and CCW end counts | `az.cal.map`, `el.cal.map` |
| Display | Angle unit, display range, speed display, cardinal labels | — |
| Network | Hostname, DHCP, address, mDNS | Admin lock and password |
| Console | TCP port, GS-232 query token, echo, log level | `ports.rotctld`, `ports.easycom`, `ports.dcu1` |

## Phase 2 and phase 3

Phase 2 operates the rotator with the settings above. It does not grow
an on-box tracker, a panel display, or a remote slave.

- Heading display per axis
- Go to bearing, CW/CCW jog, STOP
- Park, auto-park, and heading-preset recall
- Enforce soft limits, coast, creep, stall, and the run timeout
- PWM ramp when the drive is the DC module
- Calibration wizard, including the multi-point map
- GS-232B commands beyond `M`, `C`, and `S`
- Hamlib rotctld, Easycom, and DCU-1 on their own ports
- Live log
- Multi-rotator dashboard

Phase 3 installs and upgrades: USB DFU, field upgrade into the inactive
slot, progress and rollback, and the version report.
