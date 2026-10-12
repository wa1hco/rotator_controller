# Rotator controller PCB outline and end panels: Hammond 1455N1601

Generated 2026-10-11 with KiCad 9.0.2. The generators, the downloaded datasheet copies, and the DRC report from that day are not in this repository. The KiCad project below is that board file. `outline.png` is the annotated top view and end view, redrawn here from the dimensions in this note. The front and rear panel sheets that used to sit on User.Drawings (and the comment frames that sat on those sheets) have been removed. Machining drawings are generated from footprint fields ([ADR 0017](../../../../docs/decisions/0017-enclosure-machining-drawings.md)). The pre-layout 1:1 sheets are in [`../panels/preliminary-pre-layout/`](../panels/preliminary-pre-layout/). The hole table below is what that generator is checked against.

Status tags: **[V]** read from a manufacturer drawing/page, **[E]** derived or scaled from one, **[U]** unverified/assumed, **[TBD]** part not chosen yet.

Heights chained from Hammond typical dimensions are about **±0.6 mm** and are not a per-slot callout. Test-fit one board in a box before drilling a batch.

## Files

| File | What |
|---|---|
| `RotatorController-1455N1601-outline.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | KiCad 9 board: Edge.Cuts, keep-outs, bar footprint, motor caps, end-plate plane markers, height-limit notes, end view. No front/rear panel sheets. 4-layer stackup + JLCPCB rules. `kicad-cli` 9.0.9 DRC after that removal: 0 violations, 0 unconnected. |
| `outline.png` | Annotated top view + end view |
| [`../panels/preliminary-pre-layout/`](../panels/preliminary-pre-layout/) | Pre-layout 1:1 panel sheets (SVG/PDF, print at 100 %, 50 mm check bar) and phone PNGs. Superseded by `gen_machining.py` once the layout has `Panel` fields. |

## Sources

- **H-DWG**: Hammond 1455N1601 drawing, https://www.hammfg.com/files/parts/pdf/1455N1601BK.pdf (one sheet; views "EXTRUSION", "END PLATE", "OPEN BEZEL" section D-D). Vector geometry also scaled with PyMuPDF (scale 90 pt = 53.00 mm).
- **H-PART**: https://www.hammfg.com/part/1455N1601BK, attributes "Max. P.C. Board Length (mm) 159", "Max. P.C. Board Width (mm) 99".
- **H-SERIES**: https://www.hammfg.com/electronics/small-case/extruded/1455 ("PC boards mount horizontally by sliding into internal slots", wall min 1.5 mm, end screw torque 5 lbf-in).
- **NKK**: Series BB, https://www.nkkswitches.eu/pdf/pushbutton_BB.pdf, page C16 "Typical switch dimensions", BB15AH-FA right angle.
- **DIALIGHT**: 551-xx07F drawing C-17306 rev G, https://www1.futureelectronics.com/doc/Dialight/551-0207F.pdf.
- **PULSE**: J403.K (03/19), https://productfinder.pulseeng.com/doc_type/WEB301/doc_num/J403/doc_part/J403.pdf, page 2 "Mechanicals A" (J0011D01BNL is mech A per page 1 table).
- **LCSC-USB**: https://www.lcsc.com/product-detail/C2988369.html (GT-USB-7010ASV, "Center Height 1.68mm").
- **JLC**: https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-10-11).
- **THERMAL**: `docs/design/triac-thermal-packaging.md` §3, §8.
- **KEMET**: R60 series datasheet F3103, https://content.kemet.com/datasheets/kem_f3103_r60.pdf : row R60EW6100(1)00(3): p 37.5 ±0.4, B 20.0 +0.3/−0.7, H 40.0 +0.1/−0.7, L 41.5 +0.3/−0.7, d 1.0 ±0.05, 63 VAC / 100 VDC. The local PDF copy was not imported.

## Enclosure dimensions

| Item | Value | Source |
|---|---|---|
| Outside L x W x H | 160.00 ±0.50 x 103.00 x 53.00 | H-DWG extrusion + side view [V] |
| Slot bottom to slot bottom | 100.00 ±0.51 ("EXTRUSION DESIGNED FOR 100MM WIDE PC BOARD") | H-DWG extrusion [V] |
| Slot depth / slot width / tooth | 2.50 / 2.00 TYP / 1.50 TYP (pitch 3.50) | H-DWG extrusion [V] |
| Inner top to upper face of slot 1 | 6.41 | H-DWG extrusion [V]; geometry check confirms it is inner top face to slot-1 upper face [E] |
| Number of slots | 11 per side | counted on H-DWG [E] |
| Slot k upper face below inner top | 6.41 + 3.50 (k-1): 6.41, 9.91, 13.41, 16.91, 20.41, **23.91 (slot 6)**, 27.41, 30.91, 34.41, 37.91, 41.41 | chained TYP dims [E]; scaled values agree within 0.07 mm |
| Inner height (top to floor) | 49.62 ±0.56 | H-DWG [V] |
| Top/bottom wall | 1.69 each (53.00 - 49.62)/2, assumed symmetric | [E] |
| Corner bosses | top: down to 5.8 below inner top, within ~6.8 of slot bottom; bottom: up to ~5.9 above floor, within ~8.3 of slot bottom | scaled from H-DWG [E] |
| Removable faces | Belly (bottom) plate slides; top + sides one piece; 2 end plates | H-SERIES, H-DWG [V] |
| End plate | 103.00 x 53.00 x 1.50, 4x Ø0.165 in (4.19) thru, csk Ø0.230 in (5.84) x 82°, pattern 95.02 x 45.00 centred | H-DWG end plate [V] |
| Open bezel | outside 106.13 x 56.13, window 97.10 x 48.70, web 1.60, skirt 6.00, overall 9.00 | H-DWG open bezel [V]; that the 1.60 web sits between extrusion end and plate is read from the exploded view [E] |
| PCB corner notches / mounting holes | none shown; boards are held by the slots only | H-DWG, H-SERIES [V] |

## Board

| Item | Value | Basis |
|---|---|---|
| Board size | **159.00 x 99.00 x 1.6 mm**, square corners | H-PART max values [V]. JLC routing ±0.2 gives 98.8-99.2 wide vs 99.49 minimum slot-bottom width; 159.2 max vs 159.5 minimum extrusion length |
| Board thickness in slot | 1.6 nominal (JLC ±10 % = 1.44-1.76) in a 2.00 slot | JLC [V] |
| Slot engagement | 2.0 per side centred, 2.5 max when shoved over | [E] |
| Copper/part keep-out | 2.5 mm rule areas on all 4 copper layers along both long edges (no tracks, vias, pads, pours, footprints) + dashed 3.5 mm component-body line | request + THERMAL §8 |
| Board end to end-plate inner face | 2.10 nominal = (160-159)/2 + 1.60 bezel web; axial float 1.0 total (0.5-1.5 with extrusion tolerance). The bezel window (97.10) is narrower than the board, so the bezel webs hold the board end-wise | [E] |
| Connectors crossing the board end | must sit inside the 97.10 x 48.70 bezel window; USB-C and RJ45 should overhang the board edge ~1.0-1.5 mm so cable plugs reach through a 3.6 mm (2.1 gap + 1.5 plate) deep panel | [E] |
| Origin | rear-left board corner (aux origin and grid origin). x runs rear to front, y across | — |
| Chosen slot | **6** (the THERMAL example). Board lifted to the slot's upper face by the top-wall screws: inner top to board top **23.91**, board bottom to floor **24.11** | [E] |
| Height limits, slot 6 | top side ≤ 22.9 (D-1), ≤ 17.1 within 7 mm of long edges; bottom side ≤ 23.1, ≤ 17.2 within 8.5 mm of long edges | [E] |
| Heatsink bar zone | 10 x 50 at board x 21.9-31.9 (enclosure x 24-34 from rear-plate face), y 24.5-74.5 (centred); 2x NPTH Ø3.2 at board (26.9, 29.5) and (26.9, 69.5), each with a 5.2 mm copper-free square; F.Cu keep-out (tracks/vias/pads) under the bar, pours allowed; courtyard 10.5 x 50.5 | THERMAL §3/§8 |
| Bar height | nominal **23.26** = 23.91 - 0.65 clamped pad (THERMAL); **22.91** = 23.91 - 1.0 means pad uncompressed (no clamp) | THERMAL [E]; measure D_k [M] |
| Top-wall drill template | Ø3.4 x2, enclosure x = 29.0 from rear-plate inner face (board x 26.9), y = centreline ±20 | THERMAL §3 |
| Triac row | 3x BTA16-600SW, 12.7 pitch, leads 2.5 in front of bar face (board x ≈ 34.4) | THERMAL [U] |
| Rotor-gland nut zone | board x 0-10, y 30.5-52.5: top-side parts ≤ 1.5 mm | [E] |

The bar sits **across** the board near the rear, centred, as THERMAL §3 chose. It is not a strip along a long edge, because the inside of the side walls is the slot comb and only the top wall is flat.

### Stackup and rules (JLCPCB 4-layer, JLC04161H-7628 style)

F.Cu 35 µm / prepreg 7628 0.2104 (εr 4.4) / In1 15.2 µm / core 1.065 / In2 15.2 µm / prepreg 0.2104 / B.Cu 35 µm, 1.6 mm, HASL lead-free. Layer thicknesses are from memory of JLC's standard stack [U]; check them in JLC's impedance tool when ordering. For 2 oz outer copper, set 70 µm and change track/space to 0.15/0.15.

Board minimums: clearance 0.127, track 0.127, via Ø0.45/0.20 drill, annular 0.15, copper-to-edge 0.30, hole clearance 0.28, hole-to-hole 0.25, silk 0.15/1.0 text. Default netclass 0.2/0.2, via 0.6/0.3. `.kicad_dru` adds: inner-layer PTH-to-copper 0.3, via hole-to-copper 0.2, PTH annular 0.2, NPTH ≥ 0.5, pad hole-to-hole 0.45. All from JLC.

## Motor run capacitors (C_MOTOR1 flat + C_MOTOR2 upright, 133 µF in parallel)

Target from the CDE schematics in the V2 repo: 130–156 µF, 50 VAC. The proven V2 cap (100 µF) is about 23 % low on its own, so a 33 µF cap goes in parallel. **Total 133 µF nominal** (±10 % each, so 120–146 µF). Both are 100 VDC / 63 VAC metallized polyester. The motor sees about 26–30 VAC (roughly 37–44 VAC across the cap).

| Ref | Part | Value | Max body (mm) | Mount | Height above PCB |
|---|---|---|---|---|---|
| C_MOTOR1 | KEMET **R60EW61005000K** (Digi-Key 399-13010-ND), proven on V2 | 100 µF 100 VDC / 63 VAC | 41.8 x 20.3 x 40.1 | lying flat, 25 mm leads bent down | 20.3 (limit 22.9) |
| C_MOTOR2 | TDK **B32526T1336K000** (Digi-Key 495-4582-ND, Mouser 871-B32526T1336K000) | 33 µF 100 VDC / 63 VAC | 24.0 x 15.0 x 41.5 (w x h x l) | **upright**, leads straight down | 15.0 (limit 22.9) |

Sources: KEMET F3103 R60 datasheet (above). TDK B32520…B32529 datasheet, https://www.tdk-electronics.tdk.com/inf/20/20/db/fc_2009/B32520_529.pdf (local copy not imported), B32526 table "100 VDC 63 VAC, 33 µF, 24.0 × 15.0 × 41.5, B32526T1336+***" (max dimensions), lead spacing 37.5 ±0.4, lead d1 1.0 ±0.05, untaped lead length 6 ±1. The short TDK leads are why C_MOTOR2 stands up: there is not enough lead to lie it flat and bend down.

Footprints: `C_MOTOR1` (`C_Rect_KEMET_R60_P37.5_L41.5_W20_H40_Flat`) and `C_MOTOR2` (`C_Rect_TDK_B32526T_P37.5_L41.5_W24_H15_Upright`), bodies on F.Fab and User.Drawings, courtyards on F.CrtYd, notes on User.Comments. Pads are numbered so that **pad 1–pad 1 and pad 2–pad 2** are wired in parallel; both lead pairs sit on the same y (7.15 / 44.65), so the two parallel traces run straight along x.

| Item | Board coordinates (mm, origin = rear-left corner) |
|---|---|
| C_MOTOR1 body (flat) | x 51.5–91.6, y 5.0–46.8. The 41.5 x 40 face is on the board; the lead face (41.5 x 20) is at x = 51.5, facing the triacs |
| C_MOTOR1 lead holes, PTH 1.3 / pad 2.5 | (49.0, 7.15) and (49.0, 44.65), 37.5 apart, 2.5 outboard of the lead face |
| C_MOTOR1 cable-tie holes, NPTH 3.2 | (49.0, 25.9) and (94.1, 25.9); 2.5 mm tie over the body, or RTV instead |
| C_MOTOR1 courtyard | x 47.25–96.2, y 4.5–47.3 |
| C_MOTOR2 body (upright) | x 98.0–122.0, y 5.15–46.65 (24 x 41.5 footprint, 15.0 tall) |
| C_MOTOR2 lead holes, PTH 1.3 / pad 2.5 | (110.0, 7.15) and (110.0, 44.65), 37.5 apart, centred in the 24 mm thickness |
| C_MOTOR2 courtyard | x 97.5–122.5, y 4.65–47.15 |
| Whole cap zone | **x 47.25–122.5, y 4.5–47.3** |
| Clearances | C_MOTOR1 lead pad edge to bar front face 15.85 (courtyard 15.35); C_MOTOR2 is 66 mm from the bar. Courtyards 1.3 apart (C_MOTOR1 far tie hole at x 94.1 still has 3.9 mm to the C_MOTOR2 body for the tie). Long-edge strip ends y 3.5; courtyards start y 4.5. Front buttons/LEDs start about x 139. Heights 20.3 and 15.0 vs 22.9 limit |

C_MOTOR1 lead bend: the leads leave the 20.3 face at mid-height, about 10.2 above the PCB. They run 2.5 mm outboard, then bend 90° down: inside radius about 1 mm, with at least 1 mm straight next to the body. Each lead needs about 2.5 + 10.2 + 1.6 board + 1.5 protrusion ≈ 16 mm of its ~25 mm length.

C_MOTOR2: seat it on the board, leads straight through (6 ±1 mm leads, 1.6 mm board). An RTV dot at the base is optional.

Placement reasons:
- Both caps sit on the AC (edge-A, y = 0) side with the power-input terminal, in front of the triac row, so the /Left–/Right motor leads stay short.
- y 47.3–95.5 stays free for logic, plus x 122.5–139 on the y < 47 side.
- The height-limit note box is at y 78.5–89.5, clear of both caps.

### Why this pair (price check 2026-10-11, about 8:40 PM ET)

Digi-Key figures were read from digikey.com product pages. Mouser blocks automated lookups; Mouser numbers come from a distributor-aggregator listing (omo-ja.com) and are **unverified**. Totals are per controller; "3 sets" is 3 controllers at each part's qty-1 price tier (none reach a 10-piece break).

| Option | Parts | µF | VAC | 1 set | 3 sets | Fits? | Notes |
|---|---|---|---|---|---|---|---|
| **b (chosen)** | R60EW61005000K + B32526T1336K000 | 133 | 63 | $39.50 DK ($25.97 + $13.53) | $118.50 DK | yes: flat 20.3 + upright 15.0 | DK stock 1,136 / 125. Mouser 33 µF: $11.19, 1,033 stock [unverified]. If you already have spare R60EWs (you bought 9), it is $13.53 per controller |
| b-alt (runner-up) | R60EW61005000K + B32526T1476K000 (47 µF) | 147 | 63 | $42.73 DK ($25.97 + $16.76) | $128.19 DK | yes: upright 19.0, same 24 x 41.5 footprint | Centred in 130–156, but only 34 in stock at DK |
| b-flat | R60EW61005000K + B32524Q1476K000 (47 µF, 27.5 pitch) | 147 | 63 | $39.43 DK | $118.29 DK | **no**: 21 x 31 x 31.5; upright 31 too tall, and 6 mm leads too short to lay flat | Cheapest on paper by 7 cents |
| a | 2x R60EW61005000K | 200 | 63 | $51.94 DK | $155.82 DK | yes (2 flat, ~85 x 40) | 200 µF is 28 % over CDE max; too much phase shift. Rejected |
| c | 2x B32524Q1686K000 (68 µF) | 136 | 63 | $31.68 DK | $95.04 DK | **no**: 22 x 36.5 x 31.5, 6 mm leads, upright 36.5 | DK stock 0 (next 19-Feb-2027). KEMET R60EW 68 µF (long leads) not stocked at DK |
| c | 2x B32526R1686K000 (68 µF) | 136 | 63 | not stocked | — | no: upright 32.5, 6 mm leads | DK "available to order", no price shown |
| c | 3x B32524Q1476K000 (47 µF) | 141 | 63 | $40.38 DK | $121.14 DK | **no** (see b-flat) | |
| d | R60EW6150AA00K / B32526R1157 (150 µF) | 150 | 63 | $23.59 at 216 MOQ only (R60) | — | **no**: 24 x 44 / 28 x 42.5 minimum dimension > 22.9 | R60 150 µF not stocked |
| e | CBB60 motor-run, 2x 70 µF 250 VAC | 140 | 250 | not priced | — | **no**: about 45 mm dia x 92 mm | Polypropylene, but far too big for the 1455 |

Source URLs: https://www.digikey.com/en/products/result?keywords=R60EW61005000K, …=B32526T1336K000, …=B32526T1476K000, …=B32524Q1476K000, …=B32524Q1686K000, …=B32526R1686K000, …=R60EW (R60EW6150AA00K row); Mouser-via-aggregator https://www.omo-ja.com/chip/b08/b32526t1336k000-epcos.html; CBB60 size https://store.eurtonelectric.com/products/capacitor-cbb60-a270-70uf-250vac.

## End panels (preliminary hole table)

These coordinates are the pre-layout hole table. They are no longer
drawn on this board. `software/tools/enclosure/gen_machining.py`
reproduces them within 0.05 mm from placeholder footprints (see
[ADR 0017](../../../../docs/decisions/0017-enclosure-machining-drawings.md)).
The hand sheets are in
[`../panels/preliminary-pre-layout/`](../panels/preliminary-pre-layout/).

What the old V4 drawings showed (rendered from `/workspace/v4/Rotator-Controller-V4.kicad_pcb` Dwgs.User, not modified): a 99 x 70 board, two 35 x 76 side panels. One panel had 4 light-pipe holes (R1.5, LP4-EP O1), two NKK BB15AH buttons (SW1/SW2, Ø6.5) and the Az_Preset pot RV1 (R3.1). The other had the rotor Mate-N-Lok J3 cutout 10.8 x 23.3 and two 13.6 x 6.5 slots (USB J1 and one more). All of it is superseded: no light pipes, no pot.

**Datum:** lower-left corner of the plate, **viewed from outside**; X right, Y up. Plate centre = (51.50, 26.50). Front panel seen from outside has board y = 0 on the right; rear panel has board y = 0 on the left.
**Vertical reference:** PCB top face at Y = **27.40** (panel centre + 0.90) for slot 6. Feature Y = 27.40 + part centreline height above the PCB.

### Front panel

| # | Feature | X | Y | Hole | Part / basis |
|---|---|---|---|---|---|
| 1 | CCW button | 29.50 | 30.80 | Ø6.5 | NKK BB15AH-FA, plunger CL 3.4 above PCB [V NKK]; cap Ø5.1 protrudes ~2.7 past the panel if the body front is flush with the board edge |
| 2 | STOP button | 51.50 | 30.80 | Ø6.5 | same (red cap: BB15AH-FC) |
| 3 | CW button | 73.50 | 30.80 | Ø6.5 | same |
| 4-9 | LEDs PWR, LINK, CCW, CW, BRAKE, FAULT | 11.50, 18.50, 40.50, 62.50, 84.50, 91.50 | 32.48 | Ø4.0 | Dialight 551-xx07F 3 mm right-angle CBI, LED CL 5.08 above PCB [V DIALIGHT]. Set the housing front 0.5 mm behind the board edge so the lens (2.41 proud of housing) stops just short of the plate. Colours: 551-0207F green, 551-0307F yellow, 551-0407F red. Mouser **645-551-0207F** (seen via a distributor-aggregator listing, ~11k stock, $1.03/1; Mouser's own page not checked). **LED count and functions are TBD.** |
| M | Plate screws (existing) | 3.99 / 99.01 | 4.00 / 49.00 | Ø4.19 csk | Hammond |

### Rear panel

| # | Feature | X | Y | Cutout | Part / basis |
|---|---|---|---|---|---|
| 1 | 26 VAC Powerpoles | 17.50 | 38.40 | Ø16.3 gland, or a 2-position panel-mount bracket (cutout TBD) | Grey + black Anderson Powerpoles, the V2 pair (ADR 0018). Polarity does not matter; the colors key the plug so it is not a red/black 12 VDC pair. Drawable default is the pigtail gland, center 11.00 mm above the board. Do not drill a bracket hole from that default. The pre-layout PDF still shows the withdrawn 22.00 × 12.50 opening |
| 2 | ROTOR GLAND | 43.50 | 38.40 | Ø16.3 | **TBD**: M16x1.5 nylon gland (cable 5-10 mm), lock nut AF19 with flats horizontal, sitting above the PCB (nut bottom 1.5 above board top). Pigtail exits here and ends in the CPC 206708-1 plug; inside, the wires drop to a board-top terminal. |
| 3 | USB-C (isolated) | 69.50 | 29.08 | 13.60 x 6.50 R1.0 | GT-USB-7010ASV, centre height 1.68 [V LCSC-USB]; opening clears a cable overmold so the isolated USB shell never touches the chassis plate. Opening size is the V4 value [E] |
| 4 | GND STUD | 69.50 | 42.50 | Ø4.3 | **TBD**: M4 screw/stud, 2 nuts + star washer + ring lug (single chassis bond point) |
| 5 | RJ45 | 87.50 | 34.45 | 17.02 x 14.60 R0.25 | Pulse J0011D01BNL, Pulse recommended cutout, opening bottom 0.25 below PCB top [V PULSE mech A] |
| M | Plate screws (existing) | 3.99 / 99.01 | 4.00 / 49.00 | Ø4.19 csk | Hammond |

Matching board-edge markers (connector widths, labels with height above the PCB) are on User.Comments at x = 0 (rear) and x = 159 (front).

Vertical tolerance is about ±0.6 mm: extrusion inner height ±0.56, plus the slot position, which is chained from TYP dimensions. Before drilling a batch, put one board in a box and check the button and RJ45 heights.

## Bringing it into the V4 / F407 project

- **Recommended:** start the new F407 layout from this file. Copy the `.kicad_pcb`, `.kicad_pro` and `.kicad_dru` into the project folder renamed to the project name (or File → Open and Save As), then Tools → Update PCB from Schematic. Stackup, rules, keep-outs, the bar, the caps, and the height notes come along. Panel holes do not: add `Panel` / `PanelZ` / `PanelCutout` on the footprints and run `gen_machining.py` (ADR 0017).
- **Into the existing V4 board:**
  1. Open this file in pcbnew, set the layer filter, select Edge.Cuts + the remaining User.Drawings (end view, board dimensions, end-plate plane markers) + User.Comments + F.Fab items + the rule areas + footprint HS1, Ctrl+C. Pick the reference point at the origin cross (rear-left corner).
  2. In V4, delete the old Edge.Cuts rectangle and the old Dwgs.User panel drawings first.
  3. Ctrl+V, snapping the reference to the board corner you want.
  4. Then Board Setup → Board Stackup → set 4 layers / Import Settings from this `.kicad_pro` for rules and stackup.
- Keep the triac bar position consistent with the top-wall drill template (enclosure x = 29.0). The generator reads the bar's NPTH pads; it does not read a drawing on the board.

## Unverified / open

- Slot count (11) and per-slot heights: chained from Hammond TYP dims and scaled, not dimensioned per slot. Confirm with calipers or Hammond's STEP model (mjm@hammondmfg.com).
- Top/bottom wall thickness 1.69 assumed symmetric. It sets the panel Y = 27.40 board-top reference.
- Bezel web 1.60 between extrusion end and plate: read from the bezel section and exploded view.
- Corner-boss extents (height-limit relief near long edges) are scaled.
- JLC stackup layer thicknesses (from memory).
- Triac lead offset 2.5 mm from the bar face and pin order (THERMAL [U]).
- TBD parts: power-input connector, rotor gland, ground stud, LED count/functions. USB-C opening size is carried over from V4.
- Mouser 645-551-0207F seen only via an aggregator; Mouser blocks automated lookups.
- Mouser price/stock for the motor caps (B32526T1336K000 $11.19 / 1,033) seen only via an aggregator; R60EW61005000K Mouser price not found.
