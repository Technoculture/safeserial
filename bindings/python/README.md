# Data Bridge SDK Python Bindings

Python bindings for the C++ Data Bridge SDK.

## Installation

You can install this package using `uv`, `pip`, or build from source.

```bash
uv pip install .
```

## Usage

```python
import data_bridge_sdk

# Serial Port
serial = data_bridge_sdk.SerialPort()
serial.open("/dev/ttyUSB0", 115200)
serial.write(b"Hello")
data = serial.read(1024)

# Packet
pkt = data_bridge_sdk.Packet.serialize(data_bridge_sdk.Packet.TYPE_DATA, 1, "Payload")
```
