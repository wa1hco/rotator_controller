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
| `ui.*` | Web session limits, console echo, log level |
| `safety.*` | Dead time, maximum run, stall and overlap limits |

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
turn on an axis the board did not stuff.

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
- A wedge brake with no `engage_after_stop_s` uses 3 seconds, the DCU-3 default in the sequencing text. Any other brake with no engage time uses 0.

`support: no` and `support: later` are not shown. A row whose support is anything else outside `v1`, `v1-2axis`, `v2-dc`, and `alias` is not shown either. `alias` is shown and is not applied. Fields listed under `unverified` are marked `[?]` next to the family and the mapped settings.

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
