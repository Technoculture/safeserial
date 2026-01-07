/**
 * Deep Verification Tests for Data Bridge Protocol
 * 
 * Tests edge cases, boundary conditions, and stress scenarios.
 */

#include <gtest/gtest.h>
#include <data_bridge/protocol/packet.hpp>
#include <data_bridge/protocol/reassembler.hpp>
#include <data_bridge/protocol/crc32.hpp>
#include <random>
#include <string>

class PacketTest : public ::testing::Test {
protected:
    void SetUp() override {}
};

// ============ COBS Encoding Tests ============

TEST_F(PacketTest, CobsEncodeEmpty) {
    std::vector<uint8_t> empty;
    auto encoded = Packet::cobs_encode(empty);
    EXPECT_EQ(encoded.size(), 1);  // Just the code byte
    EXPECT_EQ(encoded[0], 1);
}

TEST_F(PacketTest, CobsEncodeNoZeros) {
    std::vector<uint8_t> data = {0x01, 0x02, 0x03};
    auto encoded = Packet::cobs_encode(data);
    EXPECT_EQ(encoded.size(), 4);  // code + 3 bytes
    EXPECT_EQ(encoded[0], 4);      // run length of 4 (code itself + 3 bytes, next is implicit 0)
}

TEST_F(PacketTest, CobsEncodeAllZeros) {
    std::vector<uint8_t> data = {0x00, 0x00, 0x00};
    auto encoded = Packet::cobs_encode(data);
    // Each zero becomes a code byte with value 1
    EXPECT_EQ(encoded.size(), 4);
}

TEST_F(PacketTest, CobsRoundtrip) {
    std::vector<uint8_t> original = {0x00, 0x11, 0x22, 0x00, 0x33};
    auto encoded = Packet::cobs_encode(original);
    auto decoded = Packet::cobs_decode(encoded);
    
    // Remove trailing zero that COBS adds
    if (!decoded.empty() && decoded.back() == 0) {
        decoded.pop_back();
    }
    
    EXPECT_EQ(decoded, original);
}

TEST_F(PacketTest, CobsMaxRunLength) {
    // 254 non-zero bytes should trigger max run handling
    std::vector<uint8_t> data(254, 0xFF);
    auto encoded = Packet::cobs_encode(data);
    auto decoded = Packet::cobs_decode(encoded);
    EXPECT_EQ(decoded.size(), data.size());
}

// ============ CRC32 Tests ============

TEST_F(PacketTest, Crc32KnownValue) {
    // "123456789" should give CRC32 = 0xCBF43926
    std::string test = "123456789";
    uint32_t crc = CRC32::calculate(reinterpret_cast<const uint8_t*>(test.data()), test.size());
    EXPECT_EQ(crc, 0xCBF43926);
}

TEST_F(PacketTest, Crc32DetectsCorruption) {
    std::string original = "Hello, Data Bridge!";
    uint32_t crc1 = CRC32::calculate(reinterpret_cast<const uint8_t*>(original.data()), original.size());
    
    std::string corrupted = "Hello, Data Bridgf!";  // 'e' -> 'f'
    uint32_t crc2 = CRC32::calculate(reinterpret_cast<const uint8_t*>(corrupted.data()), corrupted.size());
    
    EXPECT_NE(crc1, crc2);
}

// ============ Packet Serialization Tests ============

TEST_F(PacketTest, SerializeDeserializeRoundtrip) {
    std::string payload = "Test payload data";
    uint8_t seq = 42;
    
    auto packet = Packet::serialize(Packet::TYPE_DATA, seq, payload);
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_TRUE(frame.valid);
    EXPECT_EQ(frame.header.type, Packet::TYPE_DATA);
    EXPECT_EQ(frame.header.seq_id, seq);
    EXPECT_EQ(std::string(frame.payload.begin(), frame.payload.end()), payload);
}

TEST_F(PacketTest, DeserializeRejectsCorrupted) {
    std::string payload = "Test payload";
    auto packet = Packet::serialize(Packet::TYPE_DATA, 1, payload);
    
    // Corrupt a byte in the middle
    packet[packet.size() / 2] ^= 0xFF;
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_FALSE(frame.valid);
}

TEST_F(PacketTest, DeserializeRejectsTruncated) {
    std::string payload = "Test payload";
    auto packet = Packet::serialize(Packet::TYPE_DATA, 1, payload);
    
    // Remove the delimiter
    packet.pop_back();
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_FALSE(frame.valid);
}

