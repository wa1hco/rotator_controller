# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Byte transports for the console: TCP and a serial port.

A transport moves lines. It does not know which lines are commands.
"""

from __future__ import annotations

import socket
from typing import Protocol


class LineTransport(Protocol):
    def write_lines(self, lines: list[str]) -> None: ...

    def read_line(self, timeout: float) -> str: ...

    def close(self) -> None: ...


class TransportError(OSError):
    pass


class TcpTransport:
    def __init__(self, host: str, port: int, timeout: float = 3.0) -> None:
        self._timeout = timeout
        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._buf = b""

    def write_lines(self, lines: list[str]) -> None:
        payload = "".join(line + "\n" for line in lines).encode("utf-8")
        self._sock.sendall(payload)

    def read_line(self, timeout: float) -> str:
        self._sock.settimeout(timeout)
        while b"\n" not in self._buf:
            try:
                chunk = self._sock.recv(4096)
            except socket.timeout as exc:
                raise TransportError("timed out waiting for a reply") from exc
            if not chunk:
                raise TransportError("connection closed")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode("utf-8", "replace").strip("\r")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


class SerialTransport:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 3.0) -> None:
        import serial

        self._timeout = timeout
        self._ser = serial.Serial(port, baudrate=baud, timeout=timeout)

    def write_lines(self, lines: list[str]) -> None:
        payload = "".join(line + "\n" for line in lines).encode("utf-8")
        self._ser.write(payload)
        self._ser.flush()

    def read_line(self, timeout: float) -> str:
        self._ser.timeout = timeout
        raw = self._ser.readline()
        if not raw:
            raise TransportError("timed out waiting for a reply")
        return raw.decode("utf-8", "replace").strip("\r\n")

    def close(self) -> None:
        self._ser.close()


def open_target(target: str, timeout: float = 3.0) -> LineTransport:
    """Open ``tcp://host:port`` or ``serial://<path>``."""
    if target.startswith("tcp://"):
        hostport = target.removeprefix("tcp://")
        if ":" not in hostport:
            raise TransportError("tcp target needs host:port")
        host, port_text = hostport.rsplit(":", 1)
        return TcpTransport(host, int(port_text), timeout=timeout)
    if target.startswith("serial://"):
        path = target.removeprefix("serial://")
        return SerialTransport(path, timeout=timeout)
    raise TransportError("target must start with tcp:// or serial://")
