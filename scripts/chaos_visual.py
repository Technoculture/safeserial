#!/usr/bin/env python3
"""
Chaos Visualization - Tests DataBridge ARQ Reliability

This demonstrates the DataBridge protocol's ability to recover from
chaos (drops, corruption) through its ARQ (Automatic Repeat reQuest) mechanism.

Usage:
    uv run --project bindings/python python scripts/chaos_visual.py
"""

import os
import pty
import select
import random
import time
import json
import sys
import threading
from typing import Union
from collections import deque

try:
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    console = Console()
except ImportError:
    print("ERROR: 'rich' is required. Run: uv add rich --project bindings/python")
    sys.exit(1)

# Config
CHAOS_CONFIG = {
    'drop_rate': 0.10,     # 10% drop rate - should still recover!
    'corrupt_rate': 0.05,  # 5% corruption - CRC will catch it
    'baud_rate': 115200,   # Emulate standard UART speed
}

class ChaosBridge:
    """PTY Bridge with fault injection."""
    
    def __init__(self):
        self.master_a, self.slave_a = pty.openpty()
        self.master_b, self.slave_b = pty.openpty()
        self.port_a = os.ttyname(self.slave_a)
        self.port_b = os.ttyname(self.slave_b)
        
        self.running = False
        self.stats = {'ok': 0, 'drop': 0, 'corrupt': 0, 'bytes': 0, 'retries': 0}
        self.timeline = deque(maxlen=60)
        self.seen_packets = set()
        self.lock = threading.Lock()
        
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
                    # print(f"DEBUG: Read {len(data)} bytes")
                    target = self.master_b if fd == self.master_a else self.master_a
                    result = self._inject(data)
                    if result:
                        os.write(target, result)
            except:
                pass
    
    def _inject(self, data: bytes) -> bytes:
        with self.lock:
            # Detect retry (duplicate packet)
            is_retry = data in self.seen_packets
            self.seen_packets.add(data)

            if random.random() < CHAOS_CONFIG['drop_rate']:
                self.stats['drop'] += 1
                self.timeline.append('D')
                return b''  # Drop!
            
            if random.random() < CHAOS_CONFIG['corrupt_rate']:
                self.stats['corrupt'] += 1
                self.timeline.append('C')
                ba = bytearray(data)
                ba[random.randint(0, len(ba)-1)] ^= 0xFF
                return bytes(ba)  # Corrupted!
            
            # Simulate Wire Speed (Baud Rate)
            # 115200 baud ~= 11520 bytes/s (1 start + 8 data + 1 stop = 10 bits/byte)
            # Use a slightly conservative divisor to account for overhead/inter-byte gaps
            bytes_per_sec = CHAOS_CONFIG['baud_rate'] / 10.0
            wire_duration = len(data) / bytes_per_sec
            
            # Sleep to simulate transmission time
            # Only sleep if significant to avoid scheduler trash on single bytes
            if wire_duration > 0.001:
                time.sleep(wire_duration)
            
            if is_retry:
                self.stats['retries'] += 1
                self.timeline.append('R')
            else:
                self.stats['ok'] += 1
                self.timeline.append('O')
                
            self.stats['bytes'] += len(data)
            return data
    
    def get_timeline_text(self) -> Text:
        with self.lock:
            events = list(self.timeline)
        text = Text()
        for e in events:
            if e == 'O':
                text.append("█", style="green")
            elif e == 'D':
                text.append("█", style="red")
            elif e == 'C':
                text.append("█", style="yellow")
            elif e == 'R':
                text.append("█", style="blue")
        return text

import argparse

def generate_payload(target_len: int) -> Union[dict, bytes]:
    # Use simple bytes for small payloads
    if target_len < 100:
        return b'x' * target_len
        
    # Generate a complex JSON structure approx target_len bytes
    items = []
    # Dynamic item count roughly based on length (200 bytes per item approx)
    count = max(5, int(target_len / 200))
    
    for i in range(count):
        items.append({
            "index": i,
            "uuid": f"item-{random.randint(10000,99999)}",
            "values": [random.randint(0, 100) for _ in range(5)],
            "active": random.choice([True, False]),
            "metadata": {
                "created_at": time.time(),
                "source": f"sensor-{random.randint(1,5)}"
            }
        })
    
    base_dict = {
        "test_id": f"TEST-{random.randint(1000,9999)}",
        "description": "Complex JSON payload for ARQ verification",
        "timestamp": time.time(),
        "items": items,
        "padding": "" 
    }
    
    # Calculate current size and add padding to reach target
    curr_len = len(json.dumps(base_dict))
    if curr_len < target_len:
        base_dict["padding"] = "x" * (target_len - curr_len)
        
    return base_dict

