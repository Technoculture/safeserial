# @aspect-labs/data-bridge

Guaranteed reliable serial communication for Node.js and Electron.

## Installation

```bash
npm install @aspect-labs/data-bridge
```

Pre-built binaries are included for Windows and Linux (x64, arm64).

## Usage

```typescript
import { DataBridge } from '@aspect-labs/data-bridge';

// Open a serial port
const bridge = await DataBridge.open('/dev/ttyUSB0', { baudRate: 115200 });

// Receive data
bridge.on('data', (data) => {
  console.log('Received:', data.toString());
});

// Send with guaranteed delivery
await bridge.send('Hello, World!');

// Close when done
await bridge.close();
```

## Features

- **Guaranteed Delivery** — Every packet is acknowledged; lost packets are automatically retried
- **Corruption Detection** — CRC32 checksum on every packet
- **Large Message Support** — Automatic fragmentation and reassembly
- **Electron Compatible** — Works in both main and renderer processes

## API

### `DataBridge.open(port, options?)`

Opens a serial port with reliable communication enabled.

- `port` — Port path (e.g., `/dev/ttyUSB0` on Linux, `COM3` on Windows)
- `options.baudRate` — Baud rate (default: 115200)

Returns: `Promise<DataBridge>`

### `bridge.send(data)`

Sends data with guaranteed delivery.

- `data` — `Buffer` or `string` to send

Returns: `Promise<void>` — Resolves when acknowledged

### `bridge.on('data', callback)`

Subscribe to received data.

### `bridge.close()`

Closes the serial port.

## Building from Source

```bash
cd bindings/node
npm install
npm run build
```

## License

MIT
