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

Illustrative names, not the catalog:

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

The web preset picker and wizard call these same steps. Board changes
the catalog implies (pot modes, pulse inputs, run-cap placement, the
brake default, the DC module, and the unsupported 48 VAC Prosistel) are
open items in
[hardware-requirements.md](hardware-requirements.md).
