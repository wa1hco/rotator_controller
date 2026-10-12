# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""``python -m rotatorctl_gui``."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from rotatorctl_gui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    app = QApplication(sys.argv if argv is None else argv)
    window = MainWindow()
    window.resize(1280, 800)
    window.show()
    window.refresh()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
