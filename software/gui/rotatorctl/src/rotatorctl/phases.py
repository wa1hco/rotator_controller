# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Phase boundaries for the PC application.

Phase 1 is configuration. Phase 2 is operation. Phase 3 is install and
upgrade. Later milestones land behind these names.
"""

from __future__ import annotations

PHASE_CONFIGURE = 1
PHASE_OPERATE = 2
PHASE_UPGRADE = 3

OPERATE_MILESTONES = (
    "heading display per axis",
    "go to bearing",
    "cw/ccw jog",
    "stop",
    "park and auto-park",
    "heading preset recall",
    "soft limits, coast, creep, and stall stop",
    "pwm ramp on a dc drive",
    "calibration wizard and multi-point map",
    "gs-232b commands beyond M, C, and S",
    "hamlib rotctld",
    "easycom",
    "dcu-1",
    "live log",
    "multi-rotator dashboard",
)

UPGRADE_MILESTONES = (
    "usb dfu first install",
    "field upgrade into the inactive slot",
    "progress and rollback status",
    "version report",
)
