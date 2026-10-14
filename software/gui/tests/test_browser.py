# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pytest

from rotatorctl_gui.server import start_server
from rotatorctl_gui.state import AppState

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect  # noqa: E402


@pytest.fixture(scope="module")
def app_url():
    state = AppState(idle_seconds=0)
    state.token = "browser"
    running = start_server(state, idle_seconds=0)
    try:
        yield running.url
    finally:
        running.stop()


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as factory:
        launched = factory.chromium.launch()
        try:
            yield launched
        finally:
            launched.close()


@pytest.fixture
def page(browser, app_url):
    tab = browser.new_page(viewport={"width": 1280, "height": 900})
    tab.goto(app_url)
    tab.wait_for_selector("#presetCount")
    try:
        yield tab
    finally:
        tab.close()


def open_advanced(page) -> None:
    toggle = page.locator("#advancedToggle")
    expect(toggle).to_be_visible()
    if toggle.get_attribute("aria-expanded") != "true":
        toggle.click()
    expect(page.locator("#advancedBody")).to_be_visible()


def test_rotator_picker_search_labels_and_az_only(page) -> None:
    expect(page.locator("#presetCount")).to_have_text("39 of 39")
    expect(page.locator("#stop")).to_be_visible()
    expect(page.locator("#stop")).to_be_disabled()
    page.fill("#presetSearch", "g-650a")
    count = page.locator("#presetCount").inner_text()
    shown = int(count.split()[0])
    assert 0 < shown < 39
    page.fill("#presetSearch", "")
    page.locator("[data-id='yaesu-g-450a']").click()
    detail = page.locator("#presetDetail")
    expect(detail).to_contain_text("sensor.ohms [?]")
    expect(detail).to_contain_text("Yaesu-AC-pot")
    expect(detail).to_contain_text("24 V")
    expect(detail.get_by_role("heading", name="Settings this preset writes")).to_have_count(1)
    expect(detail.get_by_role("heading", name="Custom overrides")).to_have_count(1)
    expect(page.locator("#usePreset")).to_have_count(1)
    with page.expect_response("**/api/preset/apply"):
        page.locator("#usePreset").click()
    page.locator("#overrideName").select_option("az.overlap_deg")
    page.fill("#overrideValue", "100")
    with page.expect_response("**/api/override"):
        page.locator("#setOverride").click()
    expect(page.locator("#overrideList")).to_contain_text("Overlap:")
    expect(page.locator("#overrideList")).to_contain_text("100")
    expect(page.locator("#dirty")).to_be_visible()
    page.locator("[data-page='limits']").click()
    expect(page.locator("#group-el")).to_be_hidden()
    expect(page.locator("#group-az")).to_be_visible()
    travel = page.locator("label:visible", has_text="Travel min")
    expect(travel).to_have_count(1)
    title = travel.get_attribute("title") or ""
    assert "az.travel_min_deg" in title
    open_advanced(page)
    expect(page.locator(".field-key", has_text="az.creep_deg")).to_be_visible()
    page.locator("[data-page='axes']").click()
    expect(page.locator("#group-el")).to_be_hidden()
    page.locator("[data-page='park']").click()
    expect(page.get_by_role("heading", name="Park", level=2)).to_be_visible()
    open_advanced(page)
    expect(page.locator("#advancedBody")).to_be_visible()
    expect(page.locator("[data-name='preset.1.az']")).to_be_visible()
    page.locator("[data-page='console']").click()
    expect(page.locator("[id='field-ports.gs232_query']")).to_have_value("C2")
    page.locator("[data-page='controllers']").click()
    expect(page.locator("#stop")).to_be_visible()
    expect(page.get_by_text("hamlib rotctld")).to_be_disabled()


def test_text_size_persists(page, app_url) -> None:
    page.locator("#fontUp").click()
    page.locator("#fontUp").click()
    size = page.evaluate("getComputedStyle(document.documentElement).fontSize")
    assert float(size.replace("px", "")) > 16
    page.reload()
    page.wait_for_selector("#presetCount")
    again = page.evaluate("getComputedStyle(document.documentElement).fontSize")
    assert again == size
    page.goto(app_url)
    stored = page.evaluate("localStorage.getItem('rotatorctl.textScale')")
    assert stored == "3"


def test_dark_mode_and_phone_layout(browser, app_url) -> None:
    tab = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme="dark")
    tab.goto(app_url)
    tab.wait_for_selector("#presetCount")
    background = tab.evaluate("getComputedStyle(document.body).backgroundColor")
    assert background in ("rgb(28, 25, 23)", "rgba(28, 25, 23, 1)")
    box = tab.locator("#pageNav").bounding_box()
    assert box is not None
    assert box["height"] < box["width"]
    assert tab.locator("#stop").is_visible()
    tab.close()
