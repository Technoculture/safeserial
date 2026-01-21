/**
 * SafeSerial Node.js Native Addon
 *
 * Exposes the C++ SafeSerial library to JavaScript via Node-API.
 * Aligned with Python _core:
 * - SerialPort: Raw async serial I/O
 * - Packet: Serialization/Deserialization helpers
 * - Reassembler: Fragmentation handling
 */

#include <napi.h>
#include <safeserial/safeserial.hpp>
#include <safeserial/resilient_bridge.hpp>
#include <safeserial/transport/serial_port.hpp>
#include <safeserial/protocol/packet.hpp>
#include <safeserial/protocol/reassembler.hpp>
#include <memory>
#include <thread>
#include <atomic>
#include <vector>

// --- SerialPort Wrapper ---
class SerialPortWrapper : public Napi::ObjectWrap<SerialPortWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    SerialPortWrapper(const Napi::CallbackInfo& info);
    ~SerialPortWrapper();

private:
    Napi::Value Open(const Napi::CallbackInfo& info);
    Napi::Value Close(const Napi::CallbackInfo& info);
    Napi::Value Write(const Napi::CallbackInfo& info);
    Napi::Value IsOpen(const Napi::CallbackInfo& info);

    std::unique_ptr<SerialPort> serial_;
    std::atomic<bool> is_open_{false};
    std::atomic<bool> should_stop_{false};
    std::thread receive_thread_;
    Napi::ThreadSafeFunction tsfn_;

    void ReceiveLoop();
    void StopReceiveLoop();
};

static uint32_t GetUInt32(const Napi::Object& obj, const char* key, uint32_t fallback) {
    if (obj.Has(key) && obj.Get(key).IsNumber()) {
        return obj.Get(key).As<Napi::Number>().Uint32Value();
    }
    return fallback;
}

static bool GetBool(const Napi::Object& obj, const char* key, bool fallback) {
    if (obj.Has(key) && obj.Get(key).IsBoolean()) {
        return obj.Get(key).As<Napi::Boolean>().Value();
    }
    return fallback;
}

Napi::Object SerialPortWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "SerialPort", {
        InstanceMethod("open", &SerialPortWrapper::Open),
        InstanceMethod("close", &SerialPortWrapper::Close),
        InstanceMethod("write", &SerialPortWrapper::Write),
        InstanceMethod("isOpen", &SerialPortWrapper::IsOpen),
    });
    exports.Set("SerialPort", func);
    return exports;
}

SerialPortWrapper::SerialPortWrapper(const Napi::CallbackInfo& info)
    : Napi::ObjectWrap<SerialPortWrapper>(info) {
    serial_ = std::make_unique<SerialPort>();
}

SerialPortWrapper::~SerialPortWrapper() {
    StopReceiveLoop();
}

Napi::Value SerialPortWrapper::Open(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "Port path required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    std::string port = info[0].As<Napi::String>().Utf8Value();
    int baud = 115200;
    if (info.Length() >= 2 && info[1].IsNumber()) baud = info[1].As<Napi::Number>().Int32Value();

    // Callback is mandatory for raw serial port to receive data
    if (info.Length() < 3 || !info[2].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (serial_->open(port, baud)) {
        is_open_ = true;

        tsfn_ = Napi::ThreadSafeFunction::New(
            env,
            info[2].As<Napi::Function>(),
            "SerialPort Receive Callback",
            0, 1
        );

        should_stop_ = false;
        receive_thread_ = std::thread(&SerialPortWrapper::ReceiveLoop, this);

        return Napi::Boolean::New(env, true);
    }

    return Napi::Boolean::New(env, false);
}

Napi::Value SerialPortWrapper::Close(const Napi::CallbackInfo& info) {
    StopReceiveLoop();
    serial_->close();
    is_open_ = false;
    return Napi::Boolean::New(info.Env(), true);
}

Napi::Value SerialPortWrapper::Write(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsBuffer()) {
        Napi::TypeError::New(env, "Buffer required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    Napi::Buffer<uint8_t> buf = info[0].As<Napi::Buffer<uint8_t>>();
    std::vector<uint8_t> data(buf.Data(), buf.Data() + buf.Length());

    // Write is synchronous in C++ implementation usually, or we can make it async if needed.
    // For now, keeping it synchronous/blocking for simplicity as per Python binding.
    // (Node.js event loop might block briefly, but serial write is fast or buffered)
    int written = serial_->write(data);
    return Napi::Number::New(env, written);
}

Napi::Value SerialPortWrapper::IsOpen(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), is_open_.load());
}

