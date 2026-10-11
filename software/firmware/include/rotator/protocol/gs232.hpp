// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <optional>
#include <string_view>

namespace rotator::protocol {

// Subset of Yaesu GS-232A and GS-232B used by the first protocol module.
// Elevation, speed, and the GS-232B status block are later work.
enum class Gs232Verb {
  Stop,          // "A" on GS-232A, "S" on GS-232B
  SetAzimuth,    // "Maaa" with 1 to 3 digits, 0–999
  QueryAzimuth,  // "C" on GS-232A, "C2" on GS-232B
};

struct Gs232Command {
  Gs232Verb verb = Gs232Verb::Stop;
  int azimuth_deg = 0;  // meaningful for SetAzimuth
};

// One command line. Leading and trailing whitespace and CR/LF are ignored.
// Returns nullopt for an empty line or a command this module does not accept.
std::optional<Gs232Command> parse_gs232(std::string_view line);

}  // namespace rotator::protocol
