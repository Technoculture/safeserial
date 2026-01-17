# SafeSerial for Node.js

Reliable serial messaging with CRC32, fragmentation, and ACK/Retry. Built for Electron and embedded workflows where silent corruption is unacceptable.

## Install

```bash
npm install @technoculture/safeserial
```

If a prebuilt binary is not available for your platform, it will build from source on install.

## Quickstart

```ts
import { DataBridge } from "@technoculture/safeserial";

const bridge = await DataBridge.open("/dev/ttyUSB0", { baudRate: 115200 });

bridge.on("data", (data) => {
  console.log("Received:", data.toString());
});

await bridge.send("Hello, SafeSerial");
await bridge.close();
```

## Why SafeSerial

- Guaranteed delivery with ACK/Retry
- CRC32 corruption detection
- Automatic fragmentation and reassembly
- Resilient reconnect support
- Electron-friendly native bindings

## API (Essentials)

### `DataBridge.open(port, options?)`

Opens a serial port with reliable communication enabled.

- `port`: device path (e.g. `/dev/ttyUSB0`, `COM3`)
- `options.baudRate`: default `115200`

Returns: `Promise<DataBridge>`

### `bridge.send(data)`

Sends data with guaranteed delivery.

- `data`: `Buffer` or `string`

Returns: `Promise<void>`

### `bridge.on("data", callback)`

Subscribe to received data.

### `bridge.close()`

Closes the serial port.

## Build From Source

```bash
cd bindings/node
npm install
npm run build
```

## License

MIT
