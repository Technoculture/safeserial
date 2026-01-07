# Test Record - ISO 13485 Compliance
**Project:** Data Bridge Serial Protocol
**Date:** 2026-01-07T20:09:23.795211
**Tester:** Automated Runner

## 1. Scope
Verification of the reliable serial protocol implementation (Class C Medical Device component).

## 2. Test Environment
*   **OS:** darwin
*   **Build Artifacts:** `/Users/satyamtiwary/Documents/Python-Things/data-bridge/build/tests/reliability_test`
*   **Test Driver:** `/Users/satyamtiwary/Documents/Python-Things/data-bridge/tests/iso_runner.py`

## 3. Reliability Visualization
![Reliability Plot](reliability_plot.png)

## 4. Test Cases & Results

| Test ID | Condition | Items | Result | Verification |
| :--- | :--- | :--- | :--- | :--- |
| T-001 | Drop=0.0%, Corrupt=0.0% | 20 | **PASS** | Data Integrity confirmed via CRC32 |
| T-002 | Drop=5.0%, Corrupt=1.0% | 20 | **PASS** | Data Integrity confirmed via CRC32 |
| T-003 | Drop=10.0%, Corrupt=2.0% | 20 | **PASS** | Data Integrity confirmed via CRC32 |

## 5. Conclusion
**Overall Status:** PASS

The software HAS demonstrated compliance with reliability requirements.

## 4. Execution Logs

### T-001 Details
### Execution Log
```
[MEMORY] Starting In-Memory Test: Drop=0 Corrupt=0 Items=20
[RECEIVER] Listening...
[SENDER] Starting stress test with 20 items...
[SENDER] Sending SYN...
[RECEIVER] Read 24 bytes
[RECEIVER] Synqed.
[SENDER] Read 16 bytes
[SENDER] Rx Type: 32
[SENDER] Handshake OK
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 0 (Total: 1)
[SENDER] Item 0 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 25 bytes
[RECEIVER] Completed Item 1 (Total: 2)
[SENDER] Item 1 Verified.
[RECEIVER] Read 103 bytes
[RECEIVER] Completed Item 2 (Total: 3)
[SENDER] Item 2 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 3 (Total: 4)
[SENDER] Item 3 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 77 bytes
[RECEIVER] Completed Item 4 (Total: 5)
[SENDER] Item 4 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 95 bytes
[RECEIVER] Completed Item 5 (Total: 6)
[SENDER] Item 5 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 6 (Total: 7)
[SENDER] Item 6 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 109 bytes
[RECEIVER] Completed Item 7 (Total: 8)
[SENDER] Item 7 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 54 bytes
[RECEIVER] Completed Item 8 (Total: 9)
[SENDER] Item 8 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 9 (Total: 10)
[SENDER] Item 9 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 35 bytes
[RECEIVER] Completed Item 10 (Total: 11)
[SENDER] Item 10 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 31 bytes
[RECEIVER] Completed Item 11 (Total: 12)
[SENDER] Item 11 Verified.
[RECEIVER] Read 88 bytes
[RECEIVER] Completed Item 12 (Total: 13)
[SENDER] Item 12 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 44 bytes
[RECEIVER] Completed Item 13 (Total: 14)
[SENDER] Item 13 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Completed Item 14 (Total: 15)
[SENDER] Item 14 Verified.
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 15 (Total: 16)
[SENDER] Item 15 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 93 bytes
[RECEIVER] Completed Item 16 (Total: 17)
[SENDER] Item 16 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 99 bytes
[RECEIVER] Completed Item 17 (Total: 18)
[SENDER] Item 17 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 48 bytes
[RECEIVER] Completed Item 18 (Total: 19)
[SENDER] Item 18 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 135 bytes
[RECEIVER] Completed Item 19 (Total: 20)
[SENDER] Item 19 Verified.
[SENDER] TEST COMPLETE - All items transferred successfully.

```

### T-002 Details
### Execution Log
```
[MEMORY] Starting In-Memory Test: Drop=0.05 Corrupt=0.01 Items=20
[RECEIVER] Listening...
[SENDER] Starting stress test with 20 items...
[SENDER] Sending SYN...
[RECEIVER] Read 24 bytes
[RECEIVER] Synqed.
[SENDER] Read 16 bytes
[SENDER] Rx Type: 32
[SENDER] Handshake OK
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 0 (Total: 1)
[SENDER] Item 0 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 25 bytes
[RECEIVER] Completed Item 1 (Total: 2)
[SENDER] Item 1 Verified.
[RECEIVER] Read 103 bytes
[RECEIVER] Completed Item 2 (Total: 3)
[SENDER] Item 2 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 3 (Total: 4)
[SENDER] Item 3 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 4 Frag 1. Retrying...
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 4 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 77 bytes
[RECEIVER] Completed Item 4 (Total: 5)
[SENDER] Item 4 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 5 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 95 bytes
[RECEIVER] Completed Item 5 (Total: 6)
[SENDER] Item 5 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 6 (Total: 7)
[SENDER] Item 6 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 109 bytes
[RECEIVER] Completed Item 7 (Total: 8)
[SENDER] Item 7 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 54 bytes
[RECEIVER] Completed Item 8 (Total: 9)
[SENDER] Item 8 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] CORRUPTED byte 3
[RECEIVER] Read 17 bytes
[SENDER] Timeout/NACK on Item 9 Frag 1. Retrying...
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 9 (Total: 10)
[SENDER] Item 9 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 35 bytes
[RECEIVER] Completed Item 10 (Total: 11)
[SENDER] Item 10 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] CORRUPTED byte 101
[RECEIVER] Read 142 bytes
[SENDER] Timeout/NACK on Item 11 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 31 bytes
[RECEIVER] Completed Item 11 (Total: 12)
[SENDER] Item 11 Verified.
[RECEIVER] Read 88 bytes
[RECEIVER] Completed Item 12 (Total: 13)
[SENDER] Item 12 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 44 bytes
[RECEIVER] Completed Item 13 (Total: 14)
[SENDER] Item 13 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Completed Item 14 (Total: 15)
[SENDER] Item 14 Verified.
[CHAOS] DROPPED 106 bytes
[SENDER] Timeout/NACK on Item 15 Frag 0. Retrying...
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 15 (Total: 16)
[SENDER] Item 15 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 93 bytes
[RECEIVER] Completed Item 16 (Total: 17)
[SENDER] Item 16 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 99 bytes
[CHAOS] DROPPED 14 bytes
[RECEIVER] Completed Item 17 (Total: 18)
[SENDER] Timeout/NACK on Item 17 Frag 3. Retrying...
[RECEIVER] Read 99 bytes
[SENDER] Item 17 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 48 bytes
[RECEIVER] Completed Item 18 (Total: 19)
[SENDER] Item 18 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 19 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 135 bytes
[CHAOS] DROPPED 14 bytes
[RECEIVER] Completed Item 19 (Total: 20)
[SENDER] Timeout/NACK on Item 19 Frag 2. Retrying...
[RECEIVER] Read 135 bytes
[SENDER] Item 19 Verified.
[SENDER] TEST COMPLETE - All items transferred successfully.

```

