# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Rotator catalog browser: search, specs, preset settings, and custom overrides."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from rotatorctl.presets import (
    Preset,
    can_apply,
    preset_aliases,
    preset_facts,
    settings_from_preset,
    unverified_labels,
    unverified_setting_names,
)

_SUPPORT = {
    "v1": "Ready for the AC board",
    "v1-2axis": "Needs both axes",
    "v2-dc": "Needs the DC module",
    "alias": "Name for another preset",
    "no": "Out of scope",
    "later": "Needs more data",
    "check": "Needs a check before use",
}


class RotatorBrowser(QWidget):
    """Browse the whole catalog. Choosing a rotator fills the offline document."""

    use_requested = Signal(str)
    override_set = Signal(str, str)
    override_cleared = Signal(str)

    def __init__(self, presets: tuple[Preset, ...] | list[Preset], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("rotatorBrowser")
        self._presets = list(presets)
        self._by_id = {preset.id: preset for preset in self._presets}
        self._values: dict[str, str] = {}
        self._overrides: dict[str, str] = {}
        self._active_preset = ""
        self._build()
        self._refill()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("presetSearch")
        self.search.setPlaceholderText("Search model, maker, family, or alias")
        self.search.textChanged.connect(lambda _text: self._refill())
        self.family = QComboBox()
        self.family.setObjectName("familyFilter")
        self.maker = QComboBox()
        self.maker.setObjectName("makerFilter")
        self.family.addItem("All families")
        self.maker.addItem("All manufacturers")
        for name in sorted({preset.family for preset in self._presets if preset.family}):
            self.family.addItem(name)
        for name in sorted({preset.maker for preset in self._presets if preset.maker}):
            self.maker.addItem(name)
        self.family.currentIndexChanged.connect(lambda _index: self._refill())
        self.maker.currentIndexChanged.connect(lambda _index: self._refill())
        filters.addWidget(self.search, 1)
        filters.addWidget(self.family)
        filters.addWidget(self.maker)
        root.addLayout(filters)
        self.count = QLabel("")
        self.count.setObjectName("presetCount")
        root.addWidget(self.count)
        splitter = QSplitter()
        self.list = QListWidget()
        self.list.setObjectName("presetList")
        self.list.currentItemChanged.connect(lambda _cur, _prev: self._show_current())
        splitter.addWidget(self.list)
        self.detail = QScrollArea()
        self.detail.setWidgetResizable(True)
        self.detail.setObjectName("presetDetail")
        self.detail_body = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_body)
        self.detail_layout.setContentsMargins(12, 8, 12, 12)
        self.detail.setWidget(self.detail_body)
        splitter.addWidget(self.detail)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 760])
        root.addWidget(splitter, 1)

    def select(self, preset_id: str) -> None:
        self.search.clear()
        self.family.setCurrentIndex(0)
        self.maker.setCurrentIndex(0)
        self._refill()
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == preset_id:
                self.list.setCurrentItem(item)
                self.list.scrollToItem(item)
                return
        raise KeyError(preset_id)

    def current_id(self) -> str:
        item = self.list.currentItem()
        if item is None:
            return ""
        return str(item.data(Qt.ItemDataRole.UserRole))

    def set_values(self, values: dict[str, str]) -> None:
        self._values = dict(values)
        self._show_current()

    def set_overrides(self, overrides: dict[str, str], active_preset: str) -> None:
        self._overrides = dict(overrides)
        self._active_preset = active_preset
        self._show_current()

    def _visible(self, preset: Preset) -> bool:
        family = self.family.currentText()
        maker = self.maker.currentText()
        if family != "All families" and preset.family != family:
            return False
        if maker != "All manufacturers" and preset.maker != maker:
            return False
        query = self.search.text().strip().lower()
        if not query:
            return True
        hay = " ".join(
            [
                preset.id,
                preset.maker,
                preset.model,
                preset.family,
                preset.axes,
                preset.support,
                " ".join(preset_aliases(preset)),
                " ".join(preset.alias_of),
            ]
        ).lower()
        return query in hay

    def _refill(self) -> None:
        selected = self.current_id()
        self.list.blockSignals(True)
        self.list.clear()
        rows = sorted(self._presets, key=lambda preset: (preset.maker.lower(), preset.model.lower(), preset.id))
        shown = 0
        for preset in rows:
            if not self._visible(preset):
                continue
            shown += 1
            item = QListWidgetItem(f"{preset.model}\n{preset.maker}  ·  {preset.family or '—'}  ·  {preset.axes}  ·  {preset.support}")
            item.setData(Qt.ItemDataRole.UserRole, preset.id)
            item.setSizeHint(QSize(320, 52))
            self.list.addItem(item)
            if preset.id == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.count.setText(f"{shown} of {len(self._presets)} rotators")
        if self.list.currentItem() is None and self.list.count():
            self.list.setCurrentRow(0)
        else:
            self._show_current()

    def _show_current(self) -> None:
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        preset_id = self.current_id()
        preset = self._by_id.get(preset_id)
        if preset is None:
            empty = QLabel("Select a rotator to review its specs, the settings it writes, and any unverified values.")
            empty.setWordWrap(True)
            self.detail_layout.addWidget(empty)
            self.detail_layout.addStretch(1)
            return
        self._render(preset)

    def _render(self, preset: Preset) -> None:
        title = QLabel(preset.model)
        title.setObjectName("presetModel")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        title.setWordWrap(True)
        maker = QLabel(preset.maker)
        maker.setObjectName("presetMaker")
        maker.setWordWrap(True)
        head = QHBoxLayout()
        text = QVBoxLayout()
        text.addWidget(title)
        text.addWidget(maker)
        head.addLayout(text, 1)
        use = QPushButton("Use this rotator" if can_apply(preset) else "Shown for review")
        use.setObjectName("usePreset")
        use.setEnabled(can_apply(preset))
        if self._active_preset == preset.id:
            use.setText("Using this rotator")
        use.clicked.connect(lambda: self.use_requested.emit(preset.id))
        head.addWidget(use)
        self.detail_layout.addLayout(head)
        aliases = preset_aliases(preset)
        if aliases:
            alias = QLabel("Also called: " + ", ".join(aliases))
            alias.setWordWrap(True)
            self.detail_layout.addWidget(alias)
        if preset.alias_of:
            pointer = QLabel("This name points at: " + ", ".join(preset.alias_of))
            pointer.setObjectName("presetAlias")
            pointer.setWordWrap(True)
            self.detail_layout.addWidget(pointer)
        support = _SUPPORT.get(preset.support, preset.support)
        support_label = QLabel(f"{preset.id}  ·  {support}")
        support_label.setObjectName("presetSupport")
        self.detail_layout.addWidget(support_label)
        labels = unverified_labels(preset)
        box = QLabel("\n".join(labels) if labels else "No unverified fields in this row.")
        box.setObjectName("unverifiedBox")
        box.setWordWrap(True)
        box.setStyleSheet(
            "background: #fef3c7; border: 1px solid #d97706; padding: 8px; font-weight: 600;"
            if labels
            else "background: #ecfdf3; border: 1px solid #86efac; padding: 8px;"
        )
        self.detail_layout.addWidget(box)
        self.detail_layout.addWidget(self._specs(preset))
        self.detail_layout.addWidget(self._settings_block(preset))
        self.detail_layout.addWidget(self._overrides_block(preset))
        self.detail_layout.addStretch(1)

    def _specs(self, preset: Preset) -> QFrame:
        frame = QFrame()
        frame.setObjectName("specGrid")
        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 4, 0, 4)
        for index, (label, value, flagged) in enumerate(preset_facts(preset)):
            row, column = divmod(index, 2)
            name = QLabel(label)
            name.setStyleSheet("color: #57534e;")
            text = f"{value}  [?]" if flagged else value
            shown = QLabel(text)
            shown.setWordWrap(True)
            if flagged:
                shown.setObjectName("specUnverified")
                shown.setStyleSheet("color: #9a3412; font-weight: 700;")
            grid.addWidget(name, row, column * 2)
            grid.addWidget(shown, row, column * 2 + 1)
        return frame

    def _settings_block(self, preset: Preset) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 8, 0, 0)
        caption = QLabel("Settings this preset writes")
        caption.setStyleSheet("font-weight: 700;")
        layout.addWidget(caption)
        updates = settings_from_preset(preset)
        flagged = unverified_setting_names(preset)
        if not updates:
            note = QLabel("This row does not load settings by itself.")
            note.setWordWrap(True)
            layout.addWidget(note)
            return wrap
        grid = QGridLayout()
        names = list(updates)
        for index, name in enumerate(names):
            value = updates[name]
            custom = self._overrides.get(name)
            shown = value if custom is None or self._active_preset != preset.id else f"{value}  →  {custom}"
            if name in flagged:
                shown += "  [?]"
            label = QLabel(f"{name} = {shown}")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(label, index // 2, index % 2)
        layout.addLayout(grid)
        return wrap

    def _overrides_block(self, preset: Preset) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("overrideBlock")
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 8, 0, 0)
        caption = QLabel("Custom overrides")
        caption.setStyleSheet("font-weight: 700;")
        layout.addWidget(caption)
        relevant = self._overrides if self._active_preset == preset.id else {}
        if not relevant:
            layout.addWidget(QLabel("None. The preset values are unchanged."))
        else:
            for name, value in relevant.items():
                row = QHBoxLayout()
                preset_value = settings_from_preset(preset).get(name, "—")
                label = QLabel(f"{name}:  preset {preset_value}  →  custom {value}")
                label.setObjectName("overrideRow")
                clear = QPushButton("Reset")
                clear.clicked.connect(lambda checked=False, key=name: self.override_cleared.emit(key))
                row.addWidget(label, 1)
                row.addWidget(clear)
                layout.addLayout(row)
        if can_apply(preset):
            editor = QHBoxLayout()
            self._override_name = QComboBox()
            self._override_name.setObjectName("overrideName")
            names = list(settings_from_preset(preset)) or ["az.overlap_deg"]
            self._override_name.addItems(names)
            self._override_value = QLineEdit()
            self._override_value.setObjectName("overrideValue")
            self._override_value.setPlaceholderText("custom value")
            apply = QPushButton("Set override")
            apply.setObjectName("setOverride")
            apply.clicked.connect(self._emit_override)
            editor.addWidget(self._override_name)
            editor.addWidget(self._override_value, 1)
            editor.addWidget(apply)
            layout.addLayout(editor)
        return wrap

    def _emit_override(self) -> None:
        name = self._override_name.currentText()
        value = self._override_value.text().strip()
        if name and value:
            self.override_set.emit(name, value)