void SerialPortWrapper::ReceiveLoop() {
    uint8_t buffer[4096];
    while (!should_stop_) {
        // Read raw bytes
        int n = serial_->read(buffer, sizeof(buffer));
        if (n > 0) {
            // Copy data for the callback
            std::vector<uint8_t> data(buffer, buffer + n);

            auto status = tsfn_.BlockingCall([data](Napi::Env env, Napi::Function callback) {
                callback.Call({
                    Napi::Buffer<uint8_t>::Copy(env, data.data(), data.size())
                });
            });

            if (status != napi_ok) break;
        }
        // Small sleep to prevent tight loop if read is non-blocking and returns 0 often
        // But read should be blocking with timeout.
        // Assuming implementation of serial_->read handles timeout or blocking.
        // The previous implementation had a sleep, so we surely need one if non-blocking.
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

void SerialPortWrapper::StopReceiveLoop() {
    should_stop_ = true;
    if (receive_thread_.joinable()) receive_thread_.join();
    if (tsfn_) tsfn_.Release();
}

// --- Packet Wrapper ---
class PacketWrapper : public Napi::ObjectWrap<PacketWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    PacketWrapper(const Napi::CallbackInfo& info);

private:
    static Napi::Value Serialize(const Napi::CallbackInfo& info);
    static Napi::Value Deserialize(const Napi::CallbackInfo& info);
};

// --- DataBridge Wrapper ---
class DataBridgeWrapper : public Napi::ObjectWrap<DataBridgeWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    DataBridgeWrapper(const Napi::CallbackInfo& info);
    ~DataBridgeWrapper();

private:
    Napi::Value Open(const Napi::CallbackInfo& info);
    Napi::Value Close(const Napi::CallbackInfo& info);
    Napi::Value Send(const Napi::CallbackInfo& info);
    Napi::Value IsOpen(const Napi::CallbackInfo& info);
    Napi::Value OnData(const Napi::CallbackInfo& info);

    std::unique_ptr<DataBridge> bridge_;
    Napi::ThreadSafeFunction tsfn_;
};

// --- ResilientDataBridge Wrapper ---
class ResilientDataBridgeWrapper : public Napi::ObjectWrap<ResilientDataBridgeWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    ResilientDataBridgeWrapper(const Napi::CallbackInfo& info);
    ~ResilientDataBridgeWrapper();

private:
    Napi::Value Open(const Napi::CallbackInfo& info);
    Napi::Value Close(const Napi::CallbackInfo& info);
    Napi::Value Send(const Napi::CallbackInfo& info);
    Napi::Value IsConnected(const Napi::CallbackInfo& info);
    Napi::Value QueueLength(const Napi::CallbackInfo& info);

    Napi::Value OnData(const Napi::CallbackInfo& info);
    Napi::Value OnError(const Napi::CallbackInfo& info);
    Napi::Value OnDisconnect(const Napi::CallbackInfo& info);
    Napi::Value OnReconnecting(const Napi::CallbackInfo& info);
    Napi::Value OnReconnected(const Napi::CallbackInfo& info);
    Napi::Value OnClose(const Napi::CallbackInfo& info);

    std::unique_ptr<ResilientDataBridge> bridge_;
    Napi::ThreadSafeFunction data_tsfn_;
    Napi::ThreadSafeFunction error_tsfn_;
    Napi::ThreadSafeFunction disconnect_tsfn_;
    Napi::ThreadSafeFunction reconnecting_tsfn_;
    Napi::ThreadSafeFunction reconnected_tsfn_;
    Napi::ThreadSafeFunction close_tsfn_;
};

