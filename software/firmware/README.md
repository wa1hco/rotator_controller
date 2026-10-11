# Firmware

Processor-agnostic C++17 core for one or two rotator axes. The host
build is CMake and does not need a board. The on-target build is not
set up yet: `platformio.ini` is a stub and the processor is TBD. The V4
PCB is laid out for an STM32F405RG, which is the current hardware
candidate, not a dependency of this core.

Nothing under `include/` or `src/` includes Arduino headers, uses
`String`, or calls `delay()` / `pinMode()`. Platform code is expected
to implement the HAL interfaces and call `MotionController::tick()`.

## Layout

| Path | Role |
|---|---|
| `include/rotator/hal/` | Analog in, digital out, PWM, timer, storage, byte link (USB serial or optional Ethernet) |
| `include/rotator/sensor/` | `PositionSensor`; first implementation is the CDE dual-end pot |
| `include/rotator/drive/` | `AxisDrive`; first implementation is the triac AC relay + brake |
| `include/rotator/motion/` | Per-axis state machine |
| `include/rotator/protocol/` | GS-232A/B parser. `rotctld.hpp` is a placeholder |
| `include/rotator/settings/` | Typed settings, schema version 1 |
| `tests/` | Host unit tests (GoogleTest via CMake FetchContent) |

The motion states are `Idle`, `Arming`, `DeadTime`, `RunningClockwise`,
`RunningCounterClockwise`, `Stopping`, and `Fault`. CW and CCW outputs
are never both commanded. A direction change waits in `DeadTime` with
both direction gates off. `Fault` disarms the axis; only stop clears it.

The pot helper is the ideal end-voltage ratio. Cable-resistance details
beyond that ratio, the 60 Hz notch, and the FIR filter are not
implemented yet.

## Host build

```bash
cmake -S software/firmware -B software/firmware/build
cmake --build software/firmware/build
ctest --test-dir software/firmware/build --output-on-failure
```

GoogleTest is downloaded at configure time (release v1.15.2).
