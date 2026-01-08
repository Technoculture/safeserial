# Test Record - ISO 13485 Compliance
**Project:** Data Bridge Serial Protocol
**Date:** 2026-01-08T22:53:59.455626
**Tester:** Automated Runner

## 1. Scope
Verification of the reliable serial protocol implementation (Class C Medical Device component).

## 2. Test Environment
*   **OS:** darwin
*   **Build Artifacts:** `/Users/satyamtiwary/Documents/Python-Things/data-bridge/build/tests/reliability_test`
*   **Test Driver:** `/Users/satyamtiwary/Documents/Python-Things/data-bridge/scripts/verify_reliability.py`

## 3. Reliability Visualization
![Reliability Plot](test_timeline.png)

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
### Sender Log
```
1767892947.098609: [SENDER] Starting stress test with 20 items...
1767892947.098620: [SENDER] Sending SYN...
1767892947.199779: [SENDER] Rx Type: 32
1767892947.199793: [SENDER] Handshake Complete!
1767892947.199802: [SENDER] Sending Item 0 Frag 0/1
1767892947.199896: [SENDER] Item 0 Verified.
1767892947.199909: [SENDER] Sending Item 1 Frag 0/2
1767892947.199983: [SENDER] Sending Item 1 Frag 1/2
1767892947.200062: [SENDER] Item 1 Verified.
1767892947.200067: [SENDER] Sending Item 2 Frag 0/1
1767892947.200134: [SENDER] Item 2 Verified.
1767892947.200142: [SENDER] Sending Item 3 Frag 0/3
1767892947.200200: [SENDER] Sending Item 3 Frag 1/3
1767892947.200252: [SENDER] Sending Item 3 Frag 2/3
1767892949.214507: [SENDER] Timeout/NACK on Item 3 Frag 2. Retrying...
1767892949.214613: [SENDER] Item 3 Verified.
1767892949.214625: [SENDER] Sending Item 4 Frag 0/4
1767892949.214683: [SENDER] Sending Item 4 Frag 1/4
1767892949.214778: [SENDER] Sending Item 4 Frag 2/4
1767892949.214842: [SENDER] Sending Item 4 Frag 3/4
1767892949.214891: [SENDER] Item 4 Verified.
1767892949.214900: [SENDER] Sending Item 5 Frag 0/3
1767892949.214976: [SENDER] Sending Item 5 Frag 1/3
1767892949.215041: [SENDER] Sending Item 5 Frag 2/3
1767892949.215092: [SENDER] Item 5 Verified.
1767892949.215104: [SENDER] Sending Item 6 Frag 0/5
1767892949.215185: [SENDER] Sending Item 6 Frag 1/5
1767892949.215242: [SENDER] Sending Item 6 Frag 2/5
1767892951.227861: [SENDER] Timeout/NACK on Item 6 Frag 2. Retrying...
1767892951.228017: [SENDER] Sending Item 6 Frag 3/5
1767892951.228101: [SENDER] Sending Item 6 Frag 4/5
1767892951.228175: [SENDER] Item 6 Verified.
1767892951.228189: [SENDER] Sending Item 7 Frag 0/4
1767892951.228280: [SENDER] Sending Item 7 Frag 1/4
1767892951.228361: [SENDER] Sending Item 7 Frag 2/4
1767892951.228425: [SENDER] Sending Item 7 Frag 3/4
1767892951.228494: [SENDER] Item 7 Verified.
1767892951.228503: [SENDER] Sending Item 8 Frag 0/2
1767892951.228581: [SENDER] Sending Item 8 Frag 1/2
1767892951.228658: [SENDER] Item 8 Verified.
1767892951.228663: [SENDER] Sending Item 9 Frag 0/2
1767892951.228720: [SENDER] Sending Item 9 Frag 1/2
1767892951.228776: [SENDER] Item 9 Verified.
1767892951.228782: [SENDER] Sending Item 10 Frag 0/2
1767892951.228840: [SENDER] Sending Item 10 Frag 1/2
1767892951.228890: [SENDER] Item 10 Verified.
1767892951.228900: [SENDER] Sending Item 11 Frag 0/4
1767892951.228970: [SENDER] Sending Item 11 Frag 1/4
1767892951.229045: [SENDER] Sending Item 11 Frag 2/4
1767892951.229116: [SENDER] Sending Item 11 Frag 3/4
1767892951.229169: [SENDER] Item 11 Verified.
1767892951.229173: [SENDER] Sending Item 12 Frag 0/1
1767892951.229273: [SENDER] Item 12 Verified.
1767892951.229285: [SENDER] Sending Item 13 Frag 0/3
1767892951.229353: [SENDER] Sending Item 13 Frag 1/3
1767892953.245293: [SENDER] Timeout/NACK on Item 13 Frag 1. Retrying...
1767892953.245523: [SENDER] Sending Item 13 Frag 2/3
1767892953.245633: [SENDER] Item 13 Verified.
1767892953.245705: [SENDER] Sending Item 14 Frag 0/4
1767892953.245931: [SENDER] Sending Item 14 Frag 1/4
1767892953.246087: [SENDER] Sending Item 14 Frag 2/4
1767892953.246250: [SENDER] Sending Item 14 Frag 3/4
1767892953.246427: [SENDER] Item 14 Verified.
1767892953.246442: [SENDER] Sending Item 15 Frag 0/1
1767892953.246603: [SENDER] Item 15 Verified.
1767892953.246626: [SENDER] Sending Item 16 Frag 0/2
1767892953.246778: [SENDER] Sending Item 16 Frag 1/2
1767892953.246920: [SENDER] Item 16 Verified.
1767892953.246962: [SENDER] Sending Item 17 Frag 0/4
1767892953.247247: [SENDER] Sending Item 17 Frag 1/4
1767892953.247424: [SENDER] Sending Item 17 Frag 2/4
1767892953.247588: [SENDER] Sending Item 17 Frag 3/4
1767892953.247745: [SENDER] Item 17 Verified.
1767892953.247789: [SENDER] Sending Item 18 Frag 0/4
1767892953.247952: [SENDER] Sending Item 18 Frag 1/4
1767892953.248103: [SENDER] Sending Item 18 Frag 2/4
1767892953.248260: [SENDER] Sending Item 18 Frag 3/4
1767892953.248361: [SENDER] Item 18 Verified.
1767892953.248400: [SENDER] Sending Item 19 Frag 0/3
1767892953.248589: [SENDER] Sending Item 19 Frag 1/3
1767892953.248739: [SENDER] Sending Item 19 Frag 2/3
1767892953.248888: [SENDER] Item 19 Verified.
1767892953.248894: [SENDER] TEST COMPLETE - All items transferred successfully.

```
### Receiver Log
```
1767892947.098460: [RECEIVER] Listening...
1767892947.199726: [RECEIVER] Synqed.
1767892947.199859: [RECEIVER] Completed Item 0 (Total: 1)
1767892947.200043: [RECEIVER] Completed Item 1 (Total: 2)
1767892947.200106: [RECEIVER] Completed Item 2 (Total: 3)
1767892947.200292: [RECEIVER] Completed Item 3 (Total: 4)
1767892949.214875: [RECEIVER] Completed Item 4 (Total: 5)
1767892949.215075: [RECEIVER] Completed Item 5 (Total: 6)
1767892951.228151: [RECEIVER] Completed Item 6 (Total: 7)
1767892951.228480: [RECEIVER] Completed Item 7 (Total: 8)
1767892951.228638: [RECEIVER] Completed Item 8 (Total: 9)
1767892951.228754: [RECEIVER] Completed Item 9 (Total: 10)
1767892951.228875: [RECEIVER] Completed Item 10 (Total: 11)
1767892951.229152: [RECEIVER] Completed Item 11 (Total: 12)
1767892951.229233: [RECEIVER] Completed Item 12 (Total: 13)
1767892953.245604: [RECEIVER] Completed Item 13 (Total: 14)
1767892953.246380: [RECEIVER] Completed Item 14 (Total: 15)
1767892953.246563: [RECEIVER] Completed Item 15 (Total: 16)
1767892953.246874: [RECEIVER] Completed Item 16 (Total: 17)
1767892953.247688: [RECEIVER] Completed Item 17 (Total: 18)
1767892953.248328: [RECEIVER] Completed Item 18 (Total: 19)
1767892953.248858: [RECEIVER] Completed Item 19 (Total: 20)

```

