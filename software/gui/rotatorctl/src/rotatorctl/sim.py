# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Controller simulator: console protocol on TCP and on a pty.

``software/sim`` is the C++ K3NG sandbox. This process speaks the console
and GS-232 grammar in ``docs/design/configuration.md``, so it lives in the
installable library. ``software/gui/sim`` is a thin launcher.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import threading
import time
import tty

from rotatorctl.document import SettingsDocument, SettingsError
from rotatorctl.gs232 import parse_gs232
from rotatorctl.presets import Preset, can_apply, load_presets, settings_from_preset
from rotatorctl.protocol import schema_json
from rotatorctl.schema import Schema, default_schema

_VERBS = frozenset(
    {
        "help",
        "status",
        "get",
        "set",
        "save",
        "preset",
        "calibrate",
        "log",
        "dump",
        "reboot",
        "schema",
        "id",
        "restore",
        "upgrade",
    }
)

_HELP = [
    "help",
    "status",
    "id",
    "schema",
    "get <name>",
    "set <name> <value>",
    "save",
    "dump",
    "restore",
    "preset list",
    "preset apply <model>",
    "log",
    "log level <error|warn|info|debug>",
    "reboot",
    "calibrate <az|el>",
    "upgrade",
    "GS-232: A S Mnnn C C2",
]


def _ok(body: list[str] | None = None) -> list[str]:
    return [*(body or []), "OK"]


def _err(code: str, message: str) -> list[str]:
    return [f"ERR {code} {message}"]


class Engine:
    """One controller's settings, headings, and saved copy."""

    def __init__(
        self,
        *,
        serial: str,
        name: str,
        firmware: str = "0.1.0-sim",
        board: str = "f407-v1",
        azimuth: bool = True,
        elevation: bool = False,
        presets: tuple[Preset, ...] | list[Preset] = (),
    ) -> None:
        self.schema: Schema = default_schema(
            serial=serial,
            hostname=name,
            firmware=firmware,
            board=board,
            azimuth=azimuth,
            elevation=elevation,
        )
        self.doc = SettingsDocument(self.schema)
        self.saved = self.doc.snapshot()
        self.heading_az = 0
        self.heading_el = 0
        self.presets = {preset.id: preset for preset in presets}
        self.lock = threading.Lock()

    def reply(self, line: str) -> list[str]:
        with self.lock:
            return self._reply(line)

    def restore(self, lines: list[str]) -> list[str]:
        with self.lock:
            try:
                self.doc.replace_from_lines(lines)
            except SettingsError as exc:
                return _err(exc.code, exc.message)
            self.saved = self.doc.snapshot()
            return _ok()

    def _reply(self, line: str) -> list[str]:
        gs = parse_gs232(line)
        if gs is not None:
            if gs.verb == "stop":
                return []
            if gs.verb == "query":
                azimuth = self.heading_az % 1000
                return [f"+0{azimuth:03d}"]
            self.heading_az = gs.azimuth_deg
            return []
        text = line.strip()
        if not text:
            return []
        parts = text.split()
        verb = parts[0]
        if verb not in _VERBS:
            return []
        try:
            return self._verb(verb, parts)
        except SettingsError as exc:
            return _err(exc.code, exc.message)

    def _verb(self, verb: str, parts: list[str]) -> list[str]:
        if verb == "help" and len(parts) == 1:
            return _ok(list(_HELP))
        if verb == "status" and len(parts) == 1:
            return _ok(
                [
                    f"az.heading = {self.heading_az}",
                    "az.motion = stopped",
                    f"el.heading = {self.heading_el}",
                    "el.motion = stopped",
                    "faults = none",
                ]
            )
        if verb == "schema" and len(parts) == 1:
            return _ok([schema_json(self.schema)])
        if verb == "id" and len(parts) == 1:
            present_el = self.doc.get("el.present") == "true"
            present_az = self.doc.get("az.present") == "true"
            if present_az and present_el:
                axes = "az+el"
            elif present_el:
                axes = "el"
            elif present_az:
                axes = "az"
            else:
                axes = "none"
            payload = {
                "serial": self.doc.get("sys.serial"),
                "name": self.doc.get("net.hostname"),
                "fw": self.doc.get("sys.firmware"),
                "axes": axes,
                "schema": int(self.doc.get("sys.schema")),
            }
            return _ok([json.dumps(payload, separators=(",", ":"))])
        if verb == "get" and len(parts) == 2:
            name = parts[1]
            return _ok([f"{name} = {self.doc.get(name)}"])
        if verb == "set" and len(parts) == 3:
            self.doc.set(parts[1], parts[2])
            return _ok()
        if verb == "save" and len(parts) == 1:
            self.saved = self.doc.snapshot()
            return _ok()
        if verb == "dump" and len(parts) == 1:
            return _ok(self.doc.to_ini().splitlines())
        if verb == "reboot" and len(parts) == 1:
            self.doc.values = dict(self.saved)
            return _ok()
        if verb == "log" and len(parts) == 1:
            return _ok(["(no entries)"])
        if verb == "log" and len(parts) == 3 and parts[1] == "level":
            self.doc.set("ui.log_level", parts[2])
            return _ok()
        if verb == "preset" and len(parts) == 2 and parts[1] == "list":
            names = sorted(preset.id for preset in self.presets.values() if can_apply(preset))
            return _ok(names)
        if verb == "preset" and len(parts) == 3 and parts[1] == "apply":
            self._apply(parts[2])
            return _ok()
        if verb in ("calibrate", "upgrade"):
            return _err("unsupported", f"{verb} is not implemented")
        if verb == "restore":
            return _err("usage", "restore is followed by the file and a line with only a dot")
        return _err("usage", f"unsupported {verb} arguments")

    def _apply(self, ident: str) -> None:
        preset = self.presets.get(ident)
        if preset is None or preset.support == "no" or preset.support == "later":
            raise SettingsError("unknown", f"unknown preset {ident}")
        if preset.support == "alias":
            raise SettingsError("alias", f"{ident} is an alias")
        if not can_apply(preset):
            raise SettingsError("unknown", f"unknown preset {ident}")
        updates = settings_from_preset(preset)
        trial = SettingsDocument(self.schema, self.doc.snapshot())
        for name, value in updates.items():
            trial.set(name, value)
        self.doc.values = trial.values


