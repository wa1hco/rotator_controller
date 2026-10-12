# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from rotatorctl.paths import ensure_user_config_dir, user_config_dir
from rotatorctl.presets import default_preset_path, preset_path_is_bundled
from rotatorctl_gui.main_window import MainWindow
from rotatorctl_gui.selftest import run_selftest


def test_config_dir_follows_the_platform(tmp_path: Path) -> None:
    home = tmp_path / "home"
    assert user_config_dir(platform="win32", environ={"APPDATA": str(tmp_path / "Roaming")}, home=home) == (
        tmp_path / "Roaming" / "RotatorController"
    )
    assert user_config_dir(platform="win32", environ={}, home=home) == home / "AppData" / "Roaming" / "RotatorController"
    assert user_config_dir(platform="darwin", environ={}, home=home) == (
        home / "Library" / "Application Support" / "RotatorController"
    )
    assert user_config_dir(platform="linux", environ={"XDG_CONFIG_HOME": str(tmp_path / "xdg")}, home=home) == (
        tmp_path / "xdg" / "rotator-controller"
    )
    assert user_config_dir(platform="linux", environ={}, home=home) == home / ".config" / "rotator-controller"
    override = tmp_path / "override"
    assert user_config_dir(platform="linux", environ={"ROTATOR_CONFIG_DIR": str(override)}, home=home) == override


def test_ensure_creates_the_directory(tmp_path: Path) -> None:
    target = tmp_path / "cfg"
    created = ensure_user_config_dir(environ={"ROTATOR_CONFIG_DIR": str(target)})
    assert created == target
    assert target.is_dir()


def test_source_tree_finds_the_catalog(monkeypatch) -> None:
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    path = default_preset_path()
    assert path.name == "rotor-presets.yaml"
    assert path.is_file()
    assert not preset_path_is_bundled(path)


def test_env_preset_overrides_the_bundle(tmp_path: Path, monkeypatch) -> None:
    explicit = tmp_path / "mine.yaml"
    explicit.write_text("presets: []\n", encoding="utf-8")
    monkeypatch.setenv("ROTATOR_PRESETS", str(explicit))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert default_preset_path() == explicit


def test_frozen_bundle_wins_over_the_checkout(tmp_path: Path, monkeypatch) -> None:
    bundled = tmp_path / "rotatorctl" / "data" / "rotor-presets.yaml"
    bundled.parent.mkdir(parents=True)
    bundled.write_text("presets: []\n", encoding="utf-8")
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "RotatorController"), raising=False)
    assert default_preset_path() == bundled
    assert preset_path_is_bundled(bundled)


def test_frozen_without_a_bundle_is_not_inside_the_app(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "empty"), raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "empty" / "RotatorController"), raising=False)
    path = default_preset_path()
    assert path.name == "rotor-presets.yaml"
    assert "software/firmware/presets" in path.as_posix()
    assert not preset_path_is_bundled(path)


def test_macos_resources_symlink_counts_as_bundled(tmp_path: Path, monkeypatch) -> None:
    app = tmp_path / "RotatorController.app"
    frameworks = app / "Contents" / "Frameworks"
    resources = app / "Contents" / "Resources" / "rotatorctl" / "data"
    macos = app / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)
    yaml = resources / "rotor-presets.yaml"
    yaml.write_text("presets: []\n", encoding="utf-8")
    link_dir = frameworks / "rotatorctl" / "data"
    link_dir.mkdir(parents=True)
    link = link_dir / "rotor-presets.yaml"
    link.symlink_to(yaml)
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(frameworks), raising=False)
    monkeypatch.setattr(sys, "executable", str(macos / "RotatorController"), raising=False)
    found = default_preset_path()
    assert found == link
    assert preset_path_is_bundled(found)


def test_symlink_out_of_the_app_is_not_bundled(tmp_path: Path, monkeypatch) -> None:
    app = tmp_path / "RotatorController.app"
    frameworks = app / "Contents" / "Frameworks"
    macos = app / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    outside = tmp_path / "checkout" / "rotor-presets.yaml"
    outside.parent.mkdir()
    outside.write_text("presets: []\n", encoding="utf-8")
    link_dir = frameworks / "rotatorctl" / "data"
    link_dir.mkdir(parents=True)
    link = link_dir / "rotor-presets.yaml"
    link.symlink_to(outside)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(frameworks), raising=False)
    monkeypatch.setattr(sys, "executable", str(macos / "RotatorController"), raising=False)
    assert not preset_path_is_bundled(link)


def test_exe_directory_catalog_counts_as_bundled(tmp_path: Path, monkeypatch) -> None:
    exe_dir = tmp_path / "app"
    bundled = exe_dir / "rotatorctl" / "data" / "rotor-presets.yaml"
    bundled.parent.mkdir(parents=True)
    bundled.write_text("presets: []\n", encoding="utf-8")
    empty = tmp_path / "meipass"
    empty.mkdir()
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(empty), raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "RotatorController"), raising=False)
    assert default_preset_path() == bundled
    assert preset_path_is_bundled(bundled)


def test_file_dialogs_start_in_the_config_dir(qtbot, tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "cfg"
    monkeypatch.setenv("ROTATOR_CONFIG_DIR", str(target))
    seen: dict[str, str] = {}

    def fake_open(_parent, title, directory, _filter):
        seen[title] = directory
        return "", ""

    def fake_save(_parent, title, directory, _filter):
        seen[title] = directory
        return "", ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", fake_save)
    window = MainWindow(presets=[])
    qtbot.addWidget(window)
    window.on_open_rotcfg()
    window.on_save_rotcfg_as()
    class _Client:
        def close(self) -> None:
            return None

    window.client = _Client()
    window.schema = object()
    window.on_restore()

    class _Form:
        def errors(self) -> dict[str, str]:
            return {}

    window.form = _Form()
    window.on_compare()
    window.on_backup()
    assert seen["Open configuration"] == str(target)
    assert seen["Save configuration"] == str(target / "station.rotcfg")
    assert seen["Restore settings"] == str(target)
    assert seen["Compare with file"] == str(target)
    assert seen["Backup settings"] == str(target / "rotator-settings.txt")
    assert target.is_dir()


def test_selftest_exits_zero(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROTATOR_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.delenv("ROTATOR_PRESETS", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert run_selftest() == 0
    assert not (tmp_path / "cfg" / ".selftest-probe").exists()
