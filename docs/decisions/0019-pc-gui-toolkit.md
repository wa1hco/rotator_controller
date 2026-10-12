# ADR 0019: PC GUI toolkit

- Status: Accepted
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

## Decision

Two Python 3.11+ packages live under `software/gui/`:

1. `rotatorctl` has the settings model, the console client, USB and
   mDNS discovery, the rotor-preset mapping, a small CLI
   (`rotatorctl list/get/set/dump/restore`, plus `save`), and the
   controller simulator. It does not import Qt. WIMS can depend on this
   package alone.
2. `rotatorctl-gui` is the desktop app. It depends on `rotatorctl` and
   PySide6.

PySide6 is the widget toolkit: one codebase for Windows, Linux, and
macOS, native widgets that fit a laptop screen, and pytest-qt for a
headless smoke test (`QT_QPA_PLATFORM=offscreen`). pydantic carries the
schema document. pyserial opens USB CDC. zeroconf browses
`_rotatorctl._tcp`.

The forms are built from the `schema` command. A new setting of a known
type shows up without a GUI change.

Phase 1, in this repository now, is configuration. The window opens
offline on a configuration document (`.rotcfg`, YAML or JSON) so a
station can be reviewed before any controller exists. The first page is
the rotor catalog. The other preference pages edit the same document.
Discover, connect, confirm-before-write, backup, restore, compare, and
copy stay on the Controllers page and in the library. Phase 2 (operate) and
phase 3 (install and upgrade) have milestones in `software/gui/README.md`
and hooks in the library: a STOP control that stays on screen, disabled
Operate and Upgrade menus, `dfu_argv()` for the ROM DFU command in
ADR 0015, and simulator replies of `ERR unsupported` for `calibrate` and
`upgrade`.

The simulator listens on TCP and on a pty, and it can advertise
`_rotatorctl._tcp`. It is `rotatorctl.sim`, with a launcher in
`software/gui/sim`. `software/sim` remains the C++ K3NG sandbox.

A later Windows build can freeze the GUI with PyInstaller. That build
is not part of this decision. CI runs pytest, including the offscreen
GUI tests.

Tkinter would have avoided a Qt wheel and would have made the form
layout and the headless test harder to keep. A second web UI would
duplicate the one the box already serves and would not see a controller
that is only on USB. Electron would sit outside the Python library WIMS
can import.

## Consequences

- Protocol additions for the PC tool (`schema`, `id`, the `OK`/`ERR`
  trailer, restore ended by a lone dot, the USB identity, and
  `_rotatorctl._tcp`) are in `docs/design/configuration.md`. They keep
  the GS-232 coexistence rule from ADR 0015.
- The provisional USB VID `0x1209` and PID `0xF407` are a contract to
  replace when an assignment exists. They are not a completed pid.codes
  registration.
- The packed settings blob in the firmware tree is still the small
  stub. The `schema` document is the shape it grows into.
- The KiCad files are not edited by this decision.
