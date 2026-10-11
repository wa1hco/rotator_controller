// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <cstddef>
#include <cstdint>

namespace rotator::hal {

// Nonvolatile byte storage (MCU flash, FRAM, or a host file).
class Storage {
 public:
  virtual ~Storage() = default;
  virtual bool write(std::uint32_t address, const std::uint8_t* data,
                     std::size_t length) = 0;
  virtual bool read(std::uint32_t address, std::uint8_t* data,
                    std::size_t length) = 0;
};

}  // namespace rotator::hal
