#pragma once
#include <memory>
#include <vector>
#include <string>

#include <safeserial/transport/iserial_port.hpp>

class SerialPort : public ISerialPort {

public:
    SerialPort();
    ~SerialPort();

    // Prevent copying (Serial ports are unique resources)
    SerialPort(const SerialPort&) = delete;
    SerialPort& operator=(const SerialPort&) = delete;

    bool open(const std::string& port_name, int baud_rate) override;
    void close() override;
    
    int write(const std::vector<uint8_t>& data) override;
    int read(uint8_t* buffer, size_t size) override;

private:
    // The "Pimpl" - This struct is defined only in the .cpp files
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};
