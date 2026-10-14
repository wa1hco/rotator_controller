# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from rotatorctl.discovery import USB_PID, USB_VID, ControllerInfo, Endpoint
from rotatorctl.protocol import ConsoleClient
from rotatorctl.sim import SimInstance
from rotatorctl.transport import open_target
from rotatorctl_gui.server import start_server, static_dir
from rotatorctl_gui.state import AppState, describe_controller


@pytest.fixture
def live(tmp_path, monkeypatch):
    monkeypatch.setenv("ROTATOR_CONFIG_DIR", str(tmp_path))
    state = AppState(idle_seconds=0)
    state.token = "test"
    running = start_server(state, idle_seconds=0)
    try:
        yield running
    finally:
        running.stop()


def call(live, method: str, path: str, payload: dict | None = None, raw: bool = False):
    url = live.url + path.lstrip("/")
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"content-type": "application/json"} if data is not None else {}
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status = exc.code
    if raw:
        return status, body.decode()
    if not body:
        return status, {}
    return status, json.loads(body.decode())


def test_static_pages_stay_under_a_small_gzip_budget() -> None:
    total = 0
    for path in static_dir().iterdir():
        if path.suffix in {".html", ".css", ".js"}:
            total += len(gzip.compress(path.read_bytes(), 9))
    assert total < 64 * 1024


def test_catalog_pages_and_offline_preset(live) -> None:
    status, catalog = call(live, "GET", "api/catalog")
    assert status == 200
    assert len(catalog["presets"]) == 39
    row = next(item for item in catalog["presets"] if item["id"] == "yaesu-g-450a")
    assert row["family"] == "Yaesu-AC-pot"
    assert "sensor.ohms" in row["unverified"]
    assert "motor.volts" in row["unverified"]
    assert any(item["value"] == "single_ended_pot" for item in row["settings"])
    alias = next(item for item in catalog["presets"] if item["id"] == "alias-telex-dcu")
    assert alias["can_apply"] is False
    assert "hygain-ham-iv" in alias["alias_of"]
    assert not any(item["id"] == "not-a-rotor" for item in catalog["presets"])
    status, pages = call(live, "GET", "api/pages")
    assert status == 200
    by_id = {page["id"]: page for page in pages["pages"]}
    assert by_id["park"]["fields"][-1] == "preset.6.el"
    assert "az.center" in by_id["limits"]["fields"]
    assert by_id["controllers"]["title"] == "Controllers"
    status, missing = call(live, "POST", "api/preset/apply", {"id": "alias-telex-dcu"})
    assert status == 400
    status, doc = call(live, "POST", "api/preset/apply", {"id": "yaesu-g-450a"})
    assert status == 200
    assert doc["preset"] == "yaesu-g-450a"
    assert doc["settings"]["az.sensor"] == "single_ended_pot"
    assert doc["axes"] == {"azimuth": True, "elevation": False}
    assert doc["dirty"] is True
    status, doc = call(live, "POST", "api/override", {"name": "az.overlap_deg", "value": "100"})
    assert doc["overrides"]["az.overlap_deg"] == "100"
    status, preview = call(live, "POST", "api/document/preview", {})
    assert any(change["name"] == "az.overlap_deg" and change["after"] == "100" for change in preview["changes"])
    status, saved = call(live, "POST", "api/document/save", {"name": "station.rotcfg"})
    assert saved["dirty"] is False
    assert saved["filename"] == "station.rotcfg"
    status, both = call(live, "POST", "api/preset/apply", {"id": "yaesu-g-5500"})
    assert both["settings"]["el.travel_max_deg"] == "180"
    assert both["axes"]["elevation"] is True


def test_save_lands_in_the_config_folder(live, tmp_path: Path) -> None:
    call(live, "POST", "api/preset/apply", {"id": "yaesu-g-450a"})
    status, _doc = call(live, "POST", "api/document/save", {"name": "station.rotcfg"})
    assert status == 200
    written = tmp_path / "station.rotcfg"
    assert written.is_file()
    assert written.read_text(encoding="utf-8").startswith("# rotator-config 1\n")
    status, opened = call(live, "POST", "api/document/new", {})
    assert opened["preset"] == ""
    status, loaded = call(live, "POST", "api/files/open", {"name": "station.rotcfg"})
    assert loaded["preset"] == "yaesu-g-450a"
    assert loaded["settings"]["az.sensor"] == "single_ended_pot"


def test_controller_list_text() -> None:
    text = describe_controller(
        ControllerInfo(
            serial="RC-SIM-USB",
            name="Bench",
            firmware="0.1.0-sim",
            axes="az",
            vid=USB_VID,
            pid=USB_PID,
            endpoints=[Endpoint("usb", "serial:///dev/pts/9", "USB CDC")],
        )
    )
    assert "USB 1209:f407" in text
    assert "Bench" in text
    merged = describe_controller(
        ControllerInfo(
            serial="SAME",
            name="tower",
            vid=USB_VID,
            pid=USB_PID,
            endpoints=[
                Endpoint("usb", "serial:///dev/ttyACM0"),
                Endpoint("tcp", "tcp://10.0.0.5:4533"),
            ],
        )
    )
    assert "USB 1209:f407" in merged
    assert "network" in merged
    assert "tower" in merged


