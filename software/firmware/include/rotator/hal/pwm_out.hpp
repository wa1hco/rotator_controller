// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

namespace rotator::hal {

// Duty is 0.0 (fully off) through 1.0 (fully on).
// The AC triac drive does not use PWM. DC and stepper axes will.
class PwmOut {
 public:
  virtual ~PwmOut() = default;
  virtual void set_duty(float duty_0_to_1) = 0;
};

}  // namespace rotator::hal
