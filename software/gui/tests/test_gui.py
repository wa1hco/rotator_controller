# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMenu, QPushButton

from rotatorctl.discovery import USB_PID, USB_VID, ControllerInfo, Endpoint
from rotatorctl.protocol import ConsoleClient
from rotatorctl.schema import Schema, SettingSpec, SettingType, default_schema
from rotatorctl.sim import SimInstance
from rotatorctl.transport import open_target
from rotatorctl_gui.form import SettingsForm
from rotatorctl_gui.main_window import MainWindow


def test_form_grows_a_new_setting(qtbot) -> None:
    base = default_schema()
    extra = SettingSpec(name="rf.gain", type=SettingType.INT, default="3", min=0, max=10, help="A later setting")
    schema = Schema(version=1, settings=[*base.settings, extra])
    form = SettingsForm(schema, {spec.name: spec.default for spec in schema.settings})
    qtbot.addWidget(form)
    assert form.has_field("rf.gain")
    assert form.has_field("az.sensor")
    assert form.group_title("rf") == "rf"
    assert form.value("rf.gain") == "3"


def test_list_shows_usb_and_network(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    window.set_controllers(
        [
            ControllerInfo(
                serial="RC-SIM-USB",
                name="Bench",
                firmware="0.1.0-sim",
                axes="az",
                vid=USB_VID,
                pid=USB_PID,
                endpoints=[Endpoint("usb", "serial:///dev/pts/9", "USB CDC")],
            ),
            ControllerInfo(
                serial="RC-SIM-NET",
                name="Tower",
                firmware="0.1.0-sim",
                axes="az+el",
                name_from_mdns=True,
                endpoints=[Endpoint("tcp", "tcp://127.0.0.1:4533", "mDNS")],
            ),
        ]
    )
    assert window.list.count() == 2
    text = "\n".join(window.list.item(index).text() for index in range(window.list.count()))
    assert "USB 1209:f407" in text
    assert "network" in text
    assert "Bench" in text
    assert "Tower" in text
    stop = window.findChild(QPushButton, "stopButton")
    assert stop is not None and stop.isEnabled() is False
    menu = window.findChild(QMenu, "operateMenu")
    assert menu is not None
    assert menu.actions()
    assert all(not action.isEnabled() for action in menu.actions())
    dfu = window.findChild(QAction, "dfuAction")
    assert dfu is not None and dfu.isEnabled() is False
    assert "dfu-util" in dfu.toolTip()
    assert "0x08000000" in dfu.toolTip()


def test_same_serial_collapses_in_the_list(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    window.set_controllers(
        [
            ControllerInfo(
                serial="SAME",
                vid=USB_VID,
                pid=USB_PID,
                endpoints=[Endpoint("usb", "serial:///dev/ttyACM0")],
            ),
            ControllerInfo(
                serial="SAME",
                name="tower",
                name_from_mdns=True,
                endpoints=[Endpoint("tcp", "tcp://10.0.0.5:4533")],
            ),
        ]
    )
    assert window.list.count() == 1
    text = window.list.item(0).text()
    assert "USB 1209:f407" in text
    assert "network" in text
    assert "tower" in text


def test_edit_validates_and_confirms_before_write(qtbot, presets) -> None:
    inst = SimInstance(serial="RC-GUI-1", name="Alpha", presets=presets, tcp=True, pty=False, mdns=False)
    inst.start()
    try:
        window = MainWindow(presets=presets)
        qtbot.addWidget(window)
        window.resize(1280, 800)
        window.set_controllers(
            [
                ControllerInfo(
                    serial="RC-GUI-1",
                    name="Alpha",
                    endpoints=[Endpoint("tcp", inst.tcp_target(), "mDNS")],
                )
            ]
        )
        window.connect_to(0)
        assert window.form is not None
        assert window.form.value("net.hostname") == "Alpha"
        assert window.is_dirty() is False
        window.show()
        window.form.set_value("net.address", "not-an-ip")
        assert "IPv4" in window.form.error_text("net.address")
        assert window.is_dirty()
        assert window.windowTitle().endswith("*")
        assert window.dirty.isVisible()
        assert window.make_save_dialog() is None
        window.form.set_value("net.address", "10.1.1.10")
        window.form.set_value("net.hostname", "alpha-2")
        window.form.set_value("safety.dead_time_ms", "750")
        dialog = window.make_save_dialog()
        assert dialog is not None
        assert "net.hostname" in dialog.summary()
        assert "safety.dead_time_ms" in dialog.summary()
        note = dialog.findChild(QLabel, "diffNote")
        assert note is not None and "net.hostname" in note.text()
        window.write_pending()
        assert window.is_dirty() is False
        probe = ConsoleClient(open_target(inst.tcp_target()))
        try:
            assert probe.get("net.hostname") == "alpha-2"
            assert probe.get("safety.dead_time_ms") == "750"
        finally:
            probe.close()
    finally:
        window.close()
        inst.stop()


def test_copy_dirties_the_editor_only(qtbot, presets) -> None:
    left = SimInstance(serial="RC-A", name="Alpha", presets=presets, tcp=True, mdns=False)
    right = SimInstance(serial="RC-B", name="Beta", presets=presets, tcp=True, mdns=False)
    left.start()
    right.start()
    try:
        window = MainWindow(presets=presets)
        qtbot.addWidget(window)
        infos = [
            ControllerInfo(serial="RC-A", name="Alpha", endpoints=[Endpoint("tcp", left.tcp_target())]),
            ControllerInfo(serial="RC-B", name="Beta", endpoints=[Endpoint("tcp", right.tcp_target())]),
        ]
        window.set_controllers(infos)
        window.connect_to(0)
        window.copy_from(infos[1])
        assert window.form is not None
        assert window.form.value("net.hostname") == "Beta"
        assert window.is_dirty() is True
        probe = ConsoleClient(open_target(left.tcp_target()))
        try:
            assert probe.get("net.hostname") == "Alpha"
        finally:
            probe.close()
    finally:
        window.close()
        left.stop()
        right.stop()


def test_preset_dialog_shows_family_and_unverified(qtbot, presets) -> None:
    window = MainWindow(presets=presets)
    qtbot.addWidget(window)
    dialog = window.make_preset_dialog()
    qtbot.addWidget(dialog)
    dialog.select("yaesu-g-450a")
    assert "Yaesu-AC-pot" in dialog.family.text()
    assert "sensor.ohms [?]" in dialog.unverified.text()
    assert "motor.volts [?]" in dialog.unverified.text()
    assert "single_ended_pot" in dialog.settings.toPlainText()
    assert dialog.apply_btn.isEnabled()
    dialog.select("alias-telex-dcu")
    assert dialog.apply_btn.isEnabled() is False
    assert "hygain-ham-iv" in dialog.alias.text()
    try:
        dialog.select("hygain-ar-40")
    except KeyError:
        missing = True
    else:
        missing = False
    assert missing


def test_backup_and_restore(qtbot, presets, tmp_path) -> None:
    inst = SimInstance(serial="RC-GUI-2", name="Gamma", presets=presets, tcp=True, mdns=False)
    inst.start()
    try:
        window = MainWindow(presets=presets)
        qtbot.addWidget(window)
        window.set_controllers(
            [ControllerInfo(serial="RC-GUI-2", name="Gamma", endpoints=[Endpoint("tcp", inst.tcp_target())])]
        )
        window.connect_to(0)
        window.form.set_value("ui.log_level", "debug")
        path = tmp_path / "backup.txt"
        window.backup_to(str(path))
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# rotator-settings 1\n")
        assert "ui.log_level = debug" in text
        window.form.set_value("ui.log_level", "warn")
        changes = window.preview_restore(text)
        assert any(change.name == "ui.log_level" and change.new == "debug" for change in changes)
        window.apply_restore(text)
        assert window.form.value("ui.log_level") == "debug"
        probe = ConsoleClient(open_target(inst.tcp_target()))
        try:
            assert probe.get("ui.log_level") == "debug"
        finally:
            probe.close()
    finally:
        window.close()
        inst.stop()
