#include "serial_port.hpp"
#include "protocol/packet.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>

// Added FINISHED state to handle graceful program exit
enum class State { HANDSHAKING, SENDING, RECEIVING, FINISHED };

int main(int argc, char* argv[]) {

    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <passkey>" << std::endl;
        return 1;
    }

    std::string secret_passkey = argv[1];
    SerialPort serial;
    bool isSender = false;

#ifdef _WIN32
    // Windows acts as the Receiver in this flow
    std::string port = "\\\\.\\COM3";
    isSender = false; 
#else
    // Linux/Pi acts as the Sender
    std::string port = "/dev/serial0";
    isSender = true; 
#endif

    if (!serial.open(port, 115200)) {
        std::cerr << "CRITICAL ERROR: Could not open port " << port << std::endl;
        return 1;
    }

    std::cout << "PORT " << port << " opened. Mode: " << (isSender ? "Sender" : "Receiver") << std::endl;
    std::cout << "Using Passkey: " << secret_passkey << std::endl;

    State state = State::HANDSHAKING;
    uint8_t current_seq = 0;
    std::vector<uint8_t> pool;
    uint8_t temp_buf[256];

    while (state != State::FINISHED) {
        // 1. Read incoming bytes into the processing pool
        int n = serial.read(temp_buf, 256);
        if (n > 0) {
            pool.insert(pool.end(), temp_buf, temp_buf + n);
        }

        // 2. State Logic
        if (state == State::HANDSHAKING) {
            if (isSender) {
                // SENDER: Send SYN with passkey and wait for ACK
                serial.write(Packet::serialize(Packet::TYPE_SYN, 0, secret_passkey));
                
                auto start = std::chrono::steady_clock::now();
                while (std::chrono::steady_clock::now() - start < std::chrono::milliseconds(1000)) {
                    int rn = serial.read(temp_buf, 256);
                    if (rn > 0) pool.insert(pool.end(), temp_buf, temp_buf + rn);
                    
                    auto frame = Packet::deserialize(pool);
                    if (frame.valid && frame.type == Packet::TYPE_ACK) {
                        std::cout << "Connection Established: Peer authenticated." << std::endl;
                        state = State::SENDING;
                        break;
                    }
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(500)); 
            } else {
                // RECEIVER (Windows): Wait for SYN and verify passkey
                auto frame = Packet::deserialize(pool);
                if (frame.valid && frame.type == Packet::TYPE_SYN) {
                    if (frame.payload == secret_passkey) {
                        serial.write(Packet::serialize(Packet::TYPE_ACK, 0, "OK"));
                        std::cout << "Connection Established: Passkey matched." << std::endl;
                        state = State::RECEIVING;
                    } else {
                        std::cout << "Auth Failed: Received wrong passkey [" << frame.payload << "]" << std::endl;
                    }
                }
            }
        } 
        else if (state == State::SENDING && isSender) {
            // SENDER: Send the data packet
            std::string data = "{\"temp\":24.5, \"status\":\"ok\"}";
            bool acked = false;
            int retries = 0;

            while (!acked && retries < 5) {
                std::cout << "Sending Data Seq: " << (int)current_seq << " (Try " << retries + 1 << ")" << std::endl;
                serial.write(Packet::serialize(Packet::TYPE_DATA, current_seq, data));

                // Wait for ACK
                auto start = std::chrono::steady_clock::now();
                while (std::chrono::steady_clock::now() - start < std::chrono::milliseconds(800)) {
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

            if (acked) {
                std::cout << "Transfer Success! Closing program..." << std::endl;
                state = State::FINISHED;
            } else {
                std::cout << "Transfer Failed after maximum retries." << std::endl;
                break; 
            }
        } 
        else if (state == State::RECEIVING && !isSender) {
            // RECEIVER (Windows): Wait for Data, Display it, ACK, and Close
            auto frame = Packet::deserialize(pool);
            if (frame.valid && frame.type == Packet::TYPE_DATA) {
                std::cout << "\n================================" << std::endl;
                std::cout << "RECEIVED DATA ON WINDOWS:" << std::endl;
                std::cout << "Payload: " << frame.payload << std::endl;
                std::cout << "Sequence: " << (int)frame.seq << std::endl;
                std::cout << "================================\n" << std::endl;

                // Send ACK back so sender knows we got it
                serial.write(Packet::serialize(Packet::TYPE_ACK, frame.seq, "OK"));
                
                std::cout << "Data transfer complete. Shutting down." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(200)); // Ensure ACK is sent
                state = State::FINISHED;
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    std::cout << "Port closed. Goodbye!" << std::endl;
    return 0;
}
