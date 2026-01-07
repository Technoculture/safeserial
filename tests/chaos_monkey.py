
import os
import pty
import select
import random
import time
import sys

class ChaosMonkey:
    def __init__(self, drop_rate=0.01, corrupt_rate=0.01): # 1% drop, 1% corrupt
        self.drop_rate = drop_rate
        self.corrupt_rate = corrupt_rate
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.name_a = os.ttyname(self.slave_a)
        self.name_b = os.ttyname(self.slave_b)
        print(f"Chaos Link Active:")
        print(f"  Port A: {self.name_a}")
        print(f"  Port B: {self.name_b}")

    def corrupt(self, data: bytes) -> bytes:
        if not data: return data
        
        # Packet Drop
        if random.random() < self.drop_rate:
            print(f"[CHAOS] DROPPED {len(data)} bytes")
            return b""
            
        # Bit Corruption
        if random.random() < self.corrupt_rate:
            data_list = bytearray(data)
            # Flip a random bit in a random byte
            idx = random.randint(0, len(data_list) - 1)
            bit = random.randint(0, 7)
            data_list[idx] ^= (1 << bit)
            print(f"[CHAOS] CORRUPTED byte {idx}")
            return bytes(data_list)
            
        return data

    def run(self):
        try:
            while True:
                r, _, _ = select.select([self.master_a, self.master_b], [], [])
                
                for fd in r:
                    try:
                        data = os.read(fd, 1024)
                    except OSError:
                        break
                        
                    if not data: break
                    
                    target = self.master_b if fd == self.master_a else self.master_a
                    
                    clean_len = len(data)
                    dirty_data = self.corrupt(data)
                    
                    if dirty_data:
                        os.write(target, dirty_data)
                        
        except KeyboardInterrupt:
            print("Stopping Chaos Monkey...")

if __name__ == "__main__":
    drop_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
    corrupt_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    
    monkey = ChaosMonkey(drop_rate, corrupt_rate)
    monkey.run()
