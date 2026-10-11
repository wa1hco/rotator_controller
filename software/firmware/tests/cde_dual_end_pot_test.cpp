// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include <gtest/gtest.h>

#include "rotator/sensor/cde_dual_end_pot.hpp"
#include "fakes.hpp"

TEST(CdeDualEndPot, MidScaleIsHalfTheTravel) {
  FakeAnalogIn end_a;
  FakeAnalogIn end_b;
  end_a.volts = 1.5f;
  end_b.volts = 1.5f;
  rotator::sensor::CdeDualEndPot pot(end_a, end_b, 0.f, 450.f);

  const auto heading = pot.read_degrees();
  ASSERT_TRUE(heading.has_value());
  EXPECT_NEAR(*heading, 225.f, 0.01f);
}

TEST(CdeDualEndPot, OpenEndIsNotAHeading) {
  FakeAnalogIn end_a;
  FakeAnalogIn end_b;
  end_a.volts = 1.f;
  end_b.valid = false;
  rotator::sensor::CdeDualEndPot pot(end_a, end_b, 0.f, 360.f);
  EXPECT_FALSE(pot.read_degrees().has_value());
  EXPECT_FALSE(
      rotator::sensor::CdeDualEndPot::fraction_from_end_volts(0.f, 0.f));
}
