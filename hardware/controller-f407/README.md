# F407 controller schematic

This is the new controller, started from the outside in. The first sheet is the rotor interface and the AC motor drive.

The directory is `hardware/controller-f407/` because ADR 0014 names the STM32F407, and the tree sits beside the imported V4 project at `hardware/controller/` without mixing files. Leave `hardware/controller/` untouched. It is the reference for the V4 TVS, snubber, and connector practice.

| File | What it is |
| --- | --- |
| `controller-f407.kicad_sch` | Root sheet. Sheet pins are no-connects on purpose: the processor sheet and the power sheet are not drawn yet. |
| `rotor_drive.kicad_sch` | Azimuth rotor connector, motor caps, triac drive, ARM relay, 26 VAC tap. |
| `rotor-drive.pdf` | Plot of both sheets, for review away from KiCad. |
| `DESIGN-NOTES.md` | What each block does, the calculations, the bill of materials, and the open questions. |
| `symbols/controller-f407.kicad_sym` | Unused TPS3823-33 symbol (the supervisor is not on the rotor sheet) and the no-pad Powerpole gland marker. |
| `footprints/controller-f407.pretty/` | The two motor-cap footprints copied from the Hammond outline, and the gland marker. |

KiCad 9. Nets leave this sheet on hierarchical labels (`AZ_CW_EN`, `AZ_CCW_EN`, `AZ_BRAKE_EN`, `ARM_EN`, `ZC_SENSE`, and the rest listed in the design notes). MCU pin assignment is deferred.

Elevation is a later copy of this sheet (ADR 0008), not a second channel here.
