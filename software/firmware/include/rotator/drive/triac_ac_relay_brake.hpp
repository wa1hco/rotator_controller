// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include "rotator/drive/axis_drive.hpp"
#include "rotator/hal/digital_out.hpp"

namespace rotator::drive {

// AC axis: CW triac, CCW triac, brake triac, and the ARM master relay.
//
// CW and CCW are mutually exclusive in this driver. There is no command
// that turns both on. Hardware gating on the board is the backstop; this
// class is the firmware side of that rule. Dead time between directions
// belongs to the motion controller, not here.
class TriacAcRelayBrake : public AxisDrive {
 public:
  TriacAcRelayBrake(hal::DigitalOut& clockwise, hal::DigitalOut& counter_clockwise,
                    hal::DigitalOut& brake_release, hal::DigitalOut& arm);

  void apply(DriveCommand command) override;
  DriveCommand command() const override;

 private:
  hal::DigitalOut& clockwise_;
  hal::DigitalOut& counter_clockwise_;
  hal::DigitalOut& brake_release_;
  hal::DigitalOut& arm_;
  DriveCommand command_ = DriveCommand::Safe;
};

}  // namespace rotator::drive
