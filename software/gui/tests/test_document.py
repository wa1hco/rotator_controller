# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json

import pytest

from rotatorctl.document import SettingsDocument, SettingsError, format_value
from rotatorctl.protocol import schema_json
from rotatorctl.schema import Schema, SettingSpec, SettingType, default_schema


def test_canonical_values() -> None:
    schema = default_schema()
    travel = schema.get("az.travel_max_deg")
    assert travel is not None
    assert format_value(travel, "450.0") == "450"
    assert format_value(travel, "-0") == "0"
    host = schema.get("net.hostname")
    assert host is not None
    assert format_value(host, "a") == "a"
    assert format_value(host, "rot-az") == "rot-az"
    address = schema.get("net.address")
    assert address is not None
    assert format_value(address, "10.0.0.1") == "10.0.0.1"
    expect_reject(host, "a-")
    expect_reject(host, "bad host")
    expect_reject(address, "192.168.1.256")
    flag = schema.get("net.dhcp")
    assert flag is not None
    expect_reject(flag, "True")


def test_range_and_enum() -> None:
    schema = default_schema()
    port = schema.get("ports.tcp")
    assert port is not None
    expect_reject(port, "0")
    level = schema.get("ui.log_level")
    assert level is not None
    expect_reject(level, "trace")
    assert format_value(level, "debug") == "debug"


def test_replace_is_atomic() -> None:
    schema = default_schema()
    doc = SettingsDocument(schema)
    doc.set("net.hostname", "other")
    before = doc.snapshot()
    writable = [f"{spec.name} = {before[spec.name]}" for spec in schema.settings if not spec.readonly]
    with pytest.raises(SettingsError) as exc:
        doc.replace_from_lines(["net.hostname = zz"])
    assert exc.value.code == "missing"
    assert doc.snapshot() == before
    with pytest.raises(SettingsError) as unknown:
        doc.replace_from_lines([*writable, "no.such = 1"])
    assert unknown.value.code == "unknown"
    assert doc.snapshot() == before
    original = [f"{spec.name} = {spec.default}" for spec in schema.settings if not spec.readonly]
    doc.replace_from_lines(original)
    assert doc.get("net.hostname") == "rotator"


def test_schema_mismatch_and_readonly() -> None:
    schema = default_schema(serial="RC-1")
    doc = SettingsDocument(schema)
    lines = [f"{spec.name} = {doc.get(spec.name)}" for spec in schema.settings]
    lines = [line.replace("sys.schema = 1", "sys.schema = 2") for line in lines]
    with pytest.raises(SettingsError) as exc:
        doc.replace_from_lines(lines)
    assert exc.value.code == "schema"
    assert doc.get("sys.schema") == "1"
    changed = [line.replace("sys.serial = RC-1", "sys.serial = RC-2") for line in [
        f"{spec.name} = {doc.get(spec.name)}" for spec in schema.settings
    ]]
    with pytest.raises(SettingsError) as readonly:
        doc.replace_from_lines(changed)
    assert readonly.value.code == "readonly"
    assert doc.get("sys.serial") == "RC-1"


def test_schema_json_roundtrip() -> None:
    schema = default_schema()
    extra = SettingSpec(name="rf.gain", type=SettingType.INT, default="0", min=0, max=10, help="Added later")
    schema = Schema(version=1, settings=[*schema.settings, extra])
    again = Schema.model_validate(json.loads(schema_json(schema)))
    assert again.get("rf.gain") is not None
    assert again.get("ports.tcp") is not None
    assert again.get("ports.tcp").reboot is True
    assert again.get("az.present").readonly is True


def test_calibration_map_token() -> None:
    schema = default_schema()
    spec = schema.get("az.cal.map")
    assert spec is not None
    assert format_value(spec, "none") == "none"
    assert format_value(spec, "0:0,180:181") == "0:0,180:181"
    expect_reject(spec, "0:0")
    expect_reject(spec, "0:0, 180:181")


def expect_reject(spec: SettingSpec, raw: str) -> None:
    try:
        format_value(spec, raw)
    except SettingsError:
        return
    raise AssertionError(f"{spec.name} accepted {raw!r}")
