// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include <gtest/gtest.h>

#include "rotator/settings/settings.hpp"

TEST(Settings, RoundTripAndRejectsOtherVersions) {
  rotator::settings::Settings original;
  original.azimuth_min_deg = 180.f;
  original.azimuth_max_deg = 630.f;
  original.reversal_dead_time_ms = 500;
  original.max_run_s = 120;

  const std::vector<std::uint8_t> blob = rotator::settings::serialize(original);
  const auto loaded = rotator::settings::deserialize(blob.data(), blob.size());
  ASSERT_TRUE(loaded.has_value());
  EXPECT_EQ(loaded->schema_version, rotator::settings::kSchemaVersion);
  EXPECT_FLOAT_EQ(loaded->azimuth_min_deg, 180.f);
  EXPECT_FLOAT_EQ(loaded->azimuth_max_deg, 630.f);
  EXPECT_EQ(loaded->reversal_dead_time_ms, 500);
  EXPECT_EQ(loaded->max_run_s, 120);

  std::vector<std::uint8_t> corrupt = blob;
  corrupt.back() = static_cast<std::uint8_t>(corrupt.back() ^ 0xff);
  EXPECT_FALSE(rotator::settings::deserialize(corrupt.data(), corrupt.size()));

  std::vector<std::uint8_t> other_version = blob;
  other_version[4] = 99;
  other_version[5] = 0;
  std::uint16_t sum = 0;
  for (std::size_t i = 0; i + 2 < other_version.size(); ++i) {
    sum = static_cast<std::uint16_t>(sum + other_version[i]);
  }
  other_version[other_version.size() - 2] = static_cast<std::uint8_t>(sum & 0xff);
  other_version[other_version.size() - 1] =
      static_cast<std::uint8_t>((sum >> 8) & 0xff);
  EXPECT_FALSE(
      rotator::settings::deserialize(other_version.data(), other_version.size()));
}
