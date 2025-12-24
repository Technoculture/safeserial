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
    if (tcgetattr(pimpl->fd, &tty) != 0) return false;

    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);

    // RAW MODE - Essential for binary/JSON data
    tty.c_cflag |= (CLOCAL | CREAD);    
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;         // 8-bit characters
    tty.c_cflag &= ~PARENB;      // No parity
    tty.c_cflag &= ~CSTOPB;      // 1 stop bit
    
    tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG); // Disable buffering
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);         // Disable flow control
    tty.c_oflag &= ~OPOST;                          // Raw output

    tty.c_cc[VMIN]  = 0;  // Non-blocking
    tty.c_cc[VTIME] = 10; // 1 second timeout

    return tcsetattr(pimpl->fd, TCSANOW, &tty) == 0;
}

int SerialPort::write(const std::vector<uint8_t>& data) {
    return ::write(pimpl->fd, data.data(), data.size());
}

int SerialPort::read(uint8_t* buffer, size_t size) {
    return ::read(pimpl->fd, buffer, size);
}

void SerialPort::close() {
    if (pimpl->fd != -1) { ::close(pimpl->fd); pimpl->fd = -1; }
}
