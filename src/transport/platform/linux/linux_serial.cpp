#include <safeserial/transport/serial_port.hpp>
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

    // Clear O_NDELAY to make it blocking (uses VTIME)
    fcntl(pimpl->fd, F_SETFL, 0);

    struct termios tty;
    if (tcgetattr(pimpl->fd, &tty) != 0) return false;

    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);

    // RAW MODE - Essential for binary/JSON data
    cfmakeraw(&tty);
    tty.c_cflag |= (CLOCAL | CREAD);
    
    // Explicitly disable flow control just in case cfmakeraw doesn't (it should)
    tty.c_cflag &= ~CRTSCTS;

    tty.c_cc[VMIN]  = 0;  // Non-blocking
    tty.c_cc[VTIME] = 1;  // 0.1 second timeout (faster polling)

    tcflush(pimpl->fd, TCIOFLUSH); // Flush on open to clear old buffer garbage
    return tcsetattr(pimpl->fd, TCSANOW, &tty) == 0;
}

int SerialPort::write(const std::vector<uint8_t>& data) {
    int written = ::write(pimpl->fd, data.data(), data.size());
    // Note: tcdrain() removed - it blocks indefinitely on PTYs (used for testing)
    // For real serial ports, the write() is sufficient as our protocol handles ACKs
    return written;
}

int SerialPort::read(uint8_t* buffer, size_t size) {
    return ::read(pimpl->fd, buffer, size);
}

void SerialPort::close() {
    if (pimpl->fd != -1) { ::close(pimpl->fd); pimpl->fd = -1; }
}
