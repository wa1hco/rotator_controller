# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Client for the text console.

Replies end with a line ``OK`` or ``ERR <code> <message>``. That trailer
is not part of the settings file. See docs/design/configuration.md.
"""

from __future__ import annotations

import json
from typing import Any

from rotatorctl.document import SettingsDocument, parse_ini_lines
from rotatorctl.schema import Schema
from rotatorctl.transport import LineTransport, TransportError


class CommandError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ConsoleClient:
    def __init__(self, transport: LineTransport, timeout: float = 3.0) -> None:
        self.transport = transport
        self.timeout = timeout

    def close(self) -> None:
        self.transport.close()

    def command(self, *lines: str) -> list[str]:
        self.transport.write_lines(list(lines))
        return self._read_reply()

    def _read_reply(self) -> list[str]:
        body: list[str] = []
        while True:
            try:
                line = self.transport.read_line(self.timeout)
            except TransportError as exc:
                raise CommandError("timeout", str(exc)) from exc
            if line == "OK":
                return body
            if line.startswith("ERR ") or line == "ERR":
                parts = line.split(" ", 2)
                code = parts[1] if len(parts) > 1 else "error"
                message = parts[2] if len(parts) > 2 else line
                raise CommandError(code, message)
            body.append(line)

    def get(self, name: str) -> str:
        body = self.command(f"get {name}")
        prefix = f"{name} = "
        for line in body:
            if line.startswith(prefix):
                return line[len(prefix) :]
        raise CommandError("protocol", f"get {name} returned no value")

    def set(self, name: str, value: str) -> None:
        self.command(f"set {name} {value}")

    def save(self) -> None:
        self.command("save")

    def dump_text(self) -> str:
        body = self.command("dump")
        return "\n".join(body) + ("\n" if body else "")

    def dump_values(self) -> dict[str, str]:
        values, errors = parse_ini_lines(self.dump_text().splitlines())
        if errors:
            raise CommandError("protocol", errors[0])
        return values

    def restore_text(self, text: str) -> None:
        lines = ["restore"]
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == ".":
                raise CommandError("invalid", "a restore file cannot contain a line with only a dot")
            if stripped:
                lines.append(stripped)
        lines.append(".")
        self.command(*lines)

    def schema(self) -> Schema:
        body = self.command("schema")
        if len(body) != 1:
            raise CommandError("protocol", "schema reply is one JSON line")
        try:
            payload: dict[str, Any] = json.loads(body[0])
        except json.JSONDecodeError as exc:
            raise CommandError("protocol", "schema reply is not JSON") from exc
        return Schema.model_validate(payload)

    def identity(self) -> dict[str, Any]:
        body = self.command("id")
        if len(body) != 1:
            raise CommandError("protocol", "id reply is one JSON line")
        try:
            payload = json.loads(body[0])
        except json.JSONDecodeError as exc:
            raise CommandError("protocol", "id reply is not JSON") from exc
        if not isinstance(payload, dict) or "serial" not in payload:
            raise CommandError("protocol", "id reply has no serial")
        return payload

    def preset_list(self) -> list[str]:
        return [line.split()[0] for line in self.command("preset list") if line.strip()]

    def preset_apply(self, model: str) -> None:
        self.command(f"preset apply {model}")

    def status(self) -> dict[str, str]:
        values, errors = parse_ini_lines(self.command("status"))
        if errors:
            raise CommandError("protocol", errors[0])
        return values

    def load_document(self) -> SettingsDocument:
        schema = self.schema()
        values = self.dump_values()
        # dump includes read-only fields. Build with force by assigning after.
        doc = SettingsDocument(schema)
        for spec in schema.settings:
            if spec.name not in values:
                continue
            doc.set(spec.name, values[spec.name], force=True)
        return doc


def schema_json(schema: Schema) -> str:
    payload = {
        "version": schema.version,
        "settings": [spec.model_dump(mode="json") for spec in schema.settings],
    }
    return json.dumps(payload, separators=(",", ":"))
