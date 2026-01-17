import sys
import time
import asyncio
import safeserial

async def main():
    if len(sys.argv) < 2:
        print("Usage: python sender.py <port> [item_count]")
        sys.exit(1)

    port = sys.argv[1]
    item_count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    baud_rate = 115200

    print(f"[SENDER] Connecting to {port}...")
    
    bridge = safeserial.DataBridge()
    
    # We only care about sending, but ARQ needs the read loop active
    def on_data(data):
        pass

    if not bridge.open(port, baud_rate, on_data):
        print(f"[SENDER] Failed to open {port}")
        sys.exit(1)

    print(f"[SENDER] Starting transmission of {item_count} items...")

    for i in range(item_count):
        msg = f"Packet-{i}"
        try:
            # DataBridge handles ARQ/Retries internally
            bridge.send(msg.encode('utf-8'))
            print(f"[SENDER] Sent: {msg}")
        except Exception as e:
            print(f"[SENDER] Error sending {msg}: {e}")
        
        # Traffic pacing
        time.sleep(0.05)

    # Allow time for final ACKs to clear
    time.sleep(2.0)

    print("[SENDER] TEST COMPLETE")
    
    if hasattr(bridge, 'close'):
        bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
