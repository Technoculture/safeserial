#include <safeserial/resilient_bridge.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <stdexcept>

ResilientDataBridge::ResilientDataBridge()
    : options_(Options::Defaults()) {}

ResilientDataBridge::ResilientDataBridge(const Options& options)
    : options_(options) {}

ResilientDataBridge::ResilientDataBridge(
    const Options& options,
    std::function<std::shared_ptr<ISerialPort>()> serial_factory)
    : options_(options),
      serial_factory_(std::move(serial_factory)) {}

ResilientDataBridge::~ResilientDataBridge() {
    close();
}

bool ResilientDataBridge::open(const std::string& port) {
    std::lock_guard<std::mutex> lock(state_mutex_);
    if (connected_) {
        return true;
    }

    port_ = port;
    stop_ = false;
    bool ok = connect();
    if (!ok && options_.reconnect) {
        start_reconnect_thread();
    }
    return ok;
}

void ResilientDataBridge::close() {
    stop_ = true;
    if (reconnect_thread_.joinable()) {
        reconnect_thread_.join();
    }
    reconnect_thread_running_ = false;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        if (bridge_) {
            bridge_->close();
            bridge_.reset();
        }
        connected_ = false;
    }

    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        for (auto& msg : queue_) {
            std::lock_guard<std::mutex> msg_lock(msg->mutex);
            msg->failed = true;
            msg->error = "Connection closed";
            msg->done = true;
            msg->cv.notify_all();
        }
        queue_.clear();
    }

    std::function<void()> cb;
    {
        std::lock_guard<std::mutex> lock(callback_mutex_);
        cb = on_close_;
    }
    if (cb) {
        cb();
    }
}

bool ResilientDataBridge::connect() {
    if (port_.empty()) {
        notify_error("Port not set");
        return false;
    }

    if (serial_factory_) {
        auto serial = serial_factory_();
        bridge_ = std::make_unique<DataBridge>(serial, options_.bridge);
    } else {
        bridge_ = std::make_unique<DataBridge>(options_.bridge);
    }
    bridge_->set_on_data([this](const std::vector<uint8_t>& data) {
        std::function<void(const std::vector<uint8_t>&)> cb;
        {
            std::lock_guard<std::mutex> lock(callback_mutex_);
            cb = on_data_;
        }
        if (cb) {
            cb(data);
        }
    });

    if (!bridge_->open(port_, options_.bridge.baud_rate)) {
        bridge_.reset();
        return false;
    }

    connected_ = true;
    reconnect_attempt_ = 0;

    std::function<void()> cb;
    {
        std::lock_guard<std::mutex> lock(callback_mutex_);
        cb = on_reconnected_;
    }
    if (cb && reconnect_thread_running_) {
        cb();
    }

    flush_queue();
    return true;
}

void ResilientDataBridge::handle_disconnect(const std::string& reason) {
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        if (!connected_) {
            return;
        }
        connected_ = false;
        if (bridge_) {
            bridge_->close();
            bridge_.reset();
        }
    }

    std::function<void()> cb;
    {
        std::lock_guard<std::mutex> lock(callback_mutex_);
        cb = on_disconnect_;
    }
    if (cb) {
        cb();
    }

    notify_error(reason);

    if (options_.reconnect && !stop_) {
        start_reconnect_thread();
    }
}

void ResilientDataBridge::start_reconnect_thread() {
    if (reconnect_thread_running_) {
        return;
    }

    reconnect_thread_running_ = true;
    reconnect_thread_ = std::thread(&ResilientDataBridge::reconnect_loop, this);
}

