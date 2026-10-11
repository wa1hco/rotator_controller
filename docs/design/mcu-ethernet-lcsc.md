# MCU + Ethernet parts check (JLCPCB / LCSC, Mouser for through-hole)

Queried Sunday 2026-10-11, about 7:40 PM ET. Stock moves daily, so recheck before ordering.

**Sources**
- JLCPCB assembly parts search API (`jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`): JLC stock, Basic/Extended/Preferred flag, JLC price ladder.
- LCSC product API (`wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx`): LCSC warehouse stock and price.
- ST datasheet DS8626 (STM32F405xx/F407xx, DocID022152 Rev 4), via LCSC's copy: https://datasheet.lcsc.com/datasheet/pdf/eded9b3eda904d8bb3a84cf2887d6a5f.pdf?productCode=C28730 (st.com refused the automated download)
- Mouser blocks automated access ("Access Denied" to both WebFetch and curl). Mouser figures below come from search-engine snippets of aggregator pages and are marked **unverified**.

**Columns:** "JLC stock" is what JLCPCB assembly can place right now. "Price 5 / 10" is the JLC unit price in the 1-9 tier and the 10+ tier, in USD. Every SMT part below is **Extended** (about $3 setup per unique part) unless it says Basic. None of the parts that matter here came back as Preferred.

---

## Key finding: the 64-pin F407 doesn't exist from ST, and the F405 has no Ethernet

The task brief said RMII is fully available on a 64-pin F407. The datasheet says otherwise:

- DS8626 Table 2 (features and peripheral counts) lists these part numbers: **STM32F405RG (LQFP64)**, F405OG, F405VG, F405ZG, F405OE, **STM32F407Vx (LQFP100)**, **F407Zx (LQFP144)** and **F407Ix (LQFP176/UFBGA176)**. **There is no STM32F407Rx (64-pin).**
- The same table's "Ethernet" row reads **No for every F405** and **Yes for every F407**. The current V4 part, the F405RGT6, has **no Ethernet MAC**.
- The pin table does show RMII alternate functions on LQFP64 pins (PC1=9 MDC, PA1=15 REF_CLK, PA2=16 MDIO, PA7=23 CRS_DV, PC4=24 RXD0, PC5=25 RXD1, PB11=30 TX_EN, PB12=33 TXD0, PB13=34 TXD1). That table is shared by the whole family, though, and no ST device in a 64-pin package has the MAC behind those pins.
- Searching JLC for "STM32F407RGT6" turns up only the **Geehy APM32F407RGT6** (C3034689, LQFP-64), which is a third-party compatible part and not an ST part. I didn't check Geehy's datasheet for RMII on its 64-pin package. **Unverified.**

So adding RMII Ethernet to an ST part means going to **LQFP100 (F407V)** or larger. That re-lays-out the MCU area of V4, because LQFP64 to LQFP100 is a different footprint. It is not a drop-in swap.

**Second finding: the current F405RGT6 (C15742) shows 0 stock at both JLC and LCSC.** As drawn, V4 can't be assembled at JLC today.

---

## 1. MCUs

| Part (MPN) | C-number | Package | Class | JLC stock | LCSC stock | Price 5 / 10 (USD) | Notes |
|---|---|---|---|---|---|---|---|
| STM32F407VGT6 | **C12345** | LQFP-100 14x14 | Extended | **1,947** | 1,535 | 6.14 / 5.41 | 1 MB flash / 192 KB RAM, Ethernet MAC, 82 GPIO |
| STM32F407VGT6TR | C919362 | LQFP-100 | Extended | 238 | 238 | 8.67 / 7.62 | Tape-and-reel version of the same die |
| STM32F407VET6 | C28730 | LQFP-100 | Extended | 182 | 0 | 4.93 / 4.43 | 512 KB flash; thin stock |
| STM32F407ZGT6 | C19156 | LQFP-144 20x20 | Extended | 1,636 | 816 | 7.80 / 6.87 | More pins than needed |
| STM32F405RGT6 (current V4) | C15742 | LQFP-64 | Extended | **0** | **0** | 5.96 / 5.31 | **No Ethernet MAC; out of stock** |
| APM32F405RGT6 (Geehy) | C5290473 | LQFP-64 | Extended | 988 | n/a | 4.26 / 3.58 | Third-party compatible part, no Ethernet |
| APM32F407RGT6 (Geehy) | C3034689 | LQFP-64 | Extended | 1,497 | n/a | 4.26 / 3.58 | Third-party; 64-pin RMII **unverified** |
| STM32F407RGT6 (ST) | none | | | | | | No ST listing at JLC/LCSC; the part doesn't exist (see above) |
| STM32H723VGT6 | C730142 | LQFP-100 | Extended | **0** | 0 | 8.27 / 7.42 | Out of stock |
| STM32H723ZGT6 | C730146 | LQFP-144 | Extended | 412 | 16 | 11.05 / 10.04 | Available but costly; bigger rework |

