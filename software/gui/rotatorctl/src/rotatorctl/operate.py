# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Phase 2 entry points.

The configuration window shows these actions and leaves them disabled.
``stop_line`` is the GS-232B stop the operate panel will send on the
shared port. ``calibrate`` stays a console verb and the simulator
answers ``ERR unsupported``.
"""

from __future__ import annotations

from rotatorctl.phases import PHASE_OPERATE


def phase() -> int:
    return PHASE_OPERATE


def stop_line() -> str:
    return "S"