def build_display(bridge, status_msg, elapsed, payload_sent, payload_received_curr):
    stats = bridge.stats
    lines = []
    lines.append(f"[cyan]Time:[/] {elapsed:.1f}s")
    lines.append(f"[cyan]Status:[/] {status_msg}")
    lines.append("")
    lines.append(f"[green]OK:[/] {stats['ok']}  [blue]RETRY:[/] {stats['retries']}  [red]DROP:[/] {stats['drop']}  [yellow]CORRUPT:[/] {stats['corrupt']}")
    lines.append("")
    lines.append("[bold]Timeline:[/] [green]█=OK[/] [blue]█=RETRY[/] [red]█=DROP[/] [yellow]█=CORRUPT[/]")
    
    text = Text()
    for line in lines:
        text.append_text(Text.from_markup(line + "\n"))
    text.append_text(bridge.get_timeline_text())
    
    # Add a mini progress bar for payload
    pct = min(100, int(payload_received_curr / payload_sent * 100)) if payload_sent > 0 else 0
    text.append_text(Text.from_markup(f"\n\n[bold]Progress:[/] {pct}% ({payload_received_curr}/{payload_sent} bytes)"))
    
    return Panel(text, title="[bold blue]DataBridge ARQ Chaos Test[/]", border_style="blue")