def test_connect_validates_confirms_and_saves(live, presets) -> None:
    inst = SimInstance(serial="RC-GUI-1", name="Alpha", presets=presets, tcp=True, pty=False, mdns=False)
    inst.start()
    try:
        status, added = call(live, "POST", "api/controllers/add", {"kind": "tcp", "host": "127.0.0.1", "port": inst.port})
        assert status == 200
        assert any(
            "127.0.0.1" in item["text"] and any(ep["kind"] == "tcp" for ep in item["endpoints"])
            for item in added["controllers"]
        )
        status, device = call(live, "POST", "api/controllers/connect", {"target": inst.tcp_target()})
        assert status == 200
        assert device["connected"] is True
        assert device["settings"]["net.hostname"] == "Alpha"
        assert device["dirty"] is False
        status, bad = call(live, "POST", "api/device/edit", {"name": "net.address", "value": "not-an-ip"})
        assert "IPv4" in bad["errors"]["net.address"]
        assert bad["dirty"] is True
        status, blocked = call(live, "POST", "api/device/preview", {})
        assert blocked["blocked"] is True
        call(live, "POST", "api/device/edit", {"name": "net.address", "value": "10.1.1.10"})
        call(live, "POST", "api/device/edit", {"name": "net.hostname", "value": "alpha-2"})
        call(live, "POST", "api/device/edit", {"name": "safety.dead_time_ms", "value": "750"})
        status, preview = call(live, "POST", "api/device/preview", {})
        names = {change["name"] for change in preview["changes"]}
        assert "net.hostname" in names
        assert "safety.dead_time_ms" in names
        assert "net.hostname" in preview["note"]
        assert "dfu-util" in " ".join(call(live, "GET", "api/boot")[1]["dfu"])
        assert "0x08000000" in " ".join(call(live, "GET", "api/boot")[1]["dfu"])
        status, saved = call(live, "POST", "api/device/save", {})
        assert status == 200
        assert saved["dirty"] is False
        probe = ConsoleClient(open_target(inst.tcp_target()))
        try:
            assert probe.get("net.hostname") == "alpha-2"
            assert probe.get("safety.dead_time_ms") == "750"
        finally:
            probe.close()
    finally:
        inst.stop()


def test_copy_dirties_only_the_editor(live, presets) -> None:
    left = SimInstance(serial="RC-A", name="Alpha", presets=presets, tcp=True, mdns=False)
    right = SimInstance(serial="RC-B", name="Beta", presets=presets, tcp=True, mdns=False)
    left.start()
    right.start()
    try:
        call(live, "POST", "api/controllers/connect", {"target": left.tcp_target()})
        status, copied = call(live, "POST", "api/device/copy", {"target": right.tcp_target()})
        assert status == 200
        assert copied["settings"]["net.hostname"] == "Beta"
        assert copied["dirty"] is True
        probe = ConsoleClient(open_target(left.tcp_target()))
        try:
            assert probe.get("net.hostname") == "Alpha"
        finally:
            probe.close()
    finally:
        left.stop()
        right.stop()


def test_backup_and_restore(live, presets) -> None:
    inst = SimInstance(serial="RC-GUI-2", name="Gamma", presets=presets, tcp=True, mdns=False)
    inst.start()
    try:
        call(live, "POST", "api/controllers/connect", {"target": inst.tcp_target()})
        call(live, "POST", "api/device/edit", {"name": "ui.log_level", "value": "debug"})
        status, text = call(live, "POST", "api/device/backup", {}, raw=True)
        assert status == 200
        assert text.startswith("# rotator-settings 1\n")
        assert "ui.log_level = debug" in text
        call(live, "POST", "api/device/edit", {"name": "ui.log_level", "value": "warn"})
        status, preview = call(live, "POST", "api/device/restore", {"text": text, "apply": False})
        assert any(change["name"] == "ui.log_level" and change["after"] == "debug" for change in preview["changes"])
        status, restored = call(live, "POST", "api/device/restore", {"text": text, "apply": True})
        assert restored["settings"]["ui.log_level"] == "debug"
        probe = ConsoleClient(open_target(inst.tcp_target()))
        try:
            assert probe.get("ui.log_level") == "debug"
        finally:
            probe.close()
    finally:
        inst.stop()


def test_boot_advertises_phase_menus(live) -> None:
    status, boot = call(live, "GET", "api/boot")
    assert status == 200
    assert boot["role"] == "pc"
    assert boot["api"] == 1
    assert "stop" in boot["operate"]
    assert boot["stop"] == "S"
    assert boot["features"]["offline"] is True
