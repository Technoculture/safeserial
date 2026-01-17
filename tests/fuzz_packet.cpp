#include <cstddef>
#include <cstdint>
#include <vector>

#include <data_bridge/protocol/packet.hpp>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    std::vector<uint8_t> buffer(data, data + size);
    (void)Packet::deserialize(buffer);
    return 0;
}