URLs: https://www.lcsc.com/product-detail/microcontrollers-mcu-mpu-soc_stmicroelectronics-stm32f407vgt6_C12345.html ·
https://www.lcsc.com/product-detail/microcontrollers-mcu-mpu-soc_stmicroelectronics-stm32f407vet6_C28730.html ·
https://jlcpcb.com/partdetail/C15742 · https://jlcpcb.com/partdetail/C730146

### RMII pins on F407V (LQFP100), from the DS8626 pin table
On LQFP100, port G is not bonded out (footnote 1 of Table 2), so the TX pins must use the PB options:

| Signal | Pin (LQFP100 #) | Also costs you |
|---|---|---|
| REF_CLK | PA1 (24) | ADC123_IN1 |
| MDIO | PA2 (25) | ADC123_IN2, USART2_TX |
| CRS_DV | PA7 (32) | ADC12_IN7 |
| MDC | PC1 (16) | ADC123_IN11 |
| RXD0 / RXD1 | PC4 (33) / PC5 (34) | ADC12_IN14/15 |
| TX_EN | PB11 (48) | USART3_RX, I2C2_SDA |
| TXD0 / TXD1 | PB12 (51) / PB13 (52) | SPI2 NSS/SCK, OTG_HS pins |

USB FS stays on PA11/PA12 (70/71), and SWD on PA13/PA14. RMII takes 6 of the 16 ADC inputs. That leaves 10: PA0, PA3, PA4, PA5, PA6, PB0, PB1, PC0, PC2 and PC3, which is plenty for two axes of pots and sensors.

### Pin budget on F407VGT6 (82 GPIO). This is an estimate; adjust it to the real V4 netlist.
| Function | Pins |
|---|---|
| RMII + PHY nRST + nINT | 11 |
| USB FS D+/D- + VBUS sense | 3 |
| SWD (SWDIO, SWCLK, SWO) | 3 |
| Spare UART | 2 |
| HSE crystal | 2 (OSC_IN/OUT) |
| 2 axes of sensor inputs (pot/dual-end pot ADC, limit/stall/pulse inputs), about 6 per axis | 12 |
| Triac drive (CW, CCW, brake/aux per axis) | 6 |
| Buttons (about 6) and LEDs (about 6) | 12 |
| I2C/SPI for EEPROM/expansion | 4 |
| **Total** | **about 55 of 82**, leaving roughly 25 spare |

A 64-pin part with 51 GPIO would be tight even if ST made an Ethernet version.

## 2. Ethernet PHYs (all RMII)

| Part (MPN) | C-number | Package | Class | JLC stock | LCSC stock | Price 5 / 10 | Temperature |
|---|---|---|---|---|---|---|---|
| LAN8742A-CZ-TR (Microchip) | **C621424** | QFN-24-EP 4x4 | Extended | 10,467 | 10,039 | 1.57 / 1.29 | 0 to 70 °C |
| LAN8720A-CP-TR (Microchip) | **C45223** | QFN-24 4x4 | Extended | **25,757** | 25,281 | 0.80 / 0.68 | 0 to 85 °C |
| DP83848CVVX/NOPB (TI) | C16688 | LQFP-48 7x7 | Extended | 6,724 | 6,619 | 3.13 / 2.79 | 0 to 70 °C |
| IP101GRI (IC Plus) | C703537 | QFN-32-EP 4x4 | Extended | 20,152 | 17,881 | 1.08 / 0.95 | |
| JL1101 | none found | | | | | | No result for "JL1101" or "JL1101-N040C" in the JLC search. **Unverified/not listed.** |

URLs: https://www.lcsc.com/product-detail/ethernet-transceivers_microchip-tech-lan8742a-cz-tr_C621424.html ·
https://www.lcsc.com/product-detail/ethernet-transceivers_microchip-tech-lan8720a-cp-tr_C45223.html ·
https://jlcpcb.com/partdetail/C16688 · https://jlcpcb.com/partdetail/C703537

LAN8720A and LAN8742A share the same footprint and nearly the same pinout. The LAN8720A has 2.5x the stock and half the price. Both can generate the 50 MHz RMII REF_CLK from a 25 MHz crystal, so the board needs no separate 50 MHz oscillator. ST's DS8626 Figure 92 ("RMII with a 25 MHz crystal and PHY with PLL") shows this arrangement. DP83848 is the classic ST-eval PHY, but it is bigger (LQFP-48) and pricier.

## 3. WIZnet W5500 (SPI Ethernet with its own TCP/IP stack)

| Part | C-number | Package | Class | JLC stock | LCSC stock | Price 5 / 10 |
|---|---|---|---|---|---|---|
| W5500 | **C32843** | LQFP-48 7x7 | Extended | 18,316 | 18,318 | 2.82 / 2.46 |

https://lcsc.com/product-detail/ethernet-controllers_wiznet-w5500_C32843.html
It needs a 25 MHz crystal and magnetics/MagJack too. It would only make sense if the board stays on a 64-pin MCU, and the ST F405RGT6 is out of stock, so this path also means changing the MCU (for example to the Geehy APM32F405RGT6, C5290473).

## 4. PHY clock (25 MHz crystal) and 50 MHz oscillator option

| Part | C-number | Package | Class | JLC stock | Price 5 / 10 | Specs (from JLC listing) |
|---|---|---|---|---|---|---|
| X322525MOB4SI (YXC) 25 MHz | **C9006** | SMD3225-4P | **Basic** | 219,100 | 0.095 / 0.095 (0.076 @50) | 12 pF load, ±10 ppm tolerance, ±20 ppm over temperature, -40 to 85 °C |
| 7M25000014 (TXC) 25 MHz | C90912 | SMD3225-4P | Extended | 17,136 | 0.15 | Alternative |
| OT2EL4C4JI-111OLP-50M (YXC) 50 MHz oscillator | C5203552 | SMD3225-4P | Extended | 35,242 | 0.48 / 0.36 | Only needed for the external-REF_CLK scheme (DS8626 Fig. 91) |
| OT322550MJBA4SL (YXC) 50 MHz oscillator | C717684 | SMD3225-4P | Extended | 13,660 | 0.53 | Alternative |

Recommendation: use the 25 MHz crystal C9006 (Basic, so no setup fee) on the PHY, and let the PHY output the 50 MHz REF_CLK. The LAN87xx needs 25 MHz ±50 ppm, which this part meets. Size the load capacitors for 12 pF.
https://www.lcsc.com/product-detail/crystals_yxc-crystal-oscillators-x322525mob4si_C9006.html

## 5. RJ45 MagJack (through-hole, hand soldered, **bought from Mouser**)

Mouser's site blocked every automated request (WebFetch and curl both got "Access Denied"), so **none of the Mouser stock or price figures below are confirmed live**. Check them on the pages before ordering. The Mouser order numbers are also unconfirmed, except Pulse's, which an aggregator listing shows as 673-J0011D01BNL.

| Part | Mfr | Mouser page | Mouser stock / price (unverified) | Other evidence |
|---|---|---|---|---|
| **J0011D01BNL** | Pulse | https://www.mouser.com/ProductDetail/Pulse-Electronics/J0011D01BNL | Aggregator snippets show Mouser at **2,588** (Findchips) or 2,122 (omo-ic), and about **$9.53 @1, $7.59–7.92 @10** (the snippets disagree; date unknown) | Digi-Key 553-1483-ND showed 7,339 at $7.82 @10 (snippet). Tab-down, green/yellow LEDs, 100BASE-TX, 1:1. Pulse lists DP83848 among its reference PHYs |
| **RJMG1BD3B8K1ANR** | Amphenol | https://www.mouser.com/ProductDetail/Amphenol-Commercial-Products/RJMG1BD3B8K1ANR | Mouser page exists (search result), but stock and price weren't visible | TME showed 1,801 at $4.24 @10. Tab-down, yellow/green LEDs, 10/100, AutoMDIX |
| **7499010211A** | Würth (WE-RJ45LAN) | https://www.mouser.com/ProductDetail/Wurth-Elektronik/7499010211A | Not visible | RS UK showed 54 in stock at £7.24 @5. Farnell showed 56 units (thin) |
| **SI-60062-F** | Bel (Stewart) | https://www.mouser.com/ProductDetail/Bel-Fuse/SI-60062-F | Not visible | TME 599, MorrisHK 8,989 (snippets) |
| HR911105A | HanRun | Doesn't appear to be carried by Mouser (no listing found) | | **LCSC C12074**: JLC stock 51,428, about $1.52 @1 / $1.32 @10. Through-hole, but JLC could also hand-place it if Mouser sourcing were relaxed |

All of these are 10/100 MagJacks with 1:1 magnetics and center taps, which suit LAN8720A/LAN8742A. Before laying out the board, check the chosen jack's datasheet for the center-tap wiring (the LAN87xx wants the TX/RX center taps tied to 3.3 V through a ferrite) and its LED polarity.

## 6. ESD protection

| Use | Part | C-number | Class | JLC stock | Price 5 / 10 |
|---|---|---|---|---|---|
| USB D+/D- (and VBUS) | **USBLC6-2SC6** (ST) | **C7519** | Extended | 48,689 | 0.18 (0.14 @50) |
| | USBLC6-2SC6 (UMW, compatible part) | C2687116 | Extended | 69,342 | 0.048 |
| Ethernet TX±/RX± (PHY side of the MagJack) | **SRV05-4.TCT** (Semtech) | **C13612** | Extended | 43,496 | 0.16 (0.13 @50) |
| | RClamp0524PATCT (Semtech, DFN-10, low capacitance) | C40960 | Extended | 154,884 | 0.063 |

https://www.lcsc.com/product-detail/C7519.html · https://www.lcsc.com/product-detail/C13612.html · https://www.lcsc.com/product-detail/C40960.html
No Basic part turned up in these searches. One option to save a $3 setup fee is to use SRV05-4 for both USB and Ethernet. It is a 4-line TVS array, so one part per interface works for either.

---

## Recommendation

**STM32F407VGT6 (C12345, LQFP-100) + LAN8720A-CP-TR (C45223) + 25 MHz crystal X322525MOB4SI (C9006, Basic)**, with USBLC6-2SC6 (C7519) on USB, SRV05-4 (C13612) on Ethernet, and a Pulse J0011D01BNL MagJack from Mouser that you hand-solder.

Why:
- It is the only ST part with an Ethernet MAC that has good stock at JLC (1,947) at a reasonable price (about $5.41 at qty 10). The F407 isn't made in a 64-pin package, and the current F405RGT6 is out of stock anyway, so the re-layout is needed either way.
- The F405 to F407 move keeps the same family: same core, same peripheral layout, same HAL. The firmware hardware layer carries over. Only the package changes, and LQFP100 has about 25 spare pins after the full feature list.
- LAN8720A has the deepest stock (25k) and is the cheapest. LAN8742A (C621424, 10k) is a footprint-compatible fallback. Use the PHY-generated REF_CLK from the 25 MHz crystal, so there's no separate 50 MHz oscillator.
- Extended-part count for the Ethernet and USB additions: MCU, PHY, USBLC6 and SRV05-4 make 4, or about $12 in setup fees. Using SRV05-4 for both interfaces makes it 3.

The fallback is to keep a 64-pin footprint with the Geehy APM32F405RGT6 (C5290473) plus a W5500 (C32843) on SPI. That costs one third-party MCU, a simpler network stack and less flexibility. I'd only take it if re-laying out for LQFP100 is unacceptable.

## Unverified or open items
- All Mouser stock, prices and order numbers (Mouser blocked automated access); the URLs are standard ProductDetail paths.
- Whether the Geehy APM32F407RGT6 brings RMII out on LQFP-64 (Geehy datasheet not checked).
- JL1101 PHY: not found in the JLC catalog search.
- The pin budget is an estimate; reconcile it against the V4 netlist.
