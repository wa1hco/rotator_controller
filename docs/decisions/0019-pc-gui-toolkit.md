# ADR 0019: PC GUI toolkit

- Status: Accepted. The PySide6 window chosen earlier on 2026-10-12 is superseded by the browser UI below.
- Date: 2026-10-12

## Context

ADR 0015 leaves setup on a shared console: USB CDC and a TCP port, with
GS-232 on the same ports by grammar. The web UI on the box is the
primary interface. A station still wants a program on the PC that can
see several controllers at once, including one that is only on USB, and
WIMS (a separate Python project) needs the same protocol.

The firmware that will answer the console is not in this tree yet. The
PC program has to be testable against a simulator that speaks the
grammar in `docs/design/configuration.md`.

A Qt window was the first Phase 1 UI. Browser font scaling did not
reach it in a way operators could rely on, and a second widget layout
would have drifted from the pages the controller's own web server is
meant to serve.

## Decision

Two Python 3.11+ packages live under `software/gui/`:

1. `rotatorctl` has the settings model, the console client, USB and
   mDNS discovery, the rotor-preset mapping, a small CLI
   (`rotatorctl list/get/set/dump/restore`, plus `save`), and the
   controller simulator. It does not import a GUI toolkit. WIMS can
   depend on this package alone.
2. `rotatorctl-gui` is the PC helper. It depends on `rotatorctl` and
   aiohttp. There is no Qt dependency.

The helper binds `127.0.0.1` on a free port and serves one session at
`/s/<token>/`. The token is random per launch and is the session key.
The default browser opens that URL. Windows shows a console window with
the URL, because a double-clicked `.exe` otherwise has nowhere to print
it. macOS and Linux double-click launches have no terminal; the page
footer is the notice, and Quit stops the helper. The helper also quits
20 seconds after the last tab is gone (no WebSocket and no heartbeat).
`--stay` leaves it running and does not open a browser. `--selftest`
starts the server, fetches the page and the catalog, and exits.

The pages are static HTML, CSS, and JavaScript. There is no frontend
framework and no bundler. The same files are what the F407 web server
can store later. The measured gzip size of `index.html`, `app.css`, and
`app.js` together is 10,214 bytes. CSS is in rem so browser zoom and the
in-app A− / A+ control (stored in `localStorage` as
`rotatorctl.textScale`) both change the type. The layout is usable on a
phone. Dark mode follows `prefers-color-scheme`. STOP stays in the
header.

The JSON API is version 1 and is the same shape on the PC helper and on
a future device. The PC prefixes every route with `/s/<token>`. Firmware
serves the same paths at the site root. The pages use relative URLs, so
both layouts work. `GET /api/boot` tells the page which PC-only features
to show (`files`, `discovery`, `shutdown`, `multi`). The route table is
in `docs/design/configuration.md`.

Phase 1, in this repository now, is configuration. The page opens
offline on a configuration document (`.rotcfg`, YAML or JSON) so a
station can be reviewed before any controller exists. The first page is
the rotor catalog. The other preference pages edit the same document.
Discover, connect, confirm-before-write, backup, restore, compare, and
copy stay on the Controllers page and in the library. Phase 2 (operate)
and phase 3 (install and upgrade) have milestones in
`software/gui/README.md` and hooks in the library: a STOP control that
stays on screen, disabled Operate and Upgrade menus, `dfu_argv()` for
the ROM DFU command in ADR 0015, and simulator replies of
`ERR unsupported` for `calibrate` and `upgrade`.

The simulator listens on TCP and on a pty, and it can advertise
`_rotatorctl._tcp`. It is `rotatorctl.sim`, with a launcher in
`software/gui/sim`. `software/sim` remains the C++ K3NG sandbox.

Downloadable builds come from `.github/workflows/package.yml`, which
freezes the helper with PyInstaller for Windows, macOS, and Linux. Those
builds are unsigned. The bundle includes the rotor catalog and the
static pages. CI runs pytest for the library and the HTTP API, and
Playwright for a headless browser smoke test.

pydantic carries the schema document. pyserial opens USB CDC. zeroconf
browses `_rotatorctl._tcp`.

## Consequences

- Protocol additions for the PC tool (`schema`, `id`, the `OK`/`ERR`
  trailer, restore ended by a lone dot, the USB identity, and
  `_rotatorctl._tcp`) are in `docs/design/configuration.md`. They keep
  the GS-232 coexistence rule from ADR 0015. The Web API section of that
  note is the contract the firmware web server implements later.
- The provisional USB VID `0x1209` and PID `0xF407` are a contract to
  replace when an assignment exists. They are not a completed pid.codes
  registration.
- The packed settings blob in the firmware tree is still the small
  stub. The `schema` document is the shape it grows into.
- The KiCad files are not edited by this decision.
- PySide6 and pytest-qt are not dependencies.
