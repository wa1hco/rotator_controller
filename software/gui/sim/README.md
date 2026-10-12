# Console simulator

`software/sim` is the C++ K3NG sandbox. This directory is the launcher for a different program: a Python controller that speaks the text console and the GS-232 subset in `docs/design/configuration.md`.

The simulator itself is `rotatorctl.sim`, inside the GUI-free library, so tests and `rotatorctl-sim` can start it after install. Each instance has its own settings record. It listens on TCP, can open a pty in place of USB CDC, and can advertise `_rotatorctl._tcp`.

```bash
rotatorctl-sim -n 2 --pty --mdns
python software/gui/sim/rotator_sim.py -n 2 --base-port 4533 --pty --mdns
```

The first controller gets the pty when `--pty` is set. Every controller gets a TCP port at `--base-port` plus its index. `--mdns` registers `_rotatorctl._tcp` on 127.0.0.1. A firmware build will advertise the Ethernet address instead.
