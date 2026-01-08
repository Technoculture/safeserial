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

class ChaosMonkey:
    def __init__(self, 
                 drop_rate=0.05,           # 5% packet drop
                 corrupt_rate=0.02,        # 2% bit corruption
                 burst_corrupt_rate=0.01,  # 1% burst corruption (3-5 bytes)
                 insert_rate=0.005,        # 0.5% byte insertion
                 delete_rate=0.005,        # 0.5% byte deletion
                 latency_spike_rate=0.01,  # 1% latency spike (50-200ms)
                 disconnect_rate=0.001):   # 0.1% temporary disconnect (100-500ms)
        
        self.drop_rate = drop_rate
        self.corrupt_rate = corrupt_rate
        self.burst_corrupt_rate = burst_corrupt_rate
        self.insert_rate = insert_rate
        self.delete_rate = delete_rate
        self.latency_spike_rate = latency_spike_rate
        self.disconnect_rate = disconnect_rate
        
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.name_a = os.ttyname(self.slave_a)
        self.name_b = os.ttyname(self.slave_b)
        
        print(f"Chaos Monkey Active:", flush=True)
        print(f"  Port A: {self.name_a}", flush=True)
        print(f"  Port B: {self.name_b}", flush=True)
        print(f"  Failure modes: drop={drop_rate}, corrupt={corrupt_rate}, "
              f"burst={burst_corrupt_rate}, insert={insert_rate}, "
              f"delete={delete_rate}, latency={latency_spike_rate}, "
              f"disconnect={disconnect_rate}", flush=True)
        
        self.log_file = open("chaos_monkey.log", "a", buffering=1)
        self.log_file.write(f"--- START drop={drop_rate} corrupt={corrupt_rate} ---\n")
        
        # Stats
        self.stats = {
            'total_bytes': 0,
            'dropped_packets': 0,
            'corrupted_bits': 0,
            'burst_corruptions': 0,
            'inserted_bytes': 0,
            'deleted_bytes': 0,
            'latency_spikes': 0,
            'disconnects': 0,
        }

    def log(self, msg):
        self.log_file.write(f"{time.time()}: {msg}\n")

    def inject_faults(self, data: bytes) -> bytes:
        """Apply all failure modes to the data."""
        if not data:
            return data
        
        # 1. Packet Drop (entire packet lost)
        if random.random() < self.drop_rate:
            self.log(f"[CHAOS] DROPPED {len(data)} bytes")
            self.stats['dropped_packets'] += 1
            return b""
        
        data_list = bytearray(data)
        
        # 2. Single Bit Corruption
        if random.random() < self.corrupt_rate:
            idx = random.randint(0, len(data_list) - 1)
            bit = random.randint(0, 7)
            data_list[idx] ^= (1 << bit)
            self.log(f"[CHAOS] BIT_FLIP byte[{idx}] bit[{bit}]")
            self.stats['corrupted_bits'] += 1
        
        # 3. Burst Corruption (3-5 consecutive bytes)
        if random.random() < self.burst_corrupt_rate and len(data_list) > 5:
            start = random.randint(0, len(data_list) - 5)
            burst_len = random.randint(3, 5)
            for i in range(burst_len):
                data_list[start + i] = random.randint(0, 255)
            self.log(f"[CHAOS] BURST_CORRUPT bytes[{start}:{start+burst_len}]")
            self.stats['burst_corruptions'] += 1
        
        # 4. Byte Insertion (1-3 garbage bytes)
        if random.random() < self.insert_rate:
            idx = random.randint(0, len(data_list))
            insert_len = random.randint(1, 3)
            garbage = bytes([random.randint(0, 255) for _ in range(insert_len)])
            data_list = data_list[:idx] + bytearray(garbage) + data_list[idx:]
            self.log(f"[CHAOS] INSERTED {insert_len} bytes at {idx}")
            self.stats['inserted_bytes'] += insert_len
        
        # 5. Byte Deletion (1-2 bytes lost)
        if random.random() < self.delete_rate and len(data_list) > 3:
            idx = random.randint(0, len(data_list) - 2)
            delete_len = random.randint(1, 2)
            deleted = data_list[idx:idx+delete_len]
            data_list = data_list[:idx] + data_list[idx+delete_len:]
            self.log(f"[CHAOS] DELETED {delete_len} bytes at {idx}")
            self.stats['deleted_bytes'] += delete_len
        
        # 6. Latency Spike
        if random.random() < self.latency_spike_rate:
            delay = random.uniform(0.05, 0.2)  # 50-200ms
            self.log(f"[CHAOS] LATENCY_SPIKE {delay*1000:.0f}ms")
            self.stats['latency_spikes'] += 1
            time.sleep(delay)
        
        # 7. Connection Interruption (drop data + delay)
        if random.random() < self.disconnect_rate:
            delay = random.uniform(0.1, 0.5)  # 100-500ms
            self.log(f"[CHAOS] DISCONNECT {delay*1000:.0f}ms")
            self.stats['disconnects'] += 1
            time.sleep(delay)
            return b""  # Drop the packet during "disconnect"
        
        self.stats['total_bytes'] += len(data_list)
        return bytes(data_list)

    def run(self):
        try:
            while True:
                r, _, _ = select.select([self.master_a, self.master_b], [], [])
                
                for fd in r:
                    try:
                        data = os.read(fd, 1024)
                    except OSError:
                        break
                        
                    if not data:
                        break
                    
                    target = self.master_b if fd == self.master_a else self.master_a
                    
                    dirty_data = self.inject_faults(data)
                    
                    if dirty_data:
                        try:
                            os.write(target, dirty_data)
                        except OSError as e:
                            self.log(f"Write failed: {e}")
                        
        except KeyboardInterrupt:
            print("\nChaos Monkey Stats:")
            for k, v in self.stats.items():
                print(f"  {k}: {v}")
            print("Stopping...")

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
    )
    monkey.run()