Napi::Object ResilientDataBridgeWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "ResilientDataBridge", {
        InstanceMethod("open", &ResilientDataBridgeWrapper::Open),
        InstanceMethod("close", &ResilientDataBridgeWrapper::Close),
        InstanceMethod("send", &ResilientDataBridgeWrapper::Send),
        InstanceMethod("isConnected", &ResilientDataBridgeWrapper::IsConnected),
        InstanceMethod("queueLength", &ResilientDataBridgeWrapper::QueueLength),
        InstanceMethod("onData", &ResilientDataBridgeWrapper::OnData),
        InstanceMethod("onError", &ResilientDataBridgeWrapper::OnError),
        InstanceMethod("onDisconnect", &ResilientDataBridgeWrapper::OnDisconnect),
        InstanceMethod("onReconnecting", &ResilientDataBridgeWrapper::OnReconnecting),
        InstanceMethod("onReconnected", &ResilientDataBridgeWrapper::OnReconnected),
        InstanceMethod("onClose", &ResilientDataBridgeWrapper::OnClose),
    });
    exports.Set("ResilientDataBridge", func);
    return exports;
}

ResilientDataBridgeWrapper::ResilientDataBridgeWrapper(const Napi::CallbackInfo& info)
    : Napi::ObjectWrap<ResilientDataBridgeWrapper>(info) {
    ResilientDataBridge::Options options = ResilientDataBridge::Options::Defaults();
    if (info.Length() >= 1 && info[0].IsObject()) {
        Napi::Object opts = info[0].As<Napi::Object>();
        options.bridge.baud_rate = static_cast<int>(GetUInt32(opts, "baudRate", options.bridge.baud_rate));
        options.bridge.max_retries = static_cast<uint8_t>(GetUInt32(opts, "maxRetries", options.bridge.max_retries));
        options.bridge.ack_timeout_ms = static_cast<uint16_t>(GetUInt32(opts, "ackTimeoutMs", options.bridge.ack_timeout_ms));
        options.bridge.fragment_size = static_cast<uint16_t>(GetUInt32(opts, "fragmentSize", options.bridge.fragment_size));
        options.reconnect = GetBool(opts, "reconnect", options.reconnect);
        options.reconnect_delay_ms = GetUInt32(opts, "reconnectDelay", options.reconnect_delay_ms);
        options.max_reconnect_delay_ms = GetUInt32(opts, "maxReconnectDelay", options.max_reconnect_delay_ms);
        options.max_queue_size = GetUInt32(opts, "maxQueueSize", static_cast<uint32_t>(options.max_queue_size));
    }
    bridge_ = std::make_unique<ResilientDataBridge>(options);
}

ResilientDataBridgeWrapper::~ResilientDataBridgeWrapper() {
    if (bridge_) {
        bridge_->set_on_data(nullptr);
        bridge_->set_on_error(nullptr);
        bridge_->set_on_disconnect(nullptr);
        bridge_->set_on_reconnecting(nullptr);
        bridge_->set_on_reconnected(nullptr);
        bridge_->set_on_close(nullptr);
        bridge_->close();
    }
    if (data_tsfn_) data_tsfn_.Release();
    if (error_tsfn_) error_tsfn_.Release();
    if (disconnect_tsfn_) disconnect_tsfn_.Release();
    if (reconnecting_tsfn_) reconnecting_tsfn_.Release();
    if (reconnected_tsfn_) reconnected_tsfn_.Release();
    if (close_tsfn_) close_tsfn_.Release();
}

Napi::Value ResilientDataBridgeWrapper::Open(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "Port path required").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    std::string port = info[0].As<Napi::String>().Utf8Value();
    bool ok = bridge_->open(port);
    return Napi::Boolean::New(env, ok);
}

Napi::Value ResilientDataBridgeWrapper::Close(const Napi::CallbackInfo& info) {
    bridge_->close();
    return Napi::Boolean::New(info.Env(), true);
}

