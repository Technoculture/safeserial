#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "crc16.hpp"


struct Packet {
  static constexpr uint8_t SOF = 0x02;
  static constexpr uint8_t EOF_MARKER = 0x03;

  static std::vector<uint8_t> serialize(const std::string& payload){
    std::vector<uint8_t> frame;
    frame.push_back(SOF);
    frame.push_back(static_cast<uint8_t>(payload.size()));

    for(char c: payload) frame.push_back(static_cast<uint8_t>(c));
    uint16_t crc = crc16_ccitt(reinterpret_cast<const uint8_t*>(payload.data()), payload.size());

    frame.push_back((crc>>8) & 0xFF);
 frame.push_back(crc & 0xFF);
 frame.push_back(EOF_MARKER);
return frame;
  }
};
