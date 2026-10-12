# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json

from PySide6.QtWidgets import QLabel, QListWidget

from rotatorctl.presets import settings_from_preset
from rotatorctl.rotcfg import dumps, loads, new_config
from rotatorctl_gui.main_window import MainWindow


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


def test_offline_starts_on_the_rotator_catalog(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    assert window.nav.currentRow() == 0
    assert window.stack.currentWidget() is window.browser
    assert window.browser.list.count() == 39
    assert "39 of 39" in window.browser.count.text()
    window.browser.search.setText("g-650a")
    assert 0 < window.browser.list.count() < 39
    window.browser.select("yaesu-g-450a")
    texts = [label.text() for label in window.browser.findChildren(QLabel)]
    assert any("sensor.ohms [?]" in text for text in texts)
    assert any("Yaesu-AC-pot" in text for text in texts)
    assert any("[?]" in text and "24 V" in text for text in texts)
    window.use_preset("yaesu-g-450a")
    assert window.preset_id == "yaesu-g-450a"
    assert window.config.document.get("az.sensor") == "single_ended_pot"
    window.set_custom_override("az.overlap_deg", "100")
    assert window.overrides["az.overlap_deg"] == "100"
    assert window._token() != window._saved_token
    window.show()
    assert window.file_dirty.isVisible()
    text = dumps(window.config)
    window.load_rotcfg_text(text)
    assert window.config.document.get("az.overlap_deg") == "100"
    assert window.preset_id == "yaesu-g-450a"


def test_preference_pages_list_the_review_fields(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    window.use_preset("yaesu-g-5500")
    window.show_page("axes")
    assert window.page_forms["axes"].has_field("az.sensor")
    assert window.page_forms["axes"].has_field("el.brake")
    window.show_page("limits")
    assert window.page_forms["limits"].value("el.travel_max_deg") == "180"
    window.show_page("park")
    assert window.page_forms["park"].has_field("az.park_deg")
    assert window.page_forms["park"].has_field("park.brake")
    window.show_page("calibration")
    assert window.page_forms["calibration"].has_field("az.cal.cw_end")
    window.show_page("display")
    assert window.page_forms["display"].value("ui.display_range") == "full_travel"
    window.show_page("network")
    assert window.page_forms["network"].has_field("net.hostname")
    window.show_page("console")
    assert window.page_forms["console"].value("ports.gs232_query") == "C2"
    nav = window.findChild(QListWidget, "pageNav")
    assert nav is not None
    assert nav.item(nav.count() - 1).text() == "Controllers"


def test_catalog_count_matches_the_file(presets) -> None:
    assert len(presets) == 39
    both = settings_from_preset(next(item for item in presets if item.id == "yaesu-g-5500"))
    assert both["el.travel_max_deg"] == "180"
