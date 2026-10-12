# Rotator controller, PC side

Phase 1 is configuration. The app finds controllers on USB and on the network, reads the settings tree, edits it with validation, applies a rotor preset, and writes it back after showing the diff. Backup, restore, compare, and copy between controllers use the same settings file as the console.

Phases 2 and 3 are planned below. The window already reserves their places: STOP stays on screen, and the Operate and Upgrade menus are present and disabled.

## Packages

`software/gui/` holds two installable packages.

| Package | Role |
|---|---|
| `rotatorctl` | Settings model, console client, discovery, presets, CLI, simulator. No Qt. WIMS can import this package alone. |
| `rotatorctl-gui` | PySide6 desktop app. Builds its forms from the controller's `schema` command. |

Python 3.11 or newer. The toolkit decision is [ADR 0019](../../docs/decisions/0019-pc-gui-toolkit.md). PySide6 is the GUI because one codebase covers Windows, Linux, and macOS, the widgets fit a laptop, and pytest-qt can drive the window headless. pydantic holds the schema, pyserial opens the USB serial port, and zeroconf browses DNS-SD.

A later Windows build can freeze `rotatorctl-gui` with PyInstaller (`rotatorctl-gui` as the entry point). That build is not wired up here. When it is, the PySide6 and zeroconf imports need to be collected explicitly.

## Run

From the repository root, with the firmware preset file where it already lives:

```bash
python -m pip install -e software/gui/rotatorctl
python -m pip install -e software/gui/rotatorctl-gui --no-deps
python -m pip install "PySide6>=6.6"
rotatorctl-gui
```

Install `rotatorctl` first. The GUI package imports it and does not fetch a copy from PyPI.

Discovery scans serial ports for USB VID `0x1209` / PID `0xF407` (provisional; see the design note) and browses `_rotatorctl._tcp`. Add network and Add serial cover a host that multicast cannot see, and a pty that has no USB descriptor.

The CLI uses the same library:

```bash
rotatorctl list
rotatorctl get --target tcp://127.0.0.1:4533 sys.serial
rotatorctl set --target tcp://127.0.0.1:4533 ui.log_level debug
rotatorctl dump --target tcp://127.0.0.1:4533 > rotator-settings.txt
rotatorctl restore --target tcp://127.0.0.1:4533 rotator-settings.txt
rotatorctl save --target tcp://127.0.0.1:4533
```

`set` changes the working record. `save` stores it. `restore` stores it as part of the command. The GUI save button does `set` for each changed field and then `save`, and only after the confirm dialog.

## Simulator

The firmware console is not in the tree yet. `rotatorctl-sim` speaks the console protocol and the GS-232 subset over TCP, and it can open a pty and advertise `_rotatorctl._tcp`.

```bash
rotatorctl-sim -n 2 --pty --mdns
```

`software/sim` is the C++ K3NG sandbox. The console simulator lives in the Python library so an install can start it. `software/gui/sim/rotator_sim.py` is a thin launcher. Details are in [sim/README.md](sim/README.md).

## Tests

```bash
cd software/gui
QT_QPA_PLATFORM=offscreen pytest
```

Library tests talk to the simulator over TCP and over a pty, including mDNS. pytest-qt builds the window offscreen. CI is `.github/workflows/gui.yml`.

Regenerate the review images (they are committed):

```bash
QT_QPA_PLATFORM=offscreen python software/gui/scripts/capture_screenshots.py
```

| Image | What it shows |
|---|---|
| [docs/screenshots/controllers.png](docs/screenshots/controllers.png) | Bench on USB `1209:f407` and Tower on the network |
| [docs/screenshots/settings.png](docs/screenshots/settings.png) | Schema form, unsaved banner, and a field error |
| [docs/screenshots/confirm-save.png](docs/screenshots/confirm-save.png) | Diff before the write, including a reboot note |
| [docs/screenshots/presets.png](docs/screenshots/presets.png) | Yaesu G-450A family, mapped settings, and `[?]` fields |

## Architecture

```
rotatorctl-gui  MainWindow
    |  schema form, confirm diff, presets, compare, copy
    v
rotatorctl      ConsoleClient  -->  TCP or serial lines
                SettingsDocument, Schema
                discovery (USB VID/PID, _rotatorctl._tcp, manual)
                presets (rotor-presets.yaml)
                sim.Engine  (the stand-in controller)
```

