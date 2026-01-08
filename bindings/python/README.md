# Data Bridge SDK Python Bindings

Python bindings for the C++ Data Bridge SDK.

## Installation
Development install using `uv`:
```bash
uv sync
uv pip install -e .
```

## Usage

```python
import data_bridge

# High-Level Reliable Bridge (ARQ)
bridge = data_bridge.DataBridge()

def on_data(data):
    print(f"Received: {data}")

# Open connection (Auto-reconnect enabled by default)
if bridge.open("/dev/ttyUSB0", 115200, on_data):
    print("Connected!")
    
    # Check stats
    print(bridge.stats)

    # Send reliable message
    bridge.send(b"Hello World")
```
