# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Render the browser UI with Playwright and write the review PNGs.

Offline shots are written first, before the simulator starts.

Run from anywhere:

    python software/gui/scripts/capture_screenshots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rotatorctl" / "src"))
sys.path.insert(0, str(ROOT / "rotatorctl-gui" / "src"))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

from rotatorctl.sim import SimInstance  # noqa: E402
from rotatorctl_gui.server import start_server  # noqa: E402
from rotatorctl_gui.state import AppState  # noqa: E402

DOCS = ROOT / "docs"
OUT = DOCS / "screenshots"
PAGES = ("axes", "limits", "park", "calibration", "display", "network", "console")


def save(page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path))
    if path.stat().st_size < 8000:
        raise SystemExit(f"screenshot looks empty: {path} ({path.stat().st_size} bytes)")
    print(path)


def edit_device(page, name: str, value: str) -> None:
    field = page.locator(f"[id='field-{name}']")
    field.scroll_into_view_if_needed()
    field.fill(value)
    with page.expect_response("**/api/device/edit"):
        field.dispatch_event("change")


def capture_offline(browser, url: str) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(url)
    page.wait_for_selector("#presetCount")
    page.locator("[data-id='yaesu-g-450a']").click()
    with page.expect_response("**/api/preset/apply"):
        page.locator("#usePreset").click()
    page.locator("#overrideName").select_option("az.overlap_deg")
    page.fill("#overrideValue", "100")
    with page.expect_response("**/api/override"):
        page.locator("#setOverride").click()
    expect(page.locator("#overrideList")).to_contain_text("100")
    expect(page.locator("#dirty")).to_be_visible()
    save(page, DOCS / "rotator-selection.png")

    page.set_viewport_size({"width": 1280, "height": 1040})
    for key in PAGES:
        page.locator(f"[data-page='{key}']").click()
        expect(page.locator("main h2")).to_be_visible()
        save(page, DOCS / f"{key}.png")

    page.locator("[data-page='rotator']").click()
    expect(page.locator("#presetDetail")).to_contain_text("Settings this preset writes")
    page.locator("h3", has_text="Settings this preset writes").scroll_into_view_if_needed()
    save(page, OUT / "presets.png")
    page.close()

    phone = browser.new_page(viewport={"width": 390, "height": 844})
    phone.goto(url)
    phone.wait_for_selector("#presetCount")
    phone.locator("[data-id='yaesu-g-450a']").click()
    expect(phone.locator("#presetDetail")).to_contain_text("Yaesu-AC-pot")
    save(phone, DOCS / "rotator-phone.png")
    phone.close()

    large = browser.new_page(viewport={"width": 1280, "height": 900})
    large.goto(url)
    large.wait_for_selector("#presetCount")
    large.locator("#fontUp").click()
    large.locator("#fontUp").click()
    large.locator("[data-id='yaesu-g-450a']").click()
    expect(large.locator("#presetDetail")).to_contain_text("sensor.ohms [?]")
    save(large, DOCS / "rotator-large-text.png")
    large.close()


def capture_connected(browser, url: str) -> None:
    inst = SimInstance(serial="RC-SHOT", name="Alpha", tcp=True, pty=False, mdns=False)
    inst.start()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url)
        page.wait_for_selector("#presetCount")
        page.locator("[data-page='controllers']").click()
        page.fill("#addHost", "127.0.0.1")
        page.fill("#addPort", str(inst.port))
        with page.expect_response("**/api/controllers/add"):
            page.locator("#addNetwork").click()
        row = page.locator("#controllerList button").first
        expect(row).to_contain_text("127.0.0.1")
        row.click()
        save(page, OUT / "controllers.png")
        with page.expect_response("**/api/controllers/connect"):
            page.locator("#connectBtn").click()
        expect(page.locator("#modePill")).to_have_text("CONNECTED")
        page.fill("#deviceSearch", "address")
        edit_device(page, "net.address", "not-an-ip")
        expect(page.locator(".field[data-name='net.address'] .field-error")).to_contain_text("IPv4")
        expect(page.locator("#dirty")).to_be_visible()
        save(page, OUT / "settings.png")
        page.fill("#deviceSearch", "")
        edit_device(page, "net.address", "10.1.1.20")
        edit_device(page, "net.hostname", "alpha-2")
        edit_device(page, "safety.dead_time_ms", "750")
        page.locator("#deviceSave").click()
        expect(page.locator("#diff")).to_be_visible()
        expect(page.locator("#diffNote")).to_contain_text("reboot")
        save(page, OUT / "confirm-save.png")
        page.locator("#diff button[value='cancel']").click()
        page.close()
    finally:
        inst.stop()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    state = AppState(idle_seconds=0)
    state.token = "shots"
    running = start_server(state, idle_seconds=0)
    try:
        with sync_playwright() as factory:
            browser = factory.chromium.launch()
            try:
                capture_offline(browser, running.url)
                capture_connected(browser, running.url)
            finally:
                browser.close()
    finally:
        running.stop()


if __name__ == "__main__":
    main()
