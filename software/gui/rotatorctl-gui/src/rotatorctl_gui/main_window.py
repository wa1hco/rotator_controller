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
from rotatorctl.presets import Preset, load_presets
from rotatorctl.protocol import CommandError, ConsoleClient
from rotatorctl.schema import Schema
from rotatorctl.transport import TransportError, open_target
from rotatorctl.upgrade import dfu_argv
from rotatorctl_gui.dialogs import DiffDialog, HostPortDialog, PresetDialog, SerialDialog
from rotatorctl_gui.form import SettingsForm

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
QLabel#dirty { background: #f4d35e; color: #1c1917; padding: 8px 10px; font-weight: 600; }
QPushButton#stopButton { background: #9f1239; color: white; font-size: 16px; font-weight: 700; min-height: 40px; }
QPushButton#stopButton:disabled { background: #e7e5e4; color: #78716c; }
QFrame#header { background: #1f4d3a; }
QLabel#wordmark { color: white; font-size: 18px; font-weight: 700; }
QLabel#headerSub { color: #d6d3d1; }
QLabel#reboot { color: #9a3412; font-size: 11px; }
"""


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
        sub = QLabel("Configuration")
        sub.setObjectName("headerSub")
        header_layout.addWidget(wordmark)
        header_layout.addWidget(sub)
        outer.addWidget(header)

        splitter = QSplitter()
        splitter.addWidget(self._build_list())
        splitter.addWidget(self._build_editor())
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 960])
        outer.addWidget(splitter, 1)

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
        status.showMessage("Phase 1 · configuration")
        self.setStatusBar(status)

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
