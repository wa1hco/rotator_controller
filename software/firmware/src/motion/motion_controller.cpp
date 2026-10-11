// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include "rotator/motion/motion_controller.hpp"

namespace rotator::motion {

MotionController::MotionController(drive::AxisDrive& drive,
                                   sensor::PositionSensor& sensor,
                                   MotionConfig config)
    : drive_(drive), sensor_(sensor), config_(config) {
  apply();
}

void MotionController::request_clockwise() {
  request_run(MotionState::RunningClockwise);
}

void MotionController::request_counterclockwise() {
  request_run(MotionState::RunningCounterClockwise);
}

void MotionController::request_stop() {
  if (state_ == MotionState::Idle || state_ == MotionState::Stopping) {
    return;
  }
  if (state_ == MotionState::Fault) {
    enter(MotionState::Idle);
    return;
  }
  enter(MotionState::Stopping);
}

void MotionController::tick(std::uint32_t elapsed_ms) {
  last_reading_ = sensor_.read_degrees();
  elapsed_in_state_ms_ += elapsed_ms;

  if (state_ == MotionState::RunningClockwise ||
      state_ == MotionState::RunningCounterClockwise) {
    run_ms_ += elapsed_ms;
    if (run_ms_ >= config_.max_run_ms) {
      enter(MotionState::Fault);
      return;
    }
  }

  switch (state_) {
    case MotionState::Arming:
      if (elapsed_in_state_ms_ >= config_.arm_ms) {
        enter(pending_);
      }
      break;
    case MotionState::DeadTime:
      if (elapsed_in_state_ms_ >= config_.dead_time_ms) {
        enter(pending_);
      }
      break;
    case MotionState::Stopping:
      if (elapsed_in_state_ms_ >= config_.stop_ms) {
        enter(MotionState::Idle);
      }
      break;
    case MotionState::Idle:
    case MotionState::RunningClockwise:
    case MotionState::RunningCounterClockwise:
    case MotionState::Fault:
      break;
  }
}

MotionState MotionController::state() const { return state_; }

std::optional<float> MotionController::last_reading_deg() const {
  return last_reading_;
}

void MotionController::request_run(MotionState run_state) {
  if (state_ == MotionState::Fault || state_ == run_state) {
    return;
  }
  if (state_ == MotionState::Arming && pending_ == run_state) {
    return;
  }
  if (state_ == MotionState::DeadTime && pending_ == run_state) {
    return;
  }

  const bool opposite_running =
      (run_state == MotionState::RunningClockwise &&
       state_ == MotionState::RunningCounterClockwise) ||
      (run_state == MotionState::RunningCounterClockwise &&
       state_ == MotionState::RunningClockwise);

  pending_ = run_state;
  if (opposite_running) {
    enter(MotionState::DeadTime);
    return;
  }
  if (state_ == MotionState::DeadTime) {
    // Direction changed before the gap finished. Start the gap over.
    enter(MotionState::DeadTime);
    return;
  }
  if (state_ != MotionState::Arming) {
    enter(MotionState::Arming);
  }
}

void MotionController::enter(MotionState next) {
  state_ = next;
  elapsed_in_state_ms_ = 0;
  if (next == MotionState::RunningClockwise ||
      next == MotionState::RunningCounterClockwise ||
      next == MotionState::Idle || next == MotionState::Fault) {
    run_ms_ = 0;
  }
  apply();
}

void MotionController::apply() {
  using drive::DriveCommand;
  switch (state_) {
    case MotionState::Idle:
    case MotionState::Fault:
      drive_.apply(DriveCommand::Safe);
      break;
    case MotionState::Arming:
    case MotionState::DeadTime:
    case MotionState::Stopping:
      drive_.apply(DriveCommand::ArmedIdle);
      break;
    case MotionState::RunningClockwise:
      drive_.apply(DriveCommand::Clockwise);
      break;
    case MotionState::RunningCounterClockwise:
      drive_.apply(DriveCommand::CounterClockwise);
      break;
  }
}

}  // namespace rotator::motion
