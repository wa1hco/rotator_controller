// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

namespace rotator::motion {

// Per-axis motion. Direction outputs are off in every state except the
// two Running states, and those two are never active together.
enum class MotionState {
  Idle,
  Arming,
  DeadTime,
  RunningClockwise,
  RunningCounterClockwise,
  Stopping,
  Fault,
};

}  // namespace rotator::motion
