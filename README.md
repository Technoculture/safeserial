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

## Building & Verification

We use `bridge.py`, a unified CLI tool for building, testing, and verifying the entire stack.

### 1. Build Everything
Builds C++ core, Python environment, and Node bindings.
```bash
uv run python bridge.py build
```

### Sanitizers (C++ Core)
Enable sanitizers via the `DATA_BRIDGE_SANITIZERS` env var during configure. Use a semicolon or comma-separated list (Clang/GCC).
```bash
DATA_BRIDGE_SANITIZERS=address,undefined uv run python bridge.py build
DATA_BRIDGE_SANITIZERS=thread uv run python bridge.py build
```

### Coverage & Fuzzing
```bash
./scripts/run_coverage.sh
./scripts/run_fuzz.sh
```

### Traceability Artifacts
```bash
python scripts/collect_artifacts.py
```

### Traceability (Requirements → Tests)
Run end-to-end verification, generate test ID links, validate coverage, and capture evidence artifacts:
```bash
uv run python bridge.py test verify
```

What this produces:
- `docs/traceability/traceability_report.md` (coverage + consistency checks)
- `docs/traceability/testid_links.md` (TestID → GTest/pytest linkage)
- `docs/traceability/artifacts/latest/manifest.json` (evidence checksums)

Coverage threshold (default 100%):
```bash
DATA_BRIDGE_REQ_COVERAGE=1.0 uv run python bridge.py test verify
```

### Traceability Rollup (Submodules)
Aggregate traceability across git submodules:
```bash
uv run python scripts/aggregate_traceability.py
```

### CI
The default CI workflow runs build/unit tests, sanitizers, coverage, and fuzzing on Linux.

## Testing & Verification

The project includes a universal CLI tool `bridge.py` to manage builds and tests.

### 1. Build
```bash
uv run python bridge.py build
```
Builds the C++ core, Node.js bindings (if available), and sets up the Python environment.

### 2. Run Reliability Verification
Automated suite that runs traffic simulation with dropped/corrupted packets (Chaos Monkey).

```bash
# Verify C++ Bindings (Default)
uv run python bridge.py test verify       # Internal call to scripts/verify_reliability.py --target cpp

# Verify Node.js Bindings
uv run python scripts/verify_reliability.py --target node

# Cross-Language Verification (e.g. Node Sender -> Python Receiver)
uv run python scripts/verify_reliability.py --sender node --receiver python
```

### 3. Interactive Chaos Mode
Visualize the connection state and chaos effects in real-time.

```bash
# Default (Python only)
uv run python bridge.py test chaos

# Visualize C++ Agents
uv run --project bindings/python python scripts/chaos_visual.py --sender cpp --receiver cpp --items 100

# Visualize Mixed (Node -> Python) with High Chaos
uv run --project bindings/python python scripts/chaos_visual.py \
    --sender node --receiver python \
    --drop 0.05 --corrupt 0.02 \
    --burst 0.01 --latency 0.02 --disconnect 0.001
```

### 4. Unit Tests
```bash
uv run python bridge.py test unit
```

## Documentation
- **Test Reports**: Generated in `docs/test_report.md` after running verification.
- **Walkthrough**: See [walkthrough.md](walkthrough.md) for implementation details.

### 5. Generate Reports
Regenerate plots and reports from previous test runs.
```bash
uv run --with matplotlib python bridge.py viz
```

### 6. Publish
Uploads artifacts to PyPI (via `uv`) and NPM.
```bash
uv run python bridge.py publish      # Publish both
uv run python bridge.py publish python # Publish only Python bindings
```

![Fault Tolerance Test Results](docs/test_timeline.png)

---

*Built for systems where 99.9% reliability means someone gets hurt.*
