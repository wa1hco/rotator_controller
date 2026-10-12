# ADR 0015: Configuration model and user interface

- Status: Accepted
- Date: 2026-10-12
- Revised: 2026-10-12. The PC tool is in this repository. See ADR 0019.

## Context

K3NG selects features with a large set of compile-time `#define`s. Changing
a rotator, a protocol, or a limit means rebuilding and reflashing. That is
the configuration model this project is leaving (ADR 0001).

The box is headless (ADR 0006): STOP, CW, and CCW on the front, no display
and no knob. Ethernet and isolated USB are both on the rear (ADR 0007,
ADR 0014). The MCU is an STM32F407VGT6 with 1 MB of flash. Someone has to
be able to set up a rotator, calibrate it, and recover a bad firmware image
without a debugger and without a rebuild.

## Decision

### Three layers

Configuration is three layers, and only the first one is compile-time.

1. **A board file per PCB.** It names pins and which chips are stuffed.
   It does not select features. A later board gets its own file. The V4
   file will map the F407 pins, the LAN8720A, and the triac drivers.
2. **Every feature is compiled in.** There are no feature `#ifdef`s. A
   board that has no elevation sensor still contains the elevation code.
   The board file leaves those pins unused, and the running firmware
   reports the axis absent.
3. **Run-time settings are typed, named, and versioned.** They live in
   flash, not in the image. Each value has a type and limits. A value
   outside its limits is rejected and the previous record is kept. The
   record carries a schema version. Loading an older version runs a
   migration. The on-box record may be a packed blob (the firmware stub
   already is). The file a person edits is text, described below.

The draft namespaces, the command grammar, and the text file are in
`docs/design/configuration.md`. The rotor catalog is
`software/firmware/presets/rotor-presets.yaml`.

### Rotor presets

A preset is a row in a table that is always linked into the firmware.
Picking "HAM-IV" or another model writes that row's defaults into the
axis and safety settings. It does not touch `net.*`, `ports.*`, or a
calibration the operator already saved.

After the preset, a guided sweep drives the axis to one end, records it,
drives to the other end, records that, and fits the sensor map. The
operator confirms before the result is saved.

Dump and restore use one text file. Dump writes the current settings.
Restore parses the file, checks every value against the limits, and only
then replaces the stored record.

### One command layer, three ways to reach it

The web UI, the text console, and a later PC tool all call the same
settings and command layer. They do not each keep a copy of the rules.

**Web UI, primary.** The box serves it on Ethernet. The pages are:

- status, including a compass
- settings forms
- the preset picker
- the calibration wizard
- firmware upload
- a live view of the log
- backup and restore of the text file

**Text console, on USB CDC and on a TCP port.** Commands are `get`,
`set`, `save`, `status`, `calibrate`, `log`, and `help`, plus the preset
and dump commands in the grammar note. USB CDC is the serial port. The
TCP listener is the network port (telnet-style, one line at a time).

**GS-232 shares those ports by grammar, not by a mode switch.** A line
is GS-232 when its first token is in the closed Yaesu set the parser
implements. A line is a console command when its first token is one of
the reserved words. Anything else produces no reply.

The two sets are not allowed to overlap, and matching is on the whole
token, not a prefix. `S` is the GS-232B stop. `status` and `save` are
console commands. A logging program that sends only GS-232 never receives
a console sentence, because an unrecognized line is silence rather than
an error banner.

A port-mode switch was the other option. It loses: the logger and a
person would not be able to use the same cable, or the same TCP port,
without changing a setting first. The web UI is the primary interface,
but N1MM and the other loggers speak GS-232 on the serial or TCP port
they already have. Grammar detection is what "the same port" has to mean.
The invariant (no shared tokens) is part of the grammar note, and a new
GS-232 token or a new console verb has to keep it.

**Python tool.** The console library and the configuration app live in
`software/gui`. ADR 0019 records the toolkit. WIMS can import the
library without the GUI. The web UI's status and settings are the same
operations.

### Programming, upgrades, and debug

**Unbrick path: the STM32F407 system-memory USB DFU bootloader.** Hold
BOOT0 and press RESET. The ROM bootloader enumerates on PA11/PA12.
`dfu-util` or STM32CubeProgrammer can rewrite flash from address
`0x08000000`, including a broken field-upgrade bootloader. This path
needs no code of ours.

