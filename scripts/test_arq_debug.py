#!/usr/bin/env python3
"""
Debug ARQ with logging - figure out why retries fail
"""

import os
import pty
import select
import random
import time
import threading

class ChaosBridge:
    def __init__(self, drop_rate=0.1):
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
                    direction = "A->B" if fd == self.master_a else "B->A"
                    
                    if random.random() < self.drop_rate:
                        self.stats['drop'] += 1
                        print(f"[CHAOS] {direction} DROPPED {len(data)} bytes")
                        continue
                    
                    self.stats['ok'] += 1
                    os.write(target, data)
                    print(f"[BRIDGE] {direction} OK {len(data)} bytes")
            except Exception as e:
                print(f"Bridge error: {e}")

def main():
    print("="*50)
    print("Debug ARQ Test - With 1000+ byte fragmentation")
    print("="*50)
    
    import data_bridge
    print("✓ DataBridge imported")
    
    bridge = ChaosBridge(drop_rate=0.05)  # Lower drop rate for debugging
    bridge.start()
    print(f"Bridge: {bridge.port_a} <-> {bridge.port_b}")
    
    sender = data_bridge.DataBridge()
    receiver = data_bridge.DataBridge()
    
    received = []
    def on_recv(data):
        print(f"[RECEIVER CALLBACK] Got {len(data)} bytes!")
        received.append(data)
    
    print("Opening ports...")
    if not sender.open(bridge.port_a, 115200):
        print("Failed to open sender")
        return
    if not receiver.open(bridge.port_b, 115200, on_recv):
        print("Failed to open receiver")
        return
    
    print("Ports open.\n")
    
    # 1000+ byte payload
    payload = b"X" * 1000 + b"_TEST_END"
    print(f"Sending {len(payload)} bytes...")
    
    start = time.time()
    try:
        result = sender.send(payload, timeout_ms=500, max_retries=5)
        elapsed = time.time() - start
        print(f"\n✓ Send completed in {elapsed:.2f}s, returned {result}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n✗ Send failed after {elapsed:.2f}s: {e}")
    
    time.sleep(1)  # Wait for receiver
    
    print(f"\nStats: OK={bridge.stats['ok']}, DROP={bridge.stats['drop']}")
    
    if received:
        if received[0] == payload:
            print(f"✓ SUCCESS! {len(payload)} bytes received correctly!")
        else:
            print(f"✗ MISMATCH")
    else:
        print("✗ Nothing received")
    
    sender.close()
    receiver.close()
    bridge.stop()

if __name__ == "__main__":
    main()
