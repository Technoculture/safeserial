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
    'latency_ms': 10,
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
            
            # Reduce latency impact on fragmented reads
            # checking length to avoid excessive sleep on tiny reads
            if len(data) > 10: 
                time.sleep(CHAOS_CONFIG['latency_ms'] / 1000)
            
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

def generate_payload() -> dict:
    # Generate a complex JSON structure approx 1KB to test meaningful data transfer
    items = []
    for i in range(15):
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
    
    return {
        "test_id": f"TEST-{random.randint(1000,9999)}",
        "description": "Complex JSON payload for ARQ verification",
        "timestamp": time.time(),
        "items": items,
        "padding": "x" * 100 # Adjust to ensure we hit ~1KB mark 
    }

def build_display(bridge, status_msg, elapsed, payload_sent, payload_received):
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
    pct = min(100, int(payload_received / payload_sent * 100)) if payload_sent > 0 else 0
    text.append_text(Text.from_markup(f"\n\n[bold]Progress:[/] {pct}% ({payload_received}/{payload_sent} bytes)"))
    
    return Panel(text, title="[bold blue]DataBridge ARQ Chaos Test[/]", border_style="blue")

def main():
    console.print(Panel.fit("[bold blue]DataBridge ARQ Chaos Test[/]"))
    console.print(f"[yellow]Testing that DataBridge recovers from {CHAOS_CONFIG['drop_rate']*100:.0f}% drop + {CHAOS_CONFIG['corrupt_rate']*100:.0f}% corruption[/]\n")
    
    # Import DataBridge
    try:
        import data_bridge
        console.print("[green]✓ DataBridge imported successfully[/]")
    except ImportError as e:
        console.print(f"[red]✗ Failed to import data_bridge: {e}[/]")
        return
    
    # Create payload
    payload = generate_payload()
    payload_bytes = json.dumps(payload, indent=2).encode() # Pretty print for diff readability
    console.print(f"[cyan]Payload:[/] {len(payload_bytes)} bytes (Complex JSON)")
    
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
            sender.send(payload_bytes, timeout_ms=500, max_retries=20)
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
            live.update(build_display(bridge, status_msg, elapsed, len(payload_bytes), 
                                      len(received_data[0]) if received_data else 0))
            
            if elapsed > 30:  # Hard timeout
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
             recv_payload = json.loads(received_bytes.decode())
             if recv_payload == payload:
                console.print(f"\n[bold green]✓ SUCCESS! JSON payload verified perfectly![/]")
                console.print(f"[green]Transferred {len(payload_bytes)} bytes in {elapsed:.2f}s[/]")
                console.print(f"[green]Recovered from {stats['drop']} drops and {stats['corrupt']} corruptions[/]")
             else:
                console.print(f"\n[bold red]✗ JSON MISMATCH[/]")
                # Compute diff
                expected_lines = json.dumps(payload, indent=2).splitlines()
                received_lines = json.dumps(recv_payload, indent=2).splitlines()
                
                diff = difflib.unified_diff(expected_lines, received_lines, fromfile='Sent', tofile='Received', lineterm='')
                console.print("\n[bold]Diff:[/]")
                for line in diff:
                    if line.startswith('+'):
                        console.print(f"[green]{line}[/]")
                    elif line.startswith('-'):
                        console.print(f"[red]{line}[/]")
                    elif line.startswith('^'):
                        console.print(f"[yellow]{line}[/]")
                    else:
                        console.print(line)
        except json.JSONDecodeError:
            console.print(f"\n[bold red]✗ FAILED TO DECODE RECEIVED JSON[/]")
            console.print(f"[red]Sent {len(payload_bytes)} bytes, received {len(received_bytes)} bytes[/]")
            if received_bytes != payload_bytes:
                 console.print("[red]Binary mismatch![/]")
    else:
        console.print(f"\n[bold red]✗ NO DATA RECEIVED[/]")
    
    # Cleanup
    sender.close()
    receiver.close()
    bridge.stop()

if __name__ == "__main__":
    main()
