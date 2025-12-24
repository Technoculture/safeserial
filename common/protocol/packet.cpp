#include "protocol/packet.hpp"
#include <algorithm>

std::vector<uint8_t> Packet::serialize(const std::string& json) {
    std::vector<uint8_t> packet;
    packet.push_back(0x02); // Start of Frame (STX)
    for (char c : json) packet.push_back(static_cast<uint8_t>(c));
    packet.push_back(0x03); // End of Frame (ETX)
    return packet;
}

// Returns {success, json_content}
std::pair<bool, std::string> Packet::deserialize(std::vector<uint8_t>& buffer) {
    auto start = std::find(buffer.begin(), buffer.end(), 0x02);
    auto end = std::find(buffer.begin(), buffer.end(), 0x03);

    if (start != buffer.end() && end != buffer.end() && end > start) {
        std::string json(start + 1, end);
        buffer.erase(buffer.begin(), end + 1); // Clean up the buffer
        return {true, json};
    }
    return {false, ""};
}
