import sys
import safeserial

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB1"
bridge = safeserial.DataBridge()

print(f"Opening port: {port}")

def on_data(data):
    print(f"[RX] {data.decode('utf-8', errors='replace')}")

if bridge.open(port, 115200, on_data):
    print("Port opened successfully")
 
    msg = "Hello using DataBridge"
    bridge.send(msg)
    print(f"[TX] {msg}")