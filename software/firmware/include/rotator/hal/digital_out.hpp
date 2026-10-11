// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

namespace rotator::hal {

class DigitalOut {
 public:
  virtual ~DigitalOut() = default;
  virtual void write(bool level) = 0;
  virtual bool read_back() const = 0;
};

}  // namespace rotator::hal
