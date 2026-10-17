# Decision records

These record choices already made for the clean-slate controller.
They are short on purpose. The reasoning and the numbers live in
`docs/design/`.

| ADR | Decision |
|---|---|
| [0001](0001-clean-slate-core.md) | New C++ core, not a K3NG refactor |
| [0002](0002-full-replacement.md) | The box replaces the stock controller |
| [0003](0003-external-power-supply.md) | Motor and logic power supplies stay outside the box |
| [0004](0004-discrete-triacs.md) | MOC3023M + BTA16-600SW and snubbers, not CPC1966 |
| [0005](0005-direction-interlock.md) | ARM relay and dead time remain; the gate and RC hold are superseded by 0020 |
| [0006](0006-headless-panel.md) | Headless, with STOP / CW / CCW and LEDs |
| [0007](0007-usb-and-ethernet.md) | USB and Ethernet both required |
| [0008](0008-two-axes.md) | Two axes at the sensor and MCU |
| [0009](0009-hammond-enclosure.md) | Hammond 1455N1601, controls on the front, cables on the rear |
| [0010](0010-triac-heatsink-bar.md) | Triacs on an aluminum bar clamped to the top wall |
| [0011](0011-rotor-connector.md) | TE CPC Series 1 shell 13, 9-pin, controller end female |
| [0012](0012-one-repository.md) | One repository for hardware and software |
| [0013](0013-assembly-sourcing.md) | JLCPCB assembles SMT from LCSC; owner hand-solders through-hole from Mouser |
| [0014](0014-stm32f407-lan8720.md) | STM32F407VGT6 + LAN8720A; Ethernet standard; W5500 dropped |
| [0015](0015-configuration-and-ui.md) | Board file, no feature `#ifdef`s, versioned settings; web UI and a shared console |
| [0016](0016-motor-run-capacitor.md) | CDE run cap: 100 µF flat plus 33 µF upright, 133 µF |
| [0017](0017-enclosure-machining-drawings.md) | Panel holes are generated from footprint positions, not drawn on the PCB |
| [0018](0018-ac-power-and-grounding.md) | AC version: one 26 VAC Powerpole feed; logic ground is the rotor return |
| [0019](0019-pc-gui-toolkit.md) | Python console library and a browser configuration UI shared with the firmware web page |
