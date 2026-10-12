# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Configuration window: discover, edit, confirm, save, preset, backup, compare, copy."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from rotatorctl.discovery import (
    ControllerInfo,
    browse_mdns,
    manual_serial,
    manual_tcp,
    merge_controllers,
    preferred_target,
    scan_usb,
)
from rotatorctl.document import Change, SettingsDocument, SettingsError, format_value, parse_ini_lines
from rotatorctl.operate import stop_line
from rotatorctl.phases import OPERATE_MILESTONES, UPGRADE_MILESTONES
from rotatorctl.presets import Preset, axis_prefixes, can_apply, load_presets, settings_from_preset
from rotatorctl.rotcfg import RotConfig, dumps, loads, new_config, push_lines
from rotatorctl.protocol import CommandError, ConsoleClient
from rotatorctl.schema import Schema
from rotatorctl.transport import TransportError, open_target
from rotatorctl.upgrade import dfu_argv
from rotatorctl_gui.dialogs import DiffDialog, HostPortDialog, PresetDialog, SerialDialog
from rotatorctl_gui.form import SettingsForm
from rotatorctl_gui.rotator_browser import RotatorBrowser

_STYLE = """
QMainWindow, QDialog { background: #f6f3ec; color: #1c1917; }
QWidget { font-size: 13px; }
QListWidget { background: #fffdf8; border: 1px solid #d6d3d1; }
QListWidget::item { padding: 4px 6px; }
QListWidget::item:selected { background: #1f4d3a; color: white; }
QGroupBox {
    font-weight: 600;
    border: 1px solid #d6d3d1;
    margin-top: 12px;
    background: #fffdf8;
}
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit, QComboBox, QPlainTextEdit { background: white; }
QLabel#dirty, QLabel#fileDirty { background: #f4d35e; color: #1c1917; padding: 8px 10px; font-weight: 600; }
QLabel#offlinePill { background: #f4d35e; color: #1c1917; padding: 2px 8px; font-weight: 700; }
QListWidget#pageNav::item { padding: 8px 10px; }
QPushButton#stopButton { background: #9f1239; color: white; font-size: 16px; font-weight: 700; min-height: 40px; }
QPushButton#stopButton:disabled { background: #e7e5e4; color: #78716c; }
QFrame#header { background: #1f4d3a; }
QLabel#wordmark { color: white; font-size: 18px; font-weight: 700; }
QLabel#headerSub { color: #d6d3d1; }
QLabel#reboot { color: #9a3412; font-size: 11px; }
"""


def _preset_names() -> list[str]:
    names: list[str] = []
    for index in range(1, 7):
        names.append(f"preset.{index}.az")
        names.append(f"preset.{index}.el")
    return names


