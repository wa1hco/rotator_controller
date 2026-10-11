# Host tools

Placeholder for station-side tools that are not part of the firmware
core or the physics simulator.

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
