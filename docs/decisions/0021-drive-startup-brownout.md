# ADR 0021: Drive startup, brownout, and direct gate drive

- Status: Proposed
- Date: 2026-10-18

## Context

ADR 0020 leaves one hardware gate: `ARM_OK = ARM_EN AND nRESET`, fanned out by 74LVC1G08s so a supervisor reset forces the triac gates and the relay off. The owner asked to lean on the Drive MCU (STM32G431RBT6) for brownout, reset, and startup, and to take the remaining AND gates off the rotor sheet.

The numbers below are from the documents named in each paragraph, read for this record. The long sequence and the sheet change are also in `docs/design/drive-controller.md` and `hardware/controller-f407/DESIGN-NOTES.md`.

Documents:

- DS12589 Rev 6, October 2021, STM32G431x6/x8/xB datasheet.
- RM0440 Rev 9, March 2025. The STM32G431 is a category 2 device (RM0440 Table 1). Option-byte layout is RM0440 section 5.
- ES0431 Rev 9, June 2024, STM32G431xx/441xx errata. Revisions Z (REV_ID 0x2001), Y (0x2002), X (0x2003).
- AN2606 Rev 70, February 2026, system-memory boot mode. The G431/G441 bootloader is section 52.
- AOS AO3400A Rev 3.1, July 2023, for the relay FET threshold.

## What the STM32G431 documents say

### POR, PDR, BOR, PVD

RM0440 §6.2.1: the POR/PDR is coupled to the BOR. The BOR is active in every mode except Shutdown and cannot be disabled. Five thresholds are selected in the option bytes. On the way up, BOR holds reset until VDD reaches the selected VBORx. When VDD falls below the selected threshold, the device resets. Reset is released when VDD is above the VBORx upper limit. Figure 13 draws VPOR and VPDR. The datasheet does not publish separate VPOR or VPDR numbers. Note 1 under that figure: the reset temporization tRSTTEMPO exists only for the lowest threshold, VBOR0.

DS12589 §3.11.2: the lowest BOR level is 1.71 V at power-on. Higher thresholds are option bytes. Table 19 (§5.3.3) is the measured set. VBOR0 is guaranteed by design. The other BOR levels are characterized. Hysteresis is typical only.

| Level | Rising min / typ / max | Falling min / typ / max |
| --- | --- | --- |
| VBOR0 | 1.62 / 1.66 / 1.70 V | 1.60 / 1.64 / 1.69 V |
| VBOR1 | 2.06 / 2.10 / 2.14 V | 1.96 / 2.00 / 2.04 V |
| VBOR2 | 2.26 / 2.31 / 2.35 V | 2.16 / 2.20 / 2.24 V |
| VBOR3 | 2.56 / 2.61 / 2.66 V | 2.47 / 2.52 / 2.57 V |
| VBOR4 | 2.85 / 2.90 / 2.95 V | 2.76 / 2.81 / 2.86 V |

Vhyst_BORH0 is 20 mV typical in continuous mode and 30 mV typical otherwise. Vhyst_BOR_PVD is 100 mV typical for every BOR level except BOR0, and for the PVD. tRSTTEMPO after BOR0 is detected on a rising VDD is 250 µs typical, 400 µs max.

RM0440 §5.4.1, category 2 FLASH_OPTR bits 10:8 `BOR_LEV`: 000 about 1.7 V, 001 about 2.0 V, 010 about 2.2 V, 011 about 2.5 V, 100 about 2.8 V.

PVD, RM0440 §6.2.2: software enables it with PVDE in PWR_CR2. PLS[2:0] selects the falling threshold, 000 = VPVD0 through 110 = VPVD6, and 111 compares the external PVD_IN pin with VREFINT (§6.4.2). PVDO is in PWR_SR2. The event is EXTI line 16. Figure 14 shows about 100 mV of hysteresis, matching Vhyst_BOR_PVD.

DS12589 Table 19, PVD rising / falling, min / typ / max:

