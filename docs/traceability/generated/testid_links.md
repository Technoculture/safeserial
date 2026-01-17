# TestID Link Report
**Timestamp (UTC):** 2026-01-17T12:28:31.143663Z

## Summary
- Total TestIDs: 15
- Resolved: 12
- Unresolved: 3

## Links
| TestID | Matrix Location | Resolved Location | Line | Status |
| :--- | :--- | :--- | :--- | :--- |
| PacketTest.Crc32KnownValue | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 65 | RESOLVED |
| PacketTest.DeserializeRejectsCorrupted | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 99 | RESOLVED |
| PacketTest.CobsRoundtrip | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 42 | RESOLVED |
| PacketTest.DeserializeRejectsTruncated | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 112 | RESOLVED |
| test_deserialize_without_delimiter_is_incomplete | bindings/python/tests/test_protocol_edge.py | bindings/python/tests/test_protocol_edge.py | 16 | RESOLVED |
| DataBridgeTest.RetriesWhenAckMissing | tests/test_data_bridge.cpp | tests/test_data_bridge.cpp | 106 | RESOLVED |
| DataBridgeTest.SendSingleFragmentAcked | tests/test_data_bridge.cpp | tests/test_data_bridge.cpp | 73 | RESOLVED |
| PacketTest.ReassemblerMultipleFragments | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 167 | RESOLVED |
| PacketTest.ReassemblerRejectsOutOfOrder | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 197 | RESOLVED |
| PacketTest.ReassemblerDetectsDuplicateFragment | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 211 | RESOLVED |
| PacketTest.SequenceWrapAround | tests/test_deep_verification.cpp | tests/test_deep_verification.cpp | 260 | RESOLVED |
| ResilientDataBridge Types | bindings/node/test/resilient.test.ts | - | - | UNRESOLVED |
| ResilientBridgeTest.QueuesUntilReconnectAndFlushes | tests/test_resilient_bridge.cpp | tests/test_resilient_bridge.cpp | 78 | RESOLVED |
| Python Retry Test | bindings/python/tests/test_retry.py | - | - | UNRESOLVED |
| FuzzTarget.PacketDeserialize | tests/fuzz_packet.cpp | - | - | UNRESOLVED |
