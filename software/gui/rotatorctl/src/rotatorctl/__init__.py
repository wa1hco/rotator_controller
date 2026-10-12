# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Console protocol and settings model for the WA1HCO rotator controller.

This package has no GUI dependency. The desktop app is ``rotatorctl-gui``.
"""

from rotatorctl.schema import Schema, SettingSpec, default_schema

__all__ = ["Schema", "SettingSpec", "default_schema"]
__version__ = "0.1.0"
