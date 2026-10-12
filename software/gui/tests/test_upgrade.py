# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pytest

from rotatorctl.operate import stop_line
from rotatorctl.upgrade import DFU_ADDRESS, dfu_argv


def test_dfu_argv_does_not_run() -> None:
    assert dfu_argv("image.bin") == ["dfu-util", "-a", "0", "-s", f"{DFU_ADDRESS}:leave", "-D", "image.bin"]
    assert DFU_ADDRESS == "0x08000000"
    with pytest.raises(ValueError):
        dfu_argv("two words.bin")


def test_stop_line_is_gs232() -> None:
    assert stop_line() == "S"