def main():
    parser = argparse.ArgumentParser(description="DataBridge ARQ Chaos Test")
    parser.add_argument("--len", type=int, default=4096, help="Approximate payload length in bytes")
    parser.add_argument("--drop", type=float, default=0.1, help="Packet drop rate (0.0-1.0)")
    parser.add_argument("--corrupt", type=float, default=0.05, help="Packet corruption rate (0.0-1.0)")
    parser.add_argument("--baud", type=int, default=115200, help="Simulated baud rate")
    args = parser.parse_args()

    # Update global config
    CHAOS_CONFIG['drop_rate'] = args.drop
    CHAOS_CONFIG['corrupt_rate'] = args.corrupt
    CHAOS_CONFIG['baud_rate'] = args.baud

    console.print(Panel.fit("[bold blue]DataBridge ARQ Chaos Test[/]"))
    console.print(f"[yellow]Settings: {args.drop*100:.0f}% Drop, {args.corrupt*100:.0f}% Corrupt, {args.baud} Baud[/]\n")
    
    # Import DataBridge
    try:
        import data_bridge
        console.print("[green]✓ DataBridge imported successfully[/]")
    except ImportError as e:
        console.print(f"[red]✗ Failed to import data_bridge: {e}[/]")
        return
    
    # Create payload
    raw_payload = generate_payload(args.len)
    if isinstance(raw_payload, dict):
        payload_bytes = json.dumps(raw_payload, indent=2).encode()
        console.print(f"[cyan]Payload:[/] {len(payload_bytes)} bytes (Complex JSON)")
    else:
        payload_bytes = raw_payload
        console.print(f"[cyan]Payload:[/] {len(payload_bytes)} bytes (Raw Data)")
    
    # Start bridge
    bridge = ChaosBridge()
    bridge.start()
    console.print(f"[cyan]Bridge:[/] {bridge.port_a} <-> {bridge.port_b}")
    
    # Create DataBridge instances
    sender = data_bridge.DataBridge()
    receiver = data_bridge.DataBridge()
    
    received_data = []
    receive_complete = threading.Event()
    
    def on_receive(data):
        received_data.append(data)
        receive_complete.set()
    
    # Open ports
    console.print("[cyan]Opening DataBridge connections...[/]")
    
    if not sender.open(bridge.port_a, 115200):
        console.print("[red]Failed to open sender[/]")
        return
        
    if not receiver.open(bridge.port_b, 115200, on_receive):
        console.print("[red]Failed to open receiver[/]")
        return
    
    console.print("[green]✓ Connections established[/]")
    console.print("\n[yellow]Starting reliable transfer with chaos injection...[/]\n")
    
    start_time = time.time()
    status_msg = "Sending..."
    send_error = None
    
    # Send in background so we can update display
    def do_send():
        nonlocal status_msg, send_error
        try:
            # Optimization: 250ms timeout (aggressive), 200 byte fragments (efficiency)
            sender.send(payload_bytes, timeout_ms=250, max_retries=20, fragment_size=200)
            status_msg = "Send complete, waiting for receiver..."
        except Exception as e:
            send_error = str(e)
            status_msg = f"Send failed: {e}"
    
    send_thread = threading.Thread(target=do_send)
    send_thread.start()
    
    # Live display
    with Live(console=console, refresh_per_second=10) as live:
        while send_thread.is_alive() or not receive_complete.is_set():
            elapsed = time.time() - start_time
            
            # Get real-time progress
            curr_bytes = 0
            if hasattr(receiver, 'get_received_bytes'):
                curr_bytes = receiver.get_received_bytes()
            
            live.update(build_display(bridge, status_msg, elapsed, len(payload_bytes), curr_bytes))
            
            if elapsed > 60:  # Hard timeout (increased for larger payloads)
                status_msg = "TIMEOUT"
                break
            
            time.sleep(0.1)
    
    send_thread.join(timeout=1)
    elapsed = time.time() - start_time
    
    # Results
    if send_error:
        console.print(f"\n[bold red]✗ SEND FAILED: {send_error}[/]")
    elif received_data:
        stats = bridge.stats
        received_bytes = received_data[0]
        
        # Try diffing
        import difflib
        
        try:
             # Try JSON verify first
             recv_payload = json.loads(received_bytes.decode())
             if isinstance(raw_payload, dict) and recv_payload == raw_payload:
                console.print(f"\n[bold green]✓ SUCCESS! JSON payload verified perfectly![/]")
                console.print(f"[green]Transferred {len(payload_bytes)} bytes in {elapsed:.2f}s[/]")
                console.print(f"[green]Recovered from {stats['drop']} drops and {stats['corrupt']} corruptions[/]")
             else:
                # JSON but mismatch
                 raise ValueError("JSON Mismatch")
                 
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            # Fallback to binary check
            if received_bytes == payload_bytes:
                 console.print(f"\n[bold green]✓ SUCCESS! Binary payload verified perfectly![/]")
                 console.print(f"[green]Transferred {len(payload_bytes)} bytes in {elapsed:.2f}s[/]")
                 console.print(f"[green]Recovered from {stats['drop']} drops and {stats['corrupt']} corruptions[/]")
            else:
                console.print(f"\n[bold red]✗ DATA MISMATCH[/]")
                console.print(f"[red]Sent {len(payload_bytes)} bytes, received {len(received_bytes)} bytes[/]")
                if isinstance(raw_payload, dict):
                     # If we expected JSON but got here, show diff if possible
                     try:
                         recv_payload = json.loads(received_bytes.decode())
                         expected_lines = json.dumps(raw_payload, indent=2).splitlines()
                         received_lines = json.dumps(recv_payload, indent=2).splitlines()
                         diff = difflib.unified_diff(expected_lines, received_lines, fromfile='Sent', tofile='Received', lineterm='')
                         console.print("\n[bold]Diff:[/]")
                         for line in diff:
                             if line.startswith('+'): console.print(f"[green]{line}[/]")
                             elif line.startswith('-'): console.print(f"[red]{line}[/]")
                             elif line.startswith('^'): console.print(f"[yellow]{line}[/]")
                             else: console.print(line)
                     except:
                         pass # Binary mismatch, no diff
                else:
                    # Raw diff limit
                    if len(payload_bytes) < 100:
                         console.print(f"Sent: {payload_bytes.hex()}")
                         console.print(f"Recv: {received_bytes.hex()}")
    else:
        console.print(f"\n[bold red]✗ NO DATA RECEIVED[/]")
    
    # Cleanup
    sender.close()
    receiver.close()
    bridge.stop()

if __name__ == "__main__":
    main()
