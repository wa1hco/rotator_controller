# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""PyInstaller entry. The frozen executable calls this, then the GUI."""

from __future__ import annotations

from rotatorctl_gui.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