Napi::Value ResilientDataBridgeWrapper::Send(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1) {
        Napi::TypeError::New(env, "Data required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    std::vector<uint8_t> data;
    if (info[0].IsBuffer()) {
        Napi::Buffer<uint8_t> buf = info[0].As<Napi::Buffer<uint8_t>>();
        data.assign(buf.Data(), buf.Data() + buf.Length());
    } else {
        std::string payload = info[0].ToString().Utf8Value();
        data.assign(payload.begin(), payload.end());
    }

    try {
        int written = bridge_->send(data);
        if (written < 0) {
            Napi::Error::New(env, "Send failed after retries").ThrowAsJavaScriptException();
            return env.Undefined();
        }
        return Napi::Number::New(env, written);
    } catch (const std::exception& ex) {
        Napi::Error::New(env, ex.what()).ThrowAsJavaScriptException();
        return env.Undefined();
    }
}

Napi::Value ResilientDataBridgeWrapper::IsConnected(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), bridge_->is_connected());
}

Napi::Value ResilientDataBridgeWrapper::QueueLength(const Napi::CallbackInfo& info) {
    return Napi::Number::New(info.Env(), bridge_->queue_length());
}

Napi::Value ResilientDataBridgeWrapper::OnData(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (data_tsfn_) {
        data_tsfn_.Release();
    }

    data_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Data Callback",
        0, 1);

    bridge_->set_on_data([this](const std::vector<uint8_t>& data) {
        auto payload = new std::vector<uint8_t>(data);
        auto status = data_tsfn_.BlockingCall(payload, [](Napi::Env env, Napi::Function callback, std::vector<uint8_t>* payload) {
            callback.Call({
                Napi::Buffer<uint8_t>::Copy(env, payload->data(), payload->size())
            });
            delete payload;
        });
        if (status != napi_ok) {
            delete payload;
        }
    });

    return env.Undefined();
}

Napi::Value ResilientDataBridgeWrapper::OnError(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (error_tsfn_) {
        error_tsfn_.Release();
    }

    error_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Error Callback",
        0, 1);

    bridge_->set_on_error([this](const std::string& message) {
        auto payload = new std::string(message);
        auto status = error_tsfn_.BlockingCall(payload, [](Napi::Env env, Napi::Function callback, std::string* payload) {
            callback.Call({ Napi::String::New(env, *payload) });
            delete payload;
        });
        if (status != napi_ok) {
            delete payload;
        }
    });

    return env.Undefined();
}

Napi::Value ResilientDataBridgeWrapper::OnDisconnect(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (disconnect_tsfn_) {
        disconnect_tsfn_.Release();
    }

    disconnect_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Disconnect Callback",
        0, 1);

    bridge_->set_on_disconnect([this]() {
        auto status = disconnect_tsfn_.BlockingCall([](Napi::Env env, Napi::Function callback) {
            callback.Call({});
        });
        if (status != napi_ok) {
            return;
        }
    });

    return env.Undefined();
}

Napi::Value ResilientDataBridgeWrapper::OnReconnecting(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (reconnecting_tsfn_) {
        reconnecting_tsfn_.Release();
    }

    reconnecting_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Reconnecting Callback",
        0, 1);

    bridge_->set_on_reconnecting([this](uint32_t attempt, uint32_t delay) {
        auto payload = new std::pair<uint32_t, uint32_t>(attempt, delay);
        auto status = reconnecting_tsfn_.BlockingCall(payload, [](Napi::Env env, Napi::Function callback, std::pair<uint32_t, uint32_t>* payload) {
            callback.Call({
                Napi::Number::New(env, payload->first),
                Napi::Number::New(env, payload->second)
            });
            delete payload;
        });
        if (status != napi_ok) {
            delete payload;
        }
    });

    return env.Undefined();
}

Napi::Value ResilientDataBridgeWrapper::OnReconnected(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (reconnected_tsfn_) {
        reconnected_tsfn_.Release();
    }

    reconnected_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Reconnected Callback",
        0, 1);

    bridge_->set_on_reconnected([this]() {
        auto status = reconnected_tsfn_.BlockingCall([](Napi::Env env, Napi::Function callback) {
            callback.Call({});
        });
        if (status != napi_ok) {
            return;
        }
    });

    return env.Undefined();
}

