#include "serial_port.hpp"
#include "protocol/packet.hpp"
#include "protocol/reassembler.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <algorithm>

enum class State { HANDSHAKING, SENDING, RECEIVING, ERROR_STATE };

// Simple blocking read helper with timeout
bool read_with_timeout(ISerialPort& serial, std::vector<uint8_t>& pool, int timeout_ms) {
    auto start = std::chrono::steady_clock::now();
    uint8_t temp_buf[256];
    while (std::chrono::steady_clock::now() - start < std::chrono::milliseconds(timeout_ms)) {
        int n = serial.read(temp_buf, 256);
        if (n > 0) {
            pool.insert(pool.end(), temp_buf, temp_buf + n);
            return true;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
    }
    return false;
}

int main() {
    SerialPort serial; // Concrete implementation
    bool isSender = false; 
#ifdef _WIN32
    std::string port = "\\\\.\\COM3";
    isSender = false; // Windows as Receiver
#else
    std::string port = "/dev/serial0";
    isSender = true; // Pi as Sender
#endif

    if (!serial.open(port, 115200)) {
        std::cerr << "CRITICAL ERROR: Could not open port " << port << std::endl;
        return 1;
    };

    std::cout << "PORT " << port << " opened successfully. Mode: " << (isSender ? "SENDER" : "RECEIVER") << std::endl;

    State state = State::HANDSHAKING;
    uint8_t current_seq = 0;
    std::vector<uint8_t> rx_pool;
    Reassembler reassembler;

    while (true) {
        // Read incoming data into pool continuously
        uint8_t temp_buf[256];
        int n = serial.read(temp_buf, 256);
        if (n > 0) rx_pool.insert(rx_pool.end(), temp_buf, temp_buf + n);

        // State Machine
        if (state == State::HANDSHAKING) {
            if (isSender) {
                std::cout << "Sending SYN..." << std::endl;
                auto syn_pkt = Packet::serialize(Packet::TYPE_SYN, 0, "READY");
                serial.write(syn_pkt);
                
                // Wait for ACK
                auto start_wait = std::chrono::steady_clock::now();
                while(std::chrono::steady_clock::now() - start_wait < std::chrono::milliseconds(1000)) {
                   // Pump read
                   int rn = serial.read(temp_buf, 256);
                   if (rn > 0) rx_pool.insert(rx_pool.end(), temp_buf, temp_buf + rn);

                   auto frame = Packet::deserialize(rx_pool);
                   if (frame.valid && frame.header.type == Packet::TYPE_ACK) {
                       std::cout << "Handshake Complete!" << std::endl;
                       state = State::SENDING;
                       break;
                   }
                   std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            } else {
                // Receiver
                auto frame = Packet::deserialize(rx_pool);
                if (frame.valid && frame.header.type == Packet::TYPE_SYN) {
                    std::cout << "Received SYN. Sending ACK..." << std::endl;
                    serial.write(Packet::serialize(Packet::TYPE_ACK, 0, "OK"));
                    state = State::RECEIVING;
                }
            }
        }
        else if (state == State::SENDING && isSender) {
            std::string full_payload = "{\"id\": 123, \"type\": \"medical_result\", \"data\": [0.1, 0.2, 0.5]}";
            
            // Fragment logic
            uint16_t max_payload = 64; // Small fragment size for demo
            uint16_t total_len = full_payload.size();
            uint16_t total_frags = (total_len + max_payload - 1) / max_payload;

            bool message_sent = true;

            for (uint16_t i = 0; i < total_frags; ++i) {
                uint16_t start = i * max_payload;
                uint16_t len = std::min((uint16_t)(total_len - start), max_payload);
                std::string chunk = full_payload.substr(start, len);

                std::cout << "Senidng Seq " << (int)current_seq << " Frag " << i << "/" << total_frags << std::endl;
                
                auto pkt = Packet::serialize(Packet::TYPE_DATA, current_seq, chunk, i, total_frags);
                
                // Reliable Send used Stop-and-Wait
                bool acked = false;
                int retries = 0;
                while (!acked && retries < 5) {
                    serial.write(pkt);
                    
                    // Wait for ACK
                    auto wait_start = std::chrono::steady_clock::now();
                    while(std::chrono::steady_clock::now() - wait_start < std::chrono::milliseconds(200)) {
                        int rn = serial.read(temp_buf, 256);
                        if (rn > 0) rx_pool.insert(rx_pool.end(), temp_buf, temp_buf + rn);
                        
                        auto resp = Packet::deserialize(rx_pool);
                        // Check if ACK is for this message
                        // Note: Simple ACK on Seq is ambiguous for fragments if we don't ack fragments.
                        // Impl Plan said: "Sender waits for ACK for each fragment".
                        // Use SEQ for message ID. We need to know which fragment is ACKed?
                        // Currently Packet::Header has seq_id.
                        // If we use Stop-and-Wait, receiving ANY ACK for this Seq *usually* means "I got the thing I just expected".
                        // But precise protocol would require ACK to carry frag_id or next_expected_frag_id.
                        // Let's assume for now ACK means "Got the last thing you sent".
                        // Or we can peek at payload of ACK? Or header?
                        // Let's assume Receiver echoes the type/seq.
                        if (resp.valid && resp.header.type == Packet::TYPE_ACK && resp.header.seq_id == current_seq) {
                            acked = true;
                            break;
                        }
                    }
                    if (!acked) {
                         std::cout << "Retry " << retries+1 << "..." << std::endl;
                         retries++;
                    }
                }
                
                if (!acked) {
                    std::cerr << "Failed to send fragment " << i << std::endl;
                    message_sent = false;
                    break; 
                }
            }

            if (message_sent) {
                std::cout << "Message " << (int)current_seq << " Sent Successfully" << std::endl;
                current_seq++;
            }
            std::this_thread::sleep_for(std::chrono::seconds(2));
        }
        else if (state == State::RECEIVING && !isSender) {
            auto frame = Packet::deserialize(rx_pool);
            if (frame.valid) {
                if (frame.header.type == Packet::TYPE_DATA) {
                    bool accepted = reassembler.process_fragment(frame);
                     
                    // Always ACK if it's valid (even if duplicate, let sender move on)
                    // If accepted == false because out of order, maybe we should NACK?
                    // But for Stop-and-Wait, ACK is "I received X".
                    
                    serial.write(Packet::serialize(Packet::TYPE_ACK, frame.header.seq_id, ""));

                    if (reassembler.is_complete(frame)) {
                        auto data = reassembler.get_data();
                        std::string msg(data.begin(), data.end());
                        std::cout << "COMPLETE MESSAGE " << (int)frame.header.seq_id << ": " << msg << std::endl;
                    }
                }
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    return 0;
}
