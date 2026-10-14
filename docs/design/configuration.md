# Configuration and console

Draft for the command and settings shape. The rotator models are no
longer a placeholder: the readable catalog is
[rotator-catalog.md](rotator-catalog.md), and the preset table the
firmware loads is
[`software/firmware/presets/rotor-presets.yaml`](../../software/firmware/presets/rotor-presets.yaml)
(schema_version 1). That YAML sits with the firmware because applying a
preset is a firmware action, not a document. The markdown catalog is the
same data for a person to read. The decision is
[ADR 0015](../decisions/0015-configuration-and-ui.md).

The on-box record is a versioned blob in flash. This note is the text
a person reads and writes: the console, and the dump/restore file.

## Namespaces

Names are dotted. A name in a command and the same name in a file are
the same setting.

| Prefix | What it holds |
|---|---|
| `sys.*` | Schema version, board id, firmware version (read-only) |
| `az.*` | Azimuth sensor, travel, calibration, brake and speed defaults |
| `el.*` | The same for elevation. Present even when the board has no elevation sensor |
| `net.*` | Hostname, DHCP or static address, mDNS name |
| `ports.*` | USB and TCP listener ports. Not a GS-232/console mode switch |
| `ui.*` | Angle display, console echo, log level |
| `safety.*` | Dead time, maximum run, stall and overlap limits |
| `park.*` | Park heading per axis lives on `az.park_deg` and `el.park_deg`. `park.brake` says whether the brake sets on arrival. `park.idle_min` is the auto-park timeout |
| `preset.*` | Six heading memories, `preset.1` through `preset.6`, each with `.az` and `.el` |

Version 1 names shared by the PC tool and the simulator. `schema` is the machine-readable list. The packed firmware blob is still the smaller stub and grows into this list:

```
sys.schema = 1
az.sensor = dual_end_pot
az.travel_min_deg = 0
az.travel_max_deg = 450
az.cal.cw_end =          # written by the calibration sweep
az.cal.ccw_end =
el.present = false
net.hostname = rot-az
net.dhcp = true
ports.tcp = 4533
ui.log_level = info
safety.dead_time_ms = 500
safety.max_run_s = 120
```

Each stored value has a type (bool, int, float, or a closed set of
names) and limits. `set` and a file restore both reject a value outside
those limits. `el.present` follows the board file: the operator cannot
turn on an axis the board did not stuff. `sys.drive` is the same
kind of fact: `triac`, `relay`, or `dc_hbridge`.

The full in-or-out list, and which page holds each setting, is
[feature-inventory.md](feature-inventory.md). Names added from that
inventory, still schema version 1:

| Name | Role |
|---|---|
| `az.center` | `north` or `south` center of travel |
| `az.overlap_deg`, `*.travel_min_deg`, `*.travel_max_deg` | Overlap and the soft limits |
| `*.coast_deg` | Degrees of coast before the target |
| `*.offset_deg` | Beam heading offset |
| `*.creep_deg`, `*.ramp_s`, `*.slowdown_deg` | AC creep and DC PWM ramp. Advanced |
| `*.pulse_debounce_ms`, `*.pulse_deg`, `*.adc_samples` | Pulse input and pot averaging. Advanced |
| `*.limit_switch` | Optional end-of-travel switches. Advanced |
| `*.tolerance_deg` | Go-to stop window. Advanced |
| `*.cal.cw_end`, `*.cal.ccw_end`, `*.cal.map` | Two-point ends, and a multi-point `raw:heading` list or `none` |
| `safety.stall_timeout_s`, `safety.stall_deg` | No-motion jam stop |
| `park.idle_min`, `preset.N.az`, `preset.N.el` | Auto-park and six memories |
| `net.admin_lock`, `net.admin_password` | Web UI and console-verb lock. GS-232 lines stay open |
| `ports.rotctld`, `ports.easycom`, `ports.dcu1` | Extra listeners. `0` leaves that protocol off |
| `az.sensor` / `el.sensor` | `dual_end_pot`, `single_ended_pot`, `rheostat`, `pulse`, `incremental_encoder`, `hh12_as5045`, `none` |

