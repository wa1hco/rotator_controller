// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace rotator::settings {

// Bump kSchemaVersion when the serialized layout changes. deserialize()
// rejects a blob whose version is not this one.
inline constexpr std::uint16_t kSchemaVersion = 1;

struct Settings {
  std::uint16_t schema_version = kSchemaVersion;
  float azimuth_min_deg = 0.f;
  float azimuth_max_deg = 450.f;
  std::uint16_t reversal_dead_time_ms = 500;
  std::uint16_t max_run_s = 120;
};

// Little-endian blob: magic "RSET", schema version, reserved u16 (must be 0),
// azimuth_min, azimuth_max, reversal_dead_time_ms, max_run_s, then a u16
// sum of the preceding bytes.
std::vector<std::uint8_t> serialize(const Settings& settings);
std::optional<Settings> deserialize(const std::uint8_t* data, std::size_t size);

}  // namespace rotator::settings