### T-002 Details
### Sender Log
```
1767892954.292403: [SENDER] Starting stress test with 20 items...
1767892954.292433: [SENDER] Sending SYN...
1767892954.393327: [SENDER] Rx Type: 32
1767892954.393333: [SENDER] Handshake Complete!
1767892954.393341: [SENDER] Sending Item 0 Frag 0/1
1767892956.407126: [SENDER] Timeout/NACK on Item 0 Frag 0. Retrying...
1767892956.407283: [SENDER] Item 0 Verified.
1767892956.407290: [SENDER] Sending Item 1 Frag 0/2
1767892956.407351: [SENDER] Sending Item 1 Frag 1/2
1767892958.421021: [SENDER] Timeout/NACK on Item 1 Frag 1. Retrying...
1767892960.436338: [SENDER] Timeout/NACK on Item 1 Frag 1. Retrying...
1767892960.436457: [SENDER] Item 1 Verified.
1767892960.436464: [SENDER] Sending Item 2 Frag 0/1
1767892960.436555: [SENDER] Item 2 Verified.
1767892960.436564: [SENDER] Sending Item 3 Frag 0/3
1767892960.436636: [SENDER] Sending Item 3 Frag 1/3
1767892960.436699: [SENDER] Sending Item 3 Frag 2/3
1767892960.436749: [SENDER] Item 3 Verified.
1767892960.436760: [SENDER] Sending Item 4 Frag 0/4
1767892960.436819: [SENDER] Sending Item 4 Frag 1/4
1767892960.436934: [SENDER] Sending Item 4 Frag 2/4
1767892960.437020: [SENDER] Sending Item 4 Frag 3/4
1767892960.437073: [SENDER] Item 4 Verified.
1767892960.437082: [SENDER] Sending Item 5 Frag 0/3
1767892962.451659: [SENDER] Timeout/NACK on Item 5 Frag 0. Retrying...
1767892962.451789: [SENDER] Sending Item 5 Frag 1/3
1767892962.451882: [SENDER] Sending Item 5 Frag 2/3
1767892962.451971: [SENDER] Item 5 Verified.
1767892962.451984: [SENDER] Sending Item 6 Frag 0/5
1767892964.467112: [SENDER] Timeout/NACK on Item 6 Frag 0. Retrying...
1767892964.467249: [SENDER] Sending Item 6 Frag 1/5
1767892964.467321: [SENDER] Sending Item 6 Frag 2/5
1767892964.467389: [SENDER] Sending Item 6 Frag 3/5
1767892964.467459: [SENDER] Sending Item 6 Frag 4/5
1767892964.467505: [SENDER] Item 6 Verified.
1767892964.467518: [SENDER] Sending Item 7 Frag 0/4
1767892966.482193: [SENDER] Timeout/NACK on Item 7 Frag 0. Retrying...
1767892966.482333: [SENDER] Sending Item 7 Frag 1/4
1767892966.609034: [SENDER] Sending Item 7 Frag 2/4
1767892966.609132: [SENDER] Sending Item 7 Frag 3/4
1767892966.609200: [SENDER] Item 7 Verified.
1767892966.609208: [SENDER] Sending Item 8 Frag 0/2
1767892966.609271: [SENDER] Sending Item 8 Frag 1/2
1767892968.623411: [SENDER] Timeout/NACK on Item 8 Frag 1. Retrying...
1767892968.623795: [SENDER] Item 8 Verified.
1767892968.623857: [SENDER] Sending Item 9 Frag 0/2
1767892968.624104: [SENDER] Sending Item 9 Frag 1/2
1767892968.624223: [SENDER] Item 9 Verified.
1767892968.624271: [SENDER] Sending Item 10 Frag 0/2
1767892968.624447: [SENDER] Sending Item 10 Frag 1/2
1767892968.624612: [SENDER] Item 10 Verified.
1767892968.624651: [SENDER] Sending Item 11 Frag 0/4
1767892968.624881: [SENDER] Sending Item 11 Frag 1/4
1767892968.625162: [SENDER] Sending Item 11 Frag 2/4
1767892968.625383: [SENDER] Sending Item 11 Frag 3/4
1767892968.625614: [SENDER] Item 11 Verified.
1767892968.625628: [SENDER] Sending Item 12 Frag 0/1
1767892968.625833: [SENDER] Item 12 Verified.
1767892968.625876: [SENDER] Sending Item 13 Frag 0/3
1767892968.626005: [SENDER] Sending Item 13 Frag 1/3
1767892968.626082: [SENDER] Sending Item 13 Frag 2/3
1767892970.641983: [SENDER] Timeout/NACK on Item 13 Frag 2. Retrying...
1767892970.642276: [SENDER] Item 13 Verified.
1767892970.642327: [SENDER] Sending Item 14 Frag 0/4
1767892970.642509: [SENDER] Sending Item 14 Frag 1/4
1767892970.642759: [SENDER] Sending Item 14 Frag 2/4
1767892970.643007: [SENDER] Sending Item 14 Frag 3/4
1767892970.643180: [SENDER] Item 14 Verified.
1767892970.643195: [SENDER] Sending Item 15 Frag 0/1
1767892970.643330: [SENDER] Item 15 Verified.
1767892970.643355: [SENDER] Sending Item 16 Frag 0/2
1767892970.643503: [SENDER] Sending Item 16 Frag 1/2
1767892970.643655: [SENDER] Item 16 Verified.
1767892970.643703: [SENDER] Sending Item 17 Frag 0/4
1767892970.643882: [SENDER] Sending Item 17 Frag 1/4
1767892970.644032: [SENDER] Sending Item 17 Frag 2/4
1767892972.660226: [SENDER] Timeout/NACK on Item 17 Frag 2. Retrying...
1767892972.660363: [SENDER] Sending Item 17 Frag 3/4
1767892972.660435: [SENDER] Item 17 Verified.
1767892972.660453: [SENDER] Sending Item 18 Frag 0/4
1767892972.660518: [SENDER] Sending Item 18 Frag 1/4
1767892972.660596: [SENDER] Sending Item 18 Frag 2/4
1767892974.678408: [SENDER] Timeout/NACK on Item 18 Frag 2. Retrying...
1767892976.692615: [SENDER] Timeout/NACK on Item 18 Frag 2. Retrying...
1767892976.692753: [SENDER] Sending Item 18 Frag 3/4
1767892978.709952: [SENDER] Timeout/NACK on Item 18 Frag 3. Retrying...
1767892978.710072: [SENDER] Item 18 Verified.
1767892978.710094: [SENDER] Sending Item 19 Frag 0/3
1767892978.710206: [SENDER] Sending Item 19 Frag 1/3
1767892980.725145: [SENDER] Timeout/NACK on Item 19 Frag 1. Retrying...
1767892982.741466: [SENDER] Timeout/NACK on Item 19 Frag 1. Retrying...
1767892982.741571: [SENDER] Sending Item 19 Frag 2/3
1767892982.741663: [SENDER] Item 19 Verified.
1767892982.741667: [SENDER] TEST COMPLETE - All items transferred successfully.

```
### Receiver Log
```
1767892954.292361: [RECEIVER] Listening...
1767892954.393293: [RECEIVER] Synqed.
1767892956.407256: [RECEIVER] Completed Item 0 (Total: 1)
1767892956.407398: [RECEIVER] Completed Item 1 (Total: 2)
1767892960.436526: [RECEIVER] Completed Item 2 (Total: 3)
1767892960.436733: [RECEIVER] Completed Item 3 (Total: 4)
1767892960.437052: [RECEIVER] Completed Item 4 (Total: 5)
1767892962.451948: [RECEIVER] Completed Item 5 (Total: 6)
1767892964.467491: [RECEIVER] Completed Item 6 (Total: 7)
1767892966.609172: [RECEIVER] Completed Item 7 (Total: 8)
1767892968.623738: [RECEIVER] Completed Item 8 (Total: 9)
1767892968.624184: [RECEIVER] Completed Item 9 (Total: 10)
1767892968.624572: [RECEIVER] Completed Item 10 (Total: 11)
1767892968.625465: [RECEIVER] Completed Item 11 (Total: 12)
1767892968.625741: [RECEIVER] Completed Item 12 (Total: 13)
1767892968.626177: [RECEIVER] Completed Item 13 (Total: 14)
1767892970.643145: [RECEIVER] Completed Item 14 (Total: 15)
1767892970.643303: [RECEIVER] Completed Item 15 (Total: 16)
1767892970.643621: [RECEIVER] Completed Item 16 (Total: 17)
1767892972.660405: [RECEIVER] Completed Item 17 (Total: 18)
1767892978.710035: [RECEIVER] Completed Item 18 (Total: 19)
1767892982.741635: [RECEIVER] Completed Item 19 (Total: 20)

```

