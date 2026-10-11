// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

namespace rotator::protocol {

// hamlib rotctld is a later protocol module. GS-232 is the first one.
// This header reserves the name so board and host builds share one place
// for it. There is no parser yet.
enum class RotctldStatus {
  NotImplemented,
};

}  // namespace rotator::protocol