| PLS | Rising | Falling |
| --- | --- | --- |
| VPVD0 | 2.10 / 2.15 / 2.19 | 2.00 / 2.05 / 2.10 |
| VPVD1 | 2.26 / 2.31 / 2.36 | 2.15 / 2.20 / 2.25 |
| VPVD2 | 2.41 / 2.46 / 2.51 | 2.31 / 2.36 / 2.41 |
| VPVD3 | 2.56 / 2.61 / 2.66 | 2.47 / 2.52 / 2.57 |
| VPVD4 | 2.69 / 2.74 / 2.79 | 2.59 / 2.64 / 2.69 |
| VPVD5 | 2.85 / 2.91 / 2.96 | 2.75 / 2.81 / 2.86 |
| VPVD6 | 2.92 / 2.98 / 3.04 | 2.84 / 2.90 / 2.96 |

The highest PVD falling minimum (VPVD6, 2.84 V) sits inside the VBOR4 falling window (2.76 to 2.86 V). A PVD interrupt on VDD is therefore not guaranteed to run before BOR level 4 resets the core.

PVM, same table: VPVM1 (COMP/ADC) rising 1.61 / 1.65 / 1.69, falling 1.60 / 1.64 / 1.68. VPVM2 (OPAMP/DAC) rising 1.78 / 1.82 / 1.86, falling 1.77 / 1.81 / 1.85. Hysteresis 10 mV typical. RM0440 Table 39: EXTI lines 40 and 41.

### IWDG and WWDG

DS12589 §3.24.5: 12-bit downcounter, 8-bit prescaler, clocked from the independent LSI, able to run in Stop and Standby, hardware or software via the option bytes.

RM0440 §35.3.3: with the hardware option set, the watchdog is enabled at power-on and resets the device unless software writes IWDG_KR before the counter reaches 0, and the count is below the window. §35.3.1: writing 0xCCCC starts the counter from the reset value 0xFFF; at 0 an IWDG reset is generated; 0xAAAA reloads IWDG_RLR; once running, the IWDG cannot be stopped. The hardware option starts it without the 0xCCCC write (§35.4.1). §35.3.4: IWDG_STOP and IWDG_STDBY choose whether the counter keeps running in Stop and Standby. If it keeps running, it can wake the device. The window register IWDG_WINR resets to 0xFFF, which disables the window (§35.3.2).

Category 2 FLASH_OPTR (RM0440 §5.4.1): bit 16 IWDG_SW, 0 = hardware, 1 = software; bit 17 IWDG_STOP, 0 = frozen in Stop, 1 = running; bit 18 IWDG_STDBY, same choice for Standby; bit 19 WWDG_SW, 0 = hardware window watchdog, 1 = software.

IWDG_PR resets to 0, divider /4 (§35.4.2). IWDG_RLR resets to 0xFFF, and that reset is by Standby mode (§35.4.3), so a system reset does not put a programmed reload back to 0xFFF. A power-on reset does, because a BOR sets registers outside the RTC domain back to their reset values (RM0440 §7.1.1).

DS12589 Table 79, timeouts at 32 kHz LSI, guaranteed by design, plus one full LSI period of uncertainty (note 2):

| Prescaler | PR | Min (RL = 0) | Max (RL = 0xFFF) |
| --- | --- | --- | --- |
| /4 | 0 | 0.125 ms | 512 ms |
| /8 | 1 | 0.250 ms | 1024 ms |
| /16 | 2 | 0.500 ms | 2048 ms |
| /32 | 3 | 1.0 ms | 4096 ms |
| /64 | 4 | 2.0 ms | 8192 ms |
| /128 | 5 | 4.0 ms | 16384 ms |
| /256 | 6 or 7 | 8.0 ms | 32768 ms |

DS12589 Table 44, fLSI: at VDD = 3.0 V and TA = 30 °C, 31.04 to 32.96 kHz. Across VDD 1.62 to 3.6 V and TA −40 to 125 °C, 29.5 to 34 kHz. The power-on timeout at PR = /4 and RL = 0xFFF is (4096 × 4) / fLSI: 512 ms at 32 kHz, about 482 ms at 34 kHz, about 555 ms at 29.5 kHz.

