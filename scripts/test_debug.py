#!/usr/bin/env python3
"""Debug version with detailed logging"""

import os
import pty
import select
import random
import time
import threading

class ChaosBridge:
    def __init__(self, drop_rate=0.05):
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.port_a = os.ttyname(self.slave_a)
        self.port_b = os.ttyname(self.slave_b)
        self.drop_rate = drop_rate
        self.running = False
        
    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        
    def _run(self):
        pkt_num = 0
        while self.running:
            try:
                r, _, _ = select.select([self.master_a, self.master_b], [], [], 0.01)
                for fd in r:
                    data = os.read(fd, 4096)
                    if not data: continue
                    target = self.master_b if fd == self.master_a else self.master_a
                    direction = "A→B" if fd == self.master_a else "B→A"
                    pkt_num += 1
                    
                    if random.random() < self.drop_rate:
                        print(f"  [{pkt_num}] {direction} DROP {len(data)}b")
                        continue
                    
                    os.write(target, data)
                    print(f"  [{pkt_num}] {direction} OK {len(data)}b")
            except: pass

def main():
    print("="*60)
    print("DEBUG: Tracking all packets")
    print("="*60)
    
    import data_bridge
    
    bridge = ChaosBridge(0.05)
    bridge.start()
    print(f"Bridge: {bridge.port_a} <-> {bridge.port_b}\n")
    
    sender = data_bridge.DataBridge()
    receiver = data_bridge.DataBridge()
    
    received = []
    def on_recv(data):
        print(f"\n>>> RECEIVED {len(data)} bytes\n")
        received.append(data)
    
    sender.open(bridge.port_a, 115200)
    receiver.open(bridge.port_b, 115200, on_recv)
    
    # Small payload first
    payload = b"X" * 500 + b"_END"
    print(f"Sending {len(payload)} bytes (should be 3 fragments)...\n")
    
    try:
        result = sender.send(payload, timeout_ms=1000, max_retries=5)
        print(f"\n✓ SEND OK: {result}")
    except Exception as e:
        print(f"\n✗ SEND FAILED: {e}")
    
    time.sleep(0.5)
    
    if received and received[0] == payload:
        print("✓ RECEIVE OK")
    else:
        print(f"✗ RECEIVE FAIL: got {len(received)} chunks")
    
    sender.close()
    receiver.close()

if __name__ == "__main__":
    main()
