# Requirements (Draft)

REQ-PROTO-CRC-001: The protocol shall detect payload corruption using CRC32.
REQ-PROTO-COBS-002: The protocol shall frame packets with COBS and delimiter.
REQ-PROTO-FRAME-003: The protocol shall reject malformed or truncated frames.
REQ-ARQ-RETRY-004: The sender shall retry transmission until ACK or retry limit.
REQ-REASSEMBLY-005: The receiver shall reassemble fragmented payloads in order.
REQ-REASSEMBLY-006: The receiver shall reject out-of-order fragments.
REQ-REASSEMBLY-007: The receiver shall detect duplicate fragments.
REQ-SEQ-WRAP-008: Sequence identifiers shall wrap around safely at 8-bit.
REQ-RECONNECT-009: The resilient bridge shall queue messages during disconnect and flush on reconnection.
REQ-ERROR-010: The system shall surface transport and protocol errors to clients.
REQ-INPUT-011: Deserialization shall not crash on arbitrary input.
