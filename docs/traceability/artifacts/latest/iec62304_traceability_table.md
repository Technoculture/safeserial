# IEC 62304 Traceability (Template)

| Software Item | Requirement ID | Unit Test | Integration/System Test | Risk Control | Evidence |
| --- | --- | --- | --- | --- | --- |
| Protocol (Packet) | REQ-PROTO-CRC-001 | PacketTest.Crc32KnownValue | verify_reliability.py | RC-CRC-001 | Test logs |
| Protocol (Packet) | REQ-PROTO-FRAME-003 | PacketTest.DeserializeRejectsTruncated | verify_reliability.py | RC-VALIDATION-007 | Test logs |
| Reassembler | REQ-REASSEMBLY-006 | PacketTest.ReassemblerRejectsOutOfOrder | verify_reliability.py | RC-REASSEMBLY-004 | Test logs |
| DataBridge | REQ-ARQ-RETRY-004 | DataBridgeTest.RetriesWhenAckMissing | verify_reliability.py | RC-ARQ-003 | Test logs |
| Resilient | REQ-RECONNECT-009 | ResilientBridgeTest.QueuesUntilReconnectAndFlushes | verify_reliability.py | RC-RECONNECT-006 | Test logs |
