// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include <gtest/gtest.h>

#include "rotator/drive/triac_ac_relay_brake.hpp"
#include "fakes.hpp"

namespace {

struct Pins {
  FakeDigitalOut clockwise;
  FakeDigitalOut counter_clockwise;
  FakeDigitalOut brake_release;
  FakeDigitalOut arm;
  rotator::drive::TriacAcRelayBrake drive{clockwise, counter_clockwise,
                                          brake_release, arm};
};

}  // namespace

TEST(TriacDrive, DirectionsAreNeverBothOn) {
  Pins pins;
  pins.drive.apply(rotator::drive::DriveCommand::Clockwise);
  EXPECT_TRUE(pins.clockwise.level);
  EXPECT_FALSE(pins.counter_clockwise.level);
  EXPECT_TRUE(pins.arm.level);
  EXPECT_TRUE(pins.brake_release.level);

  pins.drive.apply(rotator::drive::DriveCommand::CounterClockwise);
  EXPECT_FALSE(pins.clockwise.level);
  EXPECT_TRUE(pins.counter_clockwise.level);

  pins.drive.apply(rotator::drive::DriveCommand::ArmedIdle);
  EXPECT_FALSE(pins.clockwise.level);
  EXPECT_FALSE(pins.counter_clockwise.level);
  EXPECT_TRUE(pins.arm.level);

  pins.drive.apply(rotator::drive::DriveCommand::Safe);
  EXPECT_FALSE(pins.arm.level);
  EXPECT_FALSE(pins.brake_release.level);
  EXPECT_FALSE(pins.clockwise.level);
  EXPECT_FALSE(pins.counter_clockwise.level);
}
