#pragma once

#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include <safeserial/config.hpp>
#include <safeserial/protocol/packet.hpp>
#include <safeserial/protocol/reassembler.hpp>
#include <safeserial/transport/iserial_port.hpp>
#include <safeserial/transport/serial_port.hpp>

class DataBridge {
public:
    struct Options {
        int baud_rate;
        uint8_t max_retries;
        uint16_t ack_timeout_ms;
        uint16_t fragment_size;

        static Options Defaults() {
            return Options{
                SafeSerialConfig::baudRate(),
                SafeSerialConfig::maxRetries(),
                SafeSerialConfig::ackTimeoutMs(),
                SafeSerialConfig::fragmentSize(),
            };
        }
    };

    DataBridge();
    explicit DataBridge(const Options& options);
    DataBridge(std::shared_ptr<ISerialPort> serial, const Options& options);
    ~DataBridge();

    DataBridge(const DataBridge&) = delete;
    DataBridge& operator=(const DataBridge&) = delete;

    bool open(const std::string& port, int baud_rate_override = -1);
    void close();
    bool is_open() const;

    int send(const std::vector<uint8_t>& data,
             uint16_t ack_timeout_ms_override = 0,
             uint8_t max_retries_override = 0,
             uint16_t fragment_size_override = 0);

    void set_on_data(std::function<void(const std::vector<uint8_t>&)> callback);
    size_t get_buffered_size() const;

private:
    void receive_loop();
    void handle_frame(const Packet::Frame& frame);
    void send_ack(const Packet::Frame& frame);

    std::shared_ptr<ISerialPort> serial_;
    Options options_;

    std::atomic<bool> stop_{false};
    std::atomic<bool> is_open_{false};
    std::thread receive_thread_;

    std::vector<uint8_t> rx_buffer_;
    Reassembler reassembler_;

    std::mutex seq_mutex_;
    uint8_t next_seq_{0};

    std::mutex send_mutex_;
    std::mutex write_mutex_;

    std::mutex ack_mutex_;
    std::condition_variable ack_cv_;
    bool waiting_for_ack_{false};
    bool acked_{false};
    uint8_t waiting_seq_{0};
    uint16_t waiting_frag_{0};

    std::mutex callback_mutex_;
    std::function<void(const std::vector<uint8_t>&)> on_data_;
};
