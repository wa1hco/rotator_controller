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
    advanced: bool = False


class Schema(BaseModel):
    version: int = 1
    settings: list[SettingSpec]

    def by_name(self) -> dict[str, SettingSpec]:
        return {spec.name: spec for spec in self.settings}

    def get(self, name: str) -> SettingSpec | None:
        return self.by_name().get(name)


_SENSORS = [
    "dual_end_pot",
    "single_ended_pot",
    "rheostat",
    "pulse",
    "incremental_encoder",
    "hh12_as5045",
    "none",
]
_BRAKES = ["wedge_solenoid", "electric_positive_lock", "none"]
_LEVELS = ["error", "warn", "info", "debug"]
_DRIVES = ["triac", "relay", "dc_hbridge"]


def _spec(name: str, kind: SettingType, default: str, **kwargs: object) -> SettingSpec:
    return SettingSpec(name=name, type=kind, default=default, **kwargs)  # type: ignore[arg-type]


def _axis(prefix: str, title: str, present: str) -> list[SettingSpec]:
    specs = [
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
            help=(
                f"{title} position sensor. Pots and pulse use the stock rotor cable. "
                "incremental_encoder and hh12_as5045 use the encoder header on a later board."
            ),
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
    ]
    if prefix == "az":
        specs.append(
            _spec(
                "az.center",
                SettingType.ENUM,
                "north",
                enum=["north", "south"],
                help="Center of azimuth travel. north puts the stops at south, the usual 450 degree overlap. south puts the stops at north.",
            )
        )
    specs.extend(
        [
        _spec(
            f"{prefix}.offset_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=-180,
            max=180,
            help=f"Added to the {title.lower()} sensor heading. Mast slip, a second antenna, or magnetic declination.",
        ),
        _spec(
            f"{prefix}.coast_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=0,
            max=30,
            help="Drop the motor this many degrees before the target and let the antenna coast in. 0 keeps the motor on until the target.",
        ),
        _spec(
            f"{prefix}.tolerance_deg",
            SettingType.FLOAT,
            "3" if prefix == "az" else "1",
            unit="deg",
            min=0,
            max=20,
            advanced=True,
            help="A go-to stops when the heading is inside this window.",
        ),
        _spec(
            f"{prefix}.creep_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=0,
            max=30,
            advanced=True,
            help="Last degrees of an AC move run at reduced drive. 0 runs full drive to the coast point.",
        ),
        _spec(
            f"{prefix}.ramp_s",
            SettingType.FLOAT,
            "0",
            unit="s",
            min=0,
            max=30,
            advanced=True,
            help="PWM ramp-up time on a DC drive. 0 is full voltage at once. An AC cap-run motor stays at 0.",
        ),
        _spec(
            f"{prefix}.slowdown_deg",
            SettingType.FLOAT,
            "0",
            unit="deg",
            min=0,
            max=45,
            advanced=True,
            help="PWM ramp-down starts this many degrees before the target. 0 holds speed until the coast point.",
        ),
        _spec(
            f"{prefix}.pulse_debounce_ms",
            SettingType.INT,
            "0",
            unit="ms",
            min=0,
            max=2000,
            advanced=True,
            help="Ignore further edges on a reed or pulse input for this long. 0 counts every edge.",
        ),
        _spec(
            f"{prefix}.pulse_deg",
            SettingType.FLOAT,
            "0.5",
            unit="deg",
            min=0.01,
            max=10,
            advanced=True,
            help="Degrees represented by one pulse, for a reed, Hall sensor, or incremental encoder.",
        ),
        _spec(
            f"{prefix}.adc_samples",
            SettingType.INT,
            "8",
            min=1,
            max=64,
            advanced=True,
            help="ADC readings averaged for a potentiometer. 1 uses each sample as it arrives.",
        ),
        _spec(
            f"{prefix}.limit_switch",
            SettingType.BOOL,
            "false",
            advanced=True,
            help="CW and CCW limit inputs are wired. An open switch stops that direction.",
        ),
        _spec(
            f"{prefix}.cal.map",
            SettingType.STRING,
            "none",
            advanced=True,
            help="Multi-point map, raw:heading pairs separated by commas, or none for the two end readings.",
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
    )
    return specs


def _memories() -> list[SettingSpec]:
    rows: list[SettingSpec] = []
    for index in range(1, 7):
        rows.append(
            _spec(
                f"preset.{index}.az",
                SettingType.FLOAT,
                "0",
                unit="deg",
                min=0,
                max=540,
                advanced=True,
                help=f"Azimuth heading memory {index}. Operate recalls it.",
            )
        )
        rows.append(
            _spec(
                f"preset.{index}.el",
                SettingType.FLOAT,
                "0",
                unit="deg",
                min=0,
                max=180,
                advanced=True,
                help=f"Elevation heading memory {index}. Operate recalls it.",
            )
        )
    return rows


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
            "sys.drive",
            SettingType.ENUM,
            "triac",
            enum=list(_DRIVES),
            readonly=True,
            help="Power stage the board file stuffed. triac and relay are AC. dc_hbridge is the later DC module.",
        ),
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
            "net.admin_lock",
            SettingType.BOOL,
            "false",
            advanced=True,
            help="Ask for net.admin_password on the web UI and on console verbs. GS-232 lines on the same port stay open.",
        ),
        _spec(
            "net.admin_password",
            SettingType.STRING,
            "station",
            advanced=True,
            help="Token the web UI and console verbs ask for when net.admin_lock is true.",
        ),
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
        _spec(
            "ports.rotctld",
            SettingType.INT,
            "0",
            unit="port",
            min=0,
            max=65535,
            reboot=True,
            advanced=True,
            help="Hamlib rotctld listener. 0 leaves it off. Phase 2 speaks the protocol.",
        ),
        _spec(
            "ports.easycom",
            SettingType.INT,
            "0",
            unit="port",
            min=0,
            max=65535,
            reboot=True,
            advanced=True,
            help="Easycom listener. 0 leaves it off. Phase 2 speaks the protocol.",
        ),
        _spec(
            "ports.dcu1",
            SettingType.INT,
            "0",
            unit="port",
            min=0,
            max=65535,
            reboot=True,
            advanced=True,
            help="Hy-Gain DCU-1 listener. 0 leaves it off. Phase 2 speaks the protocol.",
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
            "park.idle_min",
            SettingType.INT,
            "0",
            unit="min",
            min=0,
            max=1440,
            help="Minutes with no motion before Park runs. 0 leaves the antenna where it stopped.",
        ),
        *_memories(),
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
        _spec(
            "safety.stall_timeout_s",
            SettingType.INT,
            "8",
            unit="s",
            min=1,
            max=120,
            help="No-motion stop. The drive drops when the heading fails to change during this time.",
        ),
        _spec(
            "safety.stall_deg",
            SettingType.FLOAT,
            "2",
            unit="deg",
            min=0.1,
            max=30,
            advanced=True,
            help="Heading change required during safety.stall_timeout_s. Less than this is a jam.",
        ),
    ]
    return Schema(version=1, settings=settings)
