// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <optional>

#include "rotator/hal/analog_in.hpp"
#include "rotator/hal/digital_out.hpp"
#include "rotator/sensor/position_sensor.hpp"

class FakeAnalogIn : public rotator::hal::AnalogIn {
 public:
  float volts = 0.f;
  bool valid = true;

  std::optional<float> read_volts() override {
    if (!valid) {
      return std::nullopt;
    }
    return volts;
  }
};

class FakeDigitalOut : public rotator::hal::DigitalOut {
 public:
  bool level = false;

  void write(bool value) override { level = value; }
  bool read_back() const override { return level; }
};

class FakePositionSensor : public rotator::sensor::PositionSensor {
 public:
  std::optional<float> degrees = 180.f;

  std::optional<float> read_degrees() override { return degrees; }
};
