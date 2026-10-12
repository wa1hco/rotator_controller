# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Rotor presets from ``software/firmware/presets/rotor-presets.yaml``.

The GUI preview and the simulator both call ``settings_from_preset``, so
the confirm diff matches ``preset apply``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

OFFERED = frozenset({"v1", "v1-2axis", "v2-dc", "alias"})
APPLYABLE = frozenset({"v1", "v1-2axis", "v2-dc"})

_SENSOR = {
    "pot_dual_end_grounded_wiper": "dual_end_pot",
    "pot_single_ended": "single_ended_pot",
    "rheostat": "rheostat",
    "pulse": "pulse",
    "none": "none",
}
_BRAKE = {
    "wedge_solenoid": "wedge_solenoid",
    "electric_positive_lock": "electric_positive_lock",
    "none_gear": "none",
    "none": "none",
}

# Catalog paths that land on a setting. Paths with no entry are shown
# as unverified text and do not change a value.
_PATHS = {
    "sensor.type": (".sensor",),
    "sensor": (".sensor",),
    "brake.type": (".brake",),
    "travel.range_deg": (".travel_max_deg",),
    "travel.overlap_deg": (".overlap_deg",),
    "speed": (".speed_min_s", ".speed_max_s"),
    "speed.min_s": (".speed_min_s",),
    "speed.max_s": (".speed_max_s",),
    "motor.current_a": ("safety.stall_a",),
}

_cache: dict[str, tuple[Preset, ...]] = {}


@dataclass(frozen=True)
class Preset:
    id: str
    maker: str
    model: str
    family: str
    support: str
    axes: str
    alias_of: tuple[str, ...]
    unverified: tuple[str, ...]
    raw: Mapping[str, Any]


def default_preset_path() -> Path:
    env = os.environ.get("ROTATOR_PRESETS")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "software" / "firmware" / "presets" / "rotor-presets.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("rotor-presets.yaml not found; set ROTATOR_PRESETS")


def load_presets(path: Path | None = None) -> tuple[Preset, ...]:
    path = Path(path) if path else default_preset_path()
    key = str(path.resolve())
    cached = _cache.get(key)
    if cached is not None:
        return cached
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = data.get("presets") or []
    found: list[Preset] = []
    seen: set[str] = set()
    for row in rows:
        ident = str(row.get("id") or "")
        if not ident or ident in seen:
            continue
        seen.add(ident)
        alias = row.get("alias_of") or []
        unverified = row.get("unverified") or []
        found.append(
            Preset(
                id=ident,
                maker=str(row.get("maker") or ""),
                model=str(row.get("model") or ""),
                family=str(row.get("family") or ""),
                support=str(row.get("support") or ""),
                axes=str(row.get("axes") or "az"),
                alias_of=tuple(str(item) for item in alias),
                unverified=tuple(str(item) for item in unverified),
                raw=row,
            )
        )
    loaded = tuple(found)
    _cache[key] = loaded
    return loaded


def offered_presets(presets: tuple[Preset, ...] | list[Preset]) -> list[Preset]:
    return sorted((preset for preset in presets if preset.support in OFFERED), key=lambda preset: preset.id)


def can_apply(preset: Preset) -> bool:
    return preset.support in APPLYABLE


def axis_prefixes(axes: str) -> list[str]:
    token = axes.strip().lower()
    if token in ("az+el", "az-el", "el+az", "az|el", "el|az"):
        return ["az", "el"]
    if token == "el":
        return ["el"]
    if token == "az":
        return ["az"]
    has_az = "az" in token
    has_el = "el" in token
    if has_az and has_el:
        return ["az", "el"]
    if has_el:
        return ["el"]
    return ["az"]


def settings_from_preset(preset: Preset) -> dict[str, str]:
    """Writable settings ``preset apply`` loads. Empty for an alias.

    ``*.present``, calibration, ``net.*``, and ``ports.*`` stay as they are.
    An az+el row has one travel block, aimed at azimuth. Elevation then
    uses 180 degrees and no overlap when that block is an overlap rotation
    (range past 180 and a non-zero overlap). A wedge brake with no
    ``engage_after_stop_s`` uses 3 seconds.
    """
    if not can_apply(preset):
        return {}
    raw = preset.raw
    prefixes = axis_prefixes(preset.axes)
    out: dict[str, str] = {}
    sensor = _block(raw, "sensor").get("type")
    brake = _block(raw, "brake").get("type")
    travel = _block(raw, "travel")
    speed = _block(raw, "speed")
    range_deg = travel.get("range_deg")
    overlap = travel.get("overlap_deg")
    both = prefixes == ["az", "el"]
    el_override = (
        both
        and range_deg is not None
        and float(range_deg) > 180
        and overlap is not None
        and float(overlap) > 0
    )
    for prefix in prefixes:
        if sensor in _SENSOR:
            out[f"{prefix}.sensor"] = _SENSOR[str(sensor)]
        if prefix == "el" and el_override:
            out[f"{prefix}.travel_min_deg"] = "0"
            out[f"{prefix}.travel_max_deg"] = "180"
            out[f"{prefix}.overlap_deg"] = "0"
        else:
            if range_deg is not None:
                out[f"{prefix}.travel_min_deg"] = "0"
                out[f"{prefix}.travel_max_deg"] = _num(range_deg)
            if overlap is not None:
                out[f"{prefix}.overlap_deg"] = _num(overlap)
        if brake in _BRAKE:
            mapped = _BRAKE[str(brake)]
            out[f"{prefix}.brake"] = mapped
            engage = _block(raw, "brake").get("engage_after_stop_s")
            if engage is not None:
                out[f"{prefix}.brake_delay_s"] = _num(engage)
            else:
                out[f"{prefix}.brake_delay_s"] = "3" if mapped == "wedge_solenoid" else "0"
        if speed.get("min_s") is not None:
            out[f"{prefix}.speed_min_s"] = _num(speed["min_s"])
        if speed.get("max_s") is not None:
            out[f"{prefix}.speed_max_s"] = _num(speed["max_s"])
    current = _block(raw, "motor").get("current_a")
    if current is not None:
        out["safety.stall_a"] = _num(current)
    return out


def unverified_labels(preset: Preset) -> list[str]:
    return [f"{path} [?]" for path in preset.unverified]


def unverified_setting_names(preset: Preset) -> set[str]:
    names: set[str] = set()
    for path in preset.unverified:
        suffixes = _PATHS.get(path)
        if not suffixes:
            continue
        for suffix in suffixes:
            if suffix.startswith("."):
                for prefix in axis_prefixes(preset.axes):
                    names.add(f"{prefix}{suffix}")
            else:
                names.add(suffix)
    return names


def _block(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key) or {}
    if isinstance(value, Mapping):
        return value
    return {}


def _num(value: object) -> str:
    if isinstance(value, bool) or value is None:
        raise ValueError(value)
    if isinstance(value, int):
        return str(value)
    number = float(value)  # type: ignore[arg-type]
    rendered = f"{number:.4f}".rstrip("0").rstrip(".")
    if rendered in ("-0", ""):
        return "0"
    return rendered
