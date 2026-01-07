/**
 * Data Bridge Node.js Native Addon
 * 
 * Exposes the C++ Data Bridge library to JavaScript via Node-API.
 * Provides async-safe wrappers for serial port operations.
 */

#include <napi.h>
#include <data_bridge/transport/serial_port.hpp>
#include <data_bridge/protocol/packet.hpp>
#include <data_bridge/protocol/reassembler.hpp>
#include <memory>
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>

class DataBridgeWrapper : public Napi::ObjectWrap<DataBridgeWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    DataBridgeWrapper(const Napi::CallbackInfo& info);
    ~DataBridgeWrapper();

private:
    // JavaScript methods
    Napi::Value Open(const Napi::CallbackInfo& info);
    Napi::Value Send(const Napi::CallbackInfo& info);
    Napi::Value Close(const Napi::CallbackInfo& info);
    Napi::Value IsOpen(const Napi::CallbackInfo& info);
    
    // Internal state
    std::unique_ptr<SerialPort> serial_;
    std::atomic<bool> is_open_{false};
    std::atomic<bool> should_stop_{false};
    std::thread receive_thread_;
    uint8_t seq_id_ = 0;  // Per-instance sequence ID
    
    // Thread-safe receive callback
    Napi::ThreadSafeFunction tsfn_;
    
    void ReceiveLoop();
    void StopReceiveLoop();
};

Napi::Object DataBridgeWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::Function func = DefineClass(env, "DataBridge", {
        InstanceMethod("open", &DataBridgeWrapper::Open),
        InstanceMethod("send", &DataBridgeWrapper::Send),
        InstanceMethod("close", &DataBridgeWrapper::Close),
        InstanceMethod("isOpen", &DataBridgeWrapper::IsOpen),
    });

    exports.Set("DataBridge", func);
    return exports;
}

DataBridgeWrapper::DataBridgeWrapper(const Napi::CallbackInfo& info) 
    : Napi::ObjectWrap<DataBridgeWrapper>(info) {
    serial_ = std::make_unique<SerialPort>();
}

DataBridgeWrapper::~DataBridgeWrapper() {
    StopReceiveLoop();
}

Napi::Value DataBridgeWrapper::Open(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "Port path required").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    
    std::string port = info[0].As<Napi::String>().Utf8Value();
    int baud = 115200;
    
    if (info.Length() >= 2 && info[1].IsNumber()) {
        baud = info[1].As<Napi::Number>().Int32Value();
    }
    
    // Create a deferred promise
    Napi::Promise::Deferred deferred = Napi::Promise::Deferred::New(env);
    
    if (serial_->open(port, baud)) {
        is_open_ = true;
        
        // Setup receive callback if provided
        if (info.Length() >= 3 && info[2].IsFunction()) {
            tsfn_ = Napi::ThreadSafeFunction::New(
                env,
                info[2].As<Napi::Function>(),
                "DataBridge Receive Callback",
                0, 1
            );
            
            should_stop_ = false;
            receive_thread_ = std::thread(&DataBridgeWrapper::ReceiveLoop, this);
        }
        
        deferred.Resolve(Napi::Boolean::New(env, true));
    } else {
        deferred.Reject(Napi::Error::New(env, "Failed to open port: " + port).Value());
    }
    
    return deferred.Promise();
}

Napi::Value DataBridgeWrapper::Send(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    
    if (!is_open_) {
        Napi::Error::New(env, "Port not open").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    
    if (info.Length() < 1) {
        Napi::TypeError::New(env, "Data required").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    
    std::string payload;
    if (info[0].IsBuffer()) {
        Napi::Buffer<char> buf = info[0].As<Napi::Buffer<char>>();
        payload = std::string(buf.Data(), buf.Length());
    } else if (info[0].IsString()) {
        payload = info[0].As<Napi::String>().Utf8Value();
    } else {
        Napi::TypeError::New(env, "Data must be Buffer or string").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    
    // Serialize and send with fragmentation
    // Sequence ID is managed per-instance
    auto packet = Packet::serialize(Packet::TYPE_DATA, seq_id_++, payload);
    
    Napi::Promise::Deferred deferred = Napi::Promise::Deferred::New(env);
    
    // TODO: Implement proper async send with ACK waiting
    // For now, synchronous send
    int written = serial_->write(packet);
    
    if (written > 0) {
        deferred.Resolve(Napi::Number::New(env, written));
    } else {
        deferred.Reject(Napi::Error::New(env, "Write failed").Value());
    }
    
    return deferred.Promise();
}

Napi::Value DataBridgeWrapper::Close(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    
    StopReceiveLoop();
    serial_->close();
    is_open_ = false;
    
    return Napi::Boolean::New(env, true);
}

Napi::Value DataBridgeWrapper::IsOpen(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), is_open_.load());
}

void DataBridgeWrapper::ReceiveLoop() {
    uint8_t buffer[1024];
    std::vector<uint8_t> rx_pool;
    Reassembler reassembler;
    
    while (!should_stop_) {
        int n = serial_->read(buffer, sizeof(buffer));
        if (n > 0) {
            rx_pool.insert(rx_pool.end(), buffer, buffer + n);
            
            while (true) {
                auto frame = Packet::deserialize(rx_pool);
                if (!frame.valid) break;
                
                if (frame.header.type == Packet::TYPE_DATA) {
                    if (reassembler.process_fragment(frame)) {
                        if (reassembler.is_complete(frame)) {
                            // Emit to JavaScript via ThreadSafeFunction
                            auto data = reassembler.get_data();
                            
                            tsfn_.BlockingCall([data](Napi::Env env, Napi::Function callback) {
                                callback.Call({
                                    Napi::Buffer<char>::Copy(env, 
                                        reinterpret_cast<const char*>(data.data()), 
                                        data.size())
                                });
                            });
                        }
                    }
                    // Send ACK
                    serial_->write(Packet::serialize(Packet::TYPE_ACK, frame.header.seq_id, ""));
                }
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

void DataBridgeWrapper::StopReceiveLoop() {
    should_stop_ = true;
    if (receive_thread_.joinable()) {
        receive_thread_.join();
    }
    if (tsfn_) {
        tsfn_.Release();
    }
}

// Module initialization
Napi::Object InitAll(Napi::Env env, Napi::Object exports) {
    return DataBridgeWrapper::Init(env, exports);
}

NODE_API_MODULE(data_bridge_node, InitAll)
