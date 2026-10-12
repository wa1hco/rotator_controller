# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Where a station's configuration files live.

The bundled app has no repository checkout, so open and save start in the
platform config directory. ``ROTATOR_CONFIG_DIR`` overrides that for tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "RotatorController"
LINUX_NAME = "rotator-controller"


def user_config_dir(
    *,
    platform: str | None = None,
    environ: dict[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the directory for ``.rotcfg`` files. Does not create it."""

    env = os.environ if environ is None else environ
    override = env.get("ROTATOR_CONFIG_DIR")
    if override:
        return Path(override)
    system = sys.platform if platform is None else platform
    root = Path.home() if home is None else Path(home)
    if system == "win32":
        appdata = env.get("APPDATA")
        base = Path(appdata) if appdata else root / "AppData" / "Roaming"
        return base / APP_NAME
    if system == "darwin":
        return root / "Library" / "Application Support" / APP_NAME
    xdg = env.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else root / ".config"
    return base / LINUX_NAME


def ensure_user_config_dir(
    *,
    platform: str | None = None,
    environ: dict[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    path = user_config_dir(platform=platform, environ=environ, home=home)
    path.mkdir(parents=True, exist_ok=True)
    return path
