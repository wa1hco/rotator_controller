# Host tools

Station-side tools that are not part of the firmware core or the
physics simulator.

## Enclosure machining drawings

[`enclosure/gen_machining.py`](enclosure/gen_machining.py) reads a
KiCad board and writes 1:1 end-panel and top-wall drill drawings from
footprint fields (`Panel`, `PanelCutout`, `PanelZ`). The workflow,
the default cutouts, and the pre-layout sheets are in
[`hardware/controller/mechanical/README.md`](../../hardware/controller/mechanical/README.md).
Decision: [ADR 0017](../../docs/decisions/0017-enclosure-machining-drawings.md).

```bash
python3 software/tools/enclosure/gen_machining.py BOARD.kicad_pcb -o /tmp/enclosure
python3 -m unittest discover -s software/tools/enclosure -p 'test_*.py'
```

Needs matplotlib (`pip install matplotlib`). No KiCad GUI.

## Still a placeholder

The rest of this directory is reserved for station-side tools that
are not written yet.

Expected here later:

- Calibration scripts (dual-end pot end-to-end, soft limits, overlap).
- Octave (or equivalent) plots of ADC counts, fitted pot resistance, and
  heading error. The old V4 branch had `Software/octave/`
  (`AngleCalcs.m`, `ReadSerial.m`, and saved figures). Those files were
  not imported; they remain in
  [wa1hco/Rotator-Controller-V2](https://github.com/wa1hco/Rotator-Controller-V2)
  branch `Rotator_Controller_V4` at
  `27affb32f34605df6d436127cd1c47bb30fbcdb9`.
- A web compass served by the controller (or by a small host bridge).

The compass page that already exists is the simulator GUI, and it still
talks to a K3NG process. It lives in [`../sim/gui/`](../sim/gui/) and is
documented in [`../sim/README.md`](../sim/README.md).
