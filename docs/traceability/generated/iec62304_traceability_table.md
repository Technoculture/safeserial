# IEC 62304 Traceability

| Software Item | Requirement ID | Unit Test | Integration/System Test | Risk Control | Evidence |
| --- | --- | --- | --- | --- | --- |
| Protocol (Packet) | REQ-PROTO-CRC-001 | PacketTest.Crc32KnownValue | verify_reliability.py | RC-CRC-001 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-PROTO-CRC-001 | PacketTest.DeserializeRejectsCorrupted | verify_reliability.py | RC-CRC-001 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-PROTO-COBS-002 | PacketTest.CobsRoundtrip | verify_reliability.py | RC-COBS-002 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-PROTO-FRAME-003 | PacketTest.DeserializeRejectsTruncated | verify_reliability.py | RC-VALIDATION-007 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-PROTO-FRAME-003 | test_deserialize_without_delimiter_is_incomplete | verify_reliability.py | RC-VALIDATION-007 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| DataBridge | REQ-ARQ-RETRY-004 | DataBridgeTest.RetriesWhenAckMissing | verify_reliability.py | RC-ARQ-003 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| DataBridge | REQ-ARQ-RETRY-004 | DataBridgeTest.SendSingleFragmentAcked | verify_reliability.py | RC-ARQ-003 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Reassembler | REQ-REASSEMBLY-005 | PacketTest.ReassemblerMultipleFragments | verify_reliability.py | RC-REASSEMBLY-004 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Reassembler | REQ-REASSEMBLY-006 | PacketTest.ReassemblerRejectsOutOfOrder | verify_reliability.py | RC-REASSEMBLY-004 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Reassembler | REQ-REASSEMBLY-007 | PacketTest.ReassemblerDetectsDuplicateFragment | verify_reliability.py | RC-DUP-005 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-SEQ-WRAP-008 | PacketTest.SequenceWrapAround | verify_reliability.py | RC-VALIDATION-007 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Resilient | REQ-RECONNECT-009 | ResilientDataBridge Types | verify_reliability.py | RC-RECONNECT-006 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Resilient | REQ-RECONNECT-009 | ResilientBridgeTest.QueuesUntilReconnectAndFlushes | verify_reliability.py | RC-RECONNECT-006 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| DataBridge | REQ-ERROR-010 | Python Retry Test | verify_reliability.py | RC-ARQ-003 | docs/traceability/artifacts/latest/verify_reliability_report.md |
| Protocol (Packet) | REQ-INPUT-011 | FuzzTarget.PacketDeserialize | verify_reliability.py | RC-FUZZ-008 | docs/traceability/artifacts/latest/verify_reliability_report.md |
