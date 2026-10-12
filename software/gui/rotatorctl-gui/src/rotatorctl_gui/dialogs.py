# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Confirm, compare, and preset dialogs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rotatorctl.document import Change
from rotatorctl.presets import (
    Preset,
    can_apply,
    offered_presets,
    settings_from_preset,
    unverified_labels,
    unverified_setting_names,
)


class DiffDialog(QDialog):
    """A table of setting changes. Save and restore ask for confirmation. Compare does not."""

    def __init__(
        self,
        title: str,
        lead: str,
        changes: list[Change],
        notes: list[str],
        *,
        confirm: bool,
        accept_label: str = "Save",
        headers: tuple[str, str] = ("On controller", "New value"),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setObjectName("diffDialog")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        lead_label = QLabel(lead)
        lead_label.setWordWrap(True)
        layout.addWidget(lead_label)
        self.table = QTableWidget(len(changes), 3)
        self.table.setObjectName("diffTable")
        self.table.setHorizontalHeaderLabels(["Setting", headers[0], headers[1]])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        for row, change in enumerate(changes):
            self.table.setItem(row, 0, QTableWidgetItem(change.name))
            self.table.setItem(row, 1, QTableWidgetItem(change.old))
            self.table.setItem(row, 2, QTableWidgetItem(change.new))
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table, 1)
        if not changes:
            empty = QLabel("No differences.")
            empty.setObjectName("diffEmpty")
            layout.addWidget(empty)
        for note in notes:
            label = QLabel(note)
            label.setWordWrap(True)
            label.setObjectName("diffNote")
            layout.addWidget(label)
        buttons = QDialogButtonBox()
        if confirm:
            buttons.addButton(accept_label, QDialogButtonBox.ButtonRole.AcceptRole)
            buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
        else:
            buttons.addButton(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            buttons.accepted.connect(self.reject)
        layout.addWidget(buttons)

    def summary(self) -> str:
        rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                rows.append(item.text())
        return "\n".join(rows)


class PresetDialog(QDialog):
    """Family, mapped settings, and unverified catalog fields for one rotor."""

    def __init__(
        self,
        presets: tuple[Preset, ...] | list[Preset],
        baseline: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rotor presets")
        self.resize(980, 640)
        self._baseline = baseline
        self._by_id = {preset.id: preset for preset in offered_presets(presets)}
        self.selected_id = ""
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Apply loads this rotor's axis and safety defaults into the working settings. "
            "Flash is unchanged until you Save. An alias points at another row."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        splitter = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter rotors")
        self.filter.textChanged.connect(self._filter)
        self.list = QListWidget()
        self.list.setObjectName("presetList")
        left_layout.addWidget(self.filter)
        left_layout.addWidget(self.list, 1)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("")
        self.title.setObjectName("presetTitle")
        self.title.setWordWrap(True)
        self.family = QLabel("")
        self.family.setObjectName("presetFamily")
        self.alias = QLabel("")
        self.alias.setObjectName("presetAlias")
        self.alias.setWordWrap(True)
        unverified_caption = QLabel("Unverified")
        self.unverified = QLabel("none")
        self.unverified.setObjectName("presetUnverified")
        self.unverified.setWordWrap(True)
        self.settings = QPlainTextEdit()
        self.settings.setObjectName("presetSettings")
        self.settings.setReadOnly(True)
        right_layout.addWidget(self.title)
        right_layout.addWidget(self.family)
        right_layout.addWidget(self.alias)
        right_layout.addWidget(unverified_caption)
        right_layout.addWidget(self.unverified)
        right_layout.addWidget(self.settings, 1)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([280, 680])
        layout.addWidget(splitter, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.apply_btn = QPushButton("Apply preset")
        self.apply_btn.setObjectName("applyPreset")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply)
        buttons.addWidget(cancel)
        buttons.addWidget(self.apply_btn)
        layout.addLayout(buttons)
        for ident in sorted(self._by_id):
            item = QListWidgetItem(ident)
            item.setData(Qt.ItemDataRole.UserRole, ident)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._show_current)
        if self.list.count():
            self.list.setCurrentRow(0)

    def select(self, preset_id: str) -> None:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == preset_id:
                self.list.setCurrentItem(item)
                return
        raise KeyError(preset_id)

    def _filter(self, text: str) -> None:
        query = text.strip().lower()
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setHidden(bool(query) and query not in item.text().lower())

    def _show_current(self) -> None:
        item = self.list.currentItem()
        if item is None or item.isHidden():
            return
        preset = self._by_id[item.data(Qt.ItemDataRole.UserRole)]
        self.selected_id = preset.id
        self.title.setText(f"{preset.maker} {preset.model}".strip())
        self.family.setText(f"Family: {preset.family or '(none)'}    Axes: {preset.axes}    Support: {preset.support}")
        if preset.alias_of:
            self.alias.setText("Alias of: " + ", ".join(preset.alias_of))
        else:
            self.alias.setText("")
        labels = unverified_labels(preset)
        self.unverified.setText("\n".join(labels) if labels else "none")
        flagged = unverified_setting_names(preset)
        lines: list[str] = []
        for name, value in settings_from_preset(preset).items():
            old = self._baseline.get(name, "")
            mark = "" if old == value else "    (change)"
            question = " [?]" if name in flagged else ""
            lines.append(f"{name} = {value}{question}{mark}")
        self.settings.setPlainText("\n".join(lines) if lines else "(no settings)")
        self.apply_btn.setEnabled(can_apply(preset))

    def _apply(self) -> None:
        if self.selected_id and can_apply(self._by_id[self.selected_id]):
            self.accept()


class HostPortDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add network controller")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Host"))
        self.host = QLineEdit("127.0.0.1")
        layout.addWidget(self.host)
        layout.addWidget(QLabel("Port"))
        self.port = QLineEdit("4533")
        layout.addWidget(self.port)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def endpoint(self) -> tuple[str, int]:
        return self.host.text().strip(), int(self.port.text().strip())


class SerialDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add serial port")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Port path"))
        self.path = QLineEdit()
        self.path.setPlaceholderText("/dev/ttyACM0")
        layout.addWidget(self.path)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def port_path(self) -> str:
        return self.path.text().strip()
