# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""GS-232 whole-line match, the same rules as the firmware parser.

The C++ function is ``rotator::protocol::parse_gs232``. A line is GS-232
only when the whole trimmed line is in that closed set. ``S`` is stop.
``status`` and ``save`` are not.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gs232Command:
    verb: str  # stop, query, azimuth
    azimuth_deg: int = 0


def parse_gs232(line: str) -> Gs232Command | None:
    text = line.strip().upper()
    if not text:
        return None
    if text in ("A", "S"):
        return Gs232Command("stop")
    if text in ("C", "C2"):
        return Gs232Command("query")
    if text[0] != "M" or not 2 <= len(text) <= 4 or not text[1:].isdigit():
        return None
    return Gs232Command("azimuth", int(text[1:]))