The form walks `schema.settings` and groups rows by the name prefix. A firmware setting of a known type (`bool`, `int`, `float`, `enum`, `string`) appears on the next connect. Readonly rows stay disabled. A row marked `reboot` is called out in the confirm dialog. The app does not reboot the controller.

Dirty state is the open form against the last loaded record. The window title grows a `*` and a banner sits above the form. Save, restore, and preset apply each show what will change before the write. Copy from another controller loads writable values into the form and leaves them dirty, so the same confirm step still runs. Compare is read-only.

Preset preview and `preset apply` both use `settings_from_preset`, so the dialog matches the simulator. The catalog is `software/firmware/presets/rotor-presets.yaml`.

## Phase plan

### Phase 1, configuration (this tree)

Discover, connect, edit, validate, confirm, save, backup, restore, compare, copy, and apply a rotor preset. Several controllers at once. One identity when the same serial appears on USB and on Ethernet.

### Phase 2, operate

Milestones, in `rotatorctl.phases`:

- Heading display per axis, from `status`
- Go to bearing
- CW / CCW jog
- STOP, always on screen. The line it will send is GS-232 `S` (`rotatorctl.operate.stop_line`), on the same port, with no mode switch
- Park
- Heading presets (bearings, separate from rotor-model presets)
- Multi-rotator dashboard
- Calibration wizard, calling `calibrate`

The simulator answers `calibrate` with `ERR unsupported` until that wizard has a protocol to drive.

### Phase 3, install and upgrade

- First install by USB DFU, wrapping `dfu-util`. `rotatorctl.upgrade.dfu_argv` returns the command for address `0x08000000` and does not run it
- Field upgrade over the console or HTTP into the inactive A/B slot, with progress
- Rollback status from the boot record in ADR 0015
- Version report from `id` / `sys.firmware`

The simulator answers `upgrade` with `ERR unsupported`. The Upgrade menu shows the DFU command in its tooltip and stays disabled.

## Protocol

Additions on top of the console in [configuration.md](../../docs/design/configuration.md) and [ADR 0015](../../docs/decisions/0015-configuration-and-ui.md):

- Console replies end with `OK` or `ERR <code> <message>`. GS-232 keeps its own replies: `C` / `C2` return `+0nnn`, and stop / set-azimuth stay silent.
- `schema` returns one JSON line for every setting: name, type, unit, min, max, enum, default, help, reboot, readonly.
- `id` returns serial, name, firmware, axes, and schema version.
- `restore` reads file lines until a line that is only `.`, then replaces the working record and the saved record together.
- USB identity: VID `0x1209`, PID `0xF407`, manufacturer `WA1HCO`, product `Rotator Controller`, serial string equal to `sys.serial`. Provisional.
- DNS-SD type `_rotatorctl._tcp` with TXT `id`, `name`, `fw`, `axes`, `schema`.

GS-232 and the console still share the port by whole-token grammar. `S` is stop. `status` and `save` are console commands.

## Open questions

- USB VID `0x1209` and PID `0xF407` are a placeholder until a pid.codes assignment (or another VID) exists. The GUI matches those numbers.
- An `az+el` catalog row has one travel block. Elevation is filled as 180 degrees and no overlap when the azimuth block is an overlap rotation. The catalog may grow a separate elevation travel block.
- `motor.current_a` is copied to `safety.stall_a`. Nameplate current may be too low for a stall threshold once the sense path is measured.
- A wedge brake with a null engage time uses the 3 second DCU-3 default. Rows that should use another delay need `engage_after_stop_s` filled in.
- The C++ settings blob is still schema, azimuth travel, dead time, and maximum run. The `schema` command is the larger contract that blob grows into.
- Cross-field checks such as `speed_min_s` <= `speed_max_s` are not applied yet. Each field is checked against its own limits.
- The simulator advertises `127.0.0.1`. A controller on the LAN will advertise its Ethernet address.
- WIMS is not wired up in this repository. The split is what lets it import `rotatorctl` later.
- PyInstaller for Windows is a later packaging step.
