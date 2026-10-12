# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""``python -m rotatorctl_gui``."""

from __future__ import annotations

import os
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--selftest" in args:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from rotatorctl_gui.selftest import run_selftest

        return run_selftest()
    from PySide6.QtWidgets import QApplication

    from rotatorctl_gui.main_window import MainWindow

    app = QApplication(args)
    window = MainWindow()
    window.resize(1280, 800)
    window.show()
    window.refresh()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
