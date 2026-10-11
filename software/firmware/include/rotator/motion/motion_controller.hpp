// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <cstdint>
#include <optional>

#include "rotator/drive/axis_drive.hpp"
#include "rotator/motion/motion_state.hpp"
#include "rotator/sensor/position_sensor.hpp"

namespace rotator::motion {

struct MotionConfig {
  // ARM relay settle before a direction gate is allowed.
  std::uint32_t arm_ms = 50;
  // Directions-off gap before reversing. Hardware RC is the backstop
  // (about 70–110 ms). Firmware uses a longer gap.
  std::uint32_t dead_time_ms = 500;
  // Directions off, still armed, before the brake re-engages and ARM drops.
  std::uint32_t stop_ms = 150;
  // One continuous run. Past this, the axis disarms.
  std::uint32_t max_run_ms = 120000;
};

// One axis. tick() is called by the platform with elapsed milliseconds.
// The controller does not sleep and does not talk to hardware except
// through AxisDrive and PositionSensor.
class MotionController {
 public:
  MotionController(drive::AxisDrive& drive, sensor::PositionSensor& sensor,
                   MotionConfig config);

  void request_clockwise();
  void request_counterclockwise();
  void request_stop();
  void tick(std::uint32_t elapsed_ms);

  MotionState state() const;
  std::optional<float> last_reading_deg() const;

 private:
  void request_run(MotionState run_state);
  void enter(MotionState next);
  void apply();

  drive::AxisDrive& drive_;
  sensor::PositionSensor& sensor_;
  MotionConfig config_;
  MotionState state_ = MotionState::Idle;
  MotionState pending_ = MotionState::Idle;
  std::uint32_t elapsed_in_state_ms_ = 0;
  std::uint32_t run_ms_ = 0;
  std::optional<float> last_reading_;
};

}  // namespace rotator::motion
