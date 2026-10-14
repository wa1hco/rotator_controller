# Rotator controller, PC side

## Download and double-click

No Python install. The rotor catalog is inside the app. After a release is published, these names stay stable:

- Windows: [RotatorController-Windows.exe](https://github.com/wa1hco/rotator_controller/releases/latest/download/RotatorController-Windows.exe)
- macOS: [RotatorController-macOS.dmg](https://github.com/wa1hco/rotator_controller/releases/latest/download/RotatorController-macOS.dmg)
- Linux: [RotatorController-Linux.AppImage](https://github.com/wa1hco/rotator_controller/releases/latest/download/RotatorController-Linux.AppImage)

`releases/latest` is the newest release that is not marked pre-release. A `v0.1.0-preview` tag is a pre-release, so use the tag URL until a stable tag exists, for example `https://github.com/wa1hco/rotator_controller/releases/download/v0.1.0-preview/RotatorController-Windows.exe`.

Windows: download the `.exe` and double-click it. The first start unpacks the app and can take a few seconds. The build is unsigned, so SmartScreen may say it is unrecognized: choose More info, then Run anyway.

macOS: the disk image is unsigned and built for Apple silicon. Open the `.dmg` and drag Rotator Controller to Applications. The first launch is blocked by Gatekeeper: right-click the app, choose Open, then Open again. An Intel build is not published yet.

Linux: `chmod +x RotatorController-Linux.AppImage`, then double-click it or run it from a terminal. The image is x86_64, built on Ubuntu 22.04. It needs FUSE (`libfuse2`). If FUSE is unavailable, `APPIMAGE_EXTRACT_AND_RUN=1 ./RotatorController-Linux.AppImage` still starts.

Double-click starts a small helper, not a separate window toolkit. The helper listens on `127.0.0.1` only, picks a free port, and opens the default browser at `http://127.0.0.1:<port>/s/<token>/`. The token is a new random session key each launch. Anything else, including a bare `/`, is refused.

Windows shows a console window with that URL, because a double-clicked `.exe` has no other place to print it. macOS and Linux double-click launches have no terminal. The page footer is the notice there. Quit in the page stops the helper. Closing the last tab does too: the page holds a WebSocket and sends a heartbeat about every 8 seconds, and the helper exits 20 seconds after both have stopped. `--stay` keeps the helper up, skips the browser, and turns the idle quit off. Ctrl+C stops a helper that was started from a terminal.

Open, Save, and Config folder use the station config directory, which the app creates on first use. Download and the Open file picker also move a `.rotcfg` through the browser.

| System | Directory |
|---|---|
| Windows | `%APPDATA%\RotatorController` |
| macOS | `~/Library/Application Support/RotatorController` |
| Linux | `$XDG_CONFIG_HOME/rotator-controller`, or `~/.config/rotator-controller` |

The app opens offline. No controller is required. The first screen is the rotator catalog: all 39 rotators, filtered by family, manufacturer, and a search across model, maker, and alias. A row shows its specs, the settings it would write, and `[?]` on values the catalog still marks unverified. Choosing a rotator fills a configuration document. Custom overrides and the other preference pages (axes, limits, park, calibration, display, network, console) edit that same document. Save writes a `.rotcfg` file (YAML, or JSON when the text starts with `{`). Push, once a controller is connected, sends the writable settings and leaves the controller's serial and board facts alone.

Controllers stay in the app, on the last page: USB and network discovery, the schema form, confirm-before-write, backup, restore, compare, and copy. That work is not the start screen, because there is no controller to connect yet.

Phases 2 and 3 are planned below. The page already reserves their places: STOP stays in the header on every page and at phone width, and the Operate and Upgrade menus are present and disabled.

Text size follows the browser zoom and an in-app A− / A+ control. That choice is stored in the browser as `rotatorctl.textScale`. The layout works on a phone. Dark mode follows the system setting (`prefers-color-scheme`). The static pages are plain HTML, CSS, and JavaScript, 10,214 bytes gzipped (`index.html` + `app.css` + `app.js`), so the same files can sit in the controller's web server later.

## For developers

### Packages

`software/gui/` holds two installable packages.

| Package | Role |
|---|---|
| `rotatorctl` | Settings model, console client, discovery, presets, CLI, simulator. No GUI toolkit. WIMS can import this package alone. |
| `rotatorctl-gui` | Loopback server and the static pages. Forms come from `GET /api/pages` and the schema. |

Python 3.11 or newer. The UI decision is [ADR 0019](../../docs/decisions/0019-pc-gui-toolkit.md). The first cut used PySide6. That is superseded: browser font scaling is reliable, and one set of pages can be served later by the controller itself. aiohttp serves the pages and the JSON API. pydantic holds the schema, pyserial opens the USB serial port, and zeroconf browses DNS-SD.

The downloadable apps are built by [`.github/workflows/package.yml`](../../.github/workflows/package.yml). Pull requests upload the three files as workflow artifacts. A `v*` tag attaches those same names to a GitHub Release. The build script is `software/gui/packaging/pyinstaller_build.py`. It bundles `software/firmware/presets/rotor-presets.yaml` and the static pages, and checks the result with `--selftest` (start the server, fetch the page and the catalog, exit).

### Run from a checkout

From the repository root, with the firmware preset file where it already lives:

```bash
python -m pip install -e software/gui/rotatorctl
python -m pip install -e software/gui/rotatorctl-gui --no-deps
python -m pip install "aiohttp>=3.9"
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

`set` changes the working record. `save` stores it. `restore` stores it as part of the command. The page's save button does `set` for each changed field and then `save`, and only after the confirm dialog.

### Simulator

The firmware console is not in the tree yet. `rotatorctl-sim` speaks the console protocol and the GS-232 subset over TCP, and it can open a pty and advertise `_rotatorctl._tcp`.

```bash
rotatorctl-sim -n 2 --pty --mdns
```

`software/sim` is the C++ K3NG sandbox. The console simulator lives in the Python library so an install can start it. `software/gui/sim/rotator_sim.py` is a thin launcher. Details are in [sim/README.md](sim/README.md).

### Tests

```bash
cd software/gui
python -m pip install "pytest>=8" "playwright>=1.49"
python -m playwright install --with-deps chromium
pytest
```

Library tests talk to the simulator over TCP and over a pty, including mDNS. API tests drive the loopback server. Playwright runs a headless Chromium smoke test. CI is `.github/workflows/gui.yml`.

Regenerate the review images (they are committed):

```bash
python software/gui/scripts/capture_screenshots.py
```

Offline pages, the ones to review first:

| Image | What it shows |
|---|---|
| [docs/rotator-selection.png](docs/rotator-selection.png) | Desktop width. All 39 rotators. Yaesu G-450A selected, specs and settings with `[?]`, and a custom overlap override |
| [docs/rotator-phone.png](docs/rotator-phone.png) | The same picker at phone width (390×844). STOP stays on screen |
| [docs/rotator-large-text.png](docs/rotator-large-text.png) | The picker after two A+ steps (125%) |
| [docs/axes.png](docs/axes.png) | Sensor and brake for azimuth and elevation |
| [docs/limits.png](docs/limits.png) | Travel, overlap, speed, and the safety stops |
| [docs/park.png](docs/park.png) | Park headings and whether the brake sets on arrival |
| [docs/calibration.png](docs/calibration.png) | End counts. The sweep button stays disabled until phase 2 |
| [docs/display.png](docs/display.png) | Angle unit, display range, speed display, cardinal labels |
| [docs/network.png](docs/network.png) | Hostname, DHCP, address, mDNS |
| [docs/console.png](docs/console.png) | Shared TCP port, GS-232 query token, echo, log level |

Connected-controller pages, from the simulator:

| Image | What it shows |
|---|---|
| [docs/screenshots/controllers.png](docs/screenshots/controllers.png) | Bench on USB `1209:f407` and Tower on the network |
| [docs/screenshots/settings.png](docs/screenshots/settings.png) | Schema form, unsaved banner, and a field error |
| [docs/screenshots/confirm-save.png](docs/screenshots/confirm-save.png) | Diff before the write, including a reboot note |
| [docs/screenshots/presets.png](docs/screenshots/presets.png) | The settings a preset writes, and the custom overlap override |

### Architecture

```
browser         static HTML / CSS / JS
    |  relative /api and /api/ws
    v
rotatorctl-gui  aiohttp on 127.0.0.1, session token in the path
    |  schema form, confirm diff, presets, compare, copy
    v
rotatorctl      ConsoleClient  -->  TCP or serial lines
                SettingsDocument, Schema
                discovery (USB VID/PID, _rotatorctl._tcp, manual)
                presets (rotor-presets.yaml)
                sim.Engine  (the stand-in controller)
```

The form walks the page list from `GET /api/pages` and groups rows by the name prefix. A firmware setting of a known type (`bool`, `int`, `float`, `enum`, `string`) appears on the next connect. Readonly rows stay disabled. A row marked `reboot` is called out in the confirm dialog. The app does not reboot the controller. The route table is the Web API section of [configuration.md](../../docs/design/configuration.md).

Dirty state is the open form against the last loaded record. The page title grows a `*` and a banner sits above the form. Save, restore, and preset apply each show what will change before the write. Copy from another controller loads writable values into the form and leaves them dirty, so the same confirm step still runs. Compare is read-only.

Preset preview and `preset apply` both use `settings_from_preset`, so the dialog matches the simulator. The catalog is `software/firmware/presets/rotor-presets.yaml`.

### Phase plan

#### Phase 1, configuration (this tree)

Offline, a `.rotcfg` document: pick a rotator, override a mapped value, and edit axes, limits, park, calibration, display, network, and the shared console. With a controller connected: discover, connect, edit, validate, confirm, save, backup, restore, compare, copy, and push that document. Several controllers at once. One identity when the same serial appears on USB and on Ethernet.

#### Phase 2, operate

Milestones, in `rotatorctl.phases`, taken from the in-scope Operate rows of [feature-inventory.md](../../docs/design/feature-inventory.md):

- Heading display per axis, from `status`
- Go to bearing
- CW / CCW jog
- STOP, always on screen. The line it will send is GS-232 `S` (`rotatorctl.operate.stop_line`), on the same port, with no mode switch
- Park, and auto-park from `park.idle_min`
- Heading preset recall (the six `preset.N` memories)
- Soft limits, coast, creep, and the stall stop, using the settings already stored
- PWM ramp on a DC drive (`sys.drive = dc_hbridge`)
- Calibration wizard and the multi-point map
- The rest of GS-232B: `W`, `X1`–`X4`, `O`/`F`, `P36`/`P45`, `Z`, and the jog letters
- Hamlib rotctld, Easycom, and DCU-1, on the ports stored in phase 1 (`0` leaves each one off)
- Live log
- Multi-rotator dashboard

Moon, sun, and satellite tracking stay on the PC. The box accepts the next heading. The simulator answers `calibrate` with `ERR unsupported` until that wizard has a protocol to drive.

#### Phase 3, install and upgrade

- First install by USB DFU, wrapping `dfu-util`. `rotatorctl.upgrade.dfu_argv` returns the command for address `0x08000000` and does not run it
- Field upgrade over the console or HTTP into the inactive A/B slot, with progress
- Rollback status from the boot record in ADR 0015
- Version report from `id` / `sys.firmware`

The simulator answers `upgrade` with `ERR unsupported`. The Upgrade menu shows the DFU command in its tooltip and stays disabled.

### Protocol

Additions on top of the console in [configuration.md](../../docs/design/configuration.md) and [ADR 0015](../../docs/decisions/0015-configuration-and-ui.md):

- Console replies end with `OK` or `ERR <code> <message>`. GS-232 keeps its own replies: `C` / `C2` return `+0nnn`, and stop / set-azimuth stay silent.
- `schema` returns one JSON line for every setting: name, type, unit, min, max, enum, default, help, reboot, readonly.
- `id` returns serial, name, firmware, axes, and schema version.
- `restore` reads file lines until a line that is only `.`, then replaces the working record and the saved record together.
- USB identity: VID `0x1209`, PID `0xF407`, manufacturer `WA1HCO`, product `Rotator Controller`, serial string equal to `sys.serial`. Provisional.
- DNS-SD type `_rotatorctl._tcp` with TXT `id`, `name`, `fw`, `axes`, `schema`.

GS-232 and the console still share the port by whole-token grammar. `S` is stop. `status` and `save` are console commands.

### Open questions

- USB VID `0x1209` and PID `0xF407` are a placeholder until a pid.codes assignment (or another VID) exists. The GUI matches those numbers.
- An `az+el` catalog row has one travel block. Elevation is filled as 180 degrees and no overlap when the azimuth block is an overlap rotation. The catalog may grow a separate elevation travel block.
- `motor.current_a` is copied to `safety.stall_a`. Nameplate current may be too low for a stall threshold once the sense path is measured.
- A wedge brake with a null engage time uses the 3 second DCU-3 default. A pair of equal numbers is copied as that delay (HAM-V is 8 seconds). A real min/max range is not collapsed. Rows that should use another delay need `engage_after_stop_s` filled in.
- The C++ settings blob is still schema, azimuth travel, dead time, and maximum run. The `schema` command is the larger contract that blob grows into.
- Cross-field checks such as `speed_min_s` <= `speed_max_s` are not applied yet. Each field is checked against its own limits.
- The simulator advertises `127.0.0.1`. A controller on the LAN will advertise its Ethernet address.
- WIMS is not wired up in this repository. The split is what lets it import `rotatorctl` later.
- The macOS download is Apple silicon and unsigned. An Intel disk image, and signed or notarized builds, are still open.