`*.cal.map` is `none`, or at least two `raw:heading` pairs joined by
commas and no spaces (`0:0,180:181,450:448`). A preset does not write
the offset, the map, the memories, or the network lock.

`ports.*` does not contain a mode that selects GS-232 or the console.
Both are accepted on USB CDC and on the TCP port. See the grammar below.

## Command grammar

One command per line. Leading and trailing space is ignored. The first
token decides the parser.

**Console verbs** (whole token, lowercase):

| Line | Effect |
|---|---|
| `help` | List the verbs and the GS-232 tokens |
| `status` | Position, target, motion state, faults |
| `get <name>` | Print one setting |
| `set <name> <value>` | Check limits, update RAM. Does not write flash |
| `save` | Write the RAM record to flash |
| `preset list` | Names in the compiled-in table |
| `preset apply <model>` | Load that model's axis and safety defaults. Leaves `net.*`, `ports.*`, and saved calibration |
| `calibrate <az\|el>` | Start the guided end-to-end sweep on that axis |
| `log` | Print the RAM ring |
| `log level <error\|warn\|info\|debug>` | Same as `set ui.log_level` |
| `dump` | Print the text file |
| `restore` | Replace the stored record from a file ended by a line that is only `.` |
| `schema` | One JSON line describing every setting |
| `id` | One JSON line: serial, name, firmware, axes, schema version |
| `upgrade` | Reserved for field upgrade. Until that protocol exists the reply is `ERR unsupported` |
| `reboot` | Restart into the confirmed image |

`set` without `save` is lost on reset. The web forms follow the same
rule: edit, then an explicit save.

**GS-232** is the closed token set in
`software/firmware/include/rotator/protocol/gs232.hpp`. Today that is
`A` / `S` (stop), `M` plus digits (set azimuth), and `C` / `C2` (query).
A later token joins this set only if it is not a console verb.

Classification uses the whole first token. `S` is stop. `status` and
`save` are console commands. A line that matches neither set gets no
reply, so a logging program never sees a help string.

## Replies

Every console command ends with one status line:

- `OK`
- `ERR <code> <message>`

Body lines come first. The status line is not part of the settings file.

GS-232 replies are not console replies. `C` and `C2` return one Yaesu line `+0nnn` (azimuth in degrees, three digits) and no `OK`. `A`, `S`, and `Maaa` return nothing. The firmware parser already accepts those lines. The reply bytes are part of this contract; the formatter lands with the motor loop. A console client sends only console verbs, so it waits for `OK` or `ERR`.

A line that is neither a console verb nor a GS-232 command produces no reply. Console verbs are lowercase whole tokens. `SCHEMA` is silence. `S` is stop. `status` and `save` are console commands. Matching GS-232 is the whole trimmed line, the same rule as `parse_gs232`.

`calibrate` stays in the grammar. A controller that has not implemented the sweep yet, including the simulator, replies `ERR unsupported`. `upgrade` is reserved now so it cannot be taken by a GS-232 token later.

### `schema`

`schema` returns exactly one JSON line, then `OK`.

```json
{"version":1,"settings":[{"name":"ports.tcp","type":"int","unit":"port","min":1,"max":65535,"enum":[],"default":"4533","help":"TCP port for the shared console and GS-232 listener.","reboot":true,"readonly":false}]}
```

| Field | Meaning |
|---|---|
| `name` | Dotted setting name |
| `type` | `bool`, `int`, `float`, `enum`, or `string` |
| `unit` | Suffix for display. Empty when there is no unit |
| `min`, `max` | Numeric limits, or null |
| `enum` | Closed names for type `enum`, otherwise an empty list |
| `default` | Canonical text of the firmware default |
| `help` | One line of help |
| `reboot` | True when the value is read on boot |
| `readonly` | True when `set` and a file must not change it |

The PC program builds its forms from this document. A new setting of a known type appears without a GUI change. A new type needs a library update.

Bool text is `true` or `false`. Integers are decimal. Floats are decimal with trailing zeros removed. Strings are one token. `net.hostname` is a hostname label. `net.address` is an IPv4 address.

### `id`

`id` returns one JSON line, then `OK`:

```json
{"serial":"RC-0000","name":"rotator","fw":"0.0.0","axes":"az","schema":1}
```

