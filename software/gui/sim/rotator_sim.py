# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Launch the console-protocol simulator.

``software/sim`` is the C++ K3NG sandbox. This launcher starts
``rotatorctl.sim``, which speaks the console and GS-232 grammar in
``docs/design/configuration.md``. The implementation lives in the
installable library so ``rotatorctl-sim`` works after ``pip install``.
"""

from rotatorctl.sim import main

if __name__ == "__main__":
    raise SystemExit(main())
