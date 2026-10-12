# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pytest

from rotatorctl.presets import load_presets
from rotatorctl.protocol import ConsoleClient
from rotatorctl.sim import SimInstance
from rotatorctl.transport import open_target


@pytest.fixture(scope="session")
def presets():
    return load_presets()


@pytest.fixture
def sim(presets):
    inst = SimInstance(
        serial="RC-TEST-0001",
        name="Test",
        presets=presets,
        tcp=True,
        pty=False,
        mdns=False,
    )
    inst.start()
    try:
        yield inst
    finally:
        inst.stop()


@pytest.fixture
def client(sim):
    opened = ConsoleClient(open_target(sim.tcp_target()))
    try:
        yield opened
    finally:
        opened.close()