WWDG, DS12589 §3.24.6: clocked from the main clock (PCLK), 7-bit downcounter, early-warning interrupt. Table 80 at 170 MHz PCLK: prescalers 1 / 2 / 4 / 8 give minimum timeouts 0.0241 / 0.0482 / 0.0964 / 0.1928 ms and maximum timeouts 1.542 / 3.084 / 6.168 / 12.336 ms. The WWDG stops if the main clock stops. It is not the safety watchdog.

### Reset sources and flags

RM0440 §7.1.1, power reset: POR or BOR; exit from Standby; exit from Shutdown. A BOR, including POR/PDR, sets every register except the RTC domain.

§7.1.2, system reset: low on NRST; WWDG; IWDG; software SYSRESETREQ; low-power-mode security reset (nRST_STDBY, nRST_STOP, nRST_SHDW); option-byte loader (OBL_LAUNCH); BOR.

The source is in RCC_CSR §7.4.28, offset 0x94, reset value 0x0C000000. The flags are cleared by a power reset only, or by writing RMVF (bit 23). Bits: 31 LPWRRSTF, 30 WWDGRSTF, 29 IWDGRSTF, 28 SFTRSTF, 27 BORRSTF, 26 PINRSTF, 25 OBLRSTF.

§7.1.3, RTC domain reset: BDRST in RCC_BDCR, or VDD and VBAT both powering on from off.

NRST_MODE, FLASH_OPTR bits 29:28: 00 and 11 are bidirectional reset input/output (the delivery default, and the mode that is forced during POR until the option bytes load); 01 is reset input only; 10 is GPIO PG10. The internal pulse generator guarantees at least 20 µs on NRST for an internal reset. IRH_EN (bit 30) holds NRST low until the pin meets VIL. During an internal reset the internal pull-up RPU is turned off.

DS12589 Table 57: VIL(NRST) max 0.3 × VDD, VIH min 0.7 × VDD, hysteresis 200 mV typical, RPU 25 / 40 / 55 kΩ, filtered pulse max 70 ns, unfiltered pulse min 350 ns over 1.71 to 3.6 V. Figure 27 recommends 0.1 µF on NRST.

### GPIO during and after reset, and the bootloader

DS12589 §3.11.5: under and after reset the I/O state is analog (Schmitt trigger disabled). The internal reset pull-up is deactivated when the reset source is internal. Table 11 note: unless a note says otherwise, every I/O is a floating input during and after reset.

Table 12 notes:

- (5) After reset, PA13, PA14, PA15, and PB4 are JTAG/SW debug alternate functions. Internal pull-up on PA15, PA13, and PB4. Internal pull-down on PA14. PB3 is the SWO/JTDO pin and is also alternate-function at reset (port B MODER reset, below).
- (4) PG10-NRST is 5 V tolerant only when the option bytes make it GPIO, and not during startup until those bytes have loaded.
- (7) If PB8 is left unconnected, take it out of analog mode after startup to limit consumption.
- (2) PC13, PC14, and PC15 sink at most 3 mA and are not current sources.
- (6) PB4 and PB6 can have a 5.1 kΩ UCPD pulldown until UCPD1_DBDIS is set in PWR_CR3.

RM0440 §9.4.1, GPIOx_MODER reset: port A 0xABFFFFFF (PA13, PA14, PA15 = alternate function 10, every other pin analog 11); port B 0xFFFFFEBF (PB3 and PB4 = alternate function); ports C through G 0xFFFFFFFF (all analog). §9.4.4 PUPDR reset: port A 0x64000000 (PA15 pull-up, PA14 pull-down, PA13 pull-up); port B 0x00000100 (PB4 pull-up); other ports 0.

