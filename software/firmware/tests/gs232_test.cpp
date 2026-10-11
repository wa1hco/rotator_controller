// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include <gtest/gtest.h>

#include "rotator/protocol/gs232.hpp"

TEST(Gs232, ParsesAzimuthStopAndQuery) {
  const auto set = rotator::protocol::parse_gs232("M270\r\n");
  ASSERT_TRUE(set.has_value());
  EXPECT_EQ(set->verb, rotator::protocol::Gs232Verb::SetAzimuth);
  EXPECT_EQ(set->azimuth_deg, 270);

  const auto query = rotator::protocol::parse_gs232("c2");
  ASSERT_TRUE(query.has_value());
  EXPECT_EQ(query->verb, rotator::protocol::Gs232Verb::QueryAzimuth);

  const auto gs232a_query = rotator::protocol::parse_gs232("C");
  ASSERT_TRUE(gs232a_query.has_value());
  EXPECT_EQ(gs232a_query->verb, rotator::protocol::Gs232Verb::QueryAzimuth);

  const auto stop_b = rotator::protocol::parse_gs232("S");
  ASSERT_TRUE(stop_b.has_value());
  EXPECT_EQ(stop_b->verb, rotator::protocol::Gs232Verb::Stop);

  const auto stop_a = rotator::protocol::parse_gs232("A");
  ASSERT_TRUE(stop_a.has_value());
  EXPECT_EQ(stop_a->verb, rotator::protocol::Gs232Verb::Stop);

  EXPECT_FALSE(rotator::protocol::parse_gs232("M"));
  EXPECT_FALSE(rotator::protocol::parse_gs232("W180 045"));
  EXPECT_FALSE(rotator::protocol::parse_gs232(""));
}
