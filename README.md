# Rotator controller

Clean-slate amateur-radio antenna rotator controller: a shack box that
replaces the stock controller and drives the existing rotor cable.
Owner: Jeff Millar, WA1HCO.

The firmware is a new processor-agnostic C++17 core, not a refactor of
K3NG. The V4 KiCad board is the hardware starting point (STM32F405,
isolated USB, CPC1966 AC switches as currently drawn). Discrete triacs,
the Hammond enclosure, and the rest of the decisions below are accepted
and not all drawn into the board yet.

## Layout

| Path | What it is |
|---|---|
| [hardware/controller/](hardware/controller/README.md) | V4 KiCad 9 project and the project-local libraries it uses |
| [hardware/controller/mechanical/](hardware/controller/mechanical/README.md) | Placeholder for enclosure drill templates and the triac bar drawing |
| [software/firmware/](software/firmware/README.md) | C++17 core, host CMake build, unit tests. Processor TBD |
| [software/sim/](software/sim/README.md) | Physics simulator, GS-232 harness, browser compass |
| [software/tools/](software/tools/README.md) | Placeholder for calibration scripts, plots, and a web compass |
| [docs/design/](docs/README.md) | System, hardware, triac, and packaging notes |
| [docs/decisions/](docs/decisions/README.md) | Decision records |

## Status

- The KiCad project opens in KiCad 9. It is the CPC1966 V4 board.
  ERC reports many known violations (unconnected MCU pins and similar).
  CI uploads ERC and DRC reports and does not fail the build on them.
- Laptop-only edits (the triac swap and annotated design notes) are not
  in this tree yet. The change plan is
  [docs/design/v4-discrete-triac-change.md](docs/design/v4-discrete-triac-change.md).
- The firmware core builds and tests on a PC. It is not flashed to a
  board. `software/firmware/platformio.ini` is a stub.
- The simulator's physics tests run on their own. Its integration harness
  and compass page still expect a K3NG process. Retargeting notes are in
  the simulator README.

## Licenses

| Path | License |
|---|---|
| `software/` | [GPL-3.0-only](LICENSE) |
| `hardware/` | [CERN-OHL-S-2.0](hardware/LICENSE) |
| `docs/` | [CC BY-SA 4.0](docs/LICENSE) |

Details and provenance are in [NOTICE](NOTICE). The imported KiCad files
were previously published under CC0-1.0 by the same author; this
repository licenses the hardware under CERN-OHL-S-2.0.

## Build the firmware host tests

```bash
cmake -S software/firmware -B software/firmware/build -DCMAKE_CXX_COMPILER=g++
cmake --build software/firmware/build
ctest --test-dir software/firmware/build --output-on-failure
```

Simulator physics tests:

```bash
make -C software/sim test
```

## CI

- `.github/workflows/firmware.yml` builds the host core and runs the unit tests on push and pull request.
- `.github/workflows/kicad.yml` runs in the `kicad/kicad:9.0` container. It exports a schematic netlist (this fails the job if the schematic does not load) and writes ERC and DRC reports as artifacts. `--exit-code-violations` is not passed, so the known ERC and DRC violations do not fail the job.

## Where the imported work came from

- Hardware: [wa1hco/Rotator-Controller-V2](https://github.com/wa1hco/Rotator-Controller-V2) branch `Rotator_Controller_V4` at `27affb32f34605df6d436127cd1c47bb30fbcdb9`. History of the KiCad files is in this repository; see the controller README for what was left behind.
- Simulator: [wa1hco/k3ng_rotator_controller](https://github.com/wa1hco/k3ng_rotator_controller) at `27156ad04ab3bf05b93761b5a9612c2a382143ac`, itself a GPL-3.0 fork of [k3ng/k3ng_rotator_controller](https://github.com/k3ng/k3ng_rotator_controller).
