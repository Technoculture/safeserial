#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <utility>
#include <cstring>
#include <algorithm>
#include <safeserial/protocol/crc32.hpp>
#include <safeserial/config.hpp>

// Cross-platform packed struct support
#if defined(_MSC_VER)
#define PACKED_STRUCT_BEGIN __pragma(pack(push, 1))
#define PACKED_STRUCT_END __pragma(pack(pop))
#define PACKED_ATTR
#elif defined(__GNUC__) || defined(__clang__)
#define PACKED_STRUCT_BEGIN
#define PACKED_STRUCT_END
#define PACKED_ATTR __attribute__((packed))
#else
#define PACKED_STRUCT_BEGIN
#define PACKED_STRUCT_END
#define PACKED_ATTR
#endif

struct Packet {
    PACKED_STRUCT_BEGIN
    struct Header {
        uint8_t  type;
        uint8_t  seq_id;
        uint16_t fragment_id;
        uint16_t total_frags;
        uint16_t payload_len;
        uint32_t crc32;
    } PACKED_ATTR;
    PACKED_STRUCT_END

    // Packet Types
    static constexpr uint8_t TYPE_DATA = 0x10;
    static constexpr uint8_t TYPE_ACK  = 0x20;
    static constexpr uint8_t TYPE_NACK = 0x30;
    static constexpr uint8_t TYPE_SYN  = 0x40;
    
    // COBS delimiter
    static constexpr uint8_t COBS_DELIMITER = 0x00;

    // Configuration accessors (use env vars or defaults)
    static uint8_t maxRetries() { return SafeSerialConfig::maxRetries(); }
    static uint16_t retryTimeoutMs() { return SafeSerialConfig::retryTimeoutMs(); }
    static uint16_t fragmentSize() { return SafeSerialConfig::fragmentSize(); }

    struct Frame {
        Header header;
        std::vector<uint8_t> payload;
        bool valid;
    };
    
    // Consistent Overhead Byte Stuffing (COBS) Encoding
    static std::vector<uint8_t> cobs_encode(const std::vector<uint8_t>& data) {
        std::vector<uint8_t> encoded;
        encoded.reserve(data.size() + data.size() / 254 + 2);

        size_t code_idx = 0;
        encoded.push_back(0); // Placeholder for the first code
        uint8_t code = 1;

        for (uint8_t byte : data) {
            if (byte == 0) {
                encoded[code_idx] = code;
                code_idx = encoded.size();
                encoded.push_back(0); // Placeholder for next code
                code = 1;
            } else {
                encoded.push_back(byte);
                code++;
                if (code == 0xFF) { // Max run length reached
                    encoded[code_idx] = code;
                    code_idx = encoded.size();
                    encoded.push_back(0);
                    code = 1;
                }
            }
        }
        encoded[code_idx] = code;
        return encoded;
    }

    // COBS Decoding
    static std::vector<uint8_t> cobs_decode(const std::vector<uint8_t>& data) {
        std::vector<uint8_t> decoded;
        decoded.reserve(data.size());

        size_t i = 0;
        while (i < data.size()) {
            uint8_t code = data[i];
            i++;
            if (code == 0) break; // Should not happen in valid COBS before delimiter

            for (uint8_t j = 1; j < code; j++) {
                if (i >= data.size()) return {}; // Error: truncated
                decoded.push_back(data[i++]);
            }
            if (code < 0xFF && i < data.size()) {
                decoded.push_back(0);
            }
        }
        return decoded;
    }

    static std::vector<uint8_t> serialize(uint8_t type, uint8_t seq, const std::string& payload, uint16_t frag_id = 0, uint16_t total_frags = 1) {
        Header header;
        header.type = type;
        header.seq_id = seq;
        header.fragment_id = frag_id;
        header.total_frags = total_frags;
        header.payload_len = static_cast<uint16_t>(payload.size());
        header.crc32 = 0; // Calculated later

        std::vector<uint8_t> raw_packet;
        raw_packet.resize(sizeof(Header) + payload.size());
        
        std::memcpy(raw_packet.data(), &header, sizeof(Header));
        std::memcpy(raw_packet.data() + sizeof(Header), payload.data(), payload.size());

        // Calculate CRC32 of Header + Payload (with CRC field zeroed)
        uint32_t crc = CRC32::calculate(raw_packet.data(), raw_packet.size());
        
        // Update header with calculated CRC
        header.crc32 = crc;
        std::memcpy(raw_packet.data(), &header, sizeof(Header));

        // Encode with COBS
        std::vector<uint8_t> encoded = cobs_encode(raw_packet);
        encoded.push_back(COBS_DELIMITER); 
        return encoded;
    }

    static Frame deserialize(std::vector<uint8_t>& buffer) {
        // Find delimiter
        auto it = std::find(buffer.begin(), buffer.end(), COBS_DELIMITER);
        if (it == buffer.end()) return {{}, {}, false}; // No complete frame yet

        std::vector<uint8_t> frame_data(buffer.begin(), it);
        buffer.erase(buffer.begin(), it + 1); // Remove processed frame + delimiter

        if (frame_data.empty()) return {{}, {}, false};

        std::vector<uint8_t> decoded = cobs_decode(frame_data);
        if (decoded.size() < sizeof(Header)) return {{}, {}, false};

        Header header;
        std::memcpy(&header, decoded.data(), sizeof(Header));

        // Validate Length
        if (decoded.size() != sizeof(Header) + header.payload_len) return {{}, {}, false};

        // Validate CRC
        uint32_t received_crc = header.crc32;
        
        // Zero out CRC in buffer to recompute
        Header* header_ptr = reinterpret_cast<Header*>(decoded.data());
        header_ptr->crc32 = 0;
        
        uint32_t computed_crc = CRC32::calculate(decoded.data(), decoded.size());
        
        if (received_crc == computed_crc) {
            std::vector<uint8_t> payload(decoded.begin() + sizeof(Header), decoded.end());
            // Retrieve original header
            header.crc32 = received_crc; 
            return {header, payload, true};
        }

        return {{}, {}, false};
    }
};
