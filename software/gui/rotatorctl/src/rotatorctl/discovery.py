# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Find controllers on USB serial ports and on ``_rotatorctl._tcp``.

The USB numbers are the provisional identity in
``docs/design/configuration.md``. The same ``sys.serial`` on USB and on
mDNS is one controller.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

# Provisional until a pid.codes (or other) assignment exists.
USB_VID = 0x1209
USB_PID = 0xF407
USB_MANUFACTURER = "WA1HCO"
USB_PRODUCT = "Rotator Controller"
SERVICE_TYPE = "_rotatorctl._tcp.local."


@dataclass
class Endpoint:
    kind: str  # usb or tcp
    target: str  # serial://path or tcp://host:port
    detail: str = ""


@dataclass
class ControllerInfo:
    serial: str
    name: str = ""
    firmware: str = ""
    axes: str = ""
    schema_version: int = 1
    endpoints: list[Endpoint] = field(default_factory=list)
    vid: int | None = None
    pid: int | None = None
    name_from_mdns: bool = False


def preferred_target(info: ControllerInfo) -> str:
    for endpoint in info.endpoints:
        if endpoint.kind == "usb":
            return endpoint.target
    if not info.endpoints:
        raise ValueError("controller has no link")
    return info.endpoints[0].target


def scan_usb(ports: list[object] | None = None) -> list[ControllerInfo]:
    """Serial ports whose VID, PID, and serial string match the firmware."""
    if ports is None:
        from serial.tools import list_ports

        ports = list(list_ports.comports())
    found: list[ControllerInfo] = []
    for port in ports:
        vid = getattr(port, "vid", None)
        pid = getattr(port, "pid", None)
        if vid != USB_VID or pid != USB_PID:
            continue
        serial = getattr(port, "serial_number", None) or ""
        if not serial:
            continue
        device = getattr(port, "device", "") or ""
        found.append(
            ControllerInfo(
                serial=str(serial),
                name="",
                vid=vid,
                pid=pid,
                endpoints=[Endpoint("usb", f"serial://{device}", "USB CDC")],
            )
        )
    return found


def manual_tcp(host: str, port: int) -> ControllerInfo:
    return ControllerInfo(
        serial="",
        name=f"{host}:{port}",
        endpoints=[Endpoint("tcp", f"tcp://{host}:{port}", "manual")],
    )


def manual_serial(path: str) -> ControllerInfo:
    return ControllerInfo(
        serial="",
        name=path,
        endpoints=[Endpoint("usb", f"serial://{path}", "manual")],
    )


def merge_controllers(items: list[ControllerInfo]) -> list[ControllerInfo]:
    """Collapse rows that share a serial. Rows with an empty serial stay separate."""
    merged: list[ControllerInfo] = []
    index: dict[str, ControllerInfo] = {}
    for item in items:
        if not item.serial:
            merged.append(_copy(item))
            continue
        current = index.get(item.serial)
        if current is None:
            current = _copy(item)
            index[item.serial] = current
            merged.append(current)
            continue
        _fold(current, item)
    return merged


def _copy(item: ControllerInfo) -> ControllerInfo:
    return ControllerInfo(
        serial=item.serial,
        name=item.name,
        firmware=item.firmware,
        axes=item.axes,
        schema_version=item.schema_version,
        endpoints=list(item.endpoints),
        vid=item.vid,
        pid=item.pid,
        name_from_mdns=item.name_from_mdns,
    )


def _fold(dst: ControllerInfo, src: ControllerInfo) -> None:
    seen = {endpoint.target for endpoint in dst.endpoints}
    for endpoint in src.endpoints:
        if endpoint.target not in seen:
            dst.endpoints.append(endpoint)
            seen.add(endpoint.target)
    if src.name and (src.name_from_mdns or not dst.name):
        dst.name = src.name
        dst.name_from_mdns = dst.name_from_mdns or src.name_from_mdns
    if src.firmware and not dst.firmware:
        dst.firmware = src.firmware
    if src.axes and not dst.axes:
        dst.axes = src.axes
    if src.vid is not None and dst.vid is None:
        dst.vid = src.vid
        dst.pid = src.pid
    if src.schema_version and not dst.schema_version:
        dst.schema_version = src.schema_version


class _Browser:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.by_name: dict[str, ControllerInfo] = {}

    def add_service(self, zc: object, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name, timeout=1000)  # type: ignore[attr-defined]
        if info is None:
            return
        props: dict[str, str] = {}
        for key, value in info.properties.items():
            key_text = key.decode() if isinstance(key, bytes) else str(key)
            if isinstance(value, bytes):
                value = value.decode()
            props[key_text] = "" if value is None else str(value)
        addresses = list(info.parsed_addresses())
        host = addresses[0] if addresses else "127.0.0.1"
        serial = props.get("id", "")
        controller = ControllerInfo(
            serial=serial,
            name=props.get("name", ""),
            firmware=props.get("fw", ""),
            axes=props.get("axes", ""),
            schema_version=int(props.get("schema") or 1),
            endpoints=[Endpoint("tcp", f"tcp://{host}:{info.port}", "mDNS")],
            name_from_mdns=bool(props.get("name")),
        )
        with self._lock:
            self.by_name[name] = controller

    def update_service(self, zc: object, type_: str, name: str) -> None:
        self.remove_service(zc, type_, name)
        self.add_service(zc, type_, name)

    def remove_service(self, zc: object, type_: str, name: str) -> None:
        with self._lock:
            self.by_name.pop(name, None)


def browse_mdns(timeout: float = 1.0, interfaces: list[str] | None = None) -> list[ControllerInfo]:
    """Browse ``_rotatorctl._tcp`` for ``timeout`` seconds."""
    from zeroconf import ServiceBrowser, Zeroconf

    zc = Zeroconf(interfaces=interfaces) if interfaces else Zeroconf()
    listener = _Browser()
    browser = ServiceBrowser(zc, SERVICE_TYPE, listener)
    try:
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(0.05)
    finally:
        browser.cancel()
        zc.close()
    with listener._lock:
        return list(listener.by_name.values())
