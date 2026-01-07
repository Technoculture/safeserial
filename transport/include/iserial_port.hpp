#pragma once
#include <vector>
#include <string>
#include <cstdint>

class ISerialPort {
public:
    virtual ~ISerialPort() = default;

    virtual bool open(const std::string& port_name, int baud_rate) = 0;
    virtual void close() = 0;
    
    virtual int write(const std::vector<uint8_t>& data) = 0;
    virtual int read(uint8_t* buffer, size_t size) = 0;
};