`serial` is `sys.serial`. `name` is `net.hostname`. A TCP session has no USB serial string until it asks.

### `dump` and `restore`

`dump` prints the text file, then `OK`.

`restore` starts a file. The host sends `restore`, then the file lines, then a line that is only `.`. The controller parses the whole file, checks every value, and only then replaces both the working record and the saved record. A bad file leaves both as they were, and the reply is `ERR`. The lone dot is the terminator, so a settings file cannot contain a line that is only a dot. Comments and blank lines are ignored. Readonly values may be omitted, or they must match. Every writable setting is present. A different `sys.schema` is `ERR schema`. An unknown name is `ERR unknown`.

`set` changes the working record only. `save` writes it. `restore` writes both. Nothing is rebooted from a save. Settings with `reboot: true` take effect on the next boot.

## Text file

INI-like, flat. One setting per line. The same strings as `get` / `set`.

```
# rotator-settings 1
sys.schema = 1
az.sensor = dual_end_pot
az.travel_max_deg = 450
safety.dead_time_ms = 500
```

- `#` starts a comment. Blank lines are ignored.
- Names are case-sensitive and match the namespace table.
- No sections, no quoting rules beyond a single token value. A value
  that needs a space is not a valid setting; use a closed name instead
  (`dual_end_pot`, not `dual end pot`).
- `dump` writes this form. Restore reads it.

Restore does not apply a file line by line onto the live record. It
parses the whole file, checks every value, runs migration if
`sys.schema` is older than the firmware, and only then replaces the
stored record. A bad line leaves the box as it was.

## Offline configuration file

No controller is required to review a station setup. The PC app starts
offline and edits a configuration document, saved as `.rotcfg`. YAML is
the usual form. JSON is accepted when the text starts with `{`.

```
# rotator-config 1
format: rotcfg
version: 1
preset: yaesu-g-450a
name: station
overrides:
  az.overlap_deg: "100"
settings:
  az.sensor: single_ended_pot
  az.overlap_deg: "100"
```

`preset` is the catalog id last applied. `overrides` are the values the
operator changed after that. `settings` is the full tree, including
those overrides. A later push sends only the writable lines, in the
restore format above, so the controller keeps its own serial and board
facts. Readonly names such as `sys.serial` and `*.present` are omitted
from that push.

## Presets

The source table is `software/firmware/presets/rotor-presets.yaml`.
Each entry's `id` is the name `preset apply` takes (`hygain-ham-iv`,
`yaesu-g-450a`, `spid-rak`, …). `support: no` and `support: later` are
not offered. An `alias` entry points at a rotor preset instead of
loading itself. Fields listed under `unverified` are copied as written
and still need a bench check. The readable form, including family
settings and sources, is [rotator-catalog.md](rotator-catalog.md).

1. `preset list` shows the compiled-in models. The table is always
   linked. There is no per-model `#ifdef`.
2. `preset apply hygain-ham-iv` copies that row into `az.*`, `el.*`,
   and `safety.*`. A two-axis preset fills both axes.
3. Network identity and an existing calibration are left alone.
4. If the preset has limit switches, the calibration sweep drives to
   one end, records the sensor, drives to the other end, and proposes
   `az.cal.*` (or `el.cal.*`). SPID and Prosistel D have no limit
   switches, so the sweep does not hunt for a hard stop. The operator
   sets those ends. Nothing is saved until the operator confirms and
   `save` runs.

The PC library and the simulator share one mapping from a catalog row
onto settings, so the preview and `preset apply` match.

- `sensor.type` `pot_dual_end_grounded_wiper` becomes `dual_end_pot`. `pot_single_ended` becomes `single_ended_pot`.
- `brake.type` `none_gear` becomes `none`.
- `travel.range_deg` becomes `travel_max_deg`. `overlap_deg` becomes `overlap_deg`. `travel_min_deg` stays 0.
- An `az+el` row has one travel block, aimed at azimuth. Elevation `travel_max_deg` is 180 and `overlap_deg` is 0 when that block is an overlap rotation (range past 180 and a non-zero overlap). This stands in until the catalog has a separate elevation travel block.
- `speed.min_s` and `speed.max_s` become `speed_min_s` and `speed_max_s`.
- `motor.current_a`, when the catalog has a number, becomes `safety.stall_a`.
- `*.present` is left alone. It is a board fact.
- Calibration, `net.*`, and `ports.*` are left alone.
- A wedge brake with no `engage_after_stop_s` uses 3 seconds, the DCU-3 default in the sequencing text. Any other brake with no engage time uses 0. A pair of equal numbers is that delay (HAM-V is 8 and 8, so 8 seconds). A pair of different numbers is not collapsed into one setting.

