# Data Bridge

**When `31.9 mg` becomes `319 mg`, patients die.**

Serial communication is unreliable. Bits flip. Packets drop. Cables disconnect. If your embedded system sends medical dosages, sensor readings, or control commands over UART—you need guarantees, not hope.

Data Bridge ensures every byte arrives exactly as sent, or you know about it.

![Serial Data Corruption Examples](reliability_plot.png)

## The Problem

Raw serial communication fails silently:

| Sent | Received | Failure Mode |
|------|----------|--------------|
| `31.9 mg` | `319 mg` | Bit flip → 10x overdose |
| `120 bpm` | `12 bpm` | Lost byte → false alarm |
| `98.6°F` | `9.86°F` | Corruption → wrong diagnosis |
| `{"vital":...}` | `(nothing)` | Packet dropped → missing data |

These aren't hypotheticals. This is what happens on noisy links.

## The Solution

```
Your Data → [COBS Framing] → [CRC32] → [ACK/Retry] → [Auto-Reconnect] → Guaranteed Delivery
```

- **CRC32** detects every corruption (no silent errors)
- **ACK/Retry** ensures delivery (no lost packets)
- **Auto-Reconnect** survives USB disconnects (no crashed sessions)

Your data arrives intact. Always.

## Quick Start

**C++:**
```cpp
#include <data_bridge/protocol/packet.hpp>

auto packet = Packet::serialize(Packet::TYPE_DATA, seq++, sensor_json);
serial.write(packet);  // Automatic retry until ACK received
```

**TypeScript/Electron:**
```typescript
import { ResilientDataBridge } from '@aspect-labs/data-bridge';

const bridge = await ResilientDataBridge.open('/dev/ttyUSB0');

// This WILL be delivered, even if the cable gets unplugged mid-transfer
await bridge.send('{"dose": 31.9, "unit": "mg"}');

bridge.on('disconnect', () => console.log('Queuing messages...'));
bridge.on('reconnected', () => console.log('Flushed!'));
```

## Build

```bash
# C++ library
mkdir build && cd build && cmake .. && make

# Node.js bindings
cd bindings/node && npm install && npm run build
```

## Verification

We torture-test the protocol:
```bash
uv run --with matplotlib python tests/verification_suite.py
```

60 transactions × 10% packet loss × 2% byte corruption = **Zero data loss.**

![Fault Tolerance Test Results](test_timeline.png)

---

*Built for systems where 99.9% reliability means someone gets hurt.*
