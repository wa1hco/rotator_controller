# Documentation

Design notes and decision records for the rotator controller.
Licensed under CC BY-SA 4.0 (`docs/LICENSE`).

## Design notes

Imported from the design-doc set written for this project in October 2026.
They are drafts. Items marked **[U]** or **[M]** in those files are not
settled measurements.

| File | Contents |
|---|---|
| [design/system-overview.md](design/system-overview.md) | Processor-agnostic system design |
| [design/feature-survey.md](design/feature-survey.md) | What other controllers do, and the hardware plan that follows |
| [design/feature-inventory.md](design/feature-inventory.md) | Settings, Operate, and Install inventory against K3NG and the commercial controllers |
| [design/hardware-requirements.md](design/hardware-requirements.md) | v1 hardware requirements, connector and packaging addenda |
| [design/v2-relay-protection-review.md](design/v2-relay-protection-review.md) | Why the V2 relay board burned capacitors |
| [design/v4-discrete-triac-change.md](design/v4-discrete-triac-change.md) | Replace the CPC1966 channels with opto-triacs and BTA16s |
| [design/triac-thermal-packaging.md](design/triac-thermal-packaging.md) | Heatsink bar and Hammond 1455N1601 packaging |
| [design/mcu-ethernet-lcsc.md](design/mcu-ethernet-lcsc.md) | JLCPCB/LCSC check for the STM32F407VGT6, LAN8720A, and MagJack |
| [design/configuration.md](design/configuration.md) | Draft settings namespaces, console grammar, and preset flow |
| [design/rotator-catalog.md](design/rotator-catalog.md) | Rotor models, preset families, and sources. The preset YAML is under `software/firmware/presets/` |
| [design/img/](design/img/) | End, side, and top views, plus the scripts that draw them |

## Decision records

Short records of decisions already made. The index is
[decisions/README.md](decisions/README.md).
