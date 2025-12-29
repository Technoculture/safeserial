#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <utility>
#include "crc16.hpp"

struct Packet {
    static constexpr uint8_t SOF = 0x02;
    static constexpr uint8_t EOF_MARKER = 0x03;
    
    // Packet Types
    static constexpr uint8_t TYPE_DATA = 0x10;
    static constexpr uint8_t TYPE_ACK  = 0x20;
    static constexpr uint8_t TYPE_NACK = 0x30;
    static constexpr uint8_t TYPE_SYN  = 0x40;

    struct Frame {
        uint8_t type;
        uint8_t seq;
        std::string payload;
        bool valid;
    };

    static std::vector<uint8_t> serialize(uint8_t type, uint8_t seq, const std::string& payload) {
        std::vector<uint8_t> frame;
        frame.push_back(SOF);
        frame.push_back(type);
        frame.push_back(seq);
        frame.push_back(static_cast<uint8_t>(payload.size()));

        for (char c : payload) frame.push_back(static_cast<uint8_t>(c));

        // CRC covers Type, Seq, Len, and Payload
        std::vector<uint8_t> crc_data = {type, seq, static_cast<uint8_t>(payload.size())};
        crc_data.insert(crc_data.end(), payload.begin(), payload.end());
        uint16_t crc = crc16_ccitt(crc_data.data(), crc_data.size());
        
        frame.push_back((crc >> 8) & 0xFF);
        frame.push_back(crc & 0xFF);
        frame.push_back(EOF_MARKER);
        return frame;
    }

    static Frame deserialize(std::vector<uint8_t>& buffer) {
        if (buffer.size() < 7) return {0, 0, "", false}; 

        for (size_t i = 0; i < buffer.size(); ++i) {
            if (buffer[i] == SOF) {
                if (i + 4 >= buffer.size()) break;
                
                uint8_t type = buffer[i + 1];
                uint8_t seq  = buffer[i + 2];
                size_t len   = buffer[i + 3];
                size_t total_expected = i + 4 + len + 2 + 1;

                if (buffer.size() >= total_expected) {
                    if (buffer[total_expected - 1] == EOF_MARKER) {
                        // Validate CRC
                        std::vector<uint8_t> crc_data(buffer.begin() + i + 1, buffer.begin() + i + 4 + len);
                        uint16_t received_crc = (buffer[total_expected - 3] << 8) | buffer[total_expected - 2];
                        uint16_t computed_crc = crc16_ccitt(crc_data.data(), crc_data.size());

                        if (received_crc == computed_crc) {
                            std::string payload(buffer.begin() + i + 4, buffer.begin() + i + 4 + len);
                            buffer.erase(buffer.begin(), buffer.begin() + total_expected);
                            return {type, seq, payload, true};
                        } else {
                            // CRC Failed - remove this SOF to keep searching
                            buffer.erase(buffer.begin(), buffer.begin() + i + 1);
                            return {TYPE_NACK, seq, "", false};
                        }
                    }
                }
            }
        }
        return {0, 0, "", false};
    }
};
