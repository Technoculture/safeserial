# IEC 62304 Traceability

| Software Item | Requirement ID | Unit Test | Integration/System Test | Risk Control | Evidence |
| --- | --- | --- | --- | --- | --- |
| Protocol (Packet) | REQ-PROTO-CRC-001 | PacketTest.Crc32KnownValue | verify_reliability.py | RC-CRC-001 | Test logs |
| Protocol (Packet) | REQ-PROTO-CRC-001 | PacketTest.DeserializeRejectsCorrupted | verify_reliability.py | RC-CRC-001 | Test logs |
|  | REQ-PROTO-COBS-002 | PacketTest.CobsRoundtrip |  | RC-COBS-002 |  |
| Protocol (Packet) | REQ-PROTO-FRAME-003 | PacketTest.DeserializeRejectsTruncated | verify_reliability.py | RC-VALIDATION-007 | Test logs |
| Protocol (Packet) | REQ-PROTO-FRAME-003 | test_deserialize_without_delimiter_is_incomplete | verify_reliability.py | RC-VALIDATION-007 | Test logs |
| DataBridge | REQ-ARQ-RETRY-004 | DataBridgeTest.RetriesWhenAckMissing | verify_reliability.py | RC-ARQ-003 | Test logs |
| DataBridge | REQ-ARQ-RETRY-004 | DataBridgeTest.SendSingleFragmentAcked | verify_reliability.py | RC-ARQ-003 | Test logs |
|  | REQ-REASSEMBLY-005 | PacketTest.ReassemblerMultipleFragments |  | RC-REASSEMBLY-004 |  |
| Reassembler | REQ-REASSEMBLY-006 | PacketTest.ReassemblerRejectsOutOfOrder | verify_reliability.py | RC-REASSEMBLY-004 | Test logs |
|  | REQ-REASSEMBLY-007 | PacketTest.ReassemblerDetectsDuplicateFragment |  | RC-DUP-005 |  |
|  | REQ-SEQ-WRAP-008 | PacketTest.SequenceWrapAround |  | RC-VALIDATION-007 |  |
| Resilient | REQ-RECONNECT-009 | ResilientDataBridge Types | verify_reliability.py | RC-RECONNECT-006 | Test logs |
| Resilient | REQ-RECONNECT-009 | ResilientBridgeTest.QueuesUntilReconnectAndFlushes | verify_reliability.py | RC-RECONNECT-006 | Test logs |
|  | REQ-ERROR-010 | Python Retry Test |  | RC-ARQ-003 |  |
|  | REQ-INPUT-011 | FuzzTarget.PacketDeserialize |  | RC-FUZZ-008 |  |
