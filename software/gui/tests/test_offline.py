# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json

from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QPushButton, QWidget

from rotatorctl.presets import settings_from_preset
from rotatorctl.schema import default_schema, human_label
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
    assert window.page_forms["park"].has_field("park.idle_min")
    assert window.page_forms["limits"].has_field("az.center")
    assert window.page_forms["axes"].value("sys.drive") == "triac"
    body = window.page_forms["park"].findChild(QWidget, "advancedBody")
    toggle = window.page_forms["park"].findChild(QPushButton, "advancedToggle")
    assert body is not None and toggle is not None
    assert body.isHidden()
    toggle.click()
    assert not body.isHidden()
    assert window.page_forms["park"].has_field("preset.1.az")
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


def test_detail_pane_keeps_one_copy(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    window.use_preset("yaesu-g-450a")
    window.set_custom_override("az.overlap_deg", "100")
    window.show()
    qtbot.wait(10)
    body = window.browser.detail.widget()
    texts = [label.text() for label in body.findChildren(QLabel)]
    assert texts.count("Custom overrides") == 1
    assert texts.count("Settings this preset writes") == 1
    assert len(body.findChildren(QPushButton, "usePreset")) == 1
    assert any(text.startswith("Overlap:") and "100" in text for text in texts)


def test_az_only_rotor_hides_elevation_and_uses_labels(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    window.use_preset("yaesu-g-450a")
    window.show_page("limits")
    form = window.page_forms["limits"]
    elevation = form.findChild(QGroupBox, "group-el")
    azimuth = form.findChild(QGroupBox, "group-az")
    assert elevation is not None and elevation.isHidden()
    assert azimuth is not None and not azimuth.isHidden()
    visible = [
        label
        for label in form.findChildren(QLabel)
        if label.text() == "Travel min" and "az.travel_min_deg" in label.toolTip()
    ]
    assert len(visible) == 1
    assert form._rows["az.travel_min_deg"].isHidden() is False
    assert form._rows["el.travel_min_deg"].isHidden() is True
    assert any(label.text() == "az.creep_deg" and label.objectName() == "fieldKey" for label in form.findChildren(QLabel))
    window.use_preset("yaesu-g-5500")
    assert not form.findChild(QGroupBox, "group-el").isHidden()


def test_human_label_matches_the_travel_example() -> None:
    assert human_label("az.travel_min_deg") == "Travel min"
    assert default_schema().get("az.travel_min_deg").label == "Travel min"
    assert human_label("az.cal.cw_end") == "CW end"


def test_catalog_count_matches_the_file(presets) -> None:
    assert len(presets) == 39
    both = settings_from_preset(next(item for item in presets if item.id == "yaesu-g-5500"))
    assert both["el.travel_max_deg"] == "180"
