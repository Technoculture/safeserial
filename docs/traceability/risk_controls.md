# Risk Controls

RC-CRC-001: CRC32 verification on each decoded frame.
RC-COBS-002: COBS framing with delimiter to bound packets.
RC-ARQ-003: Stop-and-wait ACK/Retry with timeouts.
RC-REASSEMBLY-004: Fragment reassembly with ordering checks.
RC-DUP-005: Duplicate fragment detection and ACK.
RC-RECONNECT-006: Reconnect and queued resend for transport failures.
RC-VALIDATION-007: Input validation and rejection of malformed frames.
RC-FUZZ-008: Fuzz testing of deserialization to detect crashes.
RC-SANITIZE-009: Sanitizer builds to detect memory/UB issues.
