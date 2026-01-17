# SafeSerial for Python

Reliable serial messaging with CRC32, fragmentation, and ACK/Retry. Designed for workflows where silent corruption is unacceptable.

## Install

```bash
pip install safeserial
```

## Quickstart

```python
import safeserial

bridge = safeserial.DataBridge()

def on_data(data):
    print("Received:", data)

if bridge.open("/dev/ttyUSB0", 115200, on_data):
    bridge.send(b"Hello, SafeSerial")
    bridge.close()
```

## Why SafeSerial

- Guaranteed delivery with ACK/Retry
- CRC32 corruption detection
- Automatic fragmentation and reassembly
- Resilient reconnect support

## API (Essentials)

### `DataBridge.open(port, baud_rate, on_data)`

Opens a serial port with reliable communication enabled.

- `port`: device path (e.g. `/dev/ttyUSB0`, `COM3`)
- `baud_rate`: default `115200`
- `on_data`: callback for received payloads

Returns: `bool` (connected)

### `DataBridge.send(data)`

Sends data with guaranteed delivery.

- `data`: `bytes`

### `DataBridge.close()`

Closes the serial port.

## Build From Source

```bash
cd bindings/python
uv sync
uv pip install -e .
```

## License

MIT
