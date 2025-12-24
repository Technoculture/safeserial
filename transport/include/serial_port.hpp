#pragma once
#include <memory>
#include <vector>
#include <string>

class SerialPort {
public:
    SerialPort();
    ~SerialPort();

    // Prevent copying (Serial ports are unique resources)
    SerialPort(const SerialPort&) = delete;
    SerialPort& operator=(const SerialPort&) = delete;

    bool open(const std::string& port_name, int baud_rate);
    void close();
    
    int write(const std::vector<uint8_t>& data);
    int read(uint8_t* buffer, size_t size);

private:
    // The "Pimpl" - This struct is defined only in the .cpp files
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};
