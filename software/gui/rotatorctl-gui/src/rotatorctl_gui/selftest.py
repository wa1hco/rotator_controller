# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Launch check for a packaged build.

``RotatorController --selftest`` loads the catalog, writes the config
directory, shows the window offscreen, and returns 0. A frozen build
must read the catalog from inside the bundle. CI checks out the
repository, so a parent-directory walk would otherwise hide a missing
``--add-data``.
"""

from __future__ import annotations

import os
import sys
import traceback


def _say(message: str) -> None:
    data = (message + "\n").encode("utf-8", errors="replace")
    for fd in (2, 1):
        try:
            os.write(fd, data)
            return
        except OSError:
            continue


def run_selftest() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication

        from rotatorctl.paths import ensure_user_config_dir
        from rotatorctl.presets import default_preset_path, load_presets, preset_path_is_bundled
        from rotatorctl_gui.main_window import MainWindow

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

        app = QApplication.instance()
        if app is None:
            app = QApplication(["RotatorController", "--selftest"])
        window = MainWindow()
        window.resize(1280, 800)
        window.show()
        app.processEvents()
        shown = window.browser.list.count()
        window.close()
        app.processEvents()
        if shown < 39:
            _say(f"selftest: catalog list showed {shown} rows")
            return 1
        _say(f"selftest: ok presets={len(presets)} path={path} config={config}")
        return 0
    except Exception:
        _say("selftest: failed")
        _say(traceback.format_exc())
        return 1
