// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <cstddef>
#include <string_view>

namespace rotator::hal {

// Byte pipe used by protocol modules.
// USB and Ethernet are both required on the board. Each is one Link.
// The core does not include a TCP or USB stack, and it does not name the MCU.
class Link {
 public:
  virtual ~Link() = default;
  virtual std::size_t write(std::string_view bytes) = 0;
  virtual std::size_t read(char* buffer, std::size_t capacity) = 0;
};

}  // namespace rotator::hal
