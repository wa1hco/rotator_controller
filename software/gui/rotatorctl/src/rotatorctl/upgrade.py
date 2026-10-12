# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Phase 3 install hooks.

``dfu_argv`` is the ROM DFU command from ADR 0015. It does not run
``dfu-util``. The console verb ``upgrade`` is reserved and the simulator
answers ``ERR unsupported``.
"""

from __future__ import annotations

DFU_ADDRESS = "0x08000000"


def dfu_argv(image: str) -> list[str]:
    if not image or any(ch.isspace() for ch in image):
        raise ValueError("image path is one token")
    return ["dfu-util", "-a", "0", "-s", f"{DFU_ADDRESS}:leave", "-D", image]
