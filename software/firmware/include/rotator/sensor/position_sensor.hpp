// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <optional>

namespace rotator::sensor {

// Heading in degrees for one axis. Implementations own filtering and
// calibration. Callers see only an angle, or no sample.
class PositionSensor {
 public:
  virtual ~PositionSensor() = default;
  virtual std::optional<float> read_degrees() = 0;
};

}  // namespace rotator::sensor
