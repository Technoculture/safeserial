#include "serial_port.hpp"
#include "protocol/packet.hpp"
#include <iostream>
#include <thread>
#include <chrono>

int main() {
    SerialPort serial;
#ifdef _WIN32
    std::string port = "\\\\.\\COM3"; 
#else
    std::string port = "/dev/ttyUSB0";
#endif

    if (!serial.open(port, 115200)) {
        std::cerr << "Could not open " << port << std::endl;
        return 1;
    }

    std::cout << "Starting Mock Communication on " << port << "..." << std::endl;

    while (true) {
        std::string mock_json = R"({"sensor":"temp","val":24.5})";
        auto data = Packet::serialize(mock_json);
        serial.write(data);
        std::cout << "Sent Packet: " << mock_json << std::endl;

        uint8_t buf[256];
        int n = serial.read(buf, sizeof(buf));
        if (n > 0) {
            std::cout << "Received raw bytes: " << n << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::seconds(2));
    }
    return 0;
}
