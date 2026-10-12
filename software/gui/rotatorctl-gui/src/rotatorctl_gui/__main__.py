# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""``rotatorctl-gui`` opens the configuration UI in the default browser.

``--selftest`` starts the loopback server, fetches the page, and exits.
``--stay`` keeps the helper running with no browser and no idle quit.
"""

from __future__ import annotations

import secrets
import sys

from rotatorctl_gui.server import serve_until_stop
from rotatorctl_gui.state import AppState


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from rotatorctl_gui.selftest import run_selftest

        return run_selftest()
    stay = "--stay" in args
    state = AppState(idle_seconds=0 if stay else 20)
    state.token = secrets.token_urlsafe(18)
    return serve_until_stop(state, open_browser=not stay)


if __name__ == "__main__":
    raise SystemExit(main())
