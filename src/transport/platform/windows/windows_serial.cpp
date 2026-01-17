#include <safeserial/transport/serial_port.hpp>
#include <windows.h>

struct SerialPort::Impl {
    HANDLE hSerial = INVALID_HANDLE_VALUE;
};

SerialPort::SerialPort() : pimpl(std::make_unique<Impl>()) {}
SerialPort::~SerialPort() { close(); }

bool SerialPort::open(const std::string& port, int baud) {
    pimpl->hSerial = CreateFileA(port.c_str(), GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
    if (pimpl->hSerial == INVALID_HANDLE_VALUE) return false;

    DCB dcb = {0};
    dcb.DCBlength = sizeof(dcb);
    GetCommState(pimpl->hSerial, &dcb);
    dcb.BaudRate = CBR_115200;
    dcb.ByteSize = 8;
    dcb.StopBits = ONESTOPBIT;
    dcb.Parity   = NOPARITY;
    SetCommState(pimpl->hSerial, &dcb);

    // TIMEOUTS - Prevents the app from freezing
    COMMTIMEOUTS timeouts = { 0 };
    timeouts.ReadIntervalTimeout = 50;
    timeouts.ReadTotalTimeoutConstant = 50;
    timeouts.ReadTotalTimeoutMultiplier = 10;
    SetCommTimeouts(pimpl->hSerial, &timeouts);

    return true;
}

int SerialPort::write(const std::vector<uint8_t>& data) {
    DWORD written;
    WriteFile(pimpl->hSerial, data.data(), (DWORD)data.size(), &written, NULL);
    return (int)written;
}

int SerialPort::read(uint8_t* buffer, size_t size) {
    DWORD read;
    if (!ReadFile(pimpl->hSerial, buffer, (DWORD)size, &read, NULL)) return -1;
    return (int)read;
}

void SerialPort::close() {
    if (pimpl->hSerial != INVALID_HANDLE_VALUE) {
        CloseHandle(pimpl->hSerial);
        pimpl->hSerial = INVALID_HANDLE_VALUE;
    }
}
