#pragma once
#include <cstdint>
#include <cstddef>

class CRC32 {
public:
    static uint32_t calculate(const uint8_t* data, size_t length) {
        uint32_t crc = 0xFFFFFFFF;
        for (size_t i = 0; i < length; ++i) {
            uint8_t byte = data[i];
            crc = crc ^ byte;
            for (int j = 0; j < 8; ++j) {
                uint32_t mask = -(crc & 1);
                crc = (crc >> 1) ^ (0xEDB88320 & mask);
            }
        }
        return ~crc;
    }
};
