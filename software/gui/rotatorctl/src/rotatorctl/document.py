# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""In-memory settings record: validation, text dump, and diff.

The text form is the file described in docs/design/configuration.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rotatorctl.schema import Schema, SettingSpec, SettingType

_HOSTNAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,30}[A-Za-z0-9])?$")
_IPV4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_TOKEN = re.compile(r"^[^\s]+$")
_CAL_MAP = re.compile(
    r"^(?:none|(?:-?\d+(?:\.\d+)?:-?\d+(?:\.\d+)?)(?:,-?\d+(?:\.\d+)?:-?\d+(?:\.\d+)?){1,15})$"
)


class SettingsError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Change:
    name: str
    old: str
    new: str


def format_value(spec: SettingSpec, raw: str) -> str:
    """Return the canonical text, or raise SettingsError."""
    text = raw.strip()
    kind = spec.type
    if kind is SettingType.BOOL:
        if text not in ("true", "false"):
            raise SettingsError("type", f"{spec.name} is true or false")
        return text
    if kind is SettingType.INT:
        try:
            value = int(text, 10)
        except ValueError as exc:
            raise SettingsError("type", f"{spec.name} is an integer") from exc
        _check_range(spec, value)
        return str(value)
    if kind is SettingType.FLOAT:
        try:
            value = float(text)
        except ValueError as exc:
            raise SettingsError("type", f"{spec.name} is a number") from exc
        if value != value or value in (float("inf"), float("-inf")):
            raise SettingsError("type", f"{spec.name} is a number")
        _check_range(spec, value)
        rendered = f"{value:.4f}".rstrip("0").rstrip(".")
        if rendered in ("-0", ""):
            rendered = "0"
        return rendered
    if kind is SettingType.ENUM:
        if text not in spec.enum:
            choices = ", ".join(spec.enum)
            raise SettingsError("enum", f"{spec.name} is one of: {choices}")
        return text
    if kind is SettingType.STRING:
        if not text or not _TOKEN.match(text):
            raise SettingsError("type", f"{spec.name} is a single token")
        if spec.name == "net.hostname" and not _HOSTNAME.match(text):
            raise SettingsError("type", "net.hostname is letters, digits, and hyphens")
        if spec.name == "net.address" and not _ipv4_ok(text):
            raise SettingsError("type", "net.address is an IPv4 address")
        if spec.name.endswith(".cal.map") and not _CAL_MAP.match(text):
            raise SettingsError("type", f"{spec.name} is none, or raw:heading pairs separated by commas")
        return text
    raise SettingsError("type", f"{spec.name} has an unknown type")


def _ipv4_ok(text: str) -> bool:
    if not _IPV4.match(text):
        return False
    return all(0 <= int(part) <= 255 for part in text.split("."))


def _check_range(spec: SettingSpec, value: float) -> None:
    if spec.min is not None and value < spec.min:
        raise SettingsError("range", f"{spec.name} is below {spec.min:g}")
    if spec.max is not None and value > spec.max:
        raise SettingsError("range", f"{spec.name} is above {spec.max:g}")


class SettingsDocument:
    def __init__(self, schema: Schema, values: dict[str, str] | None = None) -> None:
        self.schema = schema
        self.values: dict[str, str] = {spec.name: spec.default for spec in schema.settings}
        if values:
            for name, raw in values.items():
                self.set(name, raw, force=True)

    def get(self, name: str) -> str:
        if name not in self.values:
            raise SettingsError("unknown", f"unknown setting {name}")
        return self.values[name]

    def set(self, name: str, raw: str, *, force: bool = False) -> None:
        spec = self.schema.get(name)
        if spec is None:
            raise SettingsError("unknown", f"unknown setting {name}")
        if spec.readonly and not force:
            raise SettingsError("readonly", f"{name} is read-only")
        self.values[name] = format_value(spec, raw)

    def validate(self, name: str, raw: str) -> str | None:
        """Error text for a field the operator is typing, or None."""
        spec = self.schema.get(name)
        if spec is None:
            return f"unknown setting {name}"
        if spec.readonly:
            return None
        try:
            format_value(spec, raw)
        except SettingsError as exc:
            return exc.message
        return None

    def snapshot(self) -> dict[str, str]:
        return dict(self.values)

    def diff(self, other: dict[str, str]) -> list[Change]:
        changes: list[Change] = []
        for spec in self.schema.settings:
            old = self.values.get(spec.name, "")
            new = other.get(spec.name, old)
            if old != new:
                changes.append(Change(spec.name, old, new))
        return changes

    def to_ini(self) -> str:
        lines = [f"# rotator-settings {self.schema.version}"]
        for spec in self.schema.settings:
            lines.append(f"{spec.name} = {self.values[spec.name]}")
        lines.append("")
        return "\n".join(lines)

    def replace_from_lines(self, lines: list[str]) -> None:
        """Replace writable values from a whole file. Reject leaves this object unchanged."""
        parsed, errors = parse_ini_lines(lines)
        if errors:
            raise SettingsError("invalid", errors[0])
        proposed = self.snapshot()
        seen: set[str] = set()
        for name, raw in parsed.items():
            spec = self.schema.get(name)
            if spec is None:
                raise SettingsError("unknown", f"unknown setting {name}")
            if name == "sys.schema" and raw.strip() != self.values[name]:
                raise SettingsError("schema", "sys.schema does not match this firmware")
            canonical = format_value(spec, raw)
            if spec.readonly and canonical != self.values[name]:
                raise SettingsError("readonly", f"{name} is read-only")
            proposed[name] = canonical
            seen.add(name)
        missing = [
            spec.name
            for spec in self.schema.settings
            if not spec.readonly and spec.name not in seen
        ]
        if missing:
            raise SettingsError("missing", f"file is missing {missing[0]}")
        self.values = proposed


def parse_ini_lines(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    found: dict[str, str] = {}
    errors: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            errors.append(f"not a setting: {line}")
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or not value or any(ch.isspace() for ch in value):
            errors.append(f"not a setting: {line}")
            continue
        found[name] = value
    return found, errors
