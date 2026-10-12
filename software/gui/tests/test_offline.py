# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json

from rotatorctl.presets import settings_from_preset
from rotatorctl.schema import default_schema, human_label
from rotatorctl.rotcfg import dumps, loads, new_config


def test_rotcfg_yaml_and_json_roundtrip() -> None:
    config = new_config()
    config.preset = "yaesu-g-450a"
    config.document.set("az.overlap_deg", "100")
    config.overrides = {"az.overlap_deg": "100"}
    text = dumps(config)
    assert text.startswith("# rotator-config 1\n")
    loaded = loads(text, config.schema)
    assert loaded.preset == "yaesu-g-450a"
    assert loaded.document.get("az.overlap_deg") == "100"
    assert loaded.overrides["az.overlap_deg"] == "100"
    again = loads(json.dumps({"format": "rotcfg", "version": 1, "preset": "yaesu-g-450a", "settings": config.document.snapshot(), "overrides": config.overrides}), config.schema)
    assert again.document.get("net.dhcp") == "true"
    assert again.document.get("az.overlap_deg") == "100"


def test_human_label_matches_the_travel_example() -> None:
    assert human_label("az.travel_min_deg") == "Travel min"
    assert default_schema().get("az.travel_min_deg").label == "Travel min"
    assert human_label("az.cal.cw_end") == "CW end"


def test_catalog_count_matches_the_file(presets) -> None:
    assert len(presets) == 39
    both = settings_from_preset(next(item for item in presets if item.id == "yaesu-g-5500"))
    assert both["el.travel_max_deg"] == "180"