RM0440 §2.6 Table 5. BOOT0 comes from PB8 when nSWBOOT0 = 1, and from the nBOOT0 option bit when nSWBOOT0 = 0. With nBOOT0 = 1 and nSWBOOT0 = 0, the boot memory is main flash, and nBOOT1 is ignored on that row. The values are latched on the 4th edge of the internal startup clock after reset release. System memory is also visible at 0x1FFF0000. DS12589 §3.7 names the same choice and calls the option bit nBOOT_SEL; the option-byte map calls it nSWBOOT0 (FLASH_OPTR bit 26). The bootloader reprograms flash over USART, I2C, SPI, and USB DFU.

Category 2 ST production value of the user option bytes at 0x1FFF7800 is 0xFFEFF8AA (RM0440 §5.4.1). Decoded: nBOOT0 = 1, nSWBOOT0 = 1 (BOOT0 comes from PB8), nBOOT1 = 1, IWDG_SW = 1 (software), IWDG_STOP = 1, IWDG_STDBY = 1, WWDG_SW = 1, BOR_LEV = 000, NRST_MODE = 11, IRH_EN = 1, SRAM_PE = 1 (parity check disabled), nRST_STOP / nRST_STDBY / nRST_SHDW = 1, RDP = 0xAA. Bit 20 is 0 in that production word. The field text says reserved bits stay 1 when the word is rewritten; this proposal copies the production word and changes only the three fields below, so bit 20 stays 0.

AN2606 §4.8 and Table 115: the bootloader does not enable the IWDG. If the hardware IWDG option is already set, the bootloader writes the prescaler to its maximum (/256, 32768 ms at 32 kHz with RL = 0xFFF) and refreshes the counter. §4.8 also says that a bootloader entry which finds the IWDG disabled can leave the PVU bit set, and application code that then enables the IWDG has to wait for PVU to clear.

AN2606 Table 115 configures these pins in system-memory boot. Several of them are driven or pulled up, so they are forbidden as triac or relay gate pins:

| Pins | What the bootloader does |
| --- | --- |
| PA9, PA2, PC10 | USART1/2/3 TX, alternate-function outputs |
| PA10, PA3, PC11 | USART1/2/3 RX, inputs with pull-up |
| PA6, PB14 | SPI1/SPI2 MISO. Note 1: after SPI init the MISO line is set to 3.3 V |
| PA7, PA5, PA4, PB15, PB13, PB12 | SPI MOSI, SCK, and NSS, inputs with pull-down |
| PC4, PA8, PC8, PC9 | I2C2/I2C3, open-drain with pull-up |
| PA11, PA12 | USB DM/DP, input, no pull |

AN2606 does not describe the pins that table leaves out. A gate pin has to be one of those leftovers, and it still needs the external pulldown, because the reset state of a leftover pin is analog.

Below VBOR0 the datasheet does not guarantee pin state. DS12589 Table 17 note 1: once RESET is released, functionality is guaranteed down to VBOR0 minimum.

### Early warning of VIN_RECT

VIN_RECT is the half-wave raw dc on the rotor sheet, crest about 37 V. It must not land on an MCU pin. The PVD watches VDD. As the table above shows, VPVD6 falling (min 2.84 V) is not above VBOR4 falling (max 2.86 V), so a VDD detector is not an early warning of the 26 VAC failing.

RM0440 §21.4.28: the ADC has three analog watchdogs. AWD1 compares a 12-bit window (HT1/LT1 in ADC_TR1) and can interrupt. AWD2 and AWD3 use the upper 8 bits and can guard several channels. The comparison sets a flag. It does not by itself drive an arbitrary GPIO. RM0440 §11.3.3 connects ADCn_AWDx_OUT to timer trigger inputs, which is a PWM-break path. The rotor gates are plain GPIO. ES0431 §2.5.4 (all revisions): ADC_AWDy_OUT is also cleared at the end of a conversion on a channel the watchdog is not guarding. The workaround is to convert only guarded channels.

RM0440 §24 and DS12589 §3.21: the G431 has four comparators. Inputs are GPIO, DAC, or VREFINT and 1/4, 1/2, 3/4 of VREFINT. Hysteresis is programmable. The output can wake from Sleep and Stop, interrupt, break a timer (BKIN / BKIN2), or appear on an alternate-function pin. §24.3.3: polarity selection and output redirection keep working without the APB clock, including in Stop. A comparator output on a timer break pin does not move our plain GPIO gates. The path that does is an interrupt, while the core is still running, that drives the four outputs to the safe level.

