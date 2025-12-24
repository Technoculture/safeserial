#include "serial_port.hpp"
#include "protocol/packet.hpp"
#include <iostream>
#include <thread>
#include <vector>

int main() {
    SerialPort serial;

#ifdef _WIN32
    std::string port = "\\\\.\\COM3";
    bool isSender = false;
#else
    std::string port = "/dev/serial0";
    bool isSender = true;
#endif

    if (!serial.open(port, 115200)) {
        std::cerr << "Failed to open " << port << std::endl;
        return 1;
    }

    if (isSender) {
        std::cout << "Pi Sender Active..." << std::endl;
        while (true) {
            auto p = Packet::serialize(R"({"temp":24.5})");
            serial.write(p);
            std::this_thread::sleep_for(std::chrono::seconds(2));
        }
    } else {
        std::cout << "Windows Receiver Active..." << std::endl;
        std::vector<uint8_t> pool;
        uint8_t temp[256];
        while (true) {
            int n = serial.read(temp, 256);
            if (n > 0) {
                pool.insert(pool.end(), temp, temp + n);
                auto [ok, msg] = Packet::deserialize(pool);
                if (ok) std::cout << "Received: " << msg << std::endl;
            }
        }
    }
    return 0;
}