Napi::Value ResilientDataBridgeWrapper::OnClose(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (close_tsfn_) {
        close_tsfn_.Release();
    }

    close_tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "ResilientDataBridge Close Callback",
        0, 1);

    bridge_->set_on_close([this]() {
        auto status = close_tsfn_.BlockingCall([](Napi::Env env, Napi::Function callback) {
            callback.Call({});
        });
        if (status != napi_ok) {
            return;
        }
    });

    return env.Undefined();
}

Napi::Object DataBridgeWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "DataBridge", {
        InstanceMethod("open", &DataBridgeWrapper::Open),
        InstanceMethod("close", &DataBridgeWrapper::Close),
        InstanceMethod("send", &DataBridgeWrapper::Send),
        InstanceMethod("isOpen", &DataBridgeWrapper::IsOpen),
        InstanceMethod("onData", &DataBridgeWrapper::OnData),
    });
    exports.Set("DataBridge", func);
    return exports;
}

DataBridgeWrapper::DataBridgeWrapper(const Napi::CallbackInfo& info)
    : Napi::ObjectWrap<DataBridgeWrapper>(info) {
    bridge_ = std::make_unique<DataBridge>();
}

DataBridgeWrapper::~DataBridgeWrapper() {
    if (bridge_) {
        bridge_->set_on_data(nullptr);
        bridge_->close();
    }
    if (tsfn_) {
        tsfn_.Release();
    }
}

Napi::Value DataBridgeWrapper::Open(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "Port path required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    std::string port = info[0].As<Napi::String>().Utf8Value();
    int baud = -1;
    if (info.Length() >= 2 && info[1].IsNumber()) {
        baud = info[1].As<Napi::Number>().Int32Value();
    }

    bool ok = bridge_->open(port, baud);
    return Napi::Boolean::New(env, ok);
}

Napi::Value DataBridgeWrapper::Close(const Napi::CallbackInfo& info) {
    bridge_->close();
    return Napi::Boolean::New(info.Env(), true);
}

Napi::Value DataBridgeWrapper::Send(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1) {
        Napi::TypeError::New(env, "Data required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    std::vector<uint8_t> data;
    if (info[0].IsBuffer()) {
        Napi::Buffer<uint8_t> buf = info[0].As<Napi::Buffer<uint8_t>>();
        data.assign(buf.Data(), buf.Data() + buf.Length());
    } else {
        std::string payload = info[0].ToString().Utf8Value();
        data.assign(payload.begin(), payload.end());
    }

    uint16_t ack_timeout_ms = 0;
    uint8_t max_retries = 0;
    uint16_t fragment_size = 0;
    if (info.Length() >= 2 && info[1].IsNumber()) {
        ack_timeout_ms = info[1].As<Napi::Number>().Uint32Value();
    }
    if (info.Length() >= 3 && info[2].IsNumber()) {
        max_retries = static_cast<uint8_t>(info[2].As<Napi::Number>().Uint32Value());
    }
    if (info.Length() >= 4 && info[3].IsNumber()) {
        fragment_size = info[3].As<Napi::Number>().Uint32Value();
    }

    try {
        int written = bridge_->send(data, ack_timeout_ms, max_retries, fragment_size);
        if (written < 0) {
            Napi::Error::New(env, "Send failed after retries").ThrowAsJavaScriptException();
            return env.Undefined();
        }
        return Napi::Number::New(env, written);
    } catch (const std::exception& ex) {
        Napi::Error::New(env, ex.what()).ThrowAsJavaScriptException();
        return env.Undefined();
    }
}

Napi::Value DataBridgeWrapper::IsOpen(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), bridge_->is_open());
}

