# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Render the configuration windows with two simulated controllers.

Run from anywhere:

    QT_QPA_PLATFORM=offscreen python software/gui/scripts/capture_screenshots.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rotatorctl" / "src"))
sys.path.insert(0, str(ROOT / "rotatorctl-gui" / "src"))

from PySide6.QtGui import QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from rotatorctl.discovery import USB_PID, USB_VID, ControllerInfo, Endpoint  # noqa: E402
from rotatorctl.sim import demo_pair  # noqa: E402
from rotatorctl_gui.main_window import MainWindow  # noqa: E402

OUT = ROOT / "docs" / "screenshots"


def save_widget(widget, path: Path, width: int, height: int) -> None:
    widget.resize(width, height)
    widget.show()
    app.processEvents()
    widget.grab().save(str(path))
    if path.stat().st_size < 8000:
        pixmap = QPixmap(widget.size())
        widget.render(pixmap)
        pixmap.save(str(path))
    if path.stat().st_size < 8000:
        raise SystemExit(f"screenshot looks empty: {path} ({path.stat().st_size} bytes)")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    usb, net = demo_pair()
    usb.start()
    net.start()
    try:
        window = MainWindow()
        window.set_controllers(
            [
                ControllerInfo(
                    serial="RC-SIM-USB",
                    name="Bench",
                    firmware="0.1.0-sim",
                    axes="az",
                    vid=USB_VID,
                    pid=USB_PID,
                    endpoints=[Endpoint("usb", usb.serial_target(), "USB CDC")],
                ),
                ControllerInfo(
                    serial="RC-SIM-NET",
                    name="Tower",
                    firmware="0.1.0-sim",
                    axes="az+el",
                    name_from_mdns=True,
                    endpoints=[Endpoint("tcp", net.tcp_target(), "mDNS")],
                ),
            ]
        )
        window.resize(1280, 800)
        window.show()
        app.processEvents()
        window.list.setCurrentRow(0)
        window.list.setFocus()
        app.processEvents()
        window.grab().save(str(OUT / "controllers.png"))

        window.connect_to(1)
        assert window.form is not None
        window.form.set_value("net.hostname", "tower-east")
        window.form.set_value("net.address", "not-an-ip")
        app.processEvents()
        save_widget(window, OUT / "settings.png", 1280, 800)

        window.form.set_value("net.address", "10.1.1.20")
        window.form.set_value("safety.dead_time_ms", "750")
        dialog = window.make_save_dialog()
        if dialog is None:
            raise SystemExit("save dialog did not open")
        save_widget(dialog, OUT / "confirm-save.png", 760, 520)

        presets = window.make_preset_dialog()
        presets.select("yaesu-g-450a")
        save_widget(presets, OUT / "presets.png", 980, 680)
        print(f"wrote {OUT}")
    finally:
        usb.stop()
        net.stop()


app = QApplication([])

if __name__ == "__main__":
    main()
