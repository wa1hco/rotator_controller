# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from rotatorctl.presets import settings_from_preset
from rotatorctl.protocol import CommandError


def test_library_does_not_import_qt() -> None:
    import rotatorctl

    root = Path(rotatorctl.__file__).resolve().parent
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name.startswith("PySide6") or name.startswith("PyQt") for name in names)


def test_get_set_save_reboot(client) -> None:
    assert client.get("sys.serial") == "RC-TEST-0001"
    assert client.get("safety.dead_time_ms") == "500"
    client.set("safety.dead_time_ms", "800")
    assert client.get("safety.dead_time_ms") == "800"
    client.command("reboot")
    assert client.get("safety.dead_time_ms") == "500"
    client.set("safety.dead_time_ms", "800")
    client.save()
    client.command("reboot")
    assert client.get("safety.dead_time_ms") == "800"


def test_schema_and_id(client) -> None:
    schema = client.schema()
    assert schema.version == 1
    assert schema.get("ports.tcp") is not None
    assert schema.get("net.hostname").reboot is True
    ident = client.identity()
    assert ident["serial"] == "RC-TEST-0001"
    assert ident["name"] == "Test"
    assert ident["axes"] == "az"
    assert ident["schema"] == 1


def test_dump_restore_roundtrip(client) -> None:
    text = client.dump_text()
    assert text.startswith("# rotator-settings 1\n")
    client.set("ui.log_level", "debug")
    client.restore_text(text)
    assert client.get("ui.log_level") == "info"
    client.command("reboot")
    assert client.get("ui.log_level") == "info"


def test_restore_rejects_bad_files(client) -> None:
    with pytest.raises(CommandError) as dotted:
        client.restore_text("# comment\n.\n")
    assert dotted.value.code == "invalid"
    before = client.get("net.hostname")
    with pytest.raises(CommandError) as missing:
        client.restore_text("# rotator-settings 1\nnet.hostname = zz\n")
    assert missing.value.code == "missing"
    assert client.get("net.hostname") == before
    dumped = client.dump_text().replace("sys.schema = 1", "sys.schema = 2")
    with pytest.raises(CommandError) as schema:
        client.restore_text(dumped)
    assert schema.value.code == "schema"
    with pytest.raises(CommandError) as readonly:
        client.set("az.present", "false")
    assert readonly.value.code == "readonly"


def test_preset_apply_matches_the_library(client, presets) -> None:
    preset = next(item for item in presets if item.id == "yaesu-g-450a")
    client.preset_apply(preset.id)
    for name, value in settings_from_preset(preset).items():
        assert client.get(name) == value
    assert client.get("net.hostname") == "Test"
    assert client.get("az.present") == "true"
    client.command("reboot")
    assert client.get("az.sensor") == "dual_end_pot"
    client.preset_apply("yaesu-g-5500")
    assert client.get("el.travel_max_deg") == "180"
    assert client.get("el.present") == "false"
    names = client.preset_list()
    assert "hygain-ham-iv" in names
    assert "hygain-ar-40" not in names
    assert "alias-telex-dcu" not in names
    with pytest.raises(CommandError) as alias:
        client.preset_apply("alias-telex-dcu")
    assert alias.value.code == "alias"


def test_reserved_verbs(client) -> None:
    with pytest.raises(CommandError) as calibrate:
        client.command("calibrate az")
    assert calibrate.value.code == "unsupported"
    with pytest.raises(CommandError) as upgrade:
        client.command("upgrade")
    assert upgrade.value.code == "unsupported"


def test_dump_includes_header_and_save_status(client) -> None:
    values = client.dump_values()
    assert values["sys.schema"] == "1"
    status = client.status()
    assert status["az.motion"] == "stopped"
    assert status["faults"] == "none"


def test_inventory_settings_round_trip_on_the_simulator(client) -> None:
    schema = client.schema()
    for name in (
        "az.center",
        "az.coast_deg",
        "az.cal.map",
        "sys.drive",
        "park.idle_min",
        "preset.6.el",
        "ports.rotctld",
        "ports.easycom",
        "ports.dcu1",
        "net.admin_lock",
        "safety.stall_timeout_s",
        "safety.stall_deg",
    ):
        assert schema.get(name) is not None
    sensor = schema.get("az.sensor")
    assert sensor is not None
    assert "hh12_as5045" in sensor.enum
    assert "incremental_encoder" in sensor.enum
    assert "compass" not in sensor.enum
    client.set("az.center", "south")
    client.set("az.cal.map", "0:0,180:181,450:448")
    client.set("park.idle_min", "15")
    assert client.get("az.center") == "south"
    assert "az.center = south" in client.dump_text()
    with pytest.raises(CommandError):
        client.set("az.cal.map", "nope")
    client.command("reboot")
    assert client.get("az.center") == "north"