Napi::Value DataBridgeWrapper::OnData(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsFunction()) {
        Napi::TypeError::New(env, "Callback required").ThrowAsJavaScriptException();
        return env.Undefined();
    }

    if (tsfn_) {
        tsfn_.Release();
    }

    tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        info[0].As<Napi::Function>(),
        "DataBridge Data Callback",
        0, 1);

    bridge_->set_on_data([this](const std::vector<uint8_t>& data) {
        auto payload = new std::vector<uint8_t>(data);
        auto status = tsfn_.BlockingCall(payload, [](Napi::Env env, Napi::Function callback, std::vector<uint8_t>* payload) {
            callback.Call({
                Napi::Buffer<uint8_t>::Copy(env, payload->data(), payload->size())
            });
            delete payload;
        });

        if (status != napi_ok) {
            delete payload;
        }
    });

    return env.Undefined();
}

Napi::Object PacketWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "Packet", {
        StaticMethod("serialize", &PacketWrapper::Serialize),
        StaticMethod("deserialize", &PacketWrapper::Deserialize),
        StaticValue("TYPE_DATA", Napi::Number::New(env, Packet::TYPE_DATA)),
        StaticValue("TYPE_ACK", Napi::Number::New(env, Packet::TYPE_ACK)),
        StaticValue("TYPE_NACK", Napi::Number::New(env, Packet::TYPE_NACK)),
        StaticValue("TYPE_SYN", Napi::Number::New(env, Packet::TYPE_SYN)),
    });
    exports.Set("Packet", func);
    return exports;
}

PacketWrapper::PacketWrapper(const Napi::CallbackInfo& info) : Napi::ObjectWrap<PacketWrapper>(info) {}

Napi::Value PacketWrapper::Serialize(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    // Args: type, seq, payload, frag_id (opt), total_frags (opt)

    if (info.Length() < 3) throw Napi::Error::New(env, "Args: type, seq, payload");

    uint8_t type = info[0].As<Napi::Number>().Uint32Value();
    uint8_t seq = info[1].As<Napi::Number>().Uint32Value();
    std::string payload;

    if (info[2].IsBuffer()) {
        Napi::Buffer<char> buf = info[2].As<Napi::Buffer<char>>();
        payload.assign(buf.Data(), buf.Length());
    } else {
        payload = info[2].ToString().Utf8Value();
    }

    uint16_t frag_id = 0;
    uint16_t total_frags = 1;
    if (info.Length() > 3) frag_id = info[3].As<Napi::Number>().Uint32Value();
    if (info.Length() > 4) total_frags = info[4].As<Napi::Number>().Uint32Value();

    auto vec = Packet::serialize(type, seq, payload, frag_id, total_frags);
    return Napi::Buffer<uint8_t>::Copy(env, vec.data(), vec.size());
}

Napi::Value PacketWrapper::Deserialize(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsBuffer()) throw Napi::Error::New(env, "Buffer required");

    Napi::Buffer<uint8_t> buf = info[0].As<Napi::Buffer<uint8_t>>();
    std::vector<uint8_t> data(buf.Data(), buf.Data() + buf.Length());

    // Packet::deserialize modifies the vector (consumes bytes)
    Packet::Frame frame = Packet::deserialize(data);

    Napi::Object result = Napi::Object::New(env);

    // Frame object
    Napi::Object frameObj = Napi::Object::New(env);
    frameObj.Set("valid", frame.valid);

    // Header
    Napi::Object header = Napi::Object::New(env);
    header.Set("type", frame.header.type);
    header.Set("seq_id", frame.header.seq_id);
    header.Set("fragment_id", frame.header.fragment_id);
    header.Set("total_frags", frame.header.total_frags);
    header.Set("payload_len", frame.header.payload_len);
    header.Set("crc32", frame.header.crc32);
    frameObj.Set("header", header);

    // Payload
    frameObj.Set("payload", Napi::Buffer<uint8_t>::Copy(env, frame.payload.data(), frame.payload.size()));

    result.Set("frame", frameObj);
    result.Set("remaining", Napi::Buffer<uint8_t>::Copy(env, data.data(), data.size()));

    return result;
}

// --- Reassembler Wrapper ---
class ReassemblerWrapper : public Napi::ObjectWrap<ReassemblerWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    ReassemblerWrapper(const Napi::CallbackInfo& info);

