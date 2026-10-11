// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include "rotator/drive/triac_ac_relay_brake.hpp"

namespace rotator::drive {

TriacAcRelayBrake::TriacAcRelayBrake(hal::DigitalOut& clockwise,
                                     hal::DigitalOut& counter_clockwise,
                                     hal::DigitalOut& brake_release,
                                     hal::DigitalOut& arm)
    : clockwise_(clockwise),
      counter_clockwise_(counter_clockwise),
      brake_release_(brake_release),
      arm_(arm) {
  apply(DriveCommand::Safe);
}

void TriacAcRelayBrake::apply(DriveCommand command) {
  command_ = command;
  const bool armed = command != DriveCommand::Safe;
  const bool clockwise = command == DriveCommand::Clockwise;
  const bool counter_clockwise = command == DriveCommand::CounterClockwise;
  // clockwise and counter_clockwise cannot both be true: the two
  // comparisons are against different enumerators.
  arm_.write(armed);
  clockwise_.write(clockwise);
  counter_clockwise_.write(counter_clockwise);
  brake_release_.write(armed);
}

DriveCommand TriacAcRelayBrake::command() const { return command_; }

}  // namespace rotator::drive
