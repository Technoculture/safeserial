#!/usr/bin/env python3
"""
Debug ARQ Test - With verbose logging
"""

import os
import pty
import select
import random
import time
import threading

# Direct minimal test without DataBridge wrapper first
# to verify the PTY bridge + packet logic works

def main():
    print("="*50)
    print("Raw Packet ARQ Test (No High-Level Wrapper)")
    print("="*50)
    
    # Import core only
    from data_bridge import _core
    
    # Create PTY pair (no chaos)
    master_a, slave_a = pty.openpty()
    master_b, slave_b = pty.openpty()
    port_a = os.ttyname(slave_a)
    port_b = os.ttyname(slave_b)
    print(f"Ports: {port_a} <-> {port_b}")
    
    # Simple bridge (no chaos for this debug)
    running = True
    def bridge():
        while running:
            try:
                r, _, _ = select.select([master_a, master_b], [], [], 0.01)
                for fd in r:
                    data = os.read(fd, 4096)
                    if data:
                        target = master_b if fd == master_a else master_a
                        os.write(target, data)
                        print(f"[BRIDGE] Forwarded {len(data)} bytes")
            except:
                pass
    
    bridge_thread = threading.Thread(target=bridge, daemon=True)
    bridge_thread.start()
    
    # Open serial ports
    sender_serial = _core.SerialPort()
    receiver_serial = _core.SerialPort()
    
    print("Opening sender...")
    if not sender_serial.open(port_a, 115200):
        print("Failed to open sender")
        return
    print("Opening receiver...")
    if not receiver_serial.open(port_b, 115200):
        print("Failed to open receiver")
        return
    
    print("Ports open.")
    
    # Send a packet
    payload = b"Hello World"
    seq = 1
    packet = _core.Packet.serialize(_core.Packet.TYPE_DATA, seq, payload)
    print(f"Serialized packet: {len(packet)} bytes")
    
    written = sender_serial.write(packet)
    print(f"Wrote {written} bytes")
    
    # Try to read on receiver
    time.sleep(0.5)
    
    rx_data = receiver_serial.read(1024)
    print(f"Receiver got {len(rx_data)} bytes: {rx_data}")
    
    if rx_data:
        # Deserialize
        frame, remaining = _core.Packet.deserialize(rx_data)
        print(f"Frame valid: {frame.valid}")
        if frame.valid:
            print(f"Payload: {frame.payload}")
    
    running = False
    sender_serial.close()
    receiver_serial.close()

if __name__ == "__main__":
    main()