void ResilientDataBridge::reconnect_loop() {
    while (!stop_ && options_.reconnect) {
        if (connected_) {
            break;
        }

        reconnect_attempt_++;
        uint32_t base_delay = options_.reconnect_delay_ms;
        uint32_t max_delay = options_.max_reconnect_delay_ms;
        uint32_t backoff = base_delay * static_cast<uint32_t>(std::pow(2, reconnect_attempt_ - 1));
        uint32_t jitter = static_cast<uint32_t>(rng_() % 1000);
        uint32_t delay = std::min(max_delay, backoff + jitter);

        std::function<void(uint32_t, uint32_t)> cb;
        {
            std::lock_guard<std::mutex> lock(callback_mutex_);
            cb = on_reconnecting_;
        }
        if (cb) {
            cb(reconnect_attempt_, delay);
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
        if (stop_) {
            break;
        }

        bool ok = false;
        if (!connected_) {
            ok = connect();
        } else {
            ok = true;
        }
        if (ok) {
            break;
        }
    }

    reconnect_thread_running_ = false;
}

void ResilientDataBridge::flush_queue() {
    while (!stop_ && connected_) {
        std::shared_ptr<QueuedMessage> msg;
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            if (queue_.empty()) {
                break;
            }
            msg = queue_.front();
            queue_.erase(queue_.begin());
        }

        try {
            int written = bridge_->send(
                msg->data,
                options_.bridge.ack_timeout_ms,
                options_.bridge.max_retries,
                options_.bridge.fragment_size);

            {
                std::lock_guard<std::mutex> msg_lock(msg->mutex);
                msg->bytes_written = written;
                msg->done = true;
                msg->cv.notify_all();
            }
        } catch (const std::exception& ex) {
            {
                std::lock_guard<std::mutex> lock(queue_mutex_);
                queue_.insert(queue_.begin(), msg);
            }
            handle_disconnect(ex.what());
            break;
        }
    }
}

int ResilientDataBridge::send(const std::vector<uint8_t>& data) {
    if (stop_) {
        throw std::runtime_error("Connection closed");
    }

    if (connected_ && bridge_) {
        try {
            return bridge_->send(
                data,
                options_.bridge.ack_timeout_ms,
                options_.bridge.max_retries,
                options_.bridge.fragment_size);
        } catch (const std::exception& ex) {
            if (!options_.reconnect) {
                throw;
            }
            handle_disconnect(ex.what());
        }
    } else if (!options_.reconnect) {
        throw std::runtime_error("Not connected");
    }

    auto msg = std::make_shared<QueuedMessage>(data);
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        while (queue_.size() >= options_.max_queue_size) {
            auto dropped = queue_.front();
            queue_.erase(queue_.begin());
            {
                std::lock_guard<std::mutex> dropped_lock(dropped->mutex);
                dropped->failed = true;
                dropped->error = "Message dropped: queue overflow";
                dropped->done = true;
                dropped->cv.notify_all();
            }
        }
        queue_.push_back(msg);
    }

    if (options_.reconnect && !reconnect_thread_running_) {
        start_reconnect_thread();
    }

    std::unique_lock<std::mutex> lock(msg->mutex);
    msg->cv.wait(lock, [&]() { return msg->done || stop_; });
    if (stop_) {
        throw std::runtime_error("Connection closed");
    }
    if (msg->failed) {
        throw std::runtime_error(msg->error);
    }
    return msg->bytes_written;
}

bool ResilientDataBridge::is_connected() const {
    return connected_.load();
}

size_t ResilientDataBridge::queue_length() const {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return queue_.size();
}

void ResilientDataBridge::set_on_data(std::function<void(const std::vector<uint8_t>&)> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_data_ = std::move(callback);
}

void ResilientDataBridge::set_on_error(std::function<void(const std::string&)> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_error_ = std::move(callback);
}

void ResilientDataBridge::set_on_disconnect(std::function<void()> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_disconnect_ = std::move(callback);
}

void ResilientDataBridge::set_on_reconnecting(std::function<void(uint32_t, uint32_t)> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_reconnecting_ = std::move(callback);
}

void ResilientDataBridge::set_on_reconnected(std::function<void()> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_reconnected_ = std::move(callback);
}

void ResilientDataBridge::set_on_close(std::function<void()> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_close_ = std::move(callback);
}

void ResilientDataBridge::notify_error(const std::string& message) {
    std::function<void(const std::string&)> cb;
    {
        std::lock_guard<std::mutex> lock(callback_mutex_);
        cb = on_error_;
    }
    if (cb) {
        cb(message);
    }
}
