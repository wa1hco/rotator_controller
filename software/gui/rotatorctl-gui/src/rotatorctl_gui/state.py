# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""In-memory session for the local browser UI.

The offline ``.rotcfg`` document and a connected controller are separate.
Push copies writable offline settings onto the controller.
"""

from __future__ import annotations

import secrets
import time
from pathlib import Path

from rotatorctl.discovery import (
    ControllerInfo,
    browse_mdns,
    manual_serial,
    manual_tcp,
    merge_controllers,
    preferred_target,
    scan_usb,
)
from rotatorctl.document import Change, SettingsDocument, SettingsError, format_value, parse_ini_lines
from rotatorctl.operate import stop_line
from rotatorctl.paths import ensure_user_config_dir
from rotatorctl.phases import OPERATE_MILESTONES, UPGRADE_MILESTONES
from rotatorctl.presets import (
    Preset,
    axis_prefixes,
    can_apply,
    load_presets,
    preset_aliases,
    preset_facts,
    settings_from_preset,
)
from rotatorctl.protocol import ConsoleClient
from rotatorctl.rotcfg import dumps, loads, new_config, push_lines
from rotatorctl.schema import Schema, human_label
from rotatorctl.transport import open_target
from rotatorctl.upgrade import dfu_argv
from rotatorctl_gui.pages import page_list

_FILE_SUFFIXES = {".rotcfg", ".yaml", ".yml", ".json"}
IDLE_SECONDS = 20


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra: object) -> None:
        super().__init__(message)
        self.status = status
        self.payload: dict[str, object] = {"error": code, "message": message, **extra}


def describe_controller(info: ControllerInfo) -> str:
    title = info.name or "(unnamed)"
    serial = info.serial or "serial pending"
    lines = [f"{title}    {serial}"]
    for endpoint in info.endpoints:
        if endpoint.kind == "usb":
            if info.vid is not None and info.pid is not None:
                vid = f"{info.vid:04x}:{info.pid:04x}"
            else:
                vid = "usb"
            path = endpoint.target.removeprefix("serial://")
            lines.append(f"USB {vid}    {path}")
        else:
            lines.append(f"network    {endpoint.target.removeprefix('tcp://')}")
    extra = " · ".join(part for part in (info.firmware, info.axes) if part)
    if extra:
        lines.append(extra)
    return "\n".join(lines)


def _change(schema: Schema, change: Change) -> dict[str, object]:
    spec = schema.get(change.name)
    return {
        "name": change.name,
        "label": spec.label if spec else human_label(change.name),
        "before": change.old,
        "after": change.new,
        "reboot": bool(spec and spec.reboot),
    }


def _preview(schema: Schema, before: dict[str, str], after: dict[str, str], errors: dict[str, str]) -> dict[str, object]:
    changes = [_change(schema, item) for item in SettingsDocument(schema, before).diff(after)]
    reboots = [item["name"] for item in changes if item["reboot"]]
    note = ""
    if reboots:
        note = (
            "Takes effect after reboot: "
            + ", ".join(str(name) for name in reboots)
            + ". This program does not reboot the controller."
        )
    return {"changes": changes, "errors": errors, "blocked": bool(errors), "note": note}


class AppState:
    def __init__(self, presets: tuple[Preset, ...] | list[Preset] | None = None, *, idle_seconds: int = IDLE_SECONDS) -> None:
        self.idle_seconds = idle_seconds
        self.token = secrets.token_urlsafe(18)
        self.last_seen = time.monotonic()
        self.socket_count = 0
        try:
            self.presets: tuple[Preset, ...] | list[Preset] = tuple(presets) if presets is not None else load_presets()
        except FileNotFoundError:
            self.presets = ()
        self.config = new_config()
        self.preset_id = ""
        self.overrides: dict[str, str] = {}
        self.rotcfg_path: Path | None = None
        self._saved = self._token()
        self.discovered: list[ControllerInfo] = []
        self.manual: list[ControllerInfo] = []
        self.controllers: list[ControllerInfo] = []
        self.client: ConsoleClient | None = None
        self.device_schema: Schema | None = None
        self.device_baseline: dict[str, str] = {}
        self.device_edits: dict[str, str] = {}
        self.connected_serial = ""
        self.connected_target = ""
        self.connected_name = ""

    def touch(self) -> None:
        self.last_seen = time.monotonic()

    def _token(self) -> tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
        return (
            self.preset_id,
            tuple(sorted(self.overrides.items())),
            tuple(sorted(self.config.document.snapshot().items())),
        )

    def offline_dirty(self) -> bool:
        return self._token() != self._saved

    def _preset(self) -> Preset | None:
        return next((item for item in self.presets if item.id == self.preset_id), None)

    def visible_axes(self) -> dict[str, bool]:
        preset = self._preset()
        if preset is None:
            return {"azimuth": True, "elevation": True}
        prefixes = axis_prefixes(preset.axes)
        return {"azimuth": "az" in prefixes, "elevation": "el" in prefixes}

    def _preset_value(self, name: str) -> str:
        preset = self._preset()
        if preset is not None:
            mapped = settings_from_preset(preset)
            if name in mapped:
                return mapped[name]
        spec = self.config.schema.get(name)
        return "" if spec is None else spec.default

    def filename(self) -> str:
        if self.rotcfg_path is not None:
            return self.rotcfg_path.name
        return "Untitled.rotcfg"

    def document_payload(self) -> dict[str, object]:
        return {
            "source": "offline",
            "preset": self.preset_id,
            "name": self.config.document.get("net.hostname"),
            "filename": self.filename(),
            "overrides": dict(self.overrides),
            "settings": self.config.document.snapshot(),
            "dirty": self.offline_dirty(),
            "axes": self.visible_axes(),
            "connected": bool(self.client),
        }

    def boot_payload(self) -> dict[str, object]:
        return {
            "api": 1,
            "role": "pc",
            "idle_seconds": self.idle_seconds,
            "features": {"offline": True, "discovery": True, "files": True, "shutdown": True, "multi": True},
            "operate": list(OPERATE_MILESTONES),
            "upgrade": list(UPGRADE_MILESTONES),
            "dfu": dfu_argv("firmware.bin"),
            "stop": stop_line(),
        }

    def schema_payload(self, schema: Schema | None = None) -> dict[str, object]:
        chosen = schema or self.config.schema
        return {
            "version": chosen.version,
            "settings": [spec.model_dump(mode="json") for spec in chosen.settings],
        }

    def catalog_payload(self) -> dict[str, object]:
        rows: list[dict[str, object]] = []
        for preset in self.presets:
            mapped = settings_from_preset(preset)
            rows.append(
                {
                    "id": preset.id,
                    "maker": preset.maker,
                    "model": preset.model,
                    "family": preset.family,
                    "support": preset.support,
                    "axes": preset.axes,
                    "alias_of": list(preset.alias_of),
                    "aliases": list(preset_aliases(preset)),
                    "can_apply": can_apply(preset),
                    "unverified": list(preset.unverified),
                    "facts": [
                        {"label": label, "value": value, "unverified": flagged}
                        for label, value, flagged in preset_facts(preset)
                    ],
                    "settings": [
                        {
                            "name": name,
                            "label": human_label(name),
                            "value": value,
                            "unverified": False,
                        }
                        for name, value in mapped.items()
                    ],
                }
            )
        return {"presets": rows}

    def pages_payload(self) -> dict[str, object]:
        return {"pages": page_list()}

    def edit_offline(self, name: str, raw: str) -> dict[str, object]:
        spec = self.config.schema.get(name)
        if spec is None:
            raise SettingsError("unknown", f"unknown setting {name}")
        if spec.readonly:
            raise SettingsError("readonly", f"{name} is read-only")
        canonical = format_value(spec, raw)
        self.config.document.set(name, canonical)
        if canonical == self._preset_value(name):
            self.overrides.pop(name, None)
        else:
            self.overrides[name] = canonical
        return self.document_payload()

    def apply_preset(self, preset_id: str) -> dict[str, object]:
        preset = next((item for item in self.presets if item.id == preset_id), None)
        if preset is None:
            raise SettingsError("unknown", f"unknown preset {preset_id}")
        if not can_apply(preset):
            raise SettingsError("support", f"{preset_id} cannot be applied")
        for name, value in settings_from_preset(preset).items():
            self.config.document.set(name, value)
            self.overrides.pop(name, None)
        self.preset_id = preset_id
        self.config.preset = preset_id
        return self.document_payload()

    def set_override(self, name: str, raw: str | None) -> dict[str, object]:
        if raw is None or raw == "":
            self.overrides.pop(name, None)
            if self.config.schema.get(name) is not None:
                self.config.document.set(name, self._preset_value(name))
            return self.document_payload()
        spec = self.config.schema.get(name)
        if spec is None or spec.readonly:
            raise SettingsError("readonly", f"{name} cannot be overridden")
        canonical = format_value(spec, raw)
        self.config.document.set(name, canonical)
        if canonical == self._preset_value(name):
            self.overrides.pop(name, None)
        else:
            self.overrides[name] = canonical
        return self.document_payload()

    def new_document(self) -> dict[str, object]:
        self.config = new_config()
        self.preset_id = ""
        self.overrides = {}
        self.rotcfg_path = None
        self._saved = self._token()
        return self.document_payload()

    def load_text(self, text: str, path: str = "") -> dict[str, object]:
        loaded = loads(text, self.config.schema)
        self.config = loaded
        self.preset_id = loaded.preset
        self.overrides = dict(loaded.overrides)
        self.rotcfg_path = Path(path) if path else None
        self._saved = self._token()
        return self.document_payload()

    def preview_offline(self) -> dict[str, object]:
        saved_settings = dict(self._saved[2])
        return _preview(self.config.schema, saved_settings, self.config.document.snapshot(), {})

    def save_offline(self, name: str = "") -> dict[str, object]:
        chosen = name or (self.rotcfg_path.name if self.rotcfg_path else "station.rotcfg")
        safe = self._safe_name(chosen)
        self.config.preset = self.preset_id
        self.config.overrides = dict(self.overrides)
        path = ensure_user_config_dir() / safe
        path.write_text(dumps(self.config), encoding="utf-8")
        self.rotcfg_path = path
        self._saved = self._token()
        return self.document_payload()

    def download_text(self) -> tuple[str, str]:
        self.config.preset = self.preset_id
        self.config.overrides = dict(self.overrides)
        name = self.filename()
        if name == "Untitled.rotcfg":
            name = "station.rotcfg"
        return name, dumps(self.config)

    def list_files(self) -> dict[str, object]:
        directory = ensure_user_config_dir()
        files = sorted(
            path.name
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in _FILE_SUFFIXES
        )
        return {"directory": str(directory), "files": files}

    def open_named(self, name: str) -> dict[str, object]:
        safe = self._safe_name(name)
        path = ensure_user_config_dir() / safe
        if not path.is_file():
            raise SettingsError("missing", f"{safe} is not in the config folder")
        return self.load_text(path.read_text(encoding="utf-8"), str(path))

    def _safe_name(self, name: str) -> str:
        safe = Path(name).name
        if safe != name or Path(safe).suffix.lower() not in _FILE_SUFFIXES:
            raise SettingsError("invalid", "file name must be a .rotcfg, .yaml, .yml, or .json in the config folder")
        return safe

    def controllers_payload(self) -> dict[str, object]:
        return {"controllers": [self._controller_json(info) for info in self.controllers]}

    def _controller_json(self, info: ControllerInfo) -> dict[str, object]:
        return {
            "serial": info.serial,
            "name": info.name,
            "firmware": info.firmware,
            "axes": info.axes,
            "text": describe_controller(info),
            "endpoints": [
                {"kind": endpoint.kind, "target": endpoint.target, "detail": endpoint.detail}
                for endpoint in info.endpoints
            ],
        }

    def scan(self, timeout: float = 0.8) -> dict[str, object]:
        found = scan_usb()
        try:
            found.extend(browse_mdns(timeout))
        except OSError:
            pass
        self.discovered = found
        self.controllers = merge_controllers([*self.discovered, *self.manual])
        return self.controllers_payload()

    def add_controller(self, kind: str, host: str = "", port: int = 0, path: str = "") -> dict[str, object]:
        if kind == "tcp":
            if not host or port <= 0:
                raise SettingsError("invalid", "network add needs a host and a port")
            info = manual_tcp(host, port)
        elif kind == "serial":
            if not path:
                raise SettingsError("invalid", "serial add needs a path")
            info = manual_serial(path)
        else:
            raise SettingsError("invalid", "kind is tcp or serial")
        self.manual.append(info)
        self.controllers = merge_controllers([*self.discovered, *self.manual])
        return self.controllers_payload()

    def connect(self, target: str, *, discard: bool = False) -> dict[str, object]:
        if self.device_dirty() and not discard:
            raise ApiError(409, "dirty", "Discard unsaved controller changes before connecting.")
        client = ConsoleClient(open_target(target))
        try:
            ident = client.identity()
            doc = client.load_document()
        except Exception:
            client.close()
            raise
        if self.client is not None:
            self.client.close()
        self.client = client
        self.connected_target = target
        serial = str(ident.get("serial") or "")
        name = str(ident.get("name") or "")
        firmware = str(ident.get("fw") or "")
        axes = str(ident.get("axes") or "")
        self._stamp(target, serial, name, firmware, axes)
        self.connected_serial = serial
        self.connected_name = name
        self.device_schema = doc.schema
        self.device_baseline = doc.snapshot()
        self.device_edits = {}
        self.controllers = merge_controllers(self.controllers)
        return self.device_payload()

    def _stamp(self, target: str, serial: str, name: str, firmware: str, axes: str) -> None:
        for entry in [*self.discovered, *self.manual, *self.controllers]:
            if any(endpoint.target == target for endpoint in entry.endpoints):
                if serial:
                    entry.serial = serial
                if name:
                    entry.name = name
                    entry.name_from_mdns = True
                if firmware:
                    entry.firmware = firmware
                if axes:
                    entry.axes = axes

    def disconnect(self) -> dict[str, object]:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.device_schema = None
        self.device_baseline = {}
        self.device_edits = {}
        self.connected_serial = ""
        self.connected_target = ""
        self.connected_name = ""
        return self.device_payload()

    def _require_device(self) -> tuple[ConsoleClient, Schema]:
        if self.client is None or self.device_schema is None:
            raise ApiError(409, "offline", "Connect a controller first.")
        return self.client, self.device_schema

    def device_errors(self) -> dict[str, str]:
        if self.device_schema is None:
            return {}
        found: dict[str, str] = {}
        for name, raw in self.device_edits.items():
            message = SettingsDocument(self.device_schema).validate(name, raw)
            if message:
                found[name] = message
        return found

    def device_current(self) -> dict[str, str]:
        schema = self.device_schema
        current = dict(self.device_baseline)
        if schema is None:
            return current
        for name, raw in self.device_edits.items():
            spec = schema.get(name)
            if spec is None or spec.readonly:
                continue
            if SettingsDocument(schema).validate(name, raw):
                continue
            current[name] = format_value(spec, raw)
        return current

    def device_dirty(self) -> bool:
        if self.device_schema is None:
            return False
        if self.device_errors():
            return True
        return bool(SettingsDocument(self.device_schema, self.device_baseline).diff(self.device_current()))

    def device_axes(self) -> dict[str, bool]:
        values = self.device_current()
        return {
            "azimuth": values.get("az.present", "true") == "true",
            "elevation": values.get("el.present", "true") == "true",
        }

    def device_payload(self) -> dict[str, object]:
        if self.client is None or self.device_schema is None:
            return {"connected": False, "dirty": False, "settings": {}, "errors": {}, "axes": {"azimuth": True, "elevation": True}}
        return {
            "connected": True,
            "serial": self.connected_serial,
            "name": self.connected_name,
            "target": self.connected_target,
            "settings": self.device_current() | {name: raw for name, raw in self.device_edits.items() if name in self.device_errors()},
            "errors": self.device_errors(),
            "dirty": self.device_dirty(),
            "axes": self.device_axes(),
            "schema": self.schema_payload(self.device_schema),
        }

    def edit_device(self, name: str, raw: str) -> dict[str, object]:
        _client, schema = self._require_device()
        spec = schema.get(name)
        if spec is None:
            raise SettingsError("unknown", f"unknown setting {name}")
        if spec.readonly:
            raise SettingsError("readonly", f"{name} is read-only")
        message = SettingsDocument(schema).validate(name, raw)
        baseline = self.device_baseline.get(name, spec.default)
        if message is None and format_value(spec, raw) == baseline:
            self.device_edits.pop(name, None)
        else:
            self.device_edits[name] = raw if message else format_value(spec, raw)
        return self.device_payload()

    def preview_device(self) -> dict[str, object]:
        _client, schema = self._require_device()
        errors = self.device_errors()
        return _preview(schema, self.device_baseline, self.device_current(), errors)

    def save_device(self) -> dict[str, object]:
        client, schema = self._require_device()
        errors = self.device_errors()
        if errors:
            raise ApiError(400, "invalid", "Fix the highlighted fields before saving.", errors=errors)
        changes = SettingsDocument(schema, self.device_baseline).diff(self.device_current())
        if not changes:
            raise ApiError(400, "clean", "Nothing to write.")
        for change in changes:
            client.set(change.name, change.new)
        client.save()
        doc = client.load_document()
        self.device_schema = doc.schema
        self.device_baseline = doc.snapshot()
        self.device_edits = {}
        return self.device_payload()

    def backup_text(self) -> str:
        _client, schema = self._require_device()
        if self.device_errors():
            raise SettingsError("invalid", "fix invalid fields before backup")
        return SettingsDocument(schema, self.device_current()).to_ini()

    def preview_restore(self, text: str) -> dict[str, object]:
        _client, schema = self._require_device()
        trial = SettingsDocument(schema, self.device_baseline)
        trial.replace_from_lines(text.splitlines())
        return _preview(schema, self.device_baseline, trial.snapshot(), {})

    def apply_restore(self, text: str) -> dict[str, object]:
        client, _schema = self._require_device()
        self.preview_restore(text)
        client.restore_text(text)
        doc = client.load_document()
        self.device_schema = doc.schema
        self.device_baseline = doc.snapshot()
        self.device_edits = {}
        return self.device_payload()

    def compare_text(self, text: str) -> dict[str, object]:
        _client, schema = self._require_device()
        if self.device_errors():
            raise SettingsError("invalid", "fix invalid fields before compare")
        values, errors = parse_ini_lines(text.splitlines())
        if errors:
            raise SettingsError("invalid", errors[0])
        other = dict(self.device_baseline)
        for name, raw in values.items():
            spec = schema.get(name)
            if spec is None:
                continue
            other[name] = format_value(spec, raw)
        current = self.device_current()
        return _preview(schema, other, current, {})

    def copy_from(self, target: str) -> dict[str, object]:
        _client, schema = self._require_device()
        other = ConsoleClient(open_target(target))
        try:
            doc = other.load_document()
        finally:
            other.close()
        for spec in schema.settings:
            if spec.readonly or spec.name not in doc.values:
                continue
            value = doc.values[spec.name]
            if value == self.device_baseline.get(spec.name, spec.default):
                self.device_edits.pop(spec.name, None)
            else:
                self.device_edits[spec.name] = value
        return self.device_payload()

    def push_offline(self) -> dict[str, object]:
        client, _schema = self._require_device()
        self.config.preset = self.preset_id
        self.config.overrides = dict(self.overrides)
        client.restore_text(push_lines(self.config))
        doc = client.load_document()
        self.device_schema = doc.schema
        self.device_baseline = doc.snapshot()
        self.device_edits = {}
        return self.device_payload()

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def find_target(self, serial: str) -> str:
        for info in self.controllers:
            if info.serial == serial and info.endpoints:
                return preferred_target(info)
        raise SettingsError("missing", "that controller is not in the list")
