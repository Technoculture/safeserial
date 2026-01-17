#include <safeserial/safeserial.hpp>

#include <algorithm>
#include <chrono>
#include <stdexcept>

namespace {
std::vector<uint8_t> slice_payload(const std::vector<uint8_t>& data, size_t offset, size_t len) {
    auto start = data.begin() + static_cast<std::vector<uint8_t>::difference_type>(offset);
    auto end = data.begin() + static_cast<std::vector<uint8_t>::difference_type>(offset + len);
    return std::vector<uint8_t>(start, end);
}
} // namespace

DataBridge::DataBridge()
    : serial_(std::make_shared<SerialPort>()),
      options_(Options::Defaults()) {}

DataBridge::DataBridge(const Options& options)
    : serial_(std::make_shared<SerialPort>()),
      options_(options) {}

DataBridge::DataBridge(std::shared_ptr<ISerialPort> serial, const Options& options)
    : serial_(std::move(serial)),
      options_(options) {
    if (!serial_) {
        serial_ = std::make_shared<SerialPort>();
    }
}

DataBridge::~DataBridge() {
    close();
}

bool DataBridge::open(const std::string& port, int baud_rate_override) {
    if (is_open_) {
        return true;
    }

    int baud_rate = baud_rate_override > 0 ? baud_rate_override : options_.baud_rate;
    if (!serial_->open(port, baud_rate)) {
        return false;
    }

    stop_ = false;
    is_open_ = true;
    receive_thread_ = std::thread(&DataBridge::receive_loop, this);
    return true;
}

void DataBridge::close() {
    if (!is_open_) {
        return;
    }

    stop_ = true;
    {
        std::lock_guard<std::mutex> lock(ack_mutex_);
        waiting_for_ack_ = false;
        acked_ = true;
    }
    ack_cv_.notify_all();

    if (receive_thread_.joinable()) {
        receive_thread_.join();
    }

    serial_->close();
    is_open_ = false;
}

bool DataBridge::is_open() const {
    return is_open_.load();
}

int DataBridge::send(const std::vector<uint8_t>& data,
                     uint16_t ack_timeout_ms_override,
                     uint8_t max_retries_override,
                     uint16_t fragment_size_override) {
    if (!is_open_) {
        throw std::runtime_error("Port not open");
    }

    std::lock_guard<std::mutex> send_lock(send_mutex_);

    uint16_t fragment_size = fragment_size_override > 0 ? fragment_size_override : options_.fragment_size;
    uint16_t ack_timeout_ms = ack_timeout_ms_override > 0 ? ack_timeout_ms_override : options_.ack_timeout_ms;
    uint8_t max_retries = max_retries_override > 0 ? max_retries_override : options_.max_retries;

    if (fragment_size == 0) {
        throw std::runtime_error("Invalid fragment size");
    }

    size_t total_frags = (data.empty() ? 1 : (data.size() + fragment_size - 1) / fragment_size);
    uint8_t seq = 0;
    {
        std::lock_guard<std::mutex> lock(seq_mutex_);
        seq = next_seq_;
        next_seq_ = static_cast<uint8_t>((next_seq_ + 1) % 256);
    }

    int total_written = 0;
    for (size_t frag_id = 0; frag_id < total_frags; ++frag_id) {
        size_t offset = frag_id * fragment_size;
        size_t len = data.empty() ? 0 : std::min<size_t>(fragment_size, data.size() - offset);
        std::vector<uint8_t> fragment = slice_payload(data, offset, len);

        std::string payload;
        if (!fragment.empty()) {
            payload.assign(reinterpret_cast<const char*>(fragment.data()), fragment.size());
        }
        std::vector<uint8_t> packet = Packet::serialize(
            Packet::TYPE_DATA,
            seq,
            payload,
            static_cast<uint16_t>(frag_id),
            static_cast<uint16_t>(total_frags));

        uint8_t retries = 0;
        bool acked = false;
        int bytes_written = 0;
        while (retries <= max_retries && !acked) {
            {
                std::lock_guard<std::mutex> lock(ack_mutex_);
                waiting_for_ack_ = true;
                acked_ = false;
                waiting_seq_ = seq;
                waiting_frag_ = static_cast<uint16_t>(frag_id);
            }

            {
                std::lock_guard<std::mutex> lock(write_mutex_);
                bytes_written = serial_->write(packet);
            }

            std::unique_lock<std::mutex> lock(ack_mutex_);
            bool notified = ack_cv_.wait_for(
                lock,
                std::chrono::milliseconds(ack_timeout_ms),
                [this]() { return acked_ || stop_; });

            if (stop_) {
                throw std::runtime_error("Connection closed");
            }

            if (notified && acked_) {
                acked = true;
                waiting_for_ack_ = false;
                total_written += bytes_written;
            } else {
                retries++;
            }
        }

        if (!acked) {
            throw std::runtime_error("Send failed after retries");
        }
    }

    return total_written;
}

void DataBridge::set_on_data(std::function<void(const std::vector<uint8_t>&)> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    on_data_ = std::move(callback);
}

size_t DataBridge::get_buffered_size() const {
    return reassembler_.get_buffered_size();
}

void DataBridge::receive_loop() {
    uint8_t buffer[1024];
    while (!stop_) {
        int n = serial_->read(buffer, sizeof(buffer));
        if (n > 0) {
            rx_buffer_.insert(rx_buffer_.end(), buffer, buffer + n);

            while (true) {
                size_t before = rx_buffer_.size();
                Packet::Frame frame = Packet::deserialize(rx_buffer_);
                if (!frame.valid) {
                    if (rx_buffer_.size() == before) {
                        break;
                    }
                    continue;
                }
                handle_frame(frame);
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

void DataBridge::handle_frame(const Packet::Frame& frame) {
    if (frame.header.type == Packet::TYPE_ACK) {
        std::lock_guard<std::mutex> lock(ack_mutex_);
        if (waiting_for_ack_ &&
            frame.header.seq_id == waiting_seq_ &&
            frame.header.fragment_id == waiting_frag_) {
            acked_ = true;
            waiting_for_ack_ = false;
            ack_cv_.notify_all();
        }
        return;
    }

    if (frame.header.type != Packet::TYPE_DATA) {
        return;
    }

    bool should_ack = false;
    if (reassembler_.process_fragment(frame)) {
        should_ack = true;
        if (reassembler_.is_complete(frame)) {
            auto data = reassembler_.get_data();
            std::function<void(const std::vector<uint8_t>&)> cb;
            {
                std::lock_guard<std::mutex> lock(callback_mutex_);
                cb = on_data_;
            }
            if (cb) {
                cb(data);
            }
        }
    } else if (reassembler_.is_duplicate(frame)) {
        should_ack = true;
    }

    if (should_ack) {
        send_ack(frame);
    }
}

void DataBridge::send_ack(const Packet::Frame& frame) {
    std::vector<uint8_t> ack = Packet::serialize(
        Packet::TYPE_ACK,
        frame.header.seq_id,
        "",
        frame.header.fragment_id,
        frame.header.total_frags);

    std::lock_guard<std::mutex> lock(write_mutex_);
    serial_->write(ack);
}
