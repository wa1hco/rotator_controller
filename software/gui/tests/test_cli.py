# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from rotatorctl.cli import main
from rotatorctl.sim import SimInstance


def test_cli_get_set_dump_restore(sim, capsys, tmp_path) -> None:
    target = sim.tcp_target()
    assert main(["get", "--target", target, "ui.log_level"]) == 0
    assert capsys.readouterr().out.strip() == "info"
    assert main(["set", "--target", target, "ui.log_level", "debug"]) == 0
    capsys.readouterr()
    assert main(["get", "--target", target, "ui.log_level"]) == 0
    assert capsys.readouterr().out.strip() == "debug"
    assert main(["dump", "--target", target]) == 0
    text = capsys.readouterr().out
    path = tmp_path / "rotator-settings.txt"
    path.write_text(text, encoding="utf-8")
    assert "ui.log_level = debug" in text
    assert main(["set", "--target", target, "ui.log_level", "warn"]) == 0
    capsys.readouterr()
    assert main(["restore", "--target", target, str(path)]) == 0
    capsys.readouterr()
    assert main(["get", "--target", target, "ui.log_level"]) == 0
    assert capsys.readouterr().out.strip() == "debug"
    assert main(["save", "--target", target]) == 0


def test_cli_list_returns(capsys) -> None:
    assert main(["list", "--timeout", "0.2"]) == 0
    capsys.readouterr()


def test_pty_transport(presets) -> None:
    inst = SimInstance(serial="RC-PTY-1", name="Bench", presets=presets, tcp=False, pty=True, mdns=False)
    inst.start()
    try:
        from rotatorctl.protocol import ConsoleClient
        from rotatorctl.transport import open_target

        client = ConsoleClient(open_target(inst.serial_target()))
        try:
            assert client.get("sys.serial") == "RC-PTY-1"
            client.set("net.hostname", "bench")
            assert client.get("net.hostname") == "bench"
        finally:
            client.close()
    finally:
        inst.stop()
