// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <optional>

#include "rotator/hal/analog_in.hpp"
#include "rotator/sensor/position_sensor.hpp"

namespace rotator::sensor {

// CDE / Hy-Gain HAM-IV and Tailtwister dual-end potentiometer.
//
// The wiper is the common return. Both element ends are measured.
// fraction_from_end_volts() is the ideal divider ratio v_a / (v_a + v_b).
// Series lead resistance that shows up on both ends cancels in that ratio.
// Notch filtering, the FIR used on the previous controller, and the
// calibration map from ratio to heading are not in this skeleton.
class CdeDualEndPot : public PositionSensor {
 public:
  CdeDualEndPot(hal::AnalogIn& end_a, hal::AnalogIn& end_b, float min_deg,
                float max_deg);

  std::optional<float> read_degrees() override;

  // Returns a fraction in [0, 1], or nullopt if the ends cannot form one.
  static std::optional<float> fraction_from_end_volts(float volts_a,
                                                      float volts_b);

 private:
  hal::AnalogIn& end_a_;
  hal::AnalogIn& end_b_;
  float min_deg_;
  float max_deg_;
};

}  // namespace rotator::sensor
