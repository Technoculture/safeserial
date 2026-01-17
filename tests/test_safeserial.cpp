/**
 * DataBridge integration tests with a mocked serial port.
 */

#include <gtest/gtest.h>

#include <condition_variable>
#include <chrono>
#include <mutex>
#include <vector>

#include <safeserial/safeserial.hpp>
#include <safeserial/protocol/packet.hpp>

namespace {

class MockSerial : public ISerialPort {
public:
    bool open(const std::string& port_name, int baud_rate) override {
        (void)port_name;
        (void)baud_rate;
        open_ = true;
        return true;
    }

    void close() override {
        open_ = false;
    }

    int write(const std::vector<uint8_t>& data) override {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            writes_.push_back(data);
        }
        if (on_write_) {
            on_write_(data);
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

    void push_read(const std::vector<uint8_t>& data) {
        std::lock_guard<std::mutex> lock(mutex_);
        read_buffer_.insert(read_buffer_.end(), data.begin(), data.end());
    }

    void set_on_write(std::function<void(const std::vector<uint8_t>&)> cb) {
        on_write_ = std::move(cb);
    }

    const std::vector<std::vector<uint8_t>>& writes() const { return writes_; }

private:
    bool open_ = false;
    std::mutex mutex_;
    std::vector<uint8_t> read_buffer_;
    std::vector<std::vector<uint8_t>> writes_;
    std::function<void(const std::vector<uint8_t>&)> on_write_;
};

} // namespace

TEST(DataBridgeTest, SendSingleFragmentAcked) {
    auto serial = std::make_shared<MockSerial>();
    DataBridge::Options options = DataBridge::Options::Defaults();
    options.ack_timeout_ms = 50;
    options.max_retries = 2;
    options.fragment_size = 512;
    DataBridge bridge(serial, options);

    serial->set_on_write([serial](const std::vector<uint8_t>& data) {
        std::vector<uint8_t> buffer(data);
        Packet::Frame frame = Packet::deserialize(buffer);
        if (!frame.valid || frame.header.type != Packet::TYPE_DATA) {
            return;
        }
        auto ack = Packet::serialize(Packet::TYPE_ACK,
                                     frame.header.seq_id,
                                     "",
                                     frame.header.fragment_id,
                                     frame.header.total_frags);
        serial->push_read(ack);
    });

    ASSERT_TRUE(bridge.open("mock"));

    std::vector<uint8_t> payload = {'H', 'i'};
    int written = bridge.send(payload, options.ack_timeout_ms, options.max_retries, options.fragment_size);

    EXPECT_GT(written, 0);
    EXPECT_EQ(serial->writes().size(), 1u);

    bridge.close();
}

TEST(DataBridgeTest, RetriesWhenAckMissing) {
    auto serial = std::make_shared<MockSerial>();
    DataBridge::Options options = DataBridge::Options::Defaults();
    options.ack_timeout_ms = 10;
    options.max_retries = 2;
    options.fragment_size = 512;
    DataBridge bridge(serial, options);

    int write_count = 0;
    serial->set_on_write([serial, &write_count](const std::vector<uint8_t>& data) {
        std::vector<uint8_t> buffer(data);
        Packet::Frame frame = Packet::deserialize(buffer);
        if (!frame.valid || frame.header.type != Packet::TYPE_DATA) {
            return;
        }
        write_count++;
        if (write_count < 2) {
            return;
        }
        auto ack = Packet::serialize(Packet::TYPE_ACK,
                                     frame.header.seq_id,
                                     "",
                                     frame.header.fragment_id,
                                     frame.header.total_frags);
        serial->push_read(ack);
    });

    ASSERT_TRUE(bridge.open("mock"));

    std::vector<uint8_t> payload = {'R', 'e', 't', 'r', 'y'};
    int written = bridge.send(payload, options.ack_timeout_ms, options.max_retries, options.fragment_size);

    EXPECT_GT(written, 0);
    EXPECT_EQ(write_count, 2);
    EXPECT_EQ(serial->writes().size(), 2u);

    bridge.close();
}

TEST(DataBridgeTest, ReassemblesFragmentsAndAcks) {
    auto serial = std::make_shared<MockSerial>();
    DataBridge::Options options = DataBridge::Options::Defaults();
    options.fragment_size = 3;
    DataBridge bridge(serial, options);

    std::mutex mutex;
    std::condition_variable cv;
    std::vector<uint8_t> received;

    bridge.set_on_data([&](const std::vector<uint8_t>& data) {
        {
            std::lock_guard<std::mutex> lock(mutex);
            received = data;
        }
        cv.notify_one();
    });

    ASSERT_TRUE(bridge.open("mock"));

    auto pkt1 = Packet::serialize(Packet::TYPE_DATA, 1, "ABC", 0, 2);
    auto pkt2 = Packet::serialize(Packet::TYPE_DATA, 1, "DEF", 1, 2);
    serial->push_read(pkt1);
    serial->push_read(pkt2);

    std::unique_lock<std::mutex> lock(mutex);
    bool ok = cv.wait_for(lock, std::chrono::milliseconds(200), [&]() {
        return !received.empty();
    });

    EXPECT_TRUE(ok);
    std::string result(received.begin(), received.end());
    EXPECT_EQ(result, "ABCDEF");

    size_t ack_count = 0;
    for (const auto& write : serial->writes()) {
        std::vector<uint8_t> buffer(write);
        Packet::Frame frame = Packet::deserialize(buffer);
        if (frame.valid && frame.header.type == Packet::TYPE_ACK) {
            ack_count++;
        }
    }
    EXPECT_EQ(ack_count, 2u);

    bridge.close();
}
