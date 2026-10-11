// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

namespace rotator::drive {

// What one axis power stage should be doing.
// On a CDE rotator the brake solenoid releases the mechanical brake when
// it is energized, so "brake released" is the powered state.
enum class DriveCommand {
  // Disarmed. Direction triacs off. Brake solenoid off (brake held).
  Safe,
  // Armed, brake solenoid on, neither direction gated.
  ArmedIdle,
  Clockwise,
  CounterClockwise,
};

class AxisDrive {
 public:
  virtual ~AxisDrive() = default;
  virtual void apply(DriveCommand command) = 0;
  virtual DriveCommand command() const = 0;
};

}  // namespace rotator::drive