The offline rotator page lists every catalog row, including `support: no`, `later`, `check`, and `alias`. `Use this rotator` loads a row only when support is `v1`, `v1-2axis`, or `v2-dc`. An alias is shown and points at the rows it names. Fields listed under `unverified` are marked `[?]`. A custom override replaces one mapped value in the `.rotcfg` file and is shown next to the preset value.

The web preset picker and wizard call these same steps. Board changes
the catalog implies (pot modes, pulse inputs, run-cap placement, the
brake default, the DC module, and the unsupported 48 VAC Prosistel) are
open items in
[hardware-requirements.md](hardware-requirements.md).

## Discovery

USB CDC identity. The numbers are provisional until a VID is assigned:

| USB field | Value |
|---|---|
| Vendor id | `0x1209` (pid.codes), provisional |
| Product id | `0xF407`, provisional |
| Manufacturer | `WA1HCO` |
| Product | `Rotator Controller` |
| Serial string | the same text as `sys.serial` |

The host lists serial ports and keeps those whose VID and PID match and whose serial string is non-empty. That serial string is the stable identity. A pty has no USB descriptor, so a bench setup can also add a serial path by hand.

mDNS/DNS-SD service type is `_rotatorctl._tcp`. Hamlib's `_rotctl._tcp` is a different grammar, and this box does not advertise it.

| TXT key | Value |
|---|---|
| `id` | `sys.serial` |
| `name` | `net.hostname` |
| `fw` | `sys.firmware` |
| `axes` | `az`, `el`, or `az+el` |
| `schema` | schema version |

The port is `ports.tcp` (default 4533), the shared console and GS-232 listener. A network that does not pass multicast can still be opened by typing host and port.

The same serial on USB and on mDNS is one controller. The user-assigned name is `net.hostname`. When both discoveries are present, the mDNS name fills an empty USB name.

## Web API

The PC helper and the controller's built-in web server speak one JSON API, version 1. The browser pages are static files (`index.html`, `app.css`, `app.js`) with relative URLs and no build step. On the PC they are served under `/s/<token>/`. On the controller they are served at the site root. `GET /api/boot` tells the page which extras exist, so the same JavaScript hides file buttons, discovery, and Quit when `role` is `device`.

The PC helper binds `127.0.0.1` only. The token in the path is a random session key, new every launch. A request to any other path, including `/`, is 404. Each HTTP call and each WebSocket message refreshes a presence timer. The page also `POST`s `/api/heartbeat` about every 8 seconds. The helper quits 20 seconds after the last tab is gone (`socket_count` is 0 and the last touch is older than `idle_seconds`). Quit calls `POST /api/shutdown`. `--stay` sets `idle_seconds` to 0, which turns that timer off, and does not open a browser.

Errors are JSON `{ "error", "message" }` with an HTTP 4xx or 502. A settings problem is 400. A console or transport failure is 502. Connecting while the open controller form is dirty is 409 `dirty` unless the body sets `discard` true.

`GET /api/boot` returns:

| Field | Meaning |
|---|---|
| `api` | `1` |
| `role` | `pc` on the helper, `device` on firmware |
| `idle_seconds` | `20` on a normal PC launch, `0` when idle quit is off. Firmware may send `0`. |
| `features.offline` | The page can edit a `.rotcfg` document |
| `features.discovery` | Show the Controllers page |
| `features.files` | Show Open, Config folder, and Download |
| `features.shutdown` | Show Quit |
| `features.multi` | More than one controller can be open |
| `operate`, `upgrade` | Milestone labels. The buttons stay disabled in phase 1 |
| `dfu` | Argument list from `dfu_argv`, shown as the Upgrade tooltip |
| `stop` | The STOP line. Phase 1 leaves the button disabled. The line is GS-232 `S` |

