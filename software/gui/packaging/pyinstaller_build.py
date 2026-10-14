# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Freeze Rotator Controller with PyInstaller.

    python software/gui/packaging/pyinstaller_build.py windows
    python software/gui/packaging/pyinstaller_build.py macos
    python software/gui/packaging/pyinstaller_build.py linux

Outputs, under ``software/gui/packaging/out/``:

- ``RotatorController-Windows.exe`` (one file)
- ``RotatorController-macOS.dmg`` (unsigned ``.app``)
- ``RotatorController-Linux.AppImage``

The rotor catalog is added as ``rotatorctl/data/rotor-presets.yaml`` inside
the bundle. Linux wraps the onedir tree in an AppImage. ``APPIMAGETOOL``
overrides the tool path; otherwise the script downloads the continuous
x86_64 build into the work directory.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

APPIMAGE_TOOL_URL = (
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
)
TARGETS = ("windows", "macos", "linux")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "software" / "firmware" / "presets" / "rotor-presets.yaml"
        if candidate.is_file():
            return parent
    raise SystemExit("rotor-presets.yaml not found above the packaging script")


def _run(cmd: list[str], **kwargs: object) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, **kwargs)


def pyinstaller_cmd(root: Path, work: Path, onefile: bool, *, windowed: bool = False) -> list[str]:
    preset = root / "software" / "firmware" / "presets" / "rotor-presets.yaml"
    entry = root / "software" / "gui" / "packaging" / "entry.py"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "RotatorController",
        "--distpath",
        str(work / "dist"),
        "--workpath",
        str(work / "build"),
        "--specpath",
        str(work / "spec"),
        "--paths",
        str(root / "software" / "gui" / "rotatorctl" / "src"),
        "--paths",
        str(root / "software" / "gui" / "rotatorctl-gui" / "src"),
        "--add-data",
        f"{preset}{os.pathsep}rotatorctl/data",
        "--add-data",
        f"{root / 'software' / 'gui' / 'rotatorctl-gui' / 'src' / 'rotatorctl_gui' / 'static'}{os.pathsep}rotatorctl_gui/static",
        "--hidden-import",
        "yaml",
        "--hidden-import",
        "serial",
        "--hidden-import",
        "serial.tools.list_ports",
        "--hidden-import",
        "zeroconf",
        "--hidden-import",
        "pydantic",
        "--hidden-import",
        "aiohttp",
        "--hidden-import",
        "yarl",
        "--hidden-import",
        "multidict",
        "--collect-submodules",
        "rotatorctl",
        "--collect-submodules",
        "rotatorctl_gui",
        "--collect-submodules",
        "aiohttp",
        "--exclude-module",
        "aiohttp.pytest_plugin",
        "--exclude-module",
        "aiohttp.test_utils",
        "--exclude-module",
        "pydantic.v1.mypy",
        "--collect-submodules",
        "zeroconf",
    ]
    if onefile:
        cmd.append("--onefile")
    # macOS needs a windowed build to emit a .app. Windows stays a console
    # app so the session URL has somewhere to print.
    if windowed:
        cmd.append("--windowed")
    cmd.append(str(entry))
    return cmd


def build_windows(root: Path, work: Path, out: Path) -> None:
    _run(pyinstaller_cmd(root, work, onefile=True))
    shutil.copy2(work / "dist" / "RotatorController.exe", out / "RotatorController-Windows.exe")


def build_macos(root: Path, work: Path, out: Path) -> None:
    _run(pyinstaller_cmd(root, work, onefile=False, windowed=True))
    app = work / "dist" / "RotatorController.app"
    stage = work / "dmg-root"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    shutil.copytree(app, stage / "RotatorController.app", symlinks=True)
    applications = stage / "Applications"
    if applications.exists() or applications.is_symlink():
        applications.unlink()
    applications.symlink_to("/Applications")
    dmg = out / "RotatorController-macOS.dmg"
    if dmg.exists():
        dmg.unlink()
    _run(
        [
            "hdiutil",
            "create",
            "-volname",
            "Rotator Controller",
            "-srcfolder",
            str(stage),
            "-ov",
            "-format",
            "UDZO",
            str(dmg),
        ]
    )


def _appimagetool(work: Path) -> Path:
    override = os.environ.get("APPIMAGETOOL")
    if override:
        return Path(override)
    tool = work / "appimagetool-x86_64.AppImage"
    if not tool.is_file():
        print(f"downloading {APPIMAGE_TOOL_URL}", flush=True)
        urllib.request.urlretrieve(APPIMAGE_TOOL_URL, tool)
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    return tool


def build_linux(root: Path, work: Path, out: Path) -> None:
    _run(pyinstaller_cmd(root, work, onefile=False))
    packaging = root / "software" / "gui" / "packaging"
    appdir = work / "AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    bindir = appdir / "usr" / "bin" / "RotatorController"
    shutil.copytree(work / "dist" / "RotatorController", bindir, symlinks=True)
    apprun = appdir / "AppRun"
    shutil.copy2(packaging / "AppRun", apprun)
    apprun.chmod(apprun.stat().st_mode | stat.S_IEXEC)
    shutil.copy2(packaging / "rotator-controller.desktop", appdir / "rotator-controller.desktop")
    icon = packaging / "rotator-controller.png"
    if not icon.is_file():
        raise SystemExit(f"missing {icon}")
    shutil.copy2(icon, appdir / "rotator-controller.png")
    image = out / "RotatorController-Linux.AppImage"
    if image.exists():
        image.unlink()
    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    env.setdefault("APPIMAGE_EXTRACT_AND_RUN", "1")
    _run([str(_appimagetool(work)), str(appdir), str(image)], env=env)
    image.chmod(image.stat().st_mode | stat.S_IEXEC)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in TARGETS:
        print(f"usage: {argv[0]} {'|'.join(TARGETS)}", file=sys.stderr)
        return 2
    target = argv[1]
    root = repo_root()
    work = root / "software" / "gui" / "packaging" / "work"
    out = root / "software" / "gui" / "packaging" / "out"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    out.mkdir(parents=True, exist_ok=True)
    if target == "windows":
        build_windows(root, work, out)
    elif target == "macos":
        build_macos(root, work, out)
    else:
        build_linux(root, work, out)
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
