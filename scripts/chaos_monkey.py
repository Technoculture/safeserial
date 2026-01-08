"""
Chaos Monkey - Serial Link Fault Injector

Simulates all real-world serial communication failure modes:
1. Packet drops (entire write lost)
2. Bit corruption (single bit flips)
3. Burst corruption (multiple consecutive bytes corrupted)
4. Byte insertion (extra garbage bytes)
5. Byte deletion (bytes lost mid-stream)
6. Latency spikes (delayed delivery)
7. Connection interruption (temporary disconnect)
"""

import os
import pty
import select
import random
import time
import sys
import threading
from collections import deque

class ChaosMonkey:
    def __init__(self, 
                 drop_rate=0.05,           # 5% packet drop
                 corrupt_rate=0.02,        # 2% bit corruption
                 burst_corrupt_rate=0.01,  # 1% burst corruption (3-5 bytes)
                 insert_rate=0.005,        # 0.5% byte insertion
                 delete_rate=0.005,        # 0.5% byte deletion
                 latency_spike_rate=0.01,  # 1% latency spike (50-200ms)
                 disconnect_rate=0.001,    # 0.1% temporary disconnect (100-500ms)
                 baud_rate=115200):        # Simulated baud rate
        
        self.drop_rate = drop_rate
        self.corrupt_rate = corrupt_rate
        self.burst_corrupt_rate = burst_corrupt_rate
        self.insert_rate = insert_rate
        self.delete_rate = delete_rate
        self.latency_spike_rate = latency_spike_rate
        self.disconnect_rate = disconnect_rate
        self.baud_rate = baud_rate
        
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.port_a = os.ttyname(self.slave_a)
        self.port_b = os.ttyname(self.slave_b)
        
        self.lock = threading.Lock()
        self.running = False
        
        # Stats
        self.stats = {
            'total_bytes': 0,
            'ok': 0, # Added for visualizer compatibility
            'drop': 0, # Added for visualizer compatibility
            'corrupt': 0, # Added for visualizer compatibility
            'retries': 0, # Added for visualizer compatibility
            
            # Detailed stats
            'dropped_packets': 0,
            'corrupted_bits': 0,
            'burst_corruptions': 0,
            'inserted_bytes': 0,
            'deleted_bytes': 0,
            'latency_spikes': 0,
            'disconnects': 0,
        }
        
        self.timeline = deque(maxlen=60)
        self.seen_packets = set()
        
        # Only log to file if running in standalone mode (checked later) or if explicitly desired
        # For now, we will open it lazily or just print if verbose
        self.log_file = None

    def start(self):
        """Start the bridge in a background thread."""
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False

    def log(self, msg):
        if self.log_file:
            self.log_file.write(f"{time.time()}: {msg}\n")

    def _inject(self, data: bytes) -> bytes:
        """Apply all failure modes to the data."""
        if not data:
            return data
            
        with self.lock:
            # Detect retry (duplicate packet) for visualizer
            is_retry = data in self.seen_packets
            self.seen_packets.add(data)
            
            # 1. Packet Drop (entire packet lost)
            if random.random() < self.drop_rate:
                if self.log_file: self.log(f"[CHAOS] DROPPED {len(data)} bytes")
                self.stats['dropped_packets'] += 1
                self.stats['drop'] += 1 # Visualizer compat
                self.timeline.append('D')
                return b""
            
            # Simulate Wire Speed (Baud Rate)
            # 115200 baud ~= 11520 bytes/s (1 start + 8 data + 1 stop = 10 bits/byte)
            if self.baud_rate > 0:
                bytes_per_sec = self.baud_rate / 10.0
                wire_duration = len(data) / bytes_per_sec
                if wire_duration > 0.001:
                    time.sleep(wire_duration)

            data_list = bytearray(data)
            modified = False
            
            # 2. Single Bit Corruption
            if random.random() < self.corrupt_rate:
                idx = random.randint(0, len(data_list) - 1)
                bit = random.randint(0, 7)
                data_list[idx] ^= (1 << bit)
                if self.log_file: self.log(f"[CHAOS] BIT_FLIP byte[{idx}] bit[{bit}]")
                self.stats['corrupted_bits'] += 1
                self.stats['corrupt'] += 1 # Visualizer compat
                self.timeline.append('C')
                modified = True
            
            # 3. Burst Corruption (3-5 consecutive bytes)
            if random.random() < self.burst_corrupt_rate and len(data_list) > 5:
                start = random.randint(0, len(data_list) - 5)
                burst_len = random.randint(3, 5)
                for i in range(burst_len):
                    data_list[start + i] = random.randint(0, 255)
                if self.log_file: self.log(f"[CHAOS] BURST_CORRUPT bytes[{start}:{start+burst_len}]")
                self.stats['burst_corruptions'] += 1
                self.stats['corrupt'] += 1
                self.timeline.append('C')
                modified = True
            
            # 4. Byte Insertion (1-3 garbage bytes)
            if random.random() < self.insert_rate:
                idx = random.randint(0, len(data_list))
                insert_len = random.randint(1, 3)
                garbage = bytes([random.randint(0, 255) for _ in range(insert_len)])
                data_list = data_list[:idx] + bytearray(garbage) + data_list[idx:]
                if self.log_file: self.log(f"[CHAOS] INSERTED {insert_len} bytes at {idx}")
                self.stats['inserted_bytes'] += insert_len
                self.stats['corrupt'] += 1
                self.timeline.append('C')
                modified = True
            
            # 5. Byte Deletion (1-2 bytes lost)
            if random.random() < self.delete_rate and len(data_list) > 3:
                idx = random.randint(0, len(data_list) - 2)
                delete_len = random.randint(1, 2)
                deleted = data_list[idx:idx+delete_len]
                data_list = data_list[:idx] + data_list[idx+delete_len:]
                if self.log_file: self.log(f"[CHAOS] DELETED {delete_len} bytes at {idx}")
                self.stats['deleted_bytes'] += delete_len
                self.stats['corrupt'] += 1
                self.timeline.append('C')
                modified = True
            
            # 6. Latency Spike
            if random.random() < self.latency_spike_rate:
                delay = random.uniform(0.05, 0.2)  # 50-200ms
                if self.log_file: self.log(f"[CHAOS] LATENCY_SPIKE {delay*1000:.0f}ms")
                self.stats['latency_spikes'] += 1
                time.sleep(delay)
            
            # 7. Connection Interruption (drop data + delay)
            if random.random() < self.disconnect_rate:
                delay = random.uniform(0.1, 0.5)  # 100-500ms
                if self.log_file: self.log(f"[CHAOS] DISCONNECT {delay*1000:.0f}ms")
                self.stats['disconnects'] += 1
                self.stats['drop'] += 1
                self.timeline.append('D')
                time.sleep(delay)
                return b""  # Drop the packet during "disconnect"
            
            self.stats['total_bytes'] += len(data_list)
            
            if not modified:
                if is_retry:
                    self.stats['retries'] += 1
                    self.timeline.append('R')
                else:
                    self.stats['ok'] += 1
                    self.timeline.append('O')
                    
            return bytes(data_list)

    def _run(self):
        while self.running:
            try:
                r, _, _ = select.select([self.master_a, self.master_b], [], [], 0.01)
                
                for fd in r:
                    try:
                        data = os.read(fd, 4096)
                    except OSError:
                        break
                        
                    if not data:
                        break
                    
                    target = self.master_b if fd == self.master_a else self.master_a
                    
                    dirty_data = self._inject(data)
                    
                    if dirty_data:
                        try:
                            os.write(target, dirty_data)
                        except OSError as e:
                            if self.log_file: self.log(f"Write failed: {e}")
                        
            except KeyboardInterrupt:
                break
            except Exception:
                pass

    def run(self):
        """Blocking run method for standalone use."""
        print(f"Chaos Monkey Active:", flush=True)
        print(f"  Port A: {self.port_a}", flush=True)
        print(f"  Port B: {self.port_b}", flush=True)
        print(f"  Failure modes: drop={self.drop_rate}, corrupt={self.corrupt_rate}, ...", flush=True)
        
        self.log_file = open("chaos_monkey.log", "a", buffering=1)
        self.log_file.write(f"--- START drop={self.drop_rate} corrupt={self.corrupt_rate} ---\n")
        
        self.running = True
        try:
            self._run()
        except KeyboardInterrupt:
            print("\nChaos Monkey Stats:")
            for k, v in self.stats.items():
                print(f"  {k}: {v}")
            print("Stopping...")

    def get_timeline_text(self):
        # Placeholder for rich text - to be filled if rich is available or returned as string
        # Ideally this returns a list or string, and UI formats it.
        # But for compatibility with existing chaos_visual, we return a Rich Text object if possible,
        # or just the list for the caller to format.
        # Im changing chaos_visual to format it, so we can just return the chars
        with self.lock:
            return list(self.timeline)

if __name__ == "__main__":
    drop_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
    corrupt_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    
    monkey = ChaosMonkey(
        drop_rate=drop_rate,
        corrupt_rate=corrupt_rate,
        burst_corrupt_rate=0.01,
        insert_rate=0.005,
        delete_rate=0.005,
        latency_spike_rate=0.01,
        disconnect_rate=0.001,
        baud_rate=0 # Disable baud simulation for C++ tests by default unless requested? C++ tests expect fast pipe? 
        # Actually verify_reliability.py invokes this.
        # C++ tests interact with it. 
        # We should keep baud_rate 0 (unlimited) for C++ tests to avoid slowing them down too much unless intended.
        # Default arg is 115200 in init, but main should probably override or verification suite.
        # The prompt says verification suite runs it.
        # The verification suite doesn't pass baud rate.
        # So I should default baud_rate to 0 in main, or update init to default 0?
        # chaos_visual uses 115200.
        # Let's default init to 0 (infinity/pipe speed) to preserve C++ test behavior, and chaos_visual will explicitly set 115200.
    )
    # Re-instating default init to 0 for baud to match legacy behavior for C++ tests
    monkey.baud_rate = 0 
    
    monkey.run()