ES0431 §2.6.1: on revisions Z and Y the comparator was not fully tested (status N, N; absent on X). The substitute Voffset is −20 mV min, −15 / +2 mV typ, +3 mV max, over the full VDDA and temperature range. No workaround. A divider threshold needs margin for that 20 mV.

### Minimum VDD at which the pins are guaranteed

DS12589 Table 17: VDD min 1.71 V, max 3.6 V. Note 1: after reset is released, functionality is guaranteed down to VBOR0 min. VDDA is 1.62 V min when a comparator or the ADC is used, 2.0 V min for an op-amp, 2.4 V min for VREFBUF.

Table 54 and the prose in §5.3.13: a GPIO can sink or source ±8 mA, and ±20 mA with a relaxed VOL/VOH. At |IIO| = 8 mA (2 mA on FT_c) and VDD ≥ 2.7 V, VOL max is 0.4 V and VOH min is VDD − 0.4 V (CMOS) or 2.4 V (TTL). At |IIO| = 20 mA and VDD ≥ 2.7 V, VOL max is 1.3 V and VOH min is VDD − 1.3 V. At |IIO| = 4 mA (1 mA on FT_c) and VDD ≥ 1.62 V, VOL max is 0.4 V and VOH min is VDD − 0.45 V. Table 15 absolute maxima: 20 mA source or sink on one pin, 100 mA summed, 150 mA on the VDD and VSS sums.

BOR level 4 holds the device in reset, pins analog, before VDD falls through the 2.7 V 8 mA specification: VBOR4 falling minimum is 2.76 V.

### Errata that touch this

ES0431 Rev 9. No erratum says a GPIO is driven during reset, or that BOR, the IWDG, or the PVD fails.

- §2.2.1: full 4-wire JTAG without NJTRST cannot be used. Use SWD. The bench header is SWD.
- §2.2.3: LSI can run far above 32 kHz when it clocks the RTC or the CSS on LSE, and VDD resets while the backup domain does not (Shutdown exit, a separate VBAT, or VBAT tied to VDD with a drop under VDD min shorter than 1 ms). That would stretch or shrink the IWDG. Workaround: clock the RTC from LSE or HSE/32 and leave LSECSSON clear, or reset the backup domain on every BORRSTF. This proposal takes the first workaround. Arming state does not live in backup registers.
- §2.2.6: a backup-domain power-on reset can be missed if VBAT/VDD falls through a window a few millivolts wide, somewhere between 100 mV and 700 mV. One effect is a spurious LSCO on PA2. Workaround: let VDD and VBAT fall below 100 mV for more than 200 ms, or software-reset the backup domain when BORRSTF is set. PA2 is already excluded as USART2_TX. Output state does not live in backup registers.
- §2.2.7: a system reset at a rare instant can make the first SRAM write fail. Dummy-read each SRAM instance the part has before the first write. The workaround in the erratum names SRAM1 at 0x20000000, an SRAM2 instance at 0x20004000, and CCM SRAM at 0x10000000.
- §2.5.4: ADC watchdog output, above. Prefer the comparator.
- §2.6.1: comparator offset on rev Z and Y, above.
- §2.7.1: an op-amp in non-inverting PGA mode is disturbed by a fast edge on its VINM0 pin (PA3, PA5, or PB2). Those pins are also bootloader pins. The gate path does not use an op-amp.

## Decision

Take U3, U6, U9, and U10 off `rotor_drive.kicad_sch`, and the four 100 nF bypasses that belonged to them (C3, C6, C9, C10). The Drive pins drive the three opto FETs and the relay FET directly.