class Session:
    """One connection. ``restore`` buffers lines until a lone dot."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._restoring = False
        self._buf: list[str] = []

    def handle(self, line: str) -> list[str]:
        text = line.strip()
        if self._restoring:
            if text == ".":
                self._restoring = False
                lines = self._buf
                self._buf = []
                return self.engine.restore(lines)
            self._buf.append(line)
            return []
        if text == "restore":
            self._restoring = True
            self._buf = []
            return []
        return self.engine.reply(line)


class SimInstance:
    """TCP listener, optional pty, optional mDNS advertisement."""

    def __init__(
        self,
        *,
        serial: str,
        name: str,
        firmware: str = "0.1.0-sim",
        azimuth: bool = True,
        elevation: bool = False,
        presets: tuple[Preset, ...] | list[Preset] | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
        tcp: bool = True,
        pty: bool = False,
        mdns: bool = False,
    ) -> None:
        if presets is None:
            presets = load_presets()
        self.engine = Engine(
            serial=serial,
            name=name,
            firmware=firmware,
            azimuth=azimuth,
            elevation=elevation,
            presets=presets,
        )
        self.serial = serial
        self.name = name
        self.host = host
        self.firmware = firmware
        self._tcp = tcp
        self._want_pty = pty
        self._want_mdns = mdns
        self._port = port
        self._server: socket.socket | None = None
        self._master: int | None = None
        self._slave: int | None = None
        self._pty_path = ""
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._zc: object | None = None
        self._info: object | None = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._stop.clear()
        if self._tcp:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self._port))
            sock.listen(8)
            sock.settimeout(0.2)
            self._server = sock
            self._port = sock.getsockname()[1]
            self._spawn(self._accept_loop)
        if self._want_pty:
            self._open_pty()
            self._spawn(self._pty_loop)
        if self._want_mdns:
            self._advertise()
        self._started = True

    def stop(self) -> None:
        self._stop.set()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
        if self._master is not None:
            os.close(self._master)
            self._master = None
        if self._slave is not None:
            os.close(self._slave)
            self._slave = None
        if self._zc is not None and self._info is not None:
            try:
                self._zc.unregister_service(self._info)  # type: ignore[attr-defined]
            except Exception:
                pass
            self._zc.close()  # type: ignore[attr-defined]
            self._zc = None
        for thread in list(self._threads):
            thread.join(timeout=1.0)
        self._threads.clear()
        self._started = False

    def __enter__(self) -> SimInstance:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    @property
    def port(self) -> int:
        return self._port

    def tcp_target(self) -> str:
        return f"tcp://{self.host}:{self._port}"

    def serial_target(self) -> str:
        if not self._pty_path:
            return ""
        return f"serial://{self._pty_path}"

    @property
    def pty_path(self) -> str:
        return self._pty_path

    def _spawn(self, target: object) -> None:
        thread = threading.Thread(target=target, daemon=True)  # type: ignore[arg-type]
        thread.start()
        self._threads.append(thread)

    def _accept_loop(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                conn, _addr = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._spawn(lambda conn=conn: self._tcp_client(conn))

    def _tcp_client(self, conn: socket.socket) -> None:
        session = Session(self.engine)
        buf = b""
        conn.settimeout(0.2)
        try:
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    replies = session.handle(raw.decode("utf-8", "replace"))
                    if replies:
                        conn.sendall(("\n".join(replies) + "\n").encode())
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _open_pty(self) -> None:
        master, slave = os.openpty()
        tty.setraw(master)
        tty.setraw(slave)
        os.set_blocking(master, False)
        self._master = master
        self._slave = slave
        self._pty_path = os.ttyname(slave)

    def _pty_loop(self) -> None:
        assert self._master is not None
        session = Session(self.engine)
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = os.read(self._master, 4096)
            except BlockingIOError:
                time.sleep(0.02)
                continue
            except OSError:
                break
            if not chunk:
                time.sleep(0.02)
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                replies = session.handle(raw.decode("utf-8", "replace"))
                if replies:
                    _write_all(self._master, ("\n".join(replies) + "\n").encode())

    def _advertise(self) -> None:
        from zeroconf import ServiceInfo, Zeroconf

        present_el = self.engine.doc.get("el.present") == "true"
        axes = "az+el" if present_el else "az"
        props = {
            "id": self.serial,
            "name": self.name,
            "fw": self.firmware,
            "axes": axes,
            "schema": "1",
        }
        info = ServiceInfo(
            "_rotatorctl._tcp.local.",
            f"{self.serial}._rotatorctl._tcp.local.",
            addresses=[socket.inet_aton("127.0.0.1")],
            port=self._port,
            properties=props,
            server=f"{self.serial.lower()}.local.",
        )
        zc = Zeroconf(interfaces=["127.0.0.1"])
        zc.register_service(info)
        self._zc = zc
        self._info = info


def demo_pair() -> list[SimInstance]:
    """One USB pty controller and one networked controller, for screenshots and manual runs."""
    presets = load_presets()
    return [
        SimInstance(
            serial="RC-SIM-USB",
            name="Bench",
            azimuth=True,
            elevation=False,
            presets=presets,
            tcp=False,
            pty=True,
            mdns=False,
        ),
        SimInstance(
            serial="RC-SIM-NET",
            name="Tower",
            azimuth=True,
            elevation=True,
            presets=presets,
            tcp=True,
            pty=False,
            mdns=True,
        ),
    ]


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        try:
            count = os.write(fd, view)
        except BlockingIOError:
            time.sleep(0.01)
            continue
        view = view[count:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rotatorctl-sim")
    parser.add_argument("-n", "--count", type=int, default=1, help="How many controllers to run")
    parser.add_argument("--base-port", type=int, default=4533)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--pty", action="store_true", help="Open a pty on the first controller")
    parser.add_argument("--mdns", action="store_true", help="Advertise _rotatorctl._tcp")
    parser.add_argument("--presets", default="", help="Override rotor-presets.yaml")
    args = parser.parse_args(argv)
    presets = load_presets(args.presets or None)
    fleet: list[SimInstance] = []
    for index in range(args.count):
        inst = SimInstance(
            serial=f"RC-SIM-{index + 1:04d}",
            name=f"rotator-{index + 1}",
            presets=presets,
            host=args.host,
            port=args.base_port + index,
            tcp=True,
            pty=args.pty and index == 0,
            mdns=args.mdns,
            azimuth=True,
            elevation=index % 2 == 1,
        )
        inst.start()
        fleet.append(inst)
        print(f"{inst.serial}\t{inst.tcp_target()}\t{inst.serial_target() or '-'}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        for inst in fleet:
            inst.stop()
    return 0