Shared routes, which firmware implements. On a device, `GET /api/document` is the live settings. On the PC it is the offline `.rotcfg` document.

| Method and path | Body | Result |
|---|---|---|
| `GET /api/schema` | | `{ version, settings }`. Each setting includes `label`, `advanced`, `reboot`, `readonly`, and the schema fields |
| `GET /api/pages` | | `{ pages: [{ id, title, intro, fields }] }`. The static page does not hard-code the inventory |
| `GET /api/catalog` | | `{ presets }`. Every catalog row, including `no`, `later`, `check`, and `alias`. `can_apply` is true for `v1`, `v1-2axis`, and `v2-dc`. `facts` carry `unverified`. `settings` is the mapped writable values, with labels |
| `GET /api/document` | | `{ source, preset, name, filename, overrides, settings, dirty, axes, connected }`. `axes` is `{ azimuth, elevation }`. Offline, that follows the applied preset's axes. On a device it follows `az.present` and `el.present` |
| `POST /api/document/new` | | Replace the offline document with a blank station |
| `POST /api/document/edit` | `{ name, value }` | Validate and store one offline value. Matching the preset value clears that override |
| `POST /api/document/preview` | | `{ changes, errors, blocked, note }` before a save |
| `POST /api/document/save` | `{ name? }` | Write the config file. The name is a bare filename ending in `.rotcfg`, `.yaml`, `.yml`, or `.json` |
| `POST /api/document/upload` | `{ text }` | Load a `.rotcfg` body. YAML, or JSON when the text starts with `{` |
| `GET /api/document/download` | | The file body as text |
| `POST /api/document/push` | | Send writable lines to the connected controller. Readonly names are omitted |
| `POST /api/preset/apply` | `{ id }` | Load an applyable preset into the document and drop overrides that the preset wrote |
| `POST /api/override` | `{ name, value }` | Set a custom override. `value` null or `""` clears it |
| `GET /api/device` | | The connected form: `connected`, `dirty`, `settings`, `errors`, `axes`, `schema`. `connected` is false when nothing is open |
| `POST /api/device/edit` | `{ name, value }` | Edit the connected controller's working form. Invalid text is kept and reported in `errors` |
| `POST /api/device/preview` | | Same preview object as the document. `blocked` is true while any field is invalid |
| `POST /api/device/save` | | `set` the changes, then `save`. Does not reboot. `note` says when a change such as `net.hostname` takes effect after reboot |
| `POST /api/device/backup` | | Text backup of the controller |
| `POST /api/device/restore` | `{ text, apply }` | `apply` false previews. `apply` true writes |
| `POST /api/device/compare` | `{ text }` | Read-only preview against a backup |
| `GET /api/ws` | | WebSocket presence. A text frame `quit` asks the PC helper to stop |

A preview `changes` entry is `{ name, label, before, after, reboot }`. `note` is empty, or it names the reboot settings and says the app does not reboot the controller.

PC-only routes. Firmware omits them and sets the matching `features` flags false.

| Method and path | Body | Result |
|---|---|---|
| `GET /api/files` | | `{ directory, files }` in the station config folder |
| `POST /api/files/open` | `{ name }` | Load one file from that folder |
| `GET /api/controllers` | | `{ controllers }`. Each has `serial`, `name`, `firmware`, `axes`, `text`, and `endpoints` |
| `POST /api/controllers/scan` | `{ timeout? }` | USB scan plus `_rotatorctl._tcp` browse |
| `POST /api/controllers/add` | `{ kind, host, port, path }` | `kind` is `tcp` or `serial` |
| `POST /api/controllers/connect` | `{ target, discard? }` | Open a console session and load its settings |
| `POST /api/controllers/disconnect` | | Close that session |
| `POST /api/device/copy` | `{ target }` | Copy writable settings from another controller into the form. They stay dirty until save |
| `POST /api/heartbeat` | | `{ ok: true }`. Refreshes the idle timer |
| `POST /api/shutdown` | | Ask the PC helper to exit |

`text` on a controller is the list line: the name and serial, then `USB 1209:f407` plus the serial path, or `network` plus `host:port`.