`AZ_CW_EN`, `AZ_CCW_EN`, and `AZ_BRAKE_EN` connect to the gates of Q2, Q3, and Q4. `R2G`, `R3G`, and `R4G` stay, 100 kΩ to GNDPWR, and R50, R51, and R52 stay on the same nets. A high-Z pin, which is the reset and boot state of a non-debug GPIO, leaves each opto FET off. `AZ_BRAKE_EN` high means release. Low, or high-Z with the pulldown, leaves the wedge engaged. K1 stays SPST-NO. Coil off, the contact is open.

The MOC3023 LED stays on the +5 V rail through the existing 180 Ω and the existing 2N7002 (Q2, Q3, Q4, LCSC C8545). The Drive pin drives that FET's gate. Steady pin current into the gate and the 100 kΩ pulldown is 3.3 V / 100 kΩ = 33 µA, inside the ±8 mA VOH/VOL specification and the 20 mA absolute maximum. No added buffer on the triac path. Driving the LED from the MCU pin would put the pin on the +5 V LED string; that current is past the 8 mA specification, so the 2N7002 stays.

The TPS3823-33DBVR (U1, LCSC C7719) stays, and only on the relay path. The datasheet review does not show a problem with the triac pulldowns: analog GPIO plus the external pulldown holds those gates off through reset, boot, and BOR. The supervisor still has a job the pulldown cannot do. Its `/RESET` is push-pull and active low (DESIGN-NOTES, TI SLVS165O). It cannot be wire-ANDed onto a GPIO the MCU is driving high. A diode from the relay gate to `/RESET` is a bad clamp: AO3400A VGS(th) is 0.65 V min, 1.05 V typ, 1.45 V max at VDS = VGS (AOS Rev 3.1; the test current is 250 µA, and text extraction of that PDF renders the micro prefix as milli on this row and on the breakdown-voltage row). A silicon diode drop sits on top of that 0.65 V minimum, so Q1 can still conduct. The clamp is a hard short to ground:

- R54, 1 kΩ, between `ARM_EN` and the relay-gate net `RELAY_GATE`. A pin driven to 3.3 V into a grounded clamp sources about 3.3 mA, inside the 8 mA VOH specification at VDD ≥ 2.7 V.
- Q8, MMBT3904, JSCJ, SOT-23, LCSC C20526. Base from `nRESET` through R55, 10 kΩ. Emitter at GNDPWR.
- Q9, 2N7002, LCSC C8545, the same part as Q2–Q4. Gate pulled to +3V3 by R56, 100 kΩ. Collector of Q8 holds that gate down while `nRESET` is high. Drain of Q9 shorts `RELAY_GATE` to GNDPWR while `nRESET` is low.
- R40, 100 kΩ, stays on the FET side of R54. R53 stays on `ARM_EN`. A floating `ARM_EN` holds Q1 off even when the supervisor has released the clamp.

`nRESET` is not tied to the MCU NRST pin. The hardware IWDG is what resets the core. The supervisor can open K1 while the core is still executing, including the case where firmware keeps petting the IWDG and stops petting WDI, and the case where `ARM_EN` is stuck high.

Q1 stays the AO3400A (LCSC C20917). The coil is 80 mA. Q9 only clamps a gate.

Option bytes. Copy production 0xFFEFF8AA and change three fields. The resulting word is 0xFBEEFCAA.

| Field | Production | This proposal |
| --- | --- | --- |
| IWDG_SW | 1, software | 0, hardware |
| nSWBOOT0 | 1, BOOT0 from PB8 | 0, BOOT0 from the nBOOT0 bit |
| BOR_LEV | 000, level 0, about 1.7 V | 100, level 4, about 2.8 V |
| nBOOT0 | 1 | 1, main flash (Table 5 row with nSWBOOT0 = 0) |
| IWDG_STOP, IWDG_STDBY | 1, counter keeps running | 1, so a Stop or Standby the firmware did not intend still resets |
| WWDG_SW | 1, software | 1 |
| NRST_MODE | 11, bidirectional | 11 |
| nRST_STOP, nRST_STDBY, nRST_SHDW | 1, no reset on entry | 1 |
| RDP | 0xAA, level 0 | 0xAA |

