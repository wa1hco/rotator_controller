// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include <gtest/gtest.h>

#include "rotator/drive/triac_ac_relay_brake.hpp"
#include "rotator/motion/motion_controller.hpp"
#include "fakes.hpp"

namespace {

struct Rig {
  FakeDigitalOut clockwise;
  FakeDigitalOut counter_clockwise;
  FakeDigitalOut brake_release;
  FakeDigitalOut arm;
  rotator::drive::TriacAcRelayBrake drive{clockwise, counter_clockwise,
                                          brake_release, arm};
  FakePositionSensor sensor;
  rotator::motion::MotionController controller{
      drive, sensor,
      rotator::motion::MotionConfig{50, 500, 150, 1000}};
};

}  // namespace

TEST(MotionController, ReversalKeepsDirectionsExclusive) {
  Rig rig;
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Idle);
  EXPECT_FALSE(rig.arm.level);

  rig.controller.request_clockwise();
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Arming);
  EXPECT_TRUE(rig.arm.level);
  EXPECT_FALSE(rig.clockwise.level);
  EXPECT_FALSE(rig.counter_clockwise.level);

  rig.controller.tick(50);
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::RunningClockwise);
  EXPECT_TRUE(rig.clockwise.level);
  EXPECT_FALSE(rig.counter_clockwise.level);

  rig.controller.request_counterclockwise();
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::DeadTime);
  EXPECT_FALSE(rig.clockwise.level);
  EXPECT_FALSE(rig.counter_clockwise.level);
  EXPECT_TRUE(rig.arm.level);

  rig.controller.tick(499);
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::DeadTime);
  rig.controller.tick(1);
  EXPECT_EQ(rig.controller.state(),
            rotator::motion::MotionState::RunningCounterClockwise);
  EXPECT_FALSE(rig.clockwise.level);
  EXPECT_TRUE(rig.counter_clockwise.level);
  ASSERT_TRUE(rig.controller.last_reading_deg().has_value());
  EXPECT_FLOAT_EQ(*rig.controller.last_reading_deg(), 180.f);
}

TEST(MotionController, StopDisarmsAndOverrunFaults) {
  Rig rig;
  rig.controller.request_clockwise();
  rig.controller.tick(50);
  rig.controller.request_stop();
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Stopping);
  EXPECT_FALSE(rig.clockwise.level);
  EXPECT_TRUE(rig.arm.level);

  rig.controller.tick(150);
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Idle);
  EXPECT_FALSE(rig.arm.level);
  EXPECT_FALSE(rig.brake_release.level);

  rig.controller.request_clockwise();
  rig.controller.tick(50);
  rig.controller.tick(1000);
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Fault);
  EXPECT_FALSE(rig.arm.level);
  EXPECT_FALSE(rig.clockwise.level);

  rig.controller.request_clockwise();
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Fault);
  rig.controller.request_stop();
  EXPECT_EQ(rig.controller.state(), rotator::motion::MotionState::Idle);
}
