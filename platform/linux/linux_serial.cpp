#include "serial_port.hpp"
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

struct SerialPort::Impl {
    int fd = -1;
};

SerialPort::SerialPort() : pimpl(std::make_unique<Impl>()) {}
SerialPort::~SerialPort() { close(); }

bool SerialPort::open(const std::string& port, int baud) {
    pimpl->fd = ::open(port.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (pimpl->fd == -1) return false;
    struct termios tty;
    tcgetattr(pimpl->fd, &tty);
    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);
    tty.c_cflag |= (CLOCAL | CREAD); 
    tcsetattr(pimpl->fd, TCSANOW, &tty);
    return true;
}

int SerialPort::write(const std::vector<uint8_t>& data) {
    return ::write(pimpl->fd, data.data(), data.size());
}

int SerialPort::read(uint8_t* buffer, size_t size) {
    return ::read(pimpl->fd, buffer, size);
}

void SerialPort::close() { if(pimpl->fd != -1) ::close(pimpl->fd); }
