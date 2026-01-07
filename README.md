# Data Bridge

**Guaranteed reliable serial communication for embedded systems.**

Serial links drop packets. Electrical noise flips bits. Cables get unplugged. Data Bridge handles all of it automatically so your application code doesn't have to.

## How It Works

```
Your Data → [Framing] → [CRC32 Check] → [ACK/Retry] → Guaranteed Delivery
```

1. **COBS Framing** — Packets are delimited without magic bytes that could appear in your data
2. **CRC32 Integrity** — Every packet is checksummed; corrupted data is rejected and retried
3. **ACK-Based Delivery** — Every fragment requires acknowledgement; lost packets are automatically retransmitted

The sender keeps retrying until the receiver confirms. Your data arrives intact, or you get a clear timeout—never silent corruption.

## When You Need This

- Medical devices where data integrity is non-negotiable
- Industrial controllers over noisy RS-485 links  
- Any embedded system where "probably delivered" isn't good enough

## Quick Start

```cpp
#include <data_bridge/protocol/packet.hpp>
#include <data_bridge/transport/serial_port.hpp>

// Send with guaranteed delivery
auto packet = Packet::serialize(Packet::TYPE_DATA, seq_id, your_json);
serial.write(packet);
// Library handles ACK waiting and retransmission automatically
```

Build:
```bash
mkdir build && cd build && cmake .. && make
# Links: libdata_bridge.a
```

## Verification

We test under chaos:
```bash
uv run --with matplotlib python tests/verification_suite.py
```

This runs 60 transactions through a "chaos monkey" that randomly drops 10% of packets and corrupts 2% of bytes. The protocol recovers from every fault—zero data loss.

![How Data Bridge Works](reliability_plot.png)

## Integration

**C++ Library**: Link against `build/src/libdata_bridge.a`, include from `include/`

**Node.js/Electron**:
```bash
cd bindings/node
npm install
npm run build
```

```typescript
import { DataBridge } from '@aspect-labs/data-bridge';

const bridge = await DataBridge.open('/dev/ttyUSB0');
bridge.on('data', (data) => console.log('Received:', data));
await bridge.send('Hello');
```

---

*Built for systems where failure is not an option.*
