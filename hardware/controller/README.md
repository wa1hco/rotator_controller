# V4 controller board

KiCad 9 project for the shack-side antenna rotator controller. The board
as imported is the CPC1966 design: STM32F405RG, ADuM4160 isolated USB,
and three CPC1966 AC solid-state relays (CW, CCW, brake).

Newer edits that exist only on the owner's laptop are **not** in this
import. Those are the discrete-triac swap (MOC3023M + BTA16-600SW and
snubbers) and the annotated design notes. They will be added later.
Until then, `docs/design/v4-discrete-triac-change.md` is the change plan,
and the schematic still shows CPC1966 parts.

## Source

Imported from [wa1hco/Rotator-Controller-V2](https://github.com/wa1hco/Rotator-Controller-V2),
branch `Rotator_Controller_V4`, commit
`27affb32f34605df6d436127cd1c47bb30fbcdb9`
("Removed some deleted files", 2025-10-09).

History was kept with `git filter-repo`: only the KiCad project and the
project-local libraries this board references were retained, then moved
under `hardware/controller/`. Commit hashes in this repository differ
from the source repo because the history was rewritten. The last source
commit that changed the schematic is
`b3b3aa526a4143c245adb577c08cf79c1521e6af`. Blob hashes of every imported
file match the source tip above. The source tip commit itself only
deleted files that were not imported, so it does not appear in this history.

That source tree was published under CC0-1.0. The same author licenses
the hardware in **this** repository under CERN-OHL-S-2.0
(`hardware/LICENSE`).

## What was kept

| Path | Why |
|---|---|
| `Rotator-Controller-V4.kicad_{pro,sch,pcb}` | The board |
| `RotatorController.kicad_sym`, `RotatorController.pretty/` | CPC1966 symbol and footprint, both used |
| `LightPipe.kicad_sym`, `Lightpipe.pretty/` | LP4-EP light pipe, used |
| `NKK_BB15AH.pretty/` | Front-panel switch footprint, used |
| `sym-lib-table`, `fp-lib-table` | Project library tables |
| `.gitignore` | KiCad backup and cache rules from the source project |

Library nicknames and `${KIPRJMOD}` URIs are unchanged for the libraries
that remain, so opening the project from this directory does not depend
on a global KiCad library path. After the move, table entries for
libraries that were **not** imported (Teensy, Button, Pushbutton) were
removed. Leaving them would make KiCad look for missing directories.

Symbols are also embedded in the schematic, and footprints are embedded
in the PCB, which is how KiCad 6+ projects open when a library is absent.
The project-local libraries are still here so "Update from library" and
a standalone open both work.

Standard-part 3D models are **not** vendored. The board references
`${KICAD8_3DMODEL_DIR}` and `${KICAD9_3DMODEL_DIR}` from the KiCad
installation. There is no project-local 3D model for the STM32 board.
The only STEP files in the source branch belonged to the unused Teensy
library.

## What was left in the source repo

- `Software/` — the previous firmware tree. This repository's firmware is
  a new core under `software/firmware/`.
- `Datasheets/` — manufacturer PDFs (about 42 MB). Not redistributed here.
- `Teensy.pretty/`, `Teensy.kicad_sym`, `teensy.kicad_sym` — not referenced
  by the V4 STM32 schematic or PCB. Third-party MIT-licensed footprints.
- `Button.pretty/`, `2024-07-13_20-59-04.kicad_sym`, and the stray
  `Button_Switch_THT:Omron.pretty/` — not used by the V4 board.
- `Rotator-Controller-V4.kicad_sch_old` — schematic backup.
- `jlcpcb/project.db` — plugin database.
- `Rotor Enclosures.odt`, `Rotor and Controller Schematics.docx`,
  `Rotator-Controller-V4.ods` — older office notes. Current design writing
  is in `docs/design/`.
- KiCad backups, lock files, `fp-info-cache`, and autosaves were not in
  git and are ignored.

## Open

KiCad 9 or newer:

```bash
kicad hardware/controller/Rotator-Controller-V4.kicad_pro
```

The schematic has many known ERC violations (unconnected MCU pins and
similar). CI runs ERC and DRC to produce reports and does not fail the
build on those violations. See the root README.

Mechanical drawings for the Hammond 1455N1601 enclosure and the triac
heatsink bar belong in [`mechanical/`](mechanical/README.md). They are
not drawn yet.
