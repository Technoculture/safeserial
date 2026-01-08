---
title: 'Data Bridge: A Reliable Serial Communication Library for Safety-Critical Embedded Systems'
tags:
  - serial communication
  - medical devices
  - embedded systems
  - reliability
  - Python
  - C++
  - Node.js
authors:
  - name: Satyam Tiwary
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 8 January 2026
bibliography: paper.bib
---

# Summary

Data Bridge is a cross-platform, multi-language library that provides reliable serial communication for embedded systems where data integrity is critical. The library implements a layered protocol stack combining Consistent Overhead Byte Stuffing (COBS) framing, CRC32 error detection, and an Automatic Repeat reQuest (ARQ) mechanism with per-fragment acknowledgment. Data Bridge is designed for applications where silent data corruption is unacceptable, particularly medical devices, industrial control systems, and safety-critical sensor networks.

The library provides native implementations in C++17 with bindings for Python and Node.js/TypeScript, enabling integration across diverse technology stacks. All implementations share the same wire protocol, allowing interoperability between different language environments.

# Statement of Need

Serial communication (UART, USB-serial) remains ubiquitous in embedded systems despite its inherent unreliability. Electromagnetic interference, cable degradation, and electrical noise can cause bit flips, byte insertions, deletions, and complete packet loss. In non-critical applications, occasional data corruption may be tolerable. However, in safety-critical domains such as medical devices, corrupted data can have severe consequences.

Consider a medical infusion pump receiving dosage commands: a single bit flip could transform "31.9 mg" into "319 mg"---a tenfold overdose. Similarly, corrupted sensor readings in patient monitoring systems could trigger false alarms or, worse, mask genuine emergencies. The FDA's recall database documents numerous incidents where serial communication failures contributed to device malfunctions [@fda_recalls].

Existing solutions to this problem fall into several categories:

1. **Low-level protocols** (SLIP, PPP, HDLC): These provide framing but require additional implementation effort for reliable delivery [@rfc1055; @simpson1994ppp].

2. **Industrial protocols** (Modbus, CAN): These target specific domains and hardware configurations, with limited cross-platform support [@modbus_spec].

3. **TCP/IP over serial**: This adds significant overhead and complexity inappropriate for resource-constrained microcontrollers.

Data Bridge addresses this gap by providing a lightweight, header-only C++ implementation with first-class support for modern development workflows. The library targets embedded systems developers, medical device manufacturers, and researchers building sensor networks who need guaranteed delivery semantics without the complexity of full network stacks.

# Key Features

**Protocol Stack**: Data Bridge implements a four-layer protocol:

- **COBS Framing**: Eliminates null bytes from payloads, enabling unambiguous frame delimiting with minimal overhead (~0.4%) [@cheshire1999cobs].
- **CRC32 Validation**: Uses the IEEE 802.3 polynomial for error detection, catching all single-bit errors and burst errors up to 32 bits.
- **Fragmentation**: Large messages are split into configurable fragments (default 256 bytes), each independently acknowledged.
- **ARQ with Selective Retransmission**: Failed fragments are retransmitted without resending the entire message.

**Cross-Language Support**: The library provides:

- C++17 header-only core library
- Python bindings via pybind11 with high-level async API
- Node.js/TypeScript bindings via N-API with Promise-based interface

**Verification Framework**: Data Bridge includes a comprehensive testing infrastructure:

- Unit tests for protocol components
- Integration tests using pseudo-terminal (PTY) pairs
- A "Chaos Monkey" fault injection system that simulates packet drops, bit corruption, burst errors, latency spikes, and connection interruptions
- Cross-language end-to-end verification across all nine sender/receiver language combinations

**Configuration**: Runtime parameters (retry count, timeout, fragment size) are configurable via environment variables, enabling tuning without recompilation.

# Implementation

The core protocol is implemented in approximately 400 lines of C++ header files, with platform-specific serial port implementations for Linux (termios) and Windows. The Python bindings add a threaded receive loop and callback-based API, while the Node.js bindings provide both callback and Promise interfaces.

The packet structure includes:

```cpp
struct Header {
    uint8_t type;           // DATA, ACK, NACK, SYN
    uint8_t seq_id;         // Message sequence number
    uint16_t fragment_id;   // Fragment index
    uint16_t total_frags;   // Total fragments
    uint16_t payload_len;   // Payload size
    uint32_t crc32;         // CRC-32 checksum
};
```

The handshake protocol ensures both endpoints are synchronized before data transfer begins. The sender transmits a SYN packet and waits for an ACK before proceeding with data transmission.

# Testing and Validation

Data Bridge includes automated verification following patterns appropriate for medical device software development. The test suite generates reports compatible with ISO 13485 documentation requirements, including:

- Test environment specifications
- Per-test-case results with timestamps
- Sender and receiver logs for audit trails

The Chaos Monkey fault injector creates a controlled adversarial environment using PTY pairs, allowing fault injection without modifying application code. Test scenarios include baseline (no faults), moderate (5% drop, 1% corruption), and aggressive (10% drop, 2% corruption) conditions.

# Acknowledgements

We acknowledge contributions from the open-source community and the developers of pybind11, cmake-js, and the various testing frameworks used in this project.

# References
