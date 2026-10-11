// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <cstdint>

namespace rotator::hal {

// Monotonic millisecond clock. The core is tick-driven and does not block.
class Timer {
 public:
  virtual ~Timer() = default;
  virtual std::uint32_t now_ms() const = 0;
};

}  // namespace rotator::hal
