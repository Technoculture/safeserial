#include <gtest/gtest.h>
#include <vector>
#include <cstring>
#include <data_bridge/protocol/crc16.hpp>

TEST(CRC16, ValidJSONPasses) {
    const char* json =
        R"({"type":"ping","seq":1,"payload":"hello"})";

    std::vector<uint8_t> data(
        json,
        json + std::strlen(json)
    );

    uint16_t crc = crc16_ccitt(data.data(), data.size());

    // append CRC (big-endian)
    data.push_back((crc >> 8) & 0xFF);
    data.push_back(crc & 0xFF);

    uint16_t received_crc =
        (data[data.size() - 2] << 8) |
         data[data.size() - 1];

    uint16_t computed_crc =
        crc16_ccitt(data.data(), data.size() - 2);

    EXPECT_EQ(received_crc, computed_crc);
}

TEST(CRC16, CorruptedJSONFails) {
    const char* json =
        R"({"type":"ping","seq":1,"payload":"hello"})";

    std::vector<uint8_t> data(
        json,
        json + std::strlen(json)
    );

    uint16_t crc = crc16_ccitt(data.data(), data.size());

    data.push_back((crc >> 8) & 0xFF);
    data.push_back(crc & 0xFF);

    // corrupt JSON data
    data[10] ^= 0x01;

    uint16_t received_crc =
        (data[data.size() - 2] << 8) |
         data[data.size() - 1];

    uint16_t computed_crc =
        crc16_ccitt(data.data(), data.size() - 2);

    EXPECT_NE(received_crc, computed_crc);
}

