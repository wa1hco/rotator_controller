# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Settings schema carried by the ``schema`` console command.

The GUI builds forms from this document. Adding a setting in the firmware
is a schema change, not a GUI change.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SettingType(str, Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    ENUM = "enum"
    STRING = "string"


class SettingSpec(BaseModel):
    name: str
    type: SettingType
    unit: str = ""
    min: float | None = None
    max: float | None = None
    enum: list[str] = Field(default_factory=list)
    default: str
    help: str = ""
    reboot: bool = False
    readonly: bool = False


class Schema(BaseModel):
    version: int = 1
    settings: list[SettingSpec]

    def by_name(self) -> dict[str, SettingSpec]:
        return {spec.name: spec for spec in self.settings}

    def get(self, name: str) -> SettingSpec | None:
        return self.by_name().get(name)


_SENSORS = ["dual_end_pot", "single_ended_pot", "rheostat", "pulse", "none"]
_BRAKES = ["wedge_solenoid", "electric_positive_lock", "none"]
_LEVELS = ["error", "warn", "info", "debug"]


def _spec(name: str, kind: SettingType, default: str, **kwargs: object) -> SettingSpec:
    return SettingSpec(name=name, type=kind, default=default, **kwargs)  # type: ignore[arg-type]


def _axis(prefix: str, title: str, present: str) -> list[SettingSpec]:
    return [
        _spec(
            f"{prefix}.present",
            SettingType.BOOL,
            present,
            help=f"The board file stuffed {title.lower()} hardware. The operator cannot turn an absent axis on.",
            readonly=True,
        ),
        _spec(
            f"{prefix}.sensor",
            SettingType.ENUM,
            "dual_end_pot",
            enum=list(_SENSORS),
            help=f"{title} position sensor.",
        ),
        _spec(
            f"{prefix}.travel_min_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=0,
            max=540,
            help=f"Counter-clockwise end of {title.lower()} travel.",
        ),
        _spec(
            f"{prefix}.travel_max_deg",
            SettingType.FLOAT,
            "450" if prefix == "az" else "180",
            unit="deg",
            min=0,
            max=540,
            help=f"Clockwise end of {title.lower()} travel, including overlap.",
        ),
        _spec(
            f"{prefix}.overlap_deg",
            SettingType.FLOAT,
            "90" if prefix == "az" else "0",
            unit="deg",
            min=0,
            max=180,
            help="Travel past 360 degrees. Zero when the rotor has no overlap.",
        ),
        _spec(
            f"{prefix}.cal.cw_end",
            SettingType.FLOAT,
            "0",
            unit="count",
            min=-10,
            max=100000,
            help="Sensor reading at the clockwise end. Written by the calibration sweep.",
        ),
        _spec(
            f"{prefix}.cal.ccw_end",
            SettingType.FLOAT,
            "0",
            unit="count",
            min=-10,
            max=100000,
            help="Sensor reading at the counter-clockwise end.",
        ),
        _spec(
            f"{prefix}.brake",
            SettingType.ENUM,
            "wedge_solenoid" if prefix == "az" else "none",
            enum=list(_BRAKES),
            help=f"{title} brake. Energized means released on a CDE wedge.",
        ),
        _spec(
            f"{prefix}.brake_delay_s",
            SettingType.FLOAT,
            "3" if prefix == "az" else "0",
            unit="s",
            min=0,
            max=30,
            help="How long the brake stays released after the motor stops.",
        ),
        _spec(
            f"{prefix}.speed_min_s",
            SettingType.INT,
            "45",
            unit="s",
            min=5,
            max=300,
            help="Fastest full-scale travel, in seconds.",
        ),
        _spec(
            f"{prefix}.speed_max_s",
            SettingType.INT,
            "60",
            unit="s",
            min=5,
            max=300,
            help="Slowest full-scale travel, in seconds.",
        ),
        _spec(
            f"{prefix}.park_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=0,
            max=540 if prefix == "az" else 180,
            help=f"{title} heading used by Park.",
        ),
    ]


def default_schema(
    *,
    serial: str = "RC-0000",
    hostname: str = "rotator",
    firmware: str = "0.0.0",
    board: str = "f407-v1",
    azimuth: bool = True,
    elevation: bool = False,
) -> Schema:
    """Schema version 1, the namespaces in docs/design/configuration.md.

    ``azimuth`` and ``elevation`` are board facts. They change the default
    of ``*.present`` and nothing else. Both flags stay read-only.
    """
    settings: list[SettingSpec] = [
        _spec("sys.schema", SettingType.INT, "1", min=1, max=1, readonly=True, help="Settings schema version."),
        _spec("sys.serial", SettingType.STRING, serial, readonly=True, help="Stable device serial. Same string on USB and Ethernet."),
        _spec("sys.firmware", SettingType.STRING, firmware, readonly=True, help="Running firmware version."),
        _spec("sys.board", SettingType.STRING, board, readonly=True, help="Board file name."),
        _spec(
            "net.hostname",
            SettingType.STRING,
            hostname,
            reboot=True,
            help="User-assigned name. Also the mDNS instance name. Letters, digits, hyphens.",
        ),
        _spec("net.dhcp", SettingType.BOOL, "true", reboot=True, help="Take an address from DHCP."),
        _spec(
            "net.address",
            SettingType.STRING,
            "192.168.1.50",
            reboot=True,
            help="Static IPv4 address, used when net.dhcp is false.",
        ),
        _spec("net.mdns", SettingType.BOOL, "true", reboot=True, help="Advertise _rotatorctl._tcp."),
        _spec(
            "ports.tcp",
            SettingType.INT,
            "4533",
            unit="port",
            min=1,
            max=65535,
            reboot=True,
            help="TCP port for the shared console and GS-232 listener. There is no GS-232/console mode switch.",
        ),
        _spec(
            "ports.gs232_query",
            SettingType.ENUM,
            "C2",
            enum=["C", "C2"],
            help="Query token this station's logger sends. The port still accepts both C and C2.",
        ),
        *_axis("az", "Azimuth", "true" if azimuth else "false"),
        *_axis("el", "Elevation", "true" if elevation else "false"),
        _spec(
            "ui.log_level",
            SettingType.ENUM,
            "info",
            enum=list(_LEVELS),
            help="RAM log level. Same as `log level`.",
        ),
        _spec("ui.console_echo", SettingType.BOOL, "false", help="Echo received console lines. Off when a logger is attached."),
        _spec(
            "ui.angle_unit",
            SettingType.ENUM,
            "deg",
            enum=["deg"],
            help="Bearings are stored and shown in degrees.",
        ),
        _spec(
            "ui.display_range",
            SettingType.ENUM,
            "full_travel",
            enum=["full_travel", "modulo_360"],
            help="full_travel shows the overlap range, such as 0 to 450. modulo_360 wraps the heading.",
        ),
        _spec(
            "ui.speed_display",
            SettingType.ENUM,
            "seconds",
            enum=["seconds", "deg_per_s"],
            help="How travel time is shown. Stored speeds stay in seconds for a full-scale move.",
        ),
        _spec(
            "ui.cardinal_labels",
            SettingType.BOOL,
            "true",
            help="Label N, E, S, and W on the heading display.",
        ),
        _spec(
            "park.brake",
            SettingType.ENUM,
            "engage",
            enum=["engage", "leave"],
            help="engage sets the brake at the park heading. leave keeps it released.",
        ),
        _spec(
            "safety.dead_time_ms",
            SettingType.INT,
            "500",
            unit="ms",
            min=0,
            max=10000,
            help="Firmware pause before reversing. The hardware interlock is separate.",
        ),
        _spec(
            "safety.max_run_s",
            SettingType.INT,
            "120",
            unit="s",
            min=1,
            max=600,
            help="Motor run limit. The drive drops when this elapses.",
        ),
        _spec(
            "safety.stall_a",
            SettingType.FLOAT,
            "6",
            unit="A",
            min=0,
            max=30,
            help="AC current above this, while commanded to move, is a stall.",
        ),
    ]
    return Schema(version=1, settings=settings)
