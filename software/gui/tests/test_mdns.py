# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import time

from rotatorctl.discovery import browse_mdns
from rotatorctl.sim import SimInstance


def test_simulator_advertises_rotatorctl(presets) -> None:
    inst = SimInstance(
        serial="RC-MDNS-1",
        name="Beacon",
        presets=presets,
        tcp=True,
        pty=False,
        mdns=True,
        azimuth=True,
        elevation=True,
    )
    inst.start()
    try:
        time.sleep(0.3)
        found = browse_mdns(2.0, interfaces=["127.0.0.1"])
        match = [item for item in found if item.serial == "RC-MDNS-1"]
        assert match, found
        assert match[0].name == "Beacon"
        assert match[0].name_from_mdns is True
        assert match[0].axes == "az+el"
        assert match[0].endpoints[0].target == inst.tcp_target()
    finally:
        inst.stop()