### T-003 Details
### Execution Log
```
[MEMORY] Starting In-Memory Test: Drop=0.1 Corrupt=0.02 Items=20
[RECEIVER] Listening...
[SENDER] Starting stress test with 20 items...
[SENDER] Sending SYN...
[RECEIVER] Read 24 bytes
[RECEIVER] Synqed.
[SENDER] Read 16 bytes
[SENDER] Rx Type: 32
[SENDER] Handshake OK
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 0 (Total: 1)
[SENDER] Item 0 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 25 bytes
[RECEIVER] Completed Item 1 (Total: 2)
[SENDER] Item 1 Verified.
[CHAOS] DROPPED 103 bytes
[SENDER] Timeout/NACK on Item 2 Frag 0. Retrying...
[RECEIVER] Read 103 bytes
[RECEIVER] Completed Item 2 (Total: 3)
[SENDER] Item 2 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 3 (Total: 4)
[SENDER] Item 3 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 4 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 77 bytes
[RECEIVER] Completed Item 4 (Total: 5)
[SENDER] Item 4 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 5 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 95 bytes
[SENDER] Timeout/NACK on Item 5 Frag 2. Retrying...
[CHAOS] DROPPED 95 bytes
[SENDER] Timeout/NACK on Item 5 Frag 2. Retrying...
[RECEIVER] Read 95 bytes
[RECEIVER] Completed Item 5 (Total: 6)
[SENDER] Item 5 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[RECEIVER] Completed Item 6 (Total: 7)
[SENDER] Item 6 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 7 Frag 2. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 109 bytes
[RECEIVER] Completed Item 7 (Total: 8)
[SENDER] Item 7 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 54 bytes
[RECEIVER] Completed Item 8 (Total: 9)
[SENDER] Item 8 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 9 Frag 0. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 17 bytes
[CHAOS] DROPPED 14 bytes
[RECEIVER] Completed Item 9 (Total: 10)
[SENDER] Timeout/NACK on Item 9 Frag 1. Retrying...
[RECEIVER] Read 17 bytes
[SENDER] Item 9 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 10 Frag 0. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 35 bytes
[RECEIVER] Completed Item 10 (Total: 11)
[SENDER] Item 10 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 31 bytes
[RECEIVER] Completed Item 11 (Total: 12)
[SENDER] Item 11 Verified.
[RECEIVER] Read 88 bytes
[RECEIVER] Completed Item 12 (Total: 13)
[SENDER] Item 12 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 13 Frag 1. Retrying...
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 13 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 44 bytes
[CHAOS] DROPPED 14 bytes
[RECEIVER] Completed Item 13 (Total: 14)
[SENDER] Timeout/NACK on Item 13 Frag 2. Retrying...
[RECEIVER] Read 44 bytes
[SENDER] Item 13 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Completed Item 14 (Total: 15)
[SENDER] Item 14 Verified.
[RECEIVER] Read 106 bytes
[RECEIVER] Completed Item 15 (Total: 16)
[SENDER] Item 15 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 93 bytes
[SENDER] Timeout/NACK on Item 16 Frag 1. Retrying...
[RECEIVER] Read 93 bytes
[RECEIVER] Completed Item 16 (Total: 17)
[SENDER] Item 16 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 99 bytes
[RECEIVER] Completed Item 17 (Total: 18)
[SENDER] Item 17 Verified.
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 18 Frag 0. Retrying...
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 18 Frag 0. Retrying...
[CHAOS] DROPPED 142 bytes
[SENDER] Timeout/NACK on Item 18 Frag 0. Retrying...
[RECEIVER] Read 142 bytes
[CHAOS] CORRUPTED byte 20
[RECEIVER] Read 142 bytes
[SENDER] Timeout/NACK on Item 18 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[RECEIVER] Read 48 bytes
[RECEIVER] Completed Item 18 (Total: 19)
[SENDER] Item 18 Verified.
[RECEIVER] Read 142 bytes
[RECEIVER] Read 142 bytes
[CHAOS] DROPPED 14 bytes
[SENDER] Timeout/NACK on Item 19 Frag 1. Retrying...
[RECEIVER] Read 142 bytes
[RECEIVER] Read 135 bytes
[RECEIVER] Completed Item 19 (Total: 20)
[SENDER] Item 19 Verified.
[SENDER] TEST COMPLETE - All items transferred successfully.

```
