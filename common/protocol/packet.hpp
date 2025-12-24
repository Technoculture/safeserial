#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <utility>
#include "crc16.hpp"

struct Packet {
    static constexpr uint8_t SOF = 0x02;
    static constexpr uint8_t EOF_MARKER = 0x03;

    // Keep the logic you have in your screenshot
    static std::vector<uint8_t> serialize(const std::string& payload) {
        std::vector<uint8_t> frame;
        frame.push_back(SOF);
        frame.push_back(static_cast<uint8_t>(payload.size()));

        for (char c : payload) frame.push_back(static_cast<uint8_t>(c));

        uint16_t crc = crc16_ccitt(reinterpret_cast<const uint8_t*>(payload.data()), payload.size());
        
        frame.push_back((crc >> 8) & 0xFF);
        frame.push_back(crc & 0xFF);
        frame.push_back(EOF_MARKER);
        return frame;
    }

    // ADD THIS: This is what main.cpp is missing
    static std::pair<bool, std::string> deserialize(std::vector<uint8_t>& buffer) {
        if (buffer.size() < 5) return {false, ""}; // Minimum: SOF + Len + 1 char + 2 CRC + EOF

        for (size_t i = 0; i < buffer.size(); ++i) {
            if (buffer[i] == SOF) {
                if (i + 1 >= buffer.size()) return {false, ""};
                size_t len = buffer[i + 1];
                
                // Check if we have the full packet: i + SOF + LEN + PAYLOAD + 2 CRC + EOF
                size_t total_expected = i + 2 + len + 2 + 1;
                
                if (buffer.size() >= total_expected) {
                    if (buffer[total_expected - 1] == EOF_MARKER) {
                        std::string payload(buffer.begin() + i + 2, buffer.begin() + i + 2 + len);
                        
                        // Optional: Verify CRC here if you want extra safety
                        
                        buffer.erase(buffer.begin(), buffer.begin() + total_expected);
                        return {true, payload};
                    }
                }
            }
        }
        return {false, ""};
    }
};
