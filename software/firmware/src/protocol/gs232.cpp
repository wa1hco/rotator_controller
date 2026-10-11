// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only

#include "rotator/protocol/gs232.hpp"

#include <cctype>
#include <string>

namespace rotator::protocol {
namespace {

std::string_view trim(std::string_view in) {
  while (!in.empty() &&
         (in.front() == ' ' || in.front() == '\t' || in.front() == '\r' ||
          in.front() == '\n')) {
    in.remove_prefix(1);
  }
  while (!in.empty() &&
         (in.back() == ' ' || in.back() == '\t' || in.back() == '\r' ||
          in.back() == '\n')) {
    in.remove_suffix(1);
  }
  return in;
}

std::string upper_copy(std::string_view in) {
  std::string out;
  out.reserve(in.size());
  for (unsigned char ch : in) {
    out.push_back(static_cast<char>(std::toupper(ch)));
  }
  return out;
}

}  // namespace

std::optional<Gs232Command> parse_gs232(std::string_view line) {
  const std::string text = upper_copy(trim(line));
  if (text.empty()) {
    return std::nullopt;
  }
  if (text == "A" || text == "S") {
    return Gs232Command{Gs232Verb::Stop, 0};
  }
  if (text == "C" || text == "C2") {
    return Gs232Command{Gs232Verb::QueryAzimuth, 0};
  }
  if (text.front() != 'M' || text.size() < 2 || text.size() > 4) {
    return std::nullopt;
  }
  int value = 0;
  for (std::size_t i = 1; i < text.size(); ++i) {
    const unsigned char ch = static_cast<unsigned char>(text[i]);
    if (!std::isdigit(ch)) {
      return std::nullopt;
    }
    value = value * 10 + (text[i] - '0');
  }
  return Gs232Command{Gs232Verb::SetAzimuth, value};
}

}  // namespace rotator::protocol