AN2606 (ST Doc ID 13801, the STM32F405/407 section) requires an HSE
crystal for USB DFU, an integer number of MHz from 4 to 26. The ROM
measures that crystal against HSI and can mis-measure a high frequency.
ST's later note on that measurement says to prefer a low frequency, with
8 MHz given as the example over 25 MHz. The 25 MHz crystal on the
LAN8720A (LCSC C9006) does not clock `OSC_IN`, and the 50 MHz RMII
REF_CLK is not HSE. The board therefore has a second crystal, 8 MHz, on
the MCU HSE pins. Its LCSC C-number is not assigned until a part is
checked. The PHY keeps C9006.

BOOT1 is PB2 on this part. System memory is BOOT0 high and BOOT1 low at
reset. PB2 is pulled down. AN2606 also requires the unused bootloader
inputs to sit at a known level during detection, otherwise the ROM can
lock onto noise instead of USB. Those pins are PA10 (USART1 RX), PB11
and PC11 (USART3 RX), and PB5 (CAN2 RX). PB11 is RMII TX_EN on this
board, so that pull-down also holds the PHY idle.

**Field upgrades: a small custom bootloader, not MCUboot.** The F407VG
1 MB map (RM0090) is four 16 KB sectors, one 64 KB sector, then seven
128 KB sectors. MCUboot wants two equal slots and, in swap mode, a
scratch sector at least as large as the biggest sector it erases
(128 KB here). After a bootloader in the small sectors, the 16 KB and
64 KB sectors are stranded, and a swap across 128 KB erases is a long
time to sit with the power stage off. MCUboot is the right tool for a
family of boards. This is one board, and the requirement is narrow:
check the image, boot it, and revert if it does not come up.

The map this bootloader uses:

| Flash | Size | Use |
|---|---|---|
| Sectors 0–2 | 48 KB | Bootloader |
| Sector 3 | 16 KB | Boot record (pending slot, confirmed flag). Its own sector, so writing the flag does not erase the bootloader |
| Sector 4 | 64 KB | Settings, two copies |
| Sectors 5–7 | 384 KB | Image A |
| Sectors 8–10 | 384 KB | Image B |
| Sector 11 | 128 KB | Spare |

384 KB is the image budget. The core, lwIP, and a modest web UI fit if
the pages stay small. If they outgrow the slot, static files can move
into sector 11. The two code slots stay equal.

The running image writes the new image into the inactive slot. It checks
a CRC and an Ed25519 signature (the public key lives in the bootloader),
marks the slot pending, and resets. The bootloader checks the signature
again and jumps. The new image must set the confirmed flag after it
reaches its main loop and kicks the watchdog. A reset before that flag
clears pending and boots the previous slot. The power stage stays off
until the application is confirmed.

The bootloader does not speak USB. Field upgrade is written by the
application, from the web UI or the console. ROM DFU is the recovery
path when the bootloader itself is wrong.

**Debug connector: Tag-Connect TC2050-IDC-NL.** Pads for SWDIO, SWCLK,
SWO, NRST, VTREF, and ground, in Tag-Connect's Cortex footprint. No
header is placed, so there is no LCSC line and no Mouser line, and the
board is cheaper than one with a 10-pin 1.27 mm Cortex header. The cable
is a shop tool, bought once. The NL footprint has no alignment holes, so
the cable has to be held square. That is acceptable: debug is occasional,
and the front panel is not where a shrouded header would go. The legged
TC2050-IDC is the fallback if the NL pad proves awkward; it still needs
no connector, only two holes.

**Log.** Levels are error, warn, info, and debug. A ring buffer in RAM
holds the recent lines. The console `log` command and the web UI read
it. It is not a flash log.

## Consequences

- The front panel stays STOP, CW, and CCW (ADR 0006). Setup is the web
  UI, with the text console as the same operations in words.
- A new PCB is a new board file. It is not a set of feature flags.
- Adding a GS-232 token or a console verb has to keep the two sets
  disjoint. Unrecognized lines stay silent.
- The next schematic adds the 8 MHz HSE, the BOOT0 and RESET tactiles,
  the TC2050-IDC-NL footprint, the boot LED, and the USB-C wiring in
  the hardware-requirements addendum. C-numbers stay TBD until those
  parts are looked up. The PHY crystal decision (C9006, REF_CLK from
  the LAN8720A) is unchanged.
- ROM DFU needs the 26 VAC feed, so the derived 3.3 V rail is up
  (ADR 0018). USB VBUS powers the upstream side of the ADuM4160 only.
  There is no separate logic supply.
- The KiCad files are not edited by this decision.