### T-003 Details
### Sender Log
```
1767892983.782203: [SENDER] Starting stress test with 20 items...
1767892983.782214: [SENDER] Sending SYN...
1767892983.883697: [SENDER] Rx Type: 32
1767892983.883706: [SENDER] Handshake Complete!
1767892983.883714: [SENDER] Sending Item 0 Frag 0/1
1767892983.883801: [SENDER] Item 0 Verified.
1767892983.883806: [SENDER] Sending Item 1 Frag 0/2
1767892983.883949: [SENDER] Sending Item 1 Frag 1/2
1767892983.884010: [SENDER] Item 1 Verified.
1767892983.884017: [SENDER] Sending Item 2 Frag 0/1
1767892983.884094: [SENDER] Item 2 Verified.
1767892983.884103: [SENDER] Sending Item 3 Frag 0/3
1767892985.899504: [SENDER] Timeout/NACK on Item 3 Frag 0. Retrying...
1767892985.899623: [SENDER] Sending Item 3 Frag 1/3
1767892985.899731: [SENDER] Sending Item 3 Frag 2/3
1767892987.916351: [SENDER] Timeout/NACK on Item 3 Frag 2. Retrying...
1767892987.916480: [SENDER] Item 3 Verified.
1767892987.916495: [SENDER] Sending Item 4 Frag 0/4
1767892989.931734: [SENDER] Timeout/NACK on Item 4 Frag 0. Retrying...
1767892991.947310: [SENDER] Timeout/NACK on Item 4 Frag 0. Retrying...
1767892991.947443: [SENDER] Sending Item 4 Frag 1/4
1767892991.947568: [SENDER] Sending Item 4 Frag 2/4
1767892993.964240: [SENDER] Timeout/NACK on Item 4 Frag 2. Retrying...
1767892995.984641: [SENDER] Timeout/NACK on Item 4 Frag 2. Retrying...
1767892998.000174: [SENDER] Timeout/NACK on Item 4 Frag 2. Retrying...
1767892998.000847: [SENDER] Sending Item 4 Frag 3/4
1767892998.001181: [SENDER] Item 4 Verified.
1767892998.001254: [SENDER] Sending Item 5 Frag 0/3
1767892998.001948: [SENDER] Sending Item 5 Frag 1/3
1767892998.126238: [SENDER] Sending Item 5 Frag 2/3
1767892998.126458: [SENDER] Item 5 Verified.
1767892998.126507: [SENDER] Sending Item 6 Frag 0/5
1767893000.141220: [SENDER] Timeout/NACK on Item 6 Frag 0. Retrying...
1767893000.141483: [SENDER] Sending Item 6 Frag 1/5
1767893000.141686: [SENDER] Sending Item 6 Frag 2/5
1767893002.156877: [SENDER] Timeout/NACK on Item 6 Frag 2. Retrying...
1767893002.157016: [SENDER] Sending Item 6 Frag 3/5
1767893004.172509: [SENDER] Timeout/NACK on Item 6 Frag 3. Retrying...
1767893006.185637: [SENDER] Timeout/NACK on Item 6 Frag 3. Retrying...
1767893008.199982: [SENDER] Timeout/NACK on Item 6 Frag 3. Retrying...
1767893008.200111: [SENDER] Sending Item 6 Frag 4/5
1767893008.200154: [SENDER] Item 6 Verified.
1767893008.200167: [SENDER] Sending Item 7 Frag 0/4
1767893008.200225: [SENDER] Sending Item 7 Frag 1/4
1767893008.200338: [SENDER] Sending Item 7 Frag 2/4
1767893010.213674: [SENDER] Timeout/NACK on Item 7 Frag 2. Retrying...
1767893010.213802: [SENDER] Sending Item 7 Frag 3/4
1767893010.213875: [SENDER] Item 7 Verified.
1767893010.213883: [SENDER] Sending Item 8 Frag 0/2
1767893012.227382: [SENDER] Timeout/NACK on Item 8 Frag 0. Retrying...
1767893012.228017: [SENDER] Sending Item 8 Frag 1/2
1767893012.228537: [SENDER] Item 8 Verified.
1767893012.228568: [SENDER] Sending Item 9 Frag 0/2
1767893014.243899: [SENDER] Timeout/NACK on Item 9 Frag 0. Retrying...
1767893014.244036: [SENDER] Sending Item 9 Frag 1/2
1767893014.244089: [SENDER] Item 9 Verified.
1767893014.244097: [SENDER] Sending Item 10 Frag 0/2
1767893014.244162: [SENDER] Sending Item 10 Frag 1/2
1767893016.258616: [SENDER] Timeout/NACK on Item 10 Frag 1. Retrying...
1767893018.274165: [SENDER] Timeout/NACK on Item 10 Frag 1. Retrying...
1767893018.275131: [SENDER] Item 10 Verified.
1767893018.275224: [SENDER] Sending Item 11 Frag 0/4
1767893020.290850: [SENDER] Timeout/NACK on Item 11 Frag 0. Retrying...
1767893020.290972: [SENDER] Sending Item 11 Frag 1/4
1767893020.291093: [SENDER] Sending Item 11 Frag 2/4
1767893020.291188: [SENDER] Sending Item 11 Frag 3/4
1767893020.291259: [SENDER] Item 11 Verified.
1767893020.291265: [SENDER] Sending Item 12 Frag 0/1
1767893022.306646: [SENDER] Timeout/NACK on Item 12 Frag 0. Retrying...
1767893022.306762: [SENDER] Item 12 Verified.
1767893022.306779: [SENDER] Sending Item 13 Frag 0/3
1767893022.306858: [SENDER] Sending Item 13 Frag 1/3
1767893022.306930: [SENDER] Sending Item 13 Frag 2/3
1767893024.322709: [SENDER] Timeout/NACK on Item 13 Frag 2. Retrying...
1767893026.339625: [SENDER] Timeout/NACK on Item 13 Frag 2. Retrying...
1767893028.358306: [SENDER] Timeout/NACK on Item 13 Frag 2. Retrying...
1767893028.358983: [SENDER] Item 13 Verified.
1767893028.359273: [SENDER] Sending Item 14 Frag 0/4
1767893028.359795: [SENDER] Sending Item 14 Frag 1/4
1767893030.378745: [SENDER] Timeout/NACK on Item 14 Frag 1. Retrying...
1767893030.379107: [SENDER] Sending Item 14 Frag 2/4
1767893030.379306: [SENDER] Sending Item 14 Frag 3/4
1767893030.379489: [SENDER] Item 14 Verified.
1767893030.379505: [SENDER] Sending Item 15 Frag 0/1
1767893030.379871: [SENDER] Item 15 Verified.
1767893030.379890: [SENDER] Sending Item 16 Frag 0/2
1767893030.379992: [SENDER] Sending Item 16 Frag 1/2
1767893030.380060: [SENDER] Item 16 Verified.
1767893030.380072: [SENDER] Sending Item 17 Frag 0/4
1767893032.396057: [SENDER] Timeout/NACK on Item 17 Frag 0. Retrying...
1767893032.396389: [SENDER] Sending Item 17 Frag 1/4
1767893032.396577: [SENDER] Sending Item 17 Frag 2/4
1767893032.396841: [SENDER] Sending Item 17 Frag 3/4
1767893034.413844: [SENDER] Timeout/NACK on Item 17 Frag 3. Retrying...
1767893034.414220: [SENDER] Item 17 Verified.
1767893034.414289: [SENDER] Sending Item 18 Frag 0/4
1767893034.414499: [SENDER] Sending Item 18 Frag 1/4
1767893034.414683: [SENDER] Sending Item 18 Frag 2/4
1767893036.432112: [SENDER] Timeout/NACK on Item 18 Frag 2. Retrying...
1767893036.432375: [SENDER] Sending Item 18 Frag 3/4
1767893036.432526: [SENDER] Item 18 Verified.
1767893036.432580: [SENDER] Sending Item 19 Frag 0/3
1767893038.446278: [SENDER] Timeout/NACK on Item 19 Frag 0. Retrying...
1767893038.446407: [SENDER] Sending Item 19 Frag 1/3
1767893038.446476: [SENDER] Sending Item 19 Frag 2/3
1767893038.446545: [SENDER] Item 19 Verified.
1767893038.446550: [SENDER] TEST COMPLETE - All items transferred successfully.

```
### Receiver Log
```
1767892983.781925: [RECEIVER] Listening...
1767892983.883613: [RECEIVER] Synqed.
1767892983.883771: [RECEIVER] Completed Item 0 (Total: 1)
1767892983.883990: [RECEIVER] Completed Item 1 (Total: 2)
1767892983.884070: [RECEIVER] Completed Item 2 (Total: 3)
1767892987.916441: [RECEIVER] Completed Item 3 (Total: 4)
1767892998.001085: [RECEIVER] Completed Item 4 (Total: 5)
1767892998.126391: [RECEIVER] Completed Item 5 (Total: 6)
1767893008.200137: [RECEIVER] Completed Item 6 (Total: 7)
1767893010.213853: [RECEIVER] Completed Item 7 (Total: 8)
1767893012.228221: [RECEIVER] Completed Item 8 (Total: 9)
1767893014.244065: [RECEIVER] Completed Item 9 (Total: 10)
1767893016.258688: [RECEIVER] Completed Item 10 (Total: 11)
1767893020.291239: [RECEIVER] Completed Item 11 (Total: 12)
1767893020.291306: [RECEIVER] Completed Item 12 (Total: 13)
1767893022.306971: [RECEIVER] Completed Item 13 (Total: 14)
1767893030.379445: [RECEIVER] Completed Item 14 (Total: 15)
1767893030.379625: [RECEIVER] Completed Item 15 (Total: 16)
1767893030.380035: [RECEIVER] Completed Item 16 (Total: 17)
1767893032.396968: [RECEIVER] Completed Item 17 (Total: 18)
1767893036.432466: [RECEIVER] Completed Item 18 (Total: 19)
1767893038.446524: [RECEIVER] Completed Item 19 (Total: 20)

```
