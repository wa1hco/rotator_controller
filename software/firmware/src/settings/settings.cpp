// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include "rotator/settings/settings.hpp"

#include <cstring>

namespace rotator::settings {
namespace {

constexpr std::uint8_t kMagic0 = 'R';
constexpr std::uint8_t kMagic1 = 'S';
constexpr std::uint8_t kMagic2 = 'E';
constexpr std::uint8_t kMagic3 = 'T';
constexpr std::size_t kBlobSize = 22;

void append_u16(std::vector<std::uint8_t>& out, std::uint16_t value) {
  out.push_back(static_cast<std::uint8_t>(value & 0xff));
  out.push_back(static_cast<std::uint8_t>((value >> 8) & 0xff));
}

void append_f32(std::vector<std::uint8_t>& out, float value) {
  static_assert(sizeof(float) == 4, "settings blob expects 32-bit float");
  std::uint32_t bits = 0;
  std::memcpy(&bits, &value, sizeof(bits));
  for (int shift = 0; shift < 32; shift += 8) {
    out.push_back(static_cast<std::uint8_t>((bits >> shift) & 0xff));
  }
}

bool read_u16(const std::uint8_t* data, std::size_t size, std::size_t offset,
              std::uint16_t* value) {
  if (offset + 2 > size) {
    return false;
  }
  *value = static_cast<std::uint16_t>(data[offset] |
                                      (static_cast<std::uint16_t>(data[offset + 1]) << 8));
  return true;
}

bool read_f32(const std::uint8_t* data, std::size_t size, std::size_t offset,
              float* value) {
  if (offset + 4 > size) {
    return false;
  }
  std::uint32_t bits = 0;
  for (int i = 0; i < 4; ++i) {
    bits |= static_cast<std::uint32_t>(data[offset + static_cast<std::size_t>(i)])
            << (8 * i);
  }
  std::memcpy(value, &bits, sizeof(*value));
  return true;
}

std::uint16_t checksum(const std::uint8_t* data, std::size_t length) {
  std::uint16_t sum = 0;
  for (std::size_t i = 0; i < length; ++i) {
    sum = static_cast<std::uint16_t>(sum + data[i]);
  }
  return sum;
}

}  // namespace

std::vector<std::uint8_t> serialize(const Settings& settings) {
  std::vector<std::uint8_t> out;
  out.reserve(kBlobSize);
  out.push_back(kMagic0);
  out.push_back(kMagic1);
  out.push_back(kMagic2);
  out.push_back(kMagic3);
  append_u16(out, settings.schema_version);
  append_u16(out, 0);  // reserved
  append_f32(out, settings.azimuth_min_deg);
  append_f32(out, settings.azimuth_max_deg);
  append_u16(out, settings.reversal_dead_time_ms);
  append_u16(out, settings.max_run_s);
  append_u16(out, checksum(out.data(), out.size()));
  return out;
}

std::optional<Settings> deserialize(const std::uint8_t* data, std::size_t size) {
  if (data == nullptr || size != kBlobSize) {
    return std::nullopt;
  }
  if (data[0] != kMagic0 || data[1] != kMagic1 || data[2] != kMagic2 ||
      data[3] != kMagic3) {
    return std::nullopt;
  }
  std::uint16_t stored = 0;
  if (!read_u16(data, size, kBlobSize - 2, &stored) ||
      stored != checksum(data, kBlobSize - 2)) {
    return std::nullopt;
  }

  Settings settings;
  std::uint16_t reserved = 0;
  if (!read_u16(data, size, 4, &settings.schema_version) ||
      !read_u16(data, size, 6, &reserved) || reserved != 0 ||
      !read_f32(data, size, 8, &settings.azimuth_min_deg) ||
      !read_f32(data, size, 12, &settings.azimuth_max_deg) ||
      !read_u16(data, size, 16, &settings.reversal_dead_time_ms) ||
      !read_u16(data, size, 18, &settings.max_run_s)) {
    return std::nullopt;
  }
  if (settings.schema_version != kSchemaVersion) {
    return std::nullopt;
  }
  return settings;
}

}  // namespace rotator::settings
