# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from rotatorctl.presets import (
    can_apply,
    offered_presets,
    settings_from_preset,
    unverified_labels,
)


def _one(presets, ident):
    return next(preset for preset in presets if preset.id == ident)


def test_offer_hides_no_later_and_unchecked(presets) -> None:
    offered = {preset.id for preset in offered_presets(presets)}
    assert "hygain-ham-iv" in offered
    assert "yaesu-g-450a" in offered
    assert "alias-telex-dcu" in offered
    assert "hygain-ar-40" not in offered
    assert "prosistel-ac-48v" not in offered
    assert can_apply(_one(presets, "hygain-ham-iv"))
    assert not can_apply(_one(presets, "alias-telex-dcu"))
    assert settings_from_preset(_one(presets, "alias-telex-dcu")) == {}


def test_ham_iv_and_g450_mapping(presets) -> None:
    ham = settings_from_preset(_one(presets, "hygain-ham-iv"))
    assert ham["az.sensor"] == "dual_end_pot"
    assert ham["az.brake"] == "wedge_solenoid"
    assert ham["az.brake_delay_s"] == "3"
    assert ham["az.travel_max_deg"] == "360"
    assert ham["az.overlap_deg"] == "0"
    assert ham["safety.stall_a"] == "2.25"
    assert "az.present" not in ham
    assert not any(name.startswith("net.") or ".cal." in name for name in ham)
    assert unverified_labels(_one(presets, "hygain-ham-iv")) == []

    yaesu = settings_from_preset(_one(presets, "yaesu-g-450a"))
    assert yaesu["az.sensor"] == "single_ended_pot"
    assert yaesu["az.brake"] == "none"
    assert yaesu["az.overlap_deg"] == "90"
    assert yaesu["az.travel_max_deg"] == "450"
    assert "safety.stall_a" not in yaesu
    labels = unverified_labels(_one(presets, "yaesu-g-450a"))
    assert "sensor.ohms [?]" in labels
    assert "motor.volts [?]" in labels


def test_two_axis_elevation_travel(presets) -> None:
    both = settings_from_preset(_one(presets, "yaesu-g-5500"))
    assert both["az.travel_max_deg"] == "450"
    assert both["az.overlap_deg"] == "90"
    assert both["el.travel_max_deg"] == "180"
    assert both["el.overlap_deg"] == "0"
    assert "az.present" not in both
    assert "el.present" not in both
    elevation = settings_from_preset(_one(presets, "yaesu-g-550"))
    assert "el.sensor" in elevation
    assert "az.sensor" not in elevation
