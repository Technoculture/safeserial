#include "serial_port.hpp"
#include "protocol/packet.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>

enum class State { HANDSHAKING, SENDING, RECEIVING };

int main() {
    SerialPort serial;
    bool isSender = false; 
#ifdef _WIN32
    std::string port = "\\\\.\\COM3";
    isSender = false; // Windows as Receiver
#else
    std::string port = "/dev/serial0";
    isSender = true; // Pi as Sender
#endif

    if (!serial.open(port, 115200)) {
std::cerr<< "CRITICAL ERROR: Could not open port"<<port << std::endl;
return 1;
    };

    std::cout<<"PORT"<<port<<"opened successfully"<<std::endl;

    State state = State::HANDSHAKING;
    uint8_t current_seq = 0;
    std::vector<uint8_t> pool;
    uint8_t temp_buf[256];

    while (true) {
        // 1. Read incoming bytes into pool
        int n = serial.read(temp_buf, 256);
        if (n > 0) pool.insert(pool.end(), temp_buf, temp_buf + n);
//static auto last_print :: std::chrono::steady_clock::now();
//if(std::chrono::steady_clock::now() - last_print > std::chrono::seconds(5)){
//..  std::cout<<"----Status:Watin ">
//}
//
static auto last_print = std::chrono::steady_clock::now();
        if (std::chrono::steady_clock::now() - last_print > std::chrono::seconds(5)) {
            std::cout << "--- Status: " << (isSender ? "Sender" : "Receiver") << " Active ---" << std::endl;
            last_print = std::chrono::steady_clock::now();
        }
        // 2. State Logic
        if (state == State::HANDSHAKING) {
            if (isSender) {
              
std::cout << "Sending SYN..." << std::endl;
                serial.write(Packet::serialize(Packet::TYPE_SYN, 0, "READY"));
                
                auto start = std::chrono::steady_clock::now();
                while(std::chrono::steady_clock::now() - start < std::chrono::milliseconds(1000)) {
                    int rn = serial.read(temp_buf, 256);
                    if (rn > 0) pool.insert(pool.end(), temp_buf, temp_buf + rn);
                    
                    auto frame = Packet::deserialize(pool);
                    if (frame.valid && frame.type == Packet::TYPE_ACK) {
                        std::cout << "Handshake Complete!" << std::endl;
                        state = State::SENDING;
                        break;
                    }
                }
            }
            } else {
                auto frame = Packet::deserialize(pool);
                if (frame.valid && frame.type == Packet::TYPE_SYN) {
                    serial.write(Packet::serialize(Packet::TYPE_ACK, 0, "OK"));
                    std::cout << "Handshake Accepted!" << std::endl;
                    state = State::RECEIVING;
                }
            }
        } 
        else if (state == State::SENDING && isSender) {
            std::string data = "{\"temp\":24.5}";
            bool acked = false;
            int retries = 0;

            while (!acked && retries < 5) {
                std::cout << "Sending Seq: " << (int)current_seq << " (Try " << retries + 1 << ")" << std::endl;
                serial.write(Packet::serialize(Packet::TYPE_DATA, current_seq, data));

                // Wait for ACK with timeout
                auto start = std::chrono::steady_clock::now();
                while (std::chrono::steady_clock::now() - start < std::chrono::milliseconds(500)) {
                    int rn = serial.read(temp_buf, 256);
                    if (rn > 0) pool.insert(pool.end(), temp_buf, temp_buf + rn);
                    
                    auto resp = Packet::deserialize(pool);
                    if (resp.valid && resp.type == Packet::TYPE_ACK && resp.seq == current_seq) {
                        acked = true;
                        break;
                    }
                }
                if (!acked) retries++;
            }
            current_seq++;
            std::this_thread::sleep_for(std::chrono::seconds(2));
        } 
        else if (state == State::RECEIVING && !isSender) {
            auto frame = Packet::deserialize(pool);
            if (frame.valid && frame.type == Packet::TYPE_DATA) {
                std::cout << "Received [" << (int)frame.seq << "]: " << frame.payload << std::endl;
                // Send ACK back
                serial.write(Packet::serialize(Packet::TYPE_ACK, frame.seq, ""));
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return 0;
}
