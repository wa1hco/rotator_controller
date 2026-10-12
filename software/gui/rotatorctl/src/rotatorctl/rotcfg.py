# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Offline configuration file (.rotcfg).

The file is YAML, or JSON when the text starts with ``{``. It holds the
preset the operator picked, any custom overrides, and the full settings
tree so the same file can later be pushed to a controller.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from rotatorctl.document import SettingsDocument, SettingsError
from rotatorctl.schema import Schema, default_schema


@dataclass
class RotConfig:
    schema: Schema
    document: SettingsDocument
    preset: str = ""
    overrides: dict[str, str] = field(default_factory=dict)
    path: str = ""

    @property
    def name(self) -> str:
        return self.document.get("net.hostname")


def new_config(
    *,
    hostname: str = "station",
    azimuth: bool = True,
    elevation: bool = True,
) -> RotConfig:
    schema = default_schema(hostname=hostname, azimuth=azimuth, elevation=elevation)
    return RotConfig(schema=schema, document=SettingsDocument(schema))


def dumps(config: RotConfig) -> str:
    payload = {
        "format": "rotcfg",
        "version": 1,
        "preset": config.preset,
        "name": config.name,
        "overrides": dict(config.overrides),
        "settings": config.document.snapshot(),
    }
    import yaml

    body = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    return f"# rotator-config 1\n{body}"


def loads(text: str, schema: Schema | None = None) -> RotConfig:
    stripped = text.lstrip()
    if stripped.startswith("{"):
        data = json.loads(text)
    else:
        import yaml

        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SettingsError("invalid", "configuration file is empty")
    if data.get("format") not in (None, "rotcfg"):
        raise SettingsError("invalid", "configuration file is not a rotcfg document")
    version = data.get("version", 1)
    if version != 1:
        raise SettingsError("schema", "rotcfg version is not 1")
    schema = schema or default_schema()
    document = SettingsDocument(schema)
    settings = data.get("settings") or {}
    if not isinstance(settings, dict):
        raise SettingsError("invalid", "settings must be a map")
    for name, raw in settings.items():
        if schema.get(str(name)) is None:
            raise SettingsError("unknown", f"unknown setting {name}")
        document.set(str(name), _as_text(raw), force=True)
    overrides_raw = data.get("overrides") or {}
    if not isinstance(overrides_raw, dict):
        raise SettingsError("invalid", "overrides must be a map")
    overrides = {str(name): _as_text(value) for name, value in overrides_raw.items()}
    preset = str(data.get("preset") or "")
    return RotConfig(schema=schema, document=document, preset=preset, overrides=overrides)


def _as_text(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def push_lines(config: RotConfig) -> str:
    """Writable settings only, so a controller keeps its own serial and board facts."""
    lines = [
        f"{spec.name} = {config.document.get(spec.name)}"
        for spec in config.schema.settings
        if not spec.readonly
    ]
    return "\n".join(lines) + "\n"
