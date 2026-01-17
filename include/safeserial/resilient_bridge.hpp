#pragma once

#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <vector>

#include <safeserial/safeserial.hpp>

class ResilientDataBridge {
public:
    struct Options {
        DataBridge::Options bridge;
        bool reconnect;
        uint32_t reconnect_delay_ms;
        uint32_t max_reconnect_delay_ms;
        size_t max_queue_size;

        static Options Defaults() {
            Options options{};
            options.bridge = DataBridge::Options::Defaults();
            options.reconnect = true;
            options.reconnect_delay_ms = 1000;
            options.max_reconnect_delay_ms = 30000;
            options.max_queue_size = 1000;
            return options;
        }
    };

    ResilientDataBridge();
    explicit ResilientDataBridge(const Options& options);
    ResilientDataBridge(const Options& options,
                        std::function<std::shared_ptr<ISerialPort>()> serial_factory);
    ~ResilientDataBridge();

    ResilientDataBridge(const ResilientDataBridge&) = delete;
    ResilientDataBridge& operator=(const ResilientDataBridge&) = delete;

    bool open(const std::string& port);
    void close();

    int send(const std::vector<uint8_t>& data);

    bool is_connected() const;
    size_t queue_length() const;

    void set_on_data(std::function<void(const std::vector<uint8_t>&)> callback);
    void set_on_error(std::function<void(const std::string&)> callback);
    void set_on_disconnect(std::function<void()> callback);
    void set_on_reconnecting(std::function<void(uint32_t, uint32_t)> callback);
    void set_on_reconnected(std::function<void()> callback);
    void set_on_close(std::function<void()> callback);

private:
    struct QueuedMessage {
        explicit QueuedMessage(std::vector<uint8_t> payload)
            : data(std::move(payload)) {}

        std::vector<uint8_t> data;
        int bytes_written = 0;
        bool done = false;
        bool failed = false;
        std::string error;
        std::mutex mutex;
        std::condition_variable cv;
    };

    bool connect();
    void handle_disconnect(const std::string& reason);
    void start_reconnect_thread();
    void reconnect_loop();
    void flush_queue();
    void notify_error(const std::string& message);

    std::string port_;
    Options options_;
    std::function<std::shared_ptr<ISerialPort>()> serial_factory_;

    std::unique_ptr<DataBridge> bridge_;
    std::atomic<bool> connected_{false};
    std::atomic<bool> stop_{false};

    std::mutex state_mutex_;
    mutable std::mutex queue_mutex_;
    std::vector<std::shared_ptr<QueuedMessage>> queue_;

    std::thread reconnect_thread_;
    std::atomic<bool> reconnect_thread_running_{false};
    uint32_t reconnect_attempt_ = 0;
    std::mt19937 rng_{std::random_device{}()};

    std::mutex callback_mutex_;
    std::function<void(const std::vector<uint8_t>&)> on_data_;
    std::function<void(const std::string&)> on_error_;
    std::function<void()> on_disconnect_;
    std::function<void(uint32_t, uint32_t)> on_reconnecting_;
    std::function<void()> on_reconnected_;
    std::function<void()> on_close_;
};
