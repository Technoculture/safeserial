#include <data_bridge/transport/serial_port.hpp>
#include <data_bridge/protocol/packet.hpp>
#include <data_bridge/protocol/reassembler.hpp>
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <random>

#include <queue>
#include <mutex>
#include <condition_variable>
#include <iomanip>

static void log_timed(const std::string& msg) {
    auto now = std::chrono::system_clock::now();
    auto seconds = std::chrono::duration_cast<std::chrono::duration<double>>(now.time_since_epoch());
    
    std::cout << std::fixed << std::setprecision(6) << seconds.count() << ": " << msg << std::endl;
}

// Usage: 
// 1. End-to-End: ./reliability_test <PORT> <MODE: sender|receiver> [ITEMS=100]
// 2. In-Memory:  ./reliability_test memory <DROP_RATE> <CORRUPT_RATE> [ITEMS=100]

class LoopbackPort : public ISerialPort {
public:
    LoopbackPort(double drop, double corrupt) : drop_rate(drop), corrupt_rate(corrupt), peer(nullptr) {}

    void set_peer(LoopbackPort* p) { peer = p; }

    bool open(const std::string& name, int baud) override { return true; }
    void close() override {}
    
    int write(const std::vector<uint8_t>& data) override {
        if (!peer) return 0;
        return peer->inject(data, drop_rate, corrupt_rate);
    }

    int read(uint8_t* buffer, size_t size) override {
        std::unique_lock<std::mutex> lock(mux);
        // Wait up to 10ms for data (simulating non-blocking/VTIME)
        if (rx_queue.empty()) {
            cv.wait_for(lock, std::chrono::milliseconds(10));
        }
        
        if (rx_queue.empty()) return 0;
        
        size_t count = 0;
        while(count < size && !rx_queue.empty()) {
            buffer[count++] = rx_queue.front();
            rx_queue.pop();
        }
        return count;
    }

    int inject(const std::vector<uint8_t>& data, double drop, double corrupt) {
        // Chaos Logic
        static std::mt19937 rng(std::random_device{}());
        std::uniform_real_distribution<double> dist(0.0, 1.0);

        // Entire write drop (simple model) or per-byte?
        // Let's do per-write drop to match Python script
        if (data.size() > 0 && dist(rng) < drop) {
            // Dropped
            log_timed("[CHAOS] DROPPED " + std::to_string(data.size()) + " bytes");
            return data.size();
        }

        std::vector<uint8_t> processed = data;
        if (dist(rng) < corrupt && processed.size() > 0) {
            int idx = rng() % processed.size();
            processed[idx] ^= (1 << (rng() % 8));
            log_timed("[CHAOS] CORRUPTED byte " + std::to_string(idx));
        }

        std::unique_lock<std::mutex> lock(mux);
        for(auto b : processed) rx_queue.push(b);
        cv.notify_one();
        return data.size();
    }

private:
    std::queue<uint8_t> rx_queue;
    std::mutex mux;
    std::condition_variable cv;
    LoopbackPort* peer;
    double drop_rate;
    double corrupt_rate;
};


