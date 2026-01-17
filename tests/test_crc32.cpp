#include <gtest/gtest.h>
#include <vector>
#include <cstring>
#include <safeserial/protocol/crc32.hpp>

TEST(CRC32, ValidJSONPasses) {
    const char* json =
        R"({"type":"ping","seq":1,"payload":"hello"})";

    std::vector<uint8_t> data(
        json,
        json + std::strlen(json)
    );

    uint32_t crc = CRC32::calculate(data.data(), data.size());
    uint32_t received_crc = crc;
    uint32_t computed_crc = CRC32::calculate(data.data(), data.size());

    EXPECT_EQ(received_crc, computed_crc);
}

TEST(CRC32, CorruptedJSONFails) {
    const char* json =
        R"({"type":"ping","seq":1,"payload":"hello"})";

    std::vector<uint8_t> data(
        json,
        json + std::strlen(json)
    );

    uint32_t crc = CRC32::calculate(data.data(), data.size());

    // corrupt JSON data
    data[10] ^= 0x01;

    uint32_t received_crc = crc;
    uint32_t computed_crc = CRC32::calculate(data.data(), data.size());

    EXPECT_NE(received_crc, computed_crc);
}
