// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <optional>

namespace rotator::hal {

// One ADC channel, scaled to volts by the platform implementation.
class AnalogIn {
 public:
  virtual ~AnalogIn() = default;
  virtual std::optional<float> read_volts() = 0;
};

}  // namespace rotator::hal