IWDG registers, after the first pet of the power-on timeout: PR = 000 (/4), RL = 799, window left at 0xFFF. Timeout is (800 × 4) / fLSI: 100 ms at 32 kHz, about 94 ms at 34 kHz, about 109 ms at 29.5 kHz, plus one LSI period. Firmware pets inside the power-on window (about 0.5 s) before it shortens the reload. Because IWDG_RLR is not cleared by a system reset, an IWDG reset keeps 799. A power-on returns it to 0xFFF until firmware writes it again.

Bring-up order: the factory word has IWDG_SW = 1, so the first image can be programmed and can pet the watchdog before it commits 0xFBEEFCAA. After that commit, the hardware watchdog is on. If the option bytes are programmed before a pet loop exists, AN2606 Table 115 still refreshes a hardware IWDG from the bootloader, at the maximum prescaler, so the ROM bootloader and SWD remain usable.

The Station reads FLASH_OPTR in the status record at link-up. It refuses to arm when BOR_LEV, IWDG_SW, IWDG_STOP, IWDG_STDBY, nSWBOOT0, or nBOOT0 disagree with this table. The Drive does the same check and, on a mismatch, sets fault `OPTION_BYTES` and leaves the outputs at the safe level: direction gates low, brake engaged, relay open. Pins that firmware has not configured stay analog, and the pulldowns hold the gates off.

Early warning of a failing 26 VAC feed is a divided, clamped sample of VIN_RECT into a comparator, with the threshold set below the crest by enough to cover the ES0431 §2.6.1 offset and the divider tolerance. The interrupt, while the core is still running, drives CW and CCW off, the brake engaged (gate low), and the relay off. The divider and the pin are not on this sheet. The PVD stays available as a VDD monitor. It is not the VIN_RECT warning.

RTC clock is LSE or HSE/32. LSECSSON stays clear, so ES0431 §2.2.3 does not apply to the IWDG's LSI. Firmware dummy-reads SRAM after each system reset (ES0431 §2.2.7) before the first write.

Gate pins, when they are assigned, avoid PA13, PA14, PA15, PB3, PB4, PG10, and PB8, and avoid every pin in the AN2606 Table 115 list above. PB8 is an input until the option bytes load when nSWBOOT0 = 0, then analog. It is not a gate.

## Consequences

The rotor sheet matches this proposal: the four AND gates and their bypasses are gone, Q8, Q9, R54, R55, and R56 are on the relay path, and the triac gates are the Drive request nets. Firmware is not in this change. The option bytes are programmed when the Drive firmware exists.

STOP_N still enters the TPS3823 `/MR`, so holding STOP drops `nRESET` and Q9 clamps the relay off. STOP does not reset the Drive, and it does not by itself drop a triac gate. The bus is open while the button is held. A readable STOP pin, still open in the design note, is what makes the Drive drop the gates and engage the brake before the button is released. Until that pin exists, releasing STOP can reclose K1 onto gates firmware is still holding on, for as long as the core is healthy and petting the IWDG.

nSWBOOT0 = 0 means the Station cannot force the ROM bootloader by driving PB8. Field update is a command the running Drive accepts, or SWD. The alternative, nSWBOOT0 = 1 with a pulldown on PB8, restores that path and reopens the bootloader pin list as a live hazard. This proposal takes the option-bit boot.

Below POR, and below VBOR0, the pin state is not guaranteed. The pulldowns define the gates while the pin is high-Z. K1's open contact defines an unpowered coil. A pin that actively drives high in that region is outside what the datasheet covers. That is the residual risk of removing the AND gates.

## Open questions

1. VIN_RECT divider ratio, clamp, and comparator input pin. Not drawn here.
2. A Drive GPIO for STOP, so the gates drop while the button is held and the core is still running.
3. Whether a later acceptance restores PB8 boot for field update. This proposal leaves it off.
4. Resistor LCSC numbers for R54, R55, and R56. The sheet marks them TBD, like the other passives.
5. K1's 5 A inductive rating against about 7.3 A of motor-plus-brake overlap, and TR1 saturation. Unchanged from ADR 0020.
