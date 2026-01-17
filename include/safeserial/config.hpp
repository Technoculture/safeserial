#pragma once
#include <cstdlib>
#include <cstdint>
#include <string>

/**
 * Configuration for SafeSerial protocol.
 * 
 * Parameters can be set via environment variables.
 * If not set, defaults are used.
 * 
 * Environment variables:
 *   SAFESERIAL_MAX_RETRIES      - Maximum retry attempts (default: 10)
 *   SAFESERIAL_RETRY_TIMEOUT_MS - Timeout between retries in ms (default: 2000)
 *   SAFESERIAL_FRAGMENT_SIZE    - Maximum fragment payload size (default: 256)
 *   SAFESERIAL_ACK_TIMEOUT_MS   - Timeout waiting for ACK in ms (default: 500)
 */

namespace SafeSerialConfig {

inline int getEnvInt(const char* name, int defaultValue) {
    const char* val = std::getenv(name);
    if (val == nullptr) return defaultValue;
    try {
        return std::stoi(val);
    } catch (...) {
        return defaultValue;
    }
}

// Maximum number of retry attempts before giving up
inline uint8_t maxRetries() {
    static uint8_t value = static_cast<uint8_t>(
        getEnvInt("SAFESERIAL_MAX_RETRIES", 10)
    );
    return value;
}

// Timeout between retries in milliseconds
inline uint16_t retryTimeoutMs() {
    static uint16_t value = static_cast<uint16_t>(
        getEnvInt("SAFESERIAL_RETRY_TIMEOUT_MS", 2000)
    );
    return value;
}

// Maximum payload size per fragment (for large message fragmentation)
inline uint16_t fragmentSize() {
    static uint16_t value = static_cast<uint16_t>(
        getEnvInt("SAFESERIAL_FRAGMENT_SIZE", 256)
    );
    return value;
}

// Timeout waiting for ACK before retry
inline uint16_t ackTimeoutMs() {
    static uint16_t value = static_cast<uint16_t>(
        getEnvInt("SAFESERIAL_ACK_TIMEOUT_MS", 500)
    );
    return value;
}

// Baud rate (default for most embedded devices)
inline int baudRate() {
    static int value = getEnvInt("SAFESERIAL_BAUD_RATE", 115200);
    return value;
}

} // namespace SafeSerialConfig
