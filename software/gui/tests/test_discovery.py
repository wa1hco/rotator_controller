# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from rotatorctl.discovery import (
    USB_PID,
    USB_VID,
    ControllerInfo,
    Endpoint,
    manual_tcp,
    merge_controllers,
    scan_usb,
)


class _Port:
    def __init__(self, device: str, vid: int | None, pid: int | None, serial_number: str | None) -> None:
        self.device = device
        self.vid = vid
        self.pid = pid
        self.serial_number = serial_number


def test_usb_match_is_vid_pid_and_serial() -> None:
    ports = [
        _Port("/dev/ttyACM0", USB_VID, USB_PID, "ABC123"),
        _Port("/dev/ttyUSB0", 0x0403, 0x6001, "FTDI"),
        _Port("/dev/ttyACM1", USB_VID, USB_PID, ""),
    ]
    found = scan_usb(ports)
    assert len(found) == 1
    assert found[0].serial == "ABC123"
    assert found[0].vid == USB_VID
    assert found[0].endpoints[0].target == "serial:///dev/ttyACM0"


def test_same_serial_is_one_controller() -> None:
    usb = ControllerInfo(
        serial="ABC123",
        name="",
        vid=USB_VID,
        pid=USB_PID,
        endpoints=[Endpoint("usb", "serial:///dev/ttyACM0", "USB CDC")],
    )
    net = ControllerInfo(
        serial="ABC123",
        name="tower",
        firmware="1.2.0",
        axes="az",
        name_from_mdns=True,
        endpoints=[Endpoint("tcp", "tcp://10.0.0.5:4533", "mDNS")],
    )
    merged = merge_controllers([usb, net])
    assert len(merged) == 1
    assert merged[0].name == "tower"
    assert merged[0].name_from_mdns is True
    assert {endpoint.kind for endpoint in merged[0].endpoints} == {"usb", "tcp"}
    flipped = merge_controllers([net, usb])
    assert flipped[0].name == "tower"
    assert len(flipped[0].endpoints) == 2


def test_blank_serials_stay_separate() -> None:
    rows = merge_controllers([manual_tcp("10.0.0.8", 4533), manual_tcp("10.0.0.9", 4533)])
    assert len(rows) == 2
