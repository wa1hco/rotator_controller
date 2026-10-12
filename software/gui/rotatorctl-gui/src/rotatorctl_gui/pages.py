# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Preference pages the browser UI renders from the schema.

The static page does not hard-code the setting list. ``GET /api/pages``
returns this document, and a later firmware web server can return the
same shape.
"""

from __future__ import annotations


def _memories() -> list[str]:
    names: list[str] = []
    for index in range(1, 7):
        names.append(f"preset.{index}.az")
        names.append(f"preset.{index}.el")
    return names


def page_list() -> list[dict[str, object]]:
    return [
        {"id": "rotator", "title": "Rotator", "intro": "", "fields": []},
        {
            "id": "axes",
            "title": "Axes",
            "intro": (
                "Sensor and brake for each axis. Presence and the power stage are board facts: "
                "a push leaves the controller's own flags alone. Pulse, encoder, and averaging "
                "options are under Advanced."
            ),
            "fields": [
                "sys.drive",
                "az.present",
                "az.sensor",
                "az.brake",
                "az.brake_delay_s",
                "el.present",
                "el.sensor",
                "el.brake",
                "el.brake_delay_s",
                "az.pulse_debounce_ms",
                "az.pulse_deg",
                "az.adc_samples",
                "az.limit_switch",
                "el.pulse_debounce_ms",
                "el.pulse_deg",
                "el.adc_samples",
                "el.limit_switch",
            ],
        },
        {
            "id": "limits",
            "title": "Limits",
            "intro": (
                "Travel, the north or south center, overlap, coast, speed, and the safety stops. "
                "Soft limits are the travel ends. Creep, PWM ramp, and the jam window are under Advanced."
            ),
            "fields": [
                "az.travel_min_deg",
                "az.travel_max_deg",
                "az.overlap_deg",
                "az.center",
                "az.coast_deg",
                "az.speed_min_s",
                "az.speed_max_s",
                "el.travel_min_deg",
                "el.travel_max_deg",
                "el.overlap_deg",
                "el.coast_deg",
                "el.speed_min_s",
                "el.speed_max_s",
                "safety.dead_time_ms",
                "safety.max_run_s",
                "safety.stall_a",
                "safety.stall_timeout_s",
                "az.creep_deg",
                "az.ramp_s",
                "az.slowdown_deg",
                "az.tolerance_deg",
                "el.creep_deg",
                "el.ramp_s",
                "el.slowdown_deg",
                "el.tolerance_deg",
                "safety.stall_deg",
            ],
        },
        {
            "id": "park",
            "title": "Park",
            "intro": (
                "Headings Park will use, whether the brake sets on arrival, and an idle timeout. "
                "Six heading memories sit under Advanced. Recalling them is an operate action."
            ),
            "fields": ["az.park_deg", "el.park_deg", "park.brake", "park.idle_min", *_memories()],
        },
        {
            "id": "calibration",
            "title": "Calibration",
            "intro": (
                "Heading offset and the end readings from the calibration sweep. The sweep itself "
                "is a later step. A preset does not overwrite these. The multi-point map is under Advanced."
            ),
            "fields": [
                "az.offset_deg",
                "el.offset_deg",
                "az.cal.cw_end",
                "az.cal.ccw_end",
                "el.cal.cw_end",
                "el.cal.ccw_end",
                "az.cal.map",
                "el.cal.map",
            ],
        },
        {
            "id": "display",
            "title": "Display",
            "intro": "How headings and speed are shown. Stored angles stay in degrees.",
            "fields": ["ui.angle_unit", "ui.display_range", "ui.speed_display", "ui.cardinal_labels"],
        },
        {
            "id": "network",
            "title": "Network",
            "intro": (
                "Name and address to push later. The name is also the mDNS hostname. Nothing is "
                "advertised until a controller is connected. The admin lock is under Advanced."
            ),
            "fields": [
                "net.hostname",
                "net.dhcp",
                "net.address",
                "net.mdns",
                "net.admin_lock",
                "net.admin_password",
            ],
        },
        {
            "id": "console",
            "title": "Console",
            "intro": (
                "The TCP port is shared by the text console and GS-232. There is no mode switch. "
                "S is stop. status and save are console commands. rotctld, Easycom, and DCU-1 are "
                "extra listeners under Advanced, off until phase 2."
            ),
            "fields": [
                "ports.tcp",
                "ports.gs232_query",
                "ui.console_echo",
                "ui.log_level",
                "ports.rotctld",
                "ports.easycom",
                "ports.dcu1",
            ],
        },
        {"id": "controllers", "title": "Controllers", "intro": "", "fields": []},
    ]