TEST_F(PacketTest, LargePayload) {
    // 1KB payload
    std::string payload(1024, 'X');
    
    auto packet = Packet::serialize(Packet::TYPE_DATA, 99, payload);
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_TRUE(frame.valid);
    EXPECT_EQ(frame.payload.size(), 1024);
}

TEST_F(PacketTest, EmptyPayload) {
    auto packet = Packet::serialize(Packet::TYPE_ACK, 0, "");
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_TRUE(frame.valid);
    EXPECT_EQ(frame.header.type, Packet::TYPE_ACK);
    EXPECT_TRUE(frame.payload.empty());
}

// ============ Reassembler Tests ============

TEST_F(PacketTest, ReassemblerSingleFragment) {
    Reassembler reassembler;
    
    std::string payload = "Complete message";
    auto packet = Packet::serialize(Packet::TYPE_DATA, 1, payload, 0, 1);
    
    std::vector<uint8_t> buffer(packet);
    auto frame = Packet::deserialize(buffer);
    
    EXPECT_TRUE(reassembler.process_fragment(frame));
    EXPECT_TRUE(reassembler.is_complete(frame));
    
    auto data = reassembler.get_data();
    EXPECT_EQ(std::string(data.begin(), data.end()), payload);
}

TEST_F(PacketTest, ReassemblerMultipleFragments) {
    Reassembler reassembler;
    
    // Create 3 fragments
    std::string part1 = "First";
    std::string part2 = "Second";
    std::string part3 = "Third";
    
    auto pkt1 = Packet::serialize(Packet::TYPE_DATA, 1, part1, 0, 3);
    auto pkt2 = Packet::serialize(Packet::TYPE_DATA, 1, part2, 1, 3);
    auto pkt3 = Packet::serialize(Packet::TYPE_DATA, 1, part3, 2, 3);
    
    std::vector<uint8_t> buf1(pkt1), buf2(pkt2), buf3(pkt3);
    auto f1 = Packet::deserialize(buf1);
    auto f2 = Packet::deserialize(buf2);
    auto f3 = Packet::deserialize(buf3);
    
    EXPECT_TRUE(reassembler.process_fragment(f1));
    EXPECT_FALSE(reassembler.is_complete(f1));
    
    EXPECT_TRUE(reassembler.process_fragment(f2));
    EXPECT_FALSE(reassembler.is_complete(f2));
    
    EXPECT_TRUE(reassembler.process_fragment(f3));
    EXPECT_TRUE(reassembler.is_complete(f3));
    
    auto data = reassembler.get_data();
    EXPECT_EQ(std::string(data.begin(), data.end()), part1 + part2 + part3);
}

TEST_F(PacketTest, ReassemblerRejectsOutOfOrder) {
    Reassembler reassembler;
    
    auto pkt1 = Packet::serialize(Packet::TYPE_DATA, 1, "First", 0, 3);
    auto pkt3 = Packet::serialize(Packet::TYPE_DATA, 1, "Third", 2, 3);  // Skip fragment 1
    
    std::vector<uint8_t> buf1(pkt1), buf3(pkt3);
    auto f1 = Packet::deserialize(buf1);
    auto f3 = Packet::deserialize(buf3);
    
    EXPECT_TRUE(reassembler.process_fragment(f1));
    EXPECT_FALSE(reassembler.process_fragment(f3));  // Out of order
}

// ============ Stress Tests ============

TEST_F(PacketTest, StressRandomPayloads) {
    std::mt19937 rng(42);
    
    for (int i = 0; i < 100; i++) {
        size_t len = rng() % 512 + 1;
        std::string payload(len, '\0');
        for (auto& c : payload) {
            c = static_cast<char>(rng() % 256);
        }
        
        auto packet = Packet::serialize(Packet::TYPE_DATA, i % 256, payload);
        std::vector<uint8_t> buffer(packet);
        auto frame = Packet::deserialize(buffer);
        
        EXPECT_TRUE(frame.valid) << "Failed on iteration " << i;
        EXPECT_EQ(std::string(frame.payload.begin(), frame.payload.end()), payload);
    }
}

TEST_F(PacketTest, SequenceWrapAround) {
    for (int seq = 0; seq <= 255; seq++) {
        auto packet = Packet::serialize(Packet::TYPE_DATA, static_cast<uint8_t>(seq), "test");
        std::vector<uint8_t> buffer(packet);
        auto frame = Packet::deserialize(buffer);
        
        EXPECT_TRUE(frame.valid);
        EXPECT_EQ(frame.header.seq_id, seq);
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
