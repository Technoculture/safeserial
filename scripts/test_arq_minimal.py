#!/usr/bin/env python3
"""
Minimal ARQ Test - Verify the retry mechanism works
"""

import os
import pty
import select
import random
import time
import threading

# Chaos bridge
class ChaosBridge:
    def __init__(self, drop_rate=0.2):
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.port_a = os.ttyname(self.slave_a)
        self.port_b = os.ttyname(self.slave_b)
        self.drop_rate = drop_rate
        self.running = False
        self.stats = {'ok': 0, 'drop': 0}
        
    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        
    def stop(self):
        self.running = False
        
    def _run(self):
        while self.running:
            try:
                r, _, _ = select.select([self.master_a, self.master_b], [], [], 0.01)
                for fd in r:
                    data = os.read(fd, 4096)
                    if not data:
                        continue
                    target = self.master_b if fd == self.master_a else self.master_a
                    
                    # Chaos: Random drop
                    if random.random() < self.drop_rate:
                        self.stats['drop'] += 1
                        print(f"[CHAOS] DROPPED {len(data)} bytes")
                        continue  # Don't forward
                    
                    self.stats['ok'] += 1
                    os.write(target, data)
            except Exception as e:
                print(f"Bridge error: {e}")

def main():
    print("="*50)
    print("Minimal ARQ Test")
    print("="*50)
    
    # Import
    try:
        import data_bridge
        print("✓ DataBridge imported")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return
    
    # Bridge with 20% drop rate
    bridge = ChaosBridge(drop_rate=0.2)
    bridge.start()
    print(f"Bridge: {bridge.port_a} <-> {bridge.port_b}")
    
    # Create instances
    sender = data_bridge.DataBridge()
    receiver = data_bridge.DataBridge()
    
    received = []
    def on_recv(data):
        print(f"[RECEIVER] Got {len(data)} bytes")
        received.append(data)
    
    # Open
    print("Opening ports...")
    if not sender.open(bridge.port_a, 115200):
        print("Failed to open sender")
        return
    if not receiver.open(bridge.port_b, 115200, on_recv):
        print("Failed to open receiver")
        return
    
    print("Ports open. Sending small payload...")
    
    # Small payload - well under fragment size
    payload = b"Hello ARQ World!"
    
    start = time.time()
    try:
        sender.send(payload, timeout_ms=500, max_retries=10)
        elapsed = time.time() - start
        print(f"✓ Send completed in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Send failed after {elapsed:.2f}s: {e}")
    
    # Wait a bit for receiver
    time.sleep(0.5)
    
    # Check
    print(f"\nStats: OK={bridge.stats['ok']}, DROP={bridge.stats['drop']}")
    
    if received:
        if received[0] == payload:
            print(f"✓ SUCCESS! Received matches sent!")
        else:
            print(f"✗ MISMATCH: sent {payload}, got {received[0]}")
    else:
        print("✗ Nothing received")
    
    sender.close()
    receiver.close()
    bridge.stop()

if __name__ == "__main__":
    main()
