import sys
import time
import asyncio
import safeserial

received_count = 0

def on_data(data):
    global received_count
    try:
        msg = data.decode('utf-8')
        received_count += 1
        print(f"[RECEIVER] Got: {msg} (Total: {received_count})")
        sys.stdout.flush()
    except Exception as e:
        print(f"[RECEIVER] Error decoding: {e}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python receiver.py <port>")
        sys.exit(1)

    port = sys.argv[1]
    baud_rate = 115200

    print(f"[RECEIVER] Connecting to {port}...")
    
    bridge = safeserial.DataBridge()

    if not bridge.open(port, baud_rate, on_data):
        print(f"[RECEIVER] Failed to open {port}")
        sys.exit(1)

    print("[RECEIVER] Listening...")

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
        
    if hasattr(bridge, 'close'):
        bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
