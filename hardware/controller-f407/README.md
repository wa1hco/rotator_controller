# F407 controller schematic

This is the new controller, started from the outside in. The rotor interface and the AC motor drive are on `rotor_drive`. The Drive MCU and the analog front end are the next two sheets.

The directory is `hardware/controller-f407/` because ADR 0014 names the STM32F407, and the tree sits beside the imported V4 project at `hardware/controller/` without mixing files. Leave `hardware/controller/` untouched. It is the reference for the V4 TVS, snubber, and connector practice.

| File | What it is |
| --- | --- |
| `controller-f407.kicad_sch` | Root sheet. `rotor_drive`, `drive_mcu`, and `analog_input` hang off it. `+5V` and `AC_FUSED` stay no-connects until the power sheet exists. |
| `rotor_drive.kicad_sch` | Azimuth rotor connector, motor caps, triac drive, ARM relay, 26 VAC tap. |
| `drive_mcu.kicad_sch` | Drive MCU, STM32G431RBT6. Power, SWD, and the UART to the Station. |
| `analog_input.kicad_sch` | Pot front end, the VIN_RECT warning, and the ADC reference filter. |
| `rotor-drive.pdf` | Plot of both sheets, for review away from KiCad. |
| `DESIGN-NOTES.md` | What each block does, the calculations, the bill of materials, and the open questions. |
| `symbols/controller-f407.kicad_sym` | Unused TPS3823-33 symbol (the supervisor is not on the rotor sheet) and the no-pad Powerpole gland marker. |
| `footprints/controller-f407.pretty/` | The two motor-cap footprints copied from the Hammond outline, and the gland marker. |

KiCad 9. Nets leave `rotor_drive` on hierarchical labels (`AZ_CW_EN`, `AZ_CCW_EN`, `AZ_BRAKE_EN`, `AMR_EN`, `ZC_SENSE`, and the rest listed in the design notes). The pin assignment is in [the Drive note](../../docs/design/drive-controller.md). Through-hole parts are bought from Mouser. SMT parts that have a checked LCSC number say so on the symbol; the rest are TBD.

Elevation is a later copy of this sheet (ADR 0008), not a second channel here.