_PAGES: tuple[tuple[str, str, str, list[str]], ...] = (
    (
        "axes",
        "Axes",
        "Sensor and brake for each axis. Presence and the power stage are board facts: a push leaves the controller's own flags alone. Pulse, encoder, and averaging options are under Advanced.",
        [
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
    ),
    (
        "limits",
        "Limits",
        "Travel, the north or south center, overlap, coast, speed, and the safety stops. Soft limits are the travel ends. Creep, PWM ramp, and the jam window are under Advanced.",
        [
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
    ),
    (
        "park",
        "Park",
        "Headings Park will use, whether the brake sets on arrival, and an idle timeout. Six heading memories sit under Advanced. Recalling them is an operate action.",
        ["az.park_deg", "el.park_deg", "park.brake", "park.idle_min", *_preset_names()],
    ),
    (
        "calibration",
        "Calibration",
        "Heading offset and the end readings from the calibration sweep. The sweep itself is a later step. A preset does not overwrite these. The multi-point map is under Advanced.",
        [
            "az.offset_deg",
            "el.offset_deg",
            "az.cal.cw_end",
            "az.cal.ccw_end",
            "el.cal.cw_end",
            "el.cal.ccw_end",
            "az.cal.map",
            "el.cal.map",
        ],
    ),
    (
        "display",
        "Display",
        "How headings and speed are shown. Stored angles stay in degrees.",
        ["ui.angle_unit", "ui.display_range", "ui.speed_display", "ui.cardinal_labels"],
    ),
    (
        "network",
        "Network",
        "Name and address to push later. The name is also the mDNS hostname. Nothing is advertised until a controller is connected. The admin lock is under Advanced.",
        ["net.hostname", "net.dhcp", "net.address", "net.mdns", "net.admin_lock", "net.admin_password"],
    ),
    (
        "console",
        "Console",
        "The TCP port is shared by the text console and GS-232. There is no mode switch. S is stop. status and save are console commands. rotctld, Easycom, and DCU-1 are extra listeners under Advanced, off until phase 2.",
        [
            "ports.tcp",
            "ports.gs232_query",
            "ui.console_echo",
            "ui.log_level",
            "ports.rotctld",
            "ports.easycom",
            "ports.dcu1",
        ],
    ),
)


class MainWindow(QMainWindow):
    def __init__(self, presets: tuple[Preset, ...] | list[Preset] | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Rotator Controller")
        self.setMinimumSize(960, 640)
        self.setStyleSheet(_STYLE)
        self.presets: tuple[Preset, ...] | list[Preset]
        if presets is None:
            try:
                self.presets = load_presets()
            except FileNotFoundError:
                self.presets = ()
        else:
            self.presets = presets
        self.config = new_config()
        self.preset_id = ""
        self.overrides: dict[str, str] = {}
        self.rotcfg_path: Path | None = None
        self._syncing = False
        self._saved_token = self._token()
        self.page_forms: dict[str, SettingsForm] = {}
        self.infos: list[ControllerInfo] = []
        self.discovered: list[ControllerInfo] = []
        self.manual: list[ControllerInfo] = []
        self.client: ConsoleClient | None = None
        self.schema: Schema | None = None
        self.baseline: dict[str, str] = {}
        self.form: SettingsForm | None = None
        self.connected_serial = ""
        self.connected_target = ""
        self._build()

    def _build(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout(header)
        wordmark = QLabel("Rotator Controller")
        wordmark.setObjectName("wordmark")
        sub = QLabel("Offline configuration")
        sub.setObjectName("headerSub")
        header_layout.addWidget(wordmark)
        header_layout.addWidget(sub)
        outer.addWidget(header)
        outer.addWidget(self._build_file_bar())
        self.file_dirty = QLabel("Unsaved configuration. Save writes a .rotcfg file. Push sends it to a controller later.")
        self.file_dirty.setObjectName("fileDirty")
        self.file_dirty.setVisible(False)
        outer.addWidget(self.file_dirty)

        body = QSplitter()
        self.nav = QListWidget()
        self.nav.setObjectName("pageNav")
        self.nav.setFixedWidth(168)
        self._nav_keys = [
            "rotator",
            "axes",
            "limits",
            "park",
            "calibration",
            "display",
            "network",
            "console",
            "controllers",
        ]
        for label in (
            "Rotator",
            "Axes",
            "Limits",
            "Park",
            "Calibration",
            "Display",
            "Network",
            "Console",
            "Controllers",
        ):
            self.nav.addItem(label)
        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.browser = RotatorBrowser(self.presets)
        self.browser.use_requested.connect(self.use_preset)
        self.browser.override_set.connect(self._on_browser_override)
        self.browser.override_cleared.connect(self.clear_override)
        self.stack.addWidget(self.browser)
        for key, title, intro, names in _PAGES:
            self.stack.addWidget(self._preference_page(key, title, intro, names))
        device = QSplitter()
        device.addWidget(self._build_list())
        device.addWidget(self._build_editor())
        device.setStretchFactor(1, 1)
        device.setSizes([320, 960])
        self.stack.addWidget(device)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)
        body.addWidget(self.nav)
        body.addWidget(self.stack)
        body.setStretchFactor(1, 1)
        outer.addWidget(body, 1)

        self.stop = QPushButton("STOP")
        self.stop.setObjectName("stopButton")
        self.stop.setEnabled(False)
        self.stop.setToolTip(
            "Phase 2. STOP stays on this screen while a rotator is moving. "
            f"The operate panel sends {stop_line()!r} on the shared port."
        )
        outer.addWidget(self.stop)
        self.setCentralWidget(root)
        self._build_menus()
        status = QStatusBar()
        status.showMessage("Offline · no controller connected")
        self.setStatusBar(status)
        self._refresh_offline_views()

    def _build_list(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Controllers"))
        self.list = QListWidget()
        self.list.setObjectName("controllerList")
        self.list.currentRowChanged.connect(lambda _row: self._sync_link_combo())
        self.list.itemDoubleClicked.connect(lambda _item: self.on_connect())
        layout.addWidget(self.list, 1)
        self.link = QComboBox()
        self.link.setObjectName("link")
        layout.addWidget(self.link)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(lambda: self.refresh())
        add_net = QPushButton("Add network")
        add_net.clicked.connect(self.on_add_network)
        add_ser = QPushButton("Add serial")
        add_ser.clicked.connect(self.on_add_serial)
        row.addWidget(refresh)
        row.addWidget(add_net)
        row.addWidget(add_ser)
        layout.addLayout(row)
        connect = QPushButton("Connect")
        connect.setObjectName("connectButton")
        connect.clicked.connect(self.on_connect)
        layout.addWidget(connect)
        return panel

    def _build_editor(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.subtitle = QLabel("Select a controller and connect.")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)
        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save…")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.on_save)
        backup = QPushButton("Backup…")
        backup.clicked.connect(self.on_backup)
        restore = QPushButton("Restore…")
        restore.clicked.connect(self.on_restore)
        presets = QPushButton("Presets…")
        presets.setObjectName("presetsButton")
        presets.clicked.connect(self.on_presets)
        compare = QPushButton("Compare…")
        compare.clicked.connect(self.on_compare)
        self.copy_btn = QPushButton("Copy from")
        self.copy_menu = QMenu(self.copy_btn)
        self.copy_btn.setMenu(self.copy_menu)
        self.copy_menu.aboutToShow.connect(self._fill_copy_menu)
        for button in (self.save_btn, backup, restore, presets, compare, self.copy_btn):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.dirty = QLabel("Unsaved changes. Save shows the diff before anything is written.")
        self.dirty.setObjectName("dirtyBanner")
        self.dirty.setVisible(False)
        layout.addWidget(self.dirty)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter settings")
        self.search.textChanged.connect(self._on_search)
        layout.addWidget(self.search)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.placeholder = QLabel("Connect a controller to read its settings.\nThe form is built from the schema command.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.placeholder.setContentsMargins(12, 12, 12, 12)
        self.scroll.setWidget(self.placeholder)
        layout.addWidget(self.scroll, 1)
        return panel

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("New", self.new_document)
        file_menu.addAction("Open…", self.on_open_rotcfg)
        file_menu.addAction("Save", self.on_save_rotcfg)
        file_menu.addAction("Save as…", self.on_save_rotcfg_as)
        self.push_action = file_menu.addAction("Push to controller", self.on_push)
        self.push_action.setEnabled(False)
        operate = self.menuBar().addMenu("Operate")
        operate.setObjectName("operateMenu")
        for milestone in OPERATE_MILESTONES:
            action = operate.addAction(milestone)
            action.setEnabled(False)
        upgrade = self.menuBar().addMenu("Upgrade")
        upgrade.setObjectName("upgradeMenu")
        for milestone in UPGRADE_MILESTONES:
            action = QAction(milestone, self)
            action.setEnabled(False)
            if milestone.startswith("usb"):
                action.setToolTip(" ".join(dfu_argv("image.bin")))
                action.setObjectName("dfuAction")
            upgrade.addAction(action)

    def _build_file_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        pill = QLabel("OFFLINE")
        pill.setObjectName("offlinePill")
        self.file_label = QLabel("Untitled.rotcfg")
        self.file_label.setObjectName("fileLabel")
        new_button = QPushButton("New")
        new_button.clicked.connect(self.new_document)
        open_button = QPushButton("Open…")
        open_button.clicked.connect(self.on_open_rotcfg)
        save_button = QPushButton("Save")
        save_button.setObjectName("saveRotcfg")
        save_button.clicked.connect(self.on_save_rotcfg)
        layout.addWidget(pill)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(new_button)
        layout.addWidget(open_button)
        layout.addWidget(save_button)
        return bar

    def _preference_page(self, key: str, title: str, intro: str, names: list[str]) -> QWidget:
        page = QWidget()
        page.setObjectName(f"page-{key}")
        layout = QVBoxLayout(page)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(heading)
        text = QLabel(intro)
        text.setWordWrap(True)
        layout.addWidget(text)
        if key == "calibration":
            sweep = QPushButton("Start calibration sweep")
            sweep.setEnabled(False)
            sweep.setToolTip("Phase 2. The sweep records the end counts on this page.")
            layout.addWidget(sweep)
        specs = [spec for name in names if (spec := self.config.schema.get(name)) is not None]
        form = SettingsForm(Schema(version=self.config.schema.version, settings=specs), self.config.document.snapshot())
        form.changed.connect(lambda form=form: self._on_preference_edit(form))
        self.page_forms[key] = form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form)
        layout.addWidget(scroll, 1)
        return page

    def show_page(self, key: str) -> None:
        self.nav.setCurrentRow(self._nav_keys.index(key))

    def use_preset(self, preset_id: str) -> None:
        preset = next((item for item in self.presets if item.id == preset_id), None)
        if preset is None or not can_apply(preset):
            return
        for name, value in settings_from_preset(preset).items():
            self.config.document.set(name, value)
            self.overrides.pop(name, None)
        self.preset_id = preset_id
        self.config.preset = preset_id
        self._refresh_offline_views()
        self._mark_file_dirty()

    def _on_browser_override(self, name: str, raw: str) -> None:
        try:
            self.set_custom_override(name, raw)
        except SettingsError as exc:
            QMessageBox.warning(self, "Override", exc.message)

    def set_custom_override(self, name: str, raw: str) -> None:
        spec = self.config.schema.get(name)
        if spec is None or spec.readonly:
            raise SettingsError("readonly", f"{name} cannot be overridden")
        canonical = format_value(spec, raw)
        self.config.document.set(name, canonical)
        reference = self._preset_value(name)
        if canonical == reference:
            self.overrides.pop(name, None)
        else:
            self.overrides[name] = canonical
        self._refresh_offline_views()
        self._mark_file_dirty()

    def clear_override(self, name: str) -> None:
        self.overrides.pop(name, None)
        reference = self._preset_value(name)
        if self.config.schema.get(name) is not None:
            self.config.document.set(name, reference)
        self._refresh_offline_views()
        self._mark_file_dirty()

    def new_document(self) -> None:
        self.config = new_config()
        self.preset_id = ""
        self.overrides = {}
        self.rotcfg_path = None
        self._saved_token = self._token()
        self._rebuild_pages()
        self._refresh_offline_views()
        self._mark_file_dirty()

    def save_rotcfg_to(self, path: str) -> None:
        self.rotcfg_path = Path(path)
        self.config.preset = self.preset_id
        self.config.overrides = dict(self.overrides)
        self.rotcfg_path.write_text(dumps(self.config), encoding="utf-8")
        self._saved_token = self._token()
        self._mark_file_dirty()

    def load_rotcfg_text(self, text: str, path: str = "") -> None:
        loaded = loads(text, self.config.schema)
        self.config = loaded
        self.preset_id = loaded.preset
        self.overrides = dict(loaded.overrides)
        if path:
            self.rotcfg_path = Path(path)
        self._rebuild_pages()
        self._saved_token = self._token()
        self._refresh_offline_views()
        self._mark_file_dirty()

    def push_document(self) -> None:
        if self.client is None:
            raise RuntimeError("connect a controller first")
        self.config.preset = self.preset_id
        self.config.overrides = dict(self.overrides)
        self.client.restore_text(push_lines(self.config))

    def on_open_rotcfg(self) -> None:
        path, _selected = QFileDialog.getOpenFileName(self, "Open configuration", "", "Configuration (*.rotcfg *.yaml *.yml *.json)")
        if path:
            self.load_rotcfg_text(Path(path).read_text(encoding="utf-8"), path)

    def on_save_rotcfg(self) -> None:
        if self.rotcfg_path is None:
            self.on_save_rotcfg_as()
            return
        self.save_rotcfg_to(str(self.rotcfg_path))

    def on_save_rotcfg_as(self) -> None:
        path, _selected = QFileDialog.getSaveFileName(self, "Save configuration", "station.rotcfg", "Configuration (*.rotcfg)")
        if path:
            self.save_rotcfg_to(path)

    def on_push(self) -> None:
        try:
            self.push_document()
        except (CommandError, TransportError, SettingsError, RuntimeError) as exc:
            QMessageBox.warning(self, "Push", str(exc))

    def _preset_value(self, name: str) -> str:
        preset = next((item for item in self.presets if item.id == self.preset_id), None)
        if preset is not None:
            mapped = settings_from_preset(preset)
            if name in mapped:
                return mapped[name]
        spec = self.config.schema.get(name)
        return "" if spec is None else spec.default

    def _on_preference_edit(self, form: SettingsForm) -> None:
        if self._syncing:
            return
        for spec in form.schema.settings:
            if spec.readonly:
                continue
            message = form.errors().get(spec.name)
            if message:
                continue
            canonical = format_value(spec, form.value(spec.name))
            if canonical == self.config.document.get(spec.name) and spec.name not in self.overrides:
                continue
            self.config.document.set(spec.name, canonical)
            if canonical == self._preset_value(spec.name):
                self.overrides.pop(spec.name, None)
            else:
                self.overrides[spec.name] = canonical
        self.browser.set_values(self.config.document.snapshot())
        self.browser.set_overrides(self.overrides, self.preset_id)
        self._mark_file_dirty()

    def _refresh_offline_views(self) -> None:
        self._syncing = True
        try:
            snapshot = self.config.document.snapshot()
            azimuth, elevation = self._visible_axes()
            for form in self.page_forms.values():
                form.load(snapshot)
                form.set_axes(azimuth=azimuth, elevation=elevation)
            self.browser.set_values(snapshot)
            self.browser.set_overrides(self.overrides, self.preset_id)
            if self.preset_id:
                try:
                    self.browser.select(self.preset_id)
                except KeyError:
                    pass
        finally:
            self._syncing = False
        name = self.config.document.get("net.hostname")
        file_name = self.rotcfg_path.name if self.rotcfg_path else "Untitled.rotcfg"
        self.file_label.setText(f"{file_name}  ·  {name}")
        self._mark_file_dirty()

    def _visible_axes(self) -> tuple[bool, bool]:
        preset = next((item for item in self.presets if item.id == self.preset_id), None)
        if preset is None:
            return True, True
        prefixes = axis_prefixes(preset.axes)
        return "az" in prefixes, "el" in prefixes

    def _rebuild_pages(self) -> None:
        """Pages keep their widgets; values are reloaded from the new document."""
        return

    def _token(self) -> tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
        return (
            self.preset_id,
            tuple(sorted(self.overrides.items())),
            tuple(sorted(self.config.document.snapshot().items())),
        )

    def _mark_file_dirty(self) -> None:
        dirty = self._token() != self._saved_token
        self.file_dirty.setVisible(dirty)
        if self.nav.currentRow() != self._nav_keys.index("controllers"):
            title = "Rotator Controller — Offline"
            if dirty:
                title += " *"
            self.setWindowTitle(title)

    def set_controllers(self, infos: list[ControllerInfo]) -> None:
        self.infos = merge_controllers(infos)
        self._fill_list()

    def refresh(self, timeout: float = 0.8) -> None:
        self.discovered = scan_usb()
        try:
            self.discovered.extend(browse_mdns(timeout))
        except OSError:
            pass
        self.set_controllers([*self.discovered, *self.manual])
        if self.connected_serial:
            self._select_serial(self.connected_serial)

    def add_manual(self, info: ControllerInfo) -> None:
        self.manual.append(info)
        self.set_controllers([*self.infos, info])

    def on_add_network(self) -> None:
        dialog = HostPortDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            host, port = dialog.endpoint()
        except ValueError:
            QMessageBox.warning(self, "Add network", "Port is a number.")
            return
        self.add_manual(manual_tcp(host, port))

    def on_add_serial(self) -> None:
        dialog = SerialDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path = dialog.port_path()
        if path:
            self.add_manual(manual_serial(path))

    def on_connect(self) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        target = self.link.currentData()
        try:
            self.connect_to(row, None if target is None else str(target))
        except (CommandError, TransportError, OSError) as exc:
            QMessageBox.warning(self, "Connect", str(exc))

    def connect_to(self, index: int, target: str | None = None, *, discard: bool = False) -> None:
        if self.is_dirty() and not discard:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Discard unsaved changes and connect?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.list.setCurrentRow(index)
        info = self.infos[index]
        if target:
            chosen = target
        elif self.link.currentData():
            chosen = str(self.link.currentData())
        else:
            chosen = preferred_target(info)
        client = ConsoleClient(open_target(chosen))
        try:
            ident = client.identity()
            doc = client.load_document()
        except Exception:
            client.close()
            raise
        if self.client is not None:
            self.client.close()
        self.client = client
        self.connected_target = chosen
        self.push_action.setEnabled(True)
        serial = str(ident.get("serial") or info.serial)
        name = str(ident.get("name") or "")
        self._stamp(chosen, serial, name, str(ident.get("fw") or ""), str(ident.get("axes") or ""))
        info.serial = serial
        if name:
            info.name = name
            info.name_from_mdns = True
        info.firmware = str(ident.get("fw") or info.firmware)
        info.axes = str(ident.get("axes") or info.axes)
        self.connected_serial = serial
        self.infos = merge_controllers(self.infos)
        self._fill_list()
        self._select_serial(serial)
        self._sync_link_combo(chosen)
        self.schema = doc.schema
        self.baseline = doc.snapshot()
        self._show_form(doc.schema, self.baseline)
        self.subtitle.setText(f"{name or serial} · {serial} · {chosen}")
        self.statusBar().showMessage(f"Connected {chosen}")

    def reload(self) -> None:
        if self.client is None:
            return
        doc = self.client.load_document()
        self.schema = doc.schema
        self.baseline = doc.snapshot()
        self._show_form(doc.schema, self.baseline)

    def is_dirty(self) -> bool:
        if self.form is None:
            return False
        if self.form.errors():
            return True
        return bool(self.pending_changes())

    def pending_changes(self) -> list[Change]:
        if self.form is None or self.schema is None:
            return []
        current: dict[str, str] = {}
        for spec in self.schema.settings:
            if spec.readonly:
                current[spec.name] = self.baseline.get(spec.name, spec.default)
            else:
                current[spec.name] = format_value(spec, self.form.value(spec.name))
        return SettingsDocument(self.schema, self.baseline).diff(current)

    def make_save_dialog(self) -> DiffDialog | None:
        if self.form is None or self.schema is None or self.form.errors():
            return None
        changes = self.pending_changes()
        if not changes:
            return None
        reboot = [change.name for change in changes if (spec := self.schema.get(change.name)) and spec.reboot]
        notes: list[str] = []
        if reboot:
            notes.append(
                "Takes effect after reboot: "
                + ", ".join(reboot)
                + ". This program does not reboot the controller."
            )
        return DiffDialog(
            "Save to controller",
            "Save writes these values to the controller and stores them.",
            changes,
            notes,
            confirm=True,
            accept_label="Save",
            parent=self,
        )

    def write_pending(self) -> None:
        if self.client is None:
            raise RuntimeError("not connected")
        for change in self.pending_changes():
            self.client.set(change.name, change.new)
        self.client.save()
        self.reload()

    def on_save(self) -> None:
        if self.form is None or self.client is None:
            return
        if self.form.errors():
            QMessageBox.warning(self, "Save", "Fix the highlighted fields before saving.")
            return
        dialog = self.make_save_dialog()
        if dialog is None:
            QMessageBox.information(self, "Save", "Nothing to write.")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.write_pending()
            except (CommandError, TransportError, SettingsError) as exc:
                QMessageBox.warning(self, "Save", str(exc))

    def backup_to(self, path: str) -> None:
        if self.form is None or self.schema is None:
            raise SettingsError("state", "connect a controller first")
        if self.form.errors():
            raise SettingsError("invalid", "fix invalid fields before backup")
        Path(path).write_text(self._canonical_document().to_ini(), encoding="utf-8")

    def on_backup(self) -> None:
        if self.form is None:
            return
        if self.form.errors():
            QMessageBox.warning(self, "Backup", "Fix the highlighted fields before backup.")
            return
        path, _selected = QFileDialog.getSaveFileName(self, "Backup settings", "rotator-settings.txt", "Settings (*.txt)")
        if path:
            self.backup_to(path)

    def preview_restore(self, text: str) -> list[Change]:
        if self.schema is None:
            raise SettingsError("state", "connect a controller first")
        trial = SettingsDocument(self.schema, self.baseline)
        trial.replace_from_lines(text.splitlines())
        return SettingsDocument(self.schema, self.baseline).diff(trial.snapshot())

    def apply_restore(self, text: str) -> None:
        if self.client is None:
            raise SettingsError("state", "connect a controller first")
        self.client.restore_text(text)
        self.reload()

    def on_restore(self) -> None:
        if self.client is None or self.schema is None:
            return
        path, _selected = QFileDialog.getOpenFileName(self, "Restore settings", "", "Settings (*.txt)")
        if not path:
            return
        text = Path(path).read_text(encoding="utf-8")
        try:
            changes = self.preview_restore(text)
        except SettingsError as exc:
            QMessageBox.warning(self, "Restore", exc.message)
            return
        dialog = DiffDialog(
            "Restore to controller",
            "Restore replaces the stored record. There is no separate save step.",
            changes,
            [],
            confirm=True,
            accept_label="Restore",
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.apply_restore(text)
            except (CommandError, TransportError, SettingsError) as exc:
                QMessageBox.warning(self, "Restore", str(exc))

    def make_preset_dialog(self) -> PresetDialog:
        return PresetDialog(self.presets, dict(self.baseline), parent=self)

    def on_presets(self) -> None:
        if self.client is None:
            QMessageBox.information(self, "Presets", "Connect a controller first.")
            return
        dialog = self.make_preset_dialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.client.preset_apply(dialog.selected_id)
            self.reload()
        except (CommandError, TransportError) as exc:
            QMessageBox.warning(self, "Presets", str(exc))

    def compare_to_values(self, other: dict[str, str], title: str) -> DiffDialog:
        if self.form is None or self.schema is None:
            raise SettingsError("state", "connect a controller first")
        if self.form.errors():
            raise SettingsError("invalid", "fix invalid fields before compare")
        merged = dict(self.baseline)
        for name, raw in other.items():
            spec = self.schema.get(name)
            if spec is None:
                continue
            merged[name] = format_value(spec, raw)
        current = self._canonical_document().snapshot()
        changes = SettingsDocument(self.schema, merged).diff(current)
        return DiffDialog(
            title,
            "Settings that differ. Nothing is written.",
            changes,
            [],
            confirm=False,
            headers=("Other", "This controller"),
            parent=self,
        )

    def on_compare(self) -> None:
        if self.form is None or self.schema is None:
            return
        path, _selected = QFileDialog.getOpenFileName(self, "Compare with file", "", "Settings (*.txt)")
        if not path:
            return
        text = Path(path).read_text(encoding="utf-8")
        try:
            values, errors = parse_ini_lines(text.splitlines())
            if errors:
                raise SettingsError("invalid", errors[0])
            dialog = self.compare_to_values(values, "Compare")
        except SettingsError as exc:
            QMessageBox.warning(self, "Compare", exc.message)
            return
        dialog.exec()

    def copy_from(self, info: ControllerInfo) -> None:
        if self.form is None or self.schema is None:
            return
        client = ConsoleClient(open_target(preferred_target(info)))
        try:
            doc = client.load_document()
        finally:
            client.close()
        for spec in self.schema.settings:
            if spec.readonly or spec.name not in doc.values:
                continue
            self.form.set_value(spec.name, doc.values[spec.name])

    def _fill_copy_menu(self) -> None:
        self.copy_menu.clear()
        others = [info for info in self.infos if info.serial != self.connected_serial and info.endpoints]
        if not others:
            action = self.copy_menu.addAction("No other controller")
            action.setEnabled(False)
            return
        for info in others:
            action = self.copy_menu.addAction(info.name or info.serial or "controller")
            action.triggered.connect(lambda checked=False, chosen=info: self._copy_clicked(chosen))

    def _copy_clicked(self, info: ControllerInfo) -> None:
        try:
            self.copy_from(info)
        except (CommandError, TransportError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Copy", str(exc))

    def _canonical_document(self) -> SettingsDocument:
        assert self.schema is not None and self.form is not None
        current: dict[str, str] = {}
        for spec in self.schema.settings:
            if spec.readonly:
                current[spec.name] = self.baseline.get(spec.name, spec.default)
            else:
                current[spec.name] = format_value(spec, self.form.value(spec.name))
        return SettingsDocument(self.schema, current)

    def _show_form(self, schema: Schema, values: dict[str, str]) -> None:
        self.form = SettingsForm(schema, values)
        self.form.set_axes(
            azimuth=values.get("az.present", "true") == "true",
            elevation=values.get("el.present", "false") == "true",
        )
        self.form.changed.connect(self._on_form_changed)
        self.scroll.setWidget(self.form)
        if self.search.text():
            self.form.set_filter(self.search.text())
        self._on_form_changed()

    def _on_form_changed(self) -> None:
        dirty = self.is_dirty()
        self.dirty.setVisible(dirty)
        title = "Rotator Controller"
        if self.connected_serial:
            title += f" — {self.connected_serial}"
        if dirty:
            title += " *"
        self.setWindowTitle(title)

    def _on_search(self, text: str) -> None:
        if self.form is not None:
            self.form.set_filter(text)

    def _fill_list(self) -> None:
        selected = self.list.currentRow()
        self.list.blockSignals(True)
        self.list.clear()
        for index, info in enumerate(self.infos):
            item = QListWidgetItem(self._item_text(info))
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setSizeHint(QSize(280, 78))
            self.list.addItem(item)
        if 0 <= selected < self.list.count():
            self.list.setCurrentRow(selected)
        self.list.blockSignals(False)
        self._sync_link_combo()

    def _item_text(self, info: ControllerInfo) -> str:
        title = info.name or "(unnamed)"
        serial = info.serial or "serial pending"
        lines = [f"{title}    {serial}"]
        for endpoint in info.endpoints:
            if endpoint.kind == "usb":
                vid = f"{info.vid:04x}:{info.pid:04x}" if info.vid is not None and info.pid is not None else "usb"
                path = endpoint.target.removeprefix("serial://")
                lines.append(f"USB {vid}    {path}")
            else:
                lines.append(f"network    {endpoint.target.removeprefix('tcp://')}")
        if info.firmware or info.axes:
            lines.append(" · ".join(part for part in (info.firmware, info.axes) if part))
        return "\n".join(lines)

    def _sync_link_combo(self, prefer: str | None = None) -> None:
        self.link.blockSignals(True)
        self.link.clear()
        info = self.current_info()
        if info is not None:
            for endpoint in info.endpoints:
                if endpoint.kind == "usb":
                    label = f"USB {endpoint.target}"
                else:
                    label = f"network {endpoint.target}"
                self.link.addItem(label, endpoint.target)
            if prefer:
                index = self.link.findData(prefer)
                if index >= 0:
                    self.link.setCurrentIndex(index)
        self.link.blockSignals(False)

    def current_info(self) -> ControllerInfo | None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self.infos):
            return None
        return self.infos[row]

    def _select_serial(self, serial: str) -> None:
        for index, info in enumerate(self.infos):
            if info.serial == serial:
                self.list.setCurrentRow(index)
                return

    def _stamp(self, target: str, serial: str, name: str, firmware: str, axes: str) -> None:
        for entry in [*self.discovered, *self.manual]:
            if any(endpoint.target == target for endpoint in entry.endpoints):
                entry.serial = serial
                if name:
                    entry.name = name
                    entry.name_from_mdns = True
                if firmware:
                    entry.firmware = firmware
                if axes:
                    entry.axes = axes

    def closeEvent(self, event: object) -> None:  # noqa: N802
        if self.client is not None:
            self.client.close()
            self.client = None
        super().closeEvent(event)  # type: ignore[arg-type]