void run_sender(ISerialPort& serial, int items) {
    log_timed("[SENDER] Starting stress test with " + std::to_string(items) + " items...");
    uint8_t temp_buf[256];
    std::vector<uint8_t> rx_pool;
    
    // Handshake
    while(true) {
        log_timed("[SENDER] Sending SYN...");
        
        // Flush any garbage from startup or previous incomplete handshakes
        int flushed = 0;
        uint8_t garbage;
        while(serial.read(&garbage, 1) > 0) flushed++;
        if (flushed > 0) log_timed("[SENDER] Flushed " + std::to_string(flushed) + " bytes garbage.");

        serial.write(Packet::serialize(Packet::TYPE_SYN, 0, "TEST_START"));
        
        // Wait up to 5000ms for response, draining buffer
        auto start_wait = std::chrono::steady_clock::now();
        bool handshook = false;
        while(std::chrono::steady_clock::now() - start_wait < std::chrono::milliseconds(5000)) {
            int n = serial.read(temp_buf, 256);
            if (n > 0) {
                // std::cout << "[SENDER] Read " << n << " bytes" << std::endl;
                rx_pool.insert(rx_pool.end(), temp_buf, temp_buf+n);
            } else if (n < 0) {
                 std::cerr << "[SENDER] Read Error: " << n << " Errno: " << errno << std::endl;
            } else {
                 // 0 bytes (timeout) - verbose log?
                 // std::cout << "." << std::flush; 
            }
            
            while(true) {
                auto f = Packet::deserialize(rx_pool);
                if (!f.valid) break; // Need more data
                
                log_timed("[SENDER] Rx Type: " + std::to_string((int)f.header.type));
                if (f.header.type == Packet::TYPE_ACK) {
                    log_timed("[SENDER] Handshake Complete!");
                    handshook = true;
                }
            }
            if(handshook) break;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        if(handshook) break;
    }

    std::mt19937 rng(42); // Deterministic for now
    
    for (int i=0; i<items; ++i) {
        // Generate random payload
        int len = 50 + (rng() % 500); // 50-550 bytes
        std::string payload;
        for(int j=0; j<len; ++j) payload += (char)('A' + (rng() % 26));
        
        uint16_t frag_size = 128;
        uint16_t total_frags = (len + frag_size - 1) / frag_size;
        
        // Send Fragments
        uint8_t current_seq = (uint8_t)(i%256);
        for (uint16_t f=0; f < total_frags; ++f) {
             log_timed("[SENDER] Sending Item " + std::to_string(current_seq) + " Frag " + std::to_string(f) + "/" + std::to_string(total_frags));
             std::string chunk = payload.substr(f*frag_size, std::min((size_t)frag_size, payload.size() - f*frag_size));
             auto pkt = Packet::serialize(Packet::TYPE_DATA, current_seq, chunk, f, total_frags);
             
             bool acked = false;
             while(!acked) {
                 serial.write(pkt);
                 
                 auto start = std::chrono::steady_clock::now();
                 while(std::chrono::steady_clock::now() - start < std::chrono::milliseconds(2000)) {
                     int n = serial.read(temp_buf, 256);
                     if (n > 0) rx_pool.insert(rx_pool.end(), temp_buf, temp_buf+n);
                     while(true) {
                         auto resp = Packet::deserialize(rx_pool);
                         if (!resp.valid) break;
                         
                         if (resp.header.type == Packet::TYPE_ACK && resp.header.seq_id == (i%256)) {
                             acked = true; 
                         }
                     }
                     if (acked) break;
                 }
                 if (!acked) log_timed("[SENDER] Timeout/NACK on Item " + std::to_string(i) + " Frag " + std::to_string(f) + ". Retrying...");
             }
        }
        log_timed("[SENDER] Item " + std::to_string(i) + " Verified.");
    }
    log_timed("[SENDER] TEST COMPLETE - All items transferred successfully.");
}

void run_receiver(ISerialPort& serial) {
    log_timed("[RECEIVER] Listening...");
    uint8_t temp_buf[256];
    std::vector<uint8_t> rx_pool;
    Reassembler reassembler;
    
    int items_received = 0;

    while(true) {
        int n = serial.read(temp_buf, 256);
        if (n > 0) {
             rx_pool.insert(rx_pool.end(), temp_buf, temp_buf+n);
        }
        
        while(true) {
            auto frame = Packet::deserialize(rx_pool);
            if (!frame.valid) break;

            if (frame.header.type == Packet::TYPE_SYN) {
                serial.write(Packet::serialize(Packet::TYPE_ACK, 0, "OK"));
                log_timed("[RECEIVER] Synced.");
            }
            else if (frame.header.type == Packet::TYPE_DATA) {
                if (reassembler.process_fragment(frame)) {
                    serial.write(Packet::serialize(Packet::TYPE_ACK, frame.header.seq_id, ""));
                    if (reassembler.is_complete(frame)) {
                        items_received++;
                        log_timed("[RECEIVER] Completed Item " + std::to_string((int)frame.header.seq_id) 
                                  + " (Total: " + std::to_string(items_received) + ")");
                    }
                } else {
                     // Duplicates or Old: standard is just ACK again so sender stops
                     serial.write(Packet::serialize(Packet::TYPE_ACK, frame.header.seq_id, ""));
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <PORT|memory> <mode|drop> [args...]" << std::endl;
        return 1;
    }
    
    std::string arg1 = argv[1];
    
    if (arg1 == "memory") {
        if (argc < 4) {
             std::cerr << "Usage: ./reliability_test memory <drop> <corrupt> [items]" << std::endl;
             return 1;
        }
        double drop = std::stod(argv[2]);
        double corrupt = std::stod(argv[3]);
        int items = (argc > 4) ? std::stoi(argv[4]) : 100;
        
        LoopbackPort portA(drop, corrupt);
        LoopbackPort portB(drop, corrupt); // Symmetric chaos
        
        portA.set_peer(&portB);
        portB.set_peer(&portA);
        
        std::cout << "[MEMORY] Starting In-Memory Test: Drop=" << drop << " Corrupt=" << corrupt << " Items=" << items << std::endl;
        
        std::thread receiver_thread([&]() {
            run_receiver(portB);
        });
        
        // Give receiver a moment to init
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        run_sender(portA, items);
        
        // Detach receiver (it runs forever in current impl)
        // In a real app we'd signal exit, but for test we can just detach and exit main
        receiver_thread.detach();
        return 0;
    }
    
    // Original Serial Mode
    if (argc < 3) return 1;
    std::string port = argv[1];
    std::string mode = argv[2];
    int count = (argc > 3) ? std::stoi(argv[3]) : 100;
    
    SerialPort serial;
    if (!serial.open(port, 115200)) {
        std::cerr << "Failed to open " << port << std::endl;
        return 1;
    }
    
    if (mode == "sender") run_sender(serial, count);
    else run_receiver(serial);
    return 0;
}
