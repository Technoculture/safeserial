/**
 * ResilientDataBridge tests with a mocked serial transport.
 */

#include <gtest/gtest.h>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <future>
#include <mutex>
#include <vector>

#include <safeserial/resilient_bridge.hpp>
#include <safeserial/protocol/packet.hpp>

namespace {

class MockSerial : public ISerialPort {
public:
    explicit MockSerial(std::shared_ptr<std::atomic<int>> open_attempts,
                        int succeed_after)
        : open_attempts_(std::move(open_attempts)),
          succeed_after_(succeed_after) {}

    bool open(const std::string& port_name, int baud_rate) override {
        (void)port_name;
        (void)baud_rate;
        int attempt = ++(*open_attempts_);
        return attempt >= succeed_after_;
    }

    void close() override {}

    int write(const std::vector<uint8_t>& data) override {
        std::lock_guard<std::mutex> lock(mutex_);
        writes_.push_back(data);

        std::vector<uint8_t> buffer(data);
        Packet::Frame frame = Packet::deserialize(buffer);
        if (frame.valid && frame.header.type == Packet::TYPE_DATA) {
            auto ack = Packet::serialize(Packet::TYPE_ACK,
                                         frame.header.seq_id,
                                         "",
                                         frame.header.fragment_id,
                                         frame.header.total_frags);
            read_buffer_.insert(read_buffer_.end(), ack.begin(), ack.end());
        }
        return static_cast<int>(data.size());
    }

    int read(uint8_t* buffer, size_t size) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (read_buffer_.empty()) {
            return 0;
        }
        size_t n = std::min(size, read_buffer_.size());
        std::copy(read_buffer_.begin(), read_buffer_.begin() + static_cast<long>(n), buffer);
        read_buffer_.erase(read_buffer_.begin(), read_buffer_.begin() + static_cast<long>(n));
        return static_cast<int>(n);
    }

    size_t write_count() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return writes_.size();
    }

private:
    std::shared_ptr<std::atomic<int>> open_attempts_;
    int succeed_after_;
    mutable std::mutex mutex_;
    std::vector<uint8_t> read_buffer_;
    std::vector<std::vector<uint8_t>> writes_;
};

} // namespace

TEST(ResilientBridgeTest, QueuesUntilReconnectAndFlushes) {
    auto attempts = std::make_shared<std::atomic<int>>(0);

    ResilientDataBridge::Options options = ResilientDataBridge::Options::Defaults();
    options.reconnect = true;
    options.reconnect_delay_ms = 1;
    options.max_reconnect_delay_ms = 5;
    options.max_queue_size = 10;
    options.bridge.ack_timeout_ms = 5;
    options.bridge.max_retries = 1;
    options.bridge.fragment_size = 64;

    auto factory = [attempts]() {
        return std::make_shared<MockSerial>(attempts, 2);
    };

    ResilientDataBridge bridge(options, factory);
    EXPECT_FALSE(bridge.open("/dev/mock"));

    auto future = std::async(std::launch::async, [&bridge]() {
        std::vector<uint8_t> payload = {'Q', 'u', 'e', 'u', 'e'};
        return bridge.send(payload);
    });

    auto status = future.wait_for(std::chrono::milliseconds(200));
    EXPECT_EQ(status, std::future_status::ready);
    EXPECT_GT(future.get(), 0);

    bridge.close();
}
