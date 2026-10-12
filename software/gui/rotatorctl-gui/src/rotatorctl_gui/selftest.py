# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Launch check for a packaged build.

Starts the loopback server, fetches the page and the catalog, and exits.
The catalog has to come from the frozen bundle when PyInstaller is running.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.error
import urllib.request

from rotatorctl.presets import default_preset_path, load_presets, preset_path_is_bundled
from rotatorctl.paths import ensure_user_config_dir
from rotatorctl_gui.server import start_server
from rotatorctl_gui.state import AppState


def _say(message: str) -> None:
    data = (message + "\n").encode("utf-8", errors="replace")
    for fd in (2, 1):
        try:
            os.write(fd, data)
            return
        except OSError:
            continue


def run_selftest() -> int:
    running = None
    try:
        path = default_preset_path()
        presets = load_presets(path)
        if len(presets) < 39:
            _say(f"selftest: expected at least 39 presets, found {len(presets)} at {path}")
            return 1
        if getattr(sys, "frozen", False) and not preset_path_is_bundled(path):
            _say(f"selftest: presets resolved outside the bundle: {path}")
            return 1
        config = ensure_user_config_dir()
        probe = config / ".selftest-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        state = AppState(presets=presets, idle_seconds=0)
        state.token = "selftest"
        running = start_server(state, idle_seconds=0)
        if "127.0.0.1" not in running.url:
            _say(f"selftest: server is not loopback: {running.url}")
            return 1
        root = running.url.split("/s/")[0]
        try:
            urllib.request.urlopen(root + "/", timeout=5)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                _say(f"selftest: bare URL returned {exc.code}")
                return 1
        else:
            _say("selftest: bare URL should be rejected")
            return 1
        page = urllib.request.urlopen(running.url, timeout=5)
        html = page.read().decode("utf-8")
        if page.status != 200 or "Rotator Controller" not in html or "app.js" not in html:
            _say("selftest: index page did not load")
            return 1
        catalog = urllib.request.urlopen(running.url + "api/catalog", timeout=5)
        payload = json.loads(catalog.read().decode("utf-8"))
        count = len(payload.get("presets") or [])
        if count < 39:
            _say(f"selftest: catalog API returned {count}")
            return 1
        _say(f"selftest: ok presets={count} path={path} url={running.url} config={config}")
        return 0
    except Exception:
        _say("selftest: failed")
        _say(traceback.format_exc())
        return 1
    finally:
        if running is not None:
            running.stop()