private:
    std::unique_ptr<Reassembler> reassembler_;

    Napi::Value ProcessFragment(const Napi::CallbackInfo& info);
    Napi::Value IsComplete(const Napi::CallbackInfo& info);
    Napi::Value GetData(const Napi::CallbackInfo& info);
    Napi::Value IsDuplicate(const Napi::CallbackInfo& info);
    Napi::Value GetBufferedSize(const Napi::CallbackInfo& info);
};

Napi::Object ReassemblerWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "Reassembler", {
        InstanceMethod("processFragment", &ReassemblerWrapper::ProcessFragment),
        InstanceMethod("isComplete", &ReassemblerWrapper::IsComplete),
        InstanceMethod("getData", &ReassemblerWrapper::GetData),
        InstanceMethod("isDuplicate", &ReassemblerWrapper::IsDuplicate),
        InstanceMethod("getBufferedSize", &ReassemblerWrapper::GetBufferedSize),
    });
    exports.Set("Reassembler", func);
    return exports;
}

ReassemblerWrapper::ReassemblerWrapper(const Napi::CallbackInfo& info) : Napi::ObjectWrap<ReassemblerWrapper>(info) {
    reassembler_ = std::make_unique<Reassembler>();
}

// Helper to extract C++ Frame from JS Frame object
Packet::Frame JsToFrame(Napi::Object jsFrame) {
    Packet::Frame frame;
    frame.valid = jsFrame.Get("valid").As<Napi::Boolean>().Value();
    Napi::Object header = jsFrame.Get("header").As<Napi::Object>();
    frame.header.type = header.Get("type").As<Napi::Number>().Uint32Value();
    frame.header.seq_id = header.Get("seq_id").As<Napi::Number>().Uint32Value();
    frame.header.fragment_id = header.Get("fragment_id").As<Napi::Number>().Uint32Value();
    frame.header.total_frags = header.Get("total_frags").As<Napi::Number>().Uint32Value();

    Napi::Buffer<uint8_t> pl = jsFrame.Get("payload").As<Napi::Buffer<uint8_t>>();
    frame.payload.assign(pl.Data(), pl.Data() + pl.Length());
    return frame;
}

Napi::Value ReassemblerWrapper::ProcessFragment(const Napi::CallbackInfo& info) {
    if (info.Length() < 1 || !info[0].IsObject()) throw Napi::Error::New(info.Env(), "Frame object required");
    Packet::Frame frame = JsToFrame(info[0].As<Napi::Object>());
    return Napi::Boolean::New(info.Env(), reassembler_->process_fragment(frame));
}

Napi::Value ReassemblerWrapper::IsComplete(const Napi::CallbackInfo& info) {
    if (info.Length() < 1 || !info[0].IsObject()) throw Napi::Error::New(info.Env(), "Frame object required");
    Packet::Frame frame = JsToFrame(info[0].As<Napi::Object>());
    return Napi::Boolean::New(info.Env(), reassembler_->is_complete(frame));
}

Napi::Value ReassemblerWrapper::GetData(const Napi::CallbackInfo& info) {
    auto data = reassembler_->get_data();
    return Napi::Buffer<uint8_t>::Copy(info.Env(), data.data(), data.size());
}

Napi::Value ReassemblerWrapper::IsDuplicate(const Napi::CallbackInfo& info) {
    if (info.Length() < 1 || !info[0].IsObject()) throw Napi::Error::New(info.Env(), "Frame object required");
    Packet::Frame frame = JsToFrame(info[0].As<Napi::Object>());
    return Napi::Boolean::New(info.Env(), reassembler_->is_duplicate(frame));
}

Napi::Value ReassemblerWrapper::GetBufferedSize(const Napi::CallbackInfo& info) {
    return Napi::Number::New(info.Env(), reassembler_->get_buffered_size());
}


// --- Init ---

Napi::Object InitAll(Napi::Env env, Napi::Object exports) {
    SerialPortWrapper::Init(env, exports);
    DataBridgeWrapper::Init(env, exports);
    ResilientDataBridgeWrapper::Init(env, exports);
    PacketWrapper::Init(env, exports);
    ReassemblerWrapper::Init(env, exports);
    return exports;
}

NODE_API_MODULE(safeserial_node, InitAll)
