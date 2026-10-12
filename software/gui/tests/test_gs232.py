# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import socket

import pytest

from rotatorctl.gs232 import parse_gs232
from rotatorctl.protocol import ConsoleClient
from rotatorctl.transport import open_target


def test_parser_matches_the_firmware_cases() -> None:
    assert parse_gs232("M270\r\n").azimuth_deg == 270
    assert parse_gs232("c2").verb == "query"
    assert parse_gs232("C").verb == "query"
    assert parse_gs232("S").verb == "stop"
    assert parse_gs232("A").verb == "stop"
    assert parse_gs232("M") is None
    assert parse_gs232("W180 045") is None
    assert parse_gs232("") is None
    assert parse_gs232("status") is None
    assert parse_gs232("save") is None
    assert parse_gs232("SCHEMA") is None


def _recv_until(sock: socket.socket, marker: bytes, timeout: float = 2.0) -> bytes:
    sock.settimeout(timeout)
    buf = b""
    while marker not in buf:
        chunk = sock.recv(4096)
        assert chunk
        buf += chunk
    return buf


def test_stop_is_silent_and_status_still_works(sim) -> None:
    host, port_text = sim.tcp_target().removeprefix("tcp://").rsplit(":", 1)
    sock = socket.create_connection((host, int(port_text)), timeout=2)
    try:
        sock.sendall(b"SCHEMA\n")
        sock.settimeout(0.3)
        with pytest.raises(socket.timeout):
            sock.recv(64)
        sock.sendall(b"S\nstatus\n")
        body = _recv_until(sock, b"OK\n")
        assert b"ERR" not in body
        assert b"az.motion = stopped" in body
        sock.sendall(b"M270\nC2\n")
        sock.settimeout(2)
        line = b""
        while b"\n" not in line:
            line += sock.recv(64)
        assert line.splitlines()[0] == b"+0270"
        sock.sendall(b"s\n")
        sock.settimeout(0.3)
        with pytest.raises(socket.timeout):
            sock.recv(64)
    finally:
        sock.close()
    client = ConsoleClient(open_target(sim.tcp_target()))
    try:
        assert client.get("sys.serial") == "RC-TEST-0001"
    finally:
        client.close()
