# Rotator physics simulator

Host-side physics model, GS-232-style protocol shim, browser compass, and
the integration-test harness copied from the WA1HCO fork of the K3NG
rotator controller.

## Source

Copied from [wa1hco/k3ng_rotator_controller](https://github.com/wa1hco/k3ng_rotator_controller)
commit `27156ad04ab3bf05b93761b5a9612c2a382143ac`
(2026-04-22, "Add HCO board config as worked example for hardware-specific native builds").

That repository is GPL-3.0, a fork of Anthony Good, K3NG's project at
<https://github.com/k3ng/k3ng_rotator_controller>. These files stay under
GPL-3.0-only, the same license as the rest of the software in this
repository (`/LICENSE`).

| Here | There |
|---|---|
| `rotator_simulator.cpp`, `rotator_simulator.h` | `k3ng_rotator_controller/` |
| `rotator_protocol_shim.cpp`, `rotator_protocol_shim.h` | `k3ng_rotator_controller/` |
| `rotator_feature_config.cpp`, `rotator_feature_config.h` | `k3ng_rotator_controller/` |
| `pc_rotator_sim.cpp`, `gui_server.cpp`, `gui/` | `simulator/` |
| `tests/` | `tests/` |
| `lib/arduino_compat/` | `lib/arduino_compat/` |

The Makefiles are the upstream ones with include paths pointed at this
directory. The C++ sources are otherwise unchanged. `lib/arduino_compat`
is the Arduino API stub that the K3NG native build uses. The K3NG sketch
itself was not copied.

## What runs today

Physics unit tests, the protocol shim, and the interactive physics CLI
do not need the K3NG sketch:

```bash
make -C software/sim test
make -C software/sim build
./software/sim/pc_rotator_sim
```

`gui_server` and `tests/run_integration_tests` still spawn a **K3NG
native binary** and speak GS-232 to it. Their default path is the old
tree's `../.pio/build/native_test/program`, which does not exist here.
Override it:

```bash
# from software/sim, once you have a binary that speaks GS-232 on stdin/stdout
./gui_server --k3ng /path/to/binary
K3NG_BINARY=/path/to/binary make -C tests integration
```

The compass page (`gui/index.html`) is served by `gui_server`. It is not
wired to `software/firmware`.

## Retargeting onto the new core

The new firmware is not a K3NG build, so this simulator is not connected
to it yet. To point the harness at the new core:

1. Give the host build of `software/firmware` a stdin/stdout GS-232 link
   (the `rotator::hal::Link` interface) and a motion loop that steps the
   `RotatorAxisSimulator` (or the firmware's own `MotionController` driven
   by that simulator's sensor and drive fakes).
2. Teach that process to answer `C` / `C2` with `AZ=nnn` lines. That is
   the response `tests/k3ng_process.h` and `gui_server.cpp` already parse.
   The firmware parser (`rotator::protocol::parse_gs232`) accepts `M`,
   `C`/`C2`, and `A`/`S`, but it does not format the reply yet.
3. Pass that binary as `K3NG_BINARY` or `gui_server --k3ng`. The harness
   can keep its current process model; only the child program changes.
4. `rotator_feature_config` checks K3NG compile-time feature conflicts.
   It is unused by the new core, which keeps features in the versioned
   `Settings` record instead of `#define`s. Leave it with the harness
   until nothing includes it, then drop it.

`lib/arduino_compat` is only needed if someone builds the K3NG sketch
again. The new core must not include it.
