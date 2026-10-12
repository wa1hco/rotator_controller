# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Settings form built from a schema document.

A setting the firmware adds, of a type this form already knows, shows up
as another row. The row list is the schema, not a table in this file.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from rotatorctl.document import SettingsDocument
from rotatorctl.schema import Schema, SettingSpec, SettingType

_TITLES = {
    "sys": "System",
    "az": "Azimuth",
    "el": "Elevation",
    "net": "Network",
    "ports": "Ports",
    "ui": "Interface",
    "safety": "Safety",
}


class SettingsForm(QWidget):
    changed = Signal()

    def __init__(self, schema: Schema, values: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.schema = schema
        self.setObjectName("settingsForm")
        self._doc = SettingsDocument(schema)
        self._editors: dict[str, QWidget] = {}
        self._errors: dict[str, QLabel] = {}
        self._rows: dict[str, QWidget] = {}
        self._groups: dict[str, QGroupBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        shown = {spec.name: values.get(spec.name, spec.default) for spec in schema.settings}
        for spec in schema.settings:
            prefix = spec.name.split(".", 1)[0]
            group = self._groups.get(prefix)
            if group is None:
                group = QGroupBox(_TITLES.get(prefix, prefix))
                group.setObjectName(f"group-{prefix}")
                group.setLayout(QVBoxLayout())
                self._groups[prefix] = group
                layout.addWidget(group)
            row = self._row(spec, shown[spec.name])
            self._rows[spec.name] = row
            group.layout().addWidget(row)
        layout.addStretch(1)

    def has_field(self, name: str) -> bool:
        return name in self._editors

    def group_title(self, prefix: str) -> str:
        group = self._groups.get(prefix)
        return "" if group is None else group.title()

    def value(self, name: str) -> str:
        widget = self._editors[name]
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    def values(self) -> dict[str, str]:
        return {spec.name: self.value(spec.name) for spec in self.schema.settings}

    def set_value(self, name: str, text: str) -> None:
        widget = self._editors[name]
        if isinstance(widget, QComboBox):
            index = widget.findText(text)
            if index >= 0:
                widget.setCurrentIndex(index)
            return
        if isinstance(widget, QLineEdit):
            widget.setText(text)

    def load(self, values: dict[str, str]) -> None:
        for name, text in values.items():
            if name not in self._editors:
                continue
            widget = self._editors[name]
            widget.blockSignals(True)
            if isinstance(widget, QComboBox):
                index = widget.findText(text)
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QLineEdit):
                widget.setText(text)
            widget.blockSignals(False)
        for spec in self.schema.settings:
            self._show_error(spec.name)
        self.changed.emit()

    def errors(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for spec in self.schema.settings:
            message = self._doc.validate(spec.name, self.value(spec.name))
            if message:
                found[spec.name] = message
        return found

    def error_text(self, name: str) -> str:
        label = self._errors.get(name)
        return "" if label is None else label.text()

    def set_filter(self, text: str) -> None:
        query = text.strip().lower()
        for spec in self.schema.settings:
            hay = f"{spec.name} {spec.help}".lower()
            self._rows[spec.name].setVisible(not query or query in hay)
        for prefix, group in self._groups.items():
            visible = any(
                self._rows[spec.name].isVisible()
                for spec in self.schema.settings
                if spec.name.split(".", 1)[0] == prefix
            )
            group.setVisible(visible)

    def _row(self, spec: SettingSpec, value: str) -> QWidget:
        row = QWidget()
        outer = QVBoxLayout(row)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(2)
        line = QHBoxLayout()
        name = QLabel(spec.name)
        name.setMinimumWidth(210)
        name.setToolTip(spec.help)
        editor = self._editor(spec, value)
        self._editors[spec.name] = editor
        line.addWidget(name)
        line.addWidget(editor, 1)
        if spec.unit:
            line.addWidget(QLabel(spec.unit))
        if spec.reboot:
            badge = QLabel("reboot")
            badge.setObjectName("reboot")
            badge.setToolTip("Read when the controller boots.")
            line.addWidget(badge)
        outer.addLayout(line)
        error = QLabel("")
        error.setObjectName(f"error-{spec.name}")
        error.setWordWrap(True)
        error.setStyleSheet("color: #9f1239;")
        self._errors[spec.name] = error
        outer.addWidget(error)
        self._show_error(spec.name)
        return row

    def _editor(self, spec: SettingSpec, value: str) -> QWidget:
        if spec.type in (SettingType.BOOL, SettingType.ENUM):
            choices = ["true", "false"] if spec.type is SettingType.BOOL else list(spec.enum)
            box = QComboBox()
            box.addItems(choices)
            index = box.findText(value)
            if index >= 0:
                box.setCurrentIndex(index)
            box.setEnabled(not spec.readonly)
            box.currentTextChanged.connect(lambda _text, name=spec.name: self._on_changed(name))
            return box
        edit = QLineEdit(value)
        edit.setEnabled(not spec.readonly)
        edit.textChanged.connect(lambda _text, name=spec.name: self._on_changed(name))
        return edit

    def _on_changed(self, name: str) -> None:
        self._show_error(name)
        self.changed.emit()

    def _show_error(self, name: str) -> None:
        if name not in self._editors:
            return
        message = self._doc.validate(name, self.value(name)) or ""
        self._errors[name].setText(message)
        self._errors[name].setVisible(bool(message))
