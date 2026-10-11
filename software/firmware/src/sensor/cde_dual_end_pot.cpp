// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include "rotator/sensor/cde_dual_end_pot.hpp"

namespace rotator::sensor {

CdeDualEndPot::CdeDualEndPot(hal::AnalogIn& end_a, hal::AnalogIn& end_b,
                             float min_deg, float max_deg)
    : end_a_(end_a), end_b_(end_b), min_deg_(min_deg), max_deg_(max_deg) {}

std::optional<float> CdeDualEndPot::fraction_from_end_volts(float volts_a,
                                                           float volts_b) {
  if (!(volts_a >= 0.f) || !(volts_b >= 0.f)) {
    return std::nullopt;
  }
  const float sum = volts_a + volts_b;
  if (!(sum > 0.f)) {
    return std::nullopt;
  }
  const float fraction = volts_a / sum;
  if (fraction < 0.f || fraction > 1.f) {
    return std::nullopt;
  }
  return fraction;
}

std::optional<float> CdeDualEndPot::read_degrees() {
  const std::optional<float> volts_a = end_a_.read_volts();
  const std::optional<float> volts_b = end_b_.read_volts();
  if (!volts_a || !volts_b) {
    return std::nullopt;
  }
  const std::optional<float> fraction =
      fraction_from_end_volts(*volts_a, *volts_b);
  if (!fraction) {
    return std::nullopt;
  }
  return min_deg_ + (*fraction) * (max_deg_ - min_deg_);
}

}  // namespace rotator::sensor
