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
                    target = self.master_b if fd == self.master_a else self.master_a
                    result = self._inject(data)
                    if result:
                        os.write(target, result)
            except:
                pass
    
    def _inject(self, data: bytes) -> bytes:
        with self.lock:
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
            
            time.sleep(CHAOS_CONFIG['latency_ms'] / 1000)
            self.stats['ok'] += 1
            self.stats['bytes'] += len(data)
            self.timeline.append('O')
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
        return text

def generate_payload() -> dict:
    return {
        "id": f"test-{random.randint(1000,9999)}",
        "timestamp": time.time(),
        "msg": "DataBridge ARQ Test",
        "checksum": random.randint(0, 1000000),
    }

def build_display(bridge, status_msg, elapsed, payload_sent, payload_received):
    stats = bridge.stats
    lines = []
    lines.append(f"[cyan]Time:[/] {elapsed:.1f}s")
    lines.append(f"[cyan]Status:[/] {status_msg}")
    lines.append("")
    lines.append(f"[green]OK:[/] {stats['ok']}  [red]DROP:[/] {stats['drop']}  [yellow]CORRUPT:[/] {stats['corrupt']}")
    lines.append("")
    lines.append("[bold]Timeline:[/] [green]█=OK[/] [red]█=DROP[/] [yellow]█=CORRUPT[/]")
    
    text = Text()
    for line in lines:
        text.append_text(Text.from_markup(line + "\n"))
    text.append_text(bridge.get_timeline_text())
    
    return Panel(text, title="[bold blue]DataBridge ARQ Chaos Test[/]", border_style="blue")

def main():
    console.print(Panel.fit("[bold blue]DataBridge ARQ Chaos Test[/]"))
    console.print("[yellow]Testing that DataBridge recovers from 10% drop + 5% corruption[/]\n")
    
    # Import DataBridge
    try:
        import data_bridge
        console.print("[green]✓ DataBridge imported successfully[/]")
    except ImportError as e:
        console.print(f"[red]✗ Failed to import data_bridge: {e}[/]")
        return
    
    # Create payload
    payload = generate_payload()
    payload_bytes = json.dumps(payload).encode()
    console.print(f"[cyan]Payload:[/] {len(payload_bytes)} bytes")
    
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
    console.print("\n" + "=" * 50)
    console.print("[bold]RESULT[/]")
    console.print("=" * 50)
    
    stats = bridge.stats
    console.print(f"\n[cyan]Chaos Stats:[/]")
    console.print(f"  Packets OK:       [green]{stats['ok']}[/]")
    console.print(f"  Packets DROPPED:  [red]{stats['drop']}[/]")
    console.print(f"  Packets CORRUPTED:[yellow]{stats['corrupt']}[/]")
    
    if send_error:
        console.print(f"\n[bold red]✗ SEND FAILED: {send_error}[/]")
    elif received_data:
        received_bytes = received_data[0]
        if received_bytes == payload_bytes:
            console.print(f"\n[bold green]✓ SUCCESS! Data integrity verified despite chaos![/]")
            console.print(f"[green]Transferred {len(payload_bytes)} bytes in {elapsed:.2f}s[/]")
            console.print(f"[green]Recovered from {stats['drop']} drops and {stats['corrupt']} corruptions[/]")
        else:
            console.print(f"\n[bold red]✗ DATA MISMATCH[/]")
            console.print(f"[red]Sent {len(payload_bytes)} bytes, received {len(received_bytes)} bytes[/]")
    else:
        console.print(f"\n[bold red]✗ NO DATA RECEIVED[/]")
    
    console.print("\n[bold]Timeline:[/]")
    console.print(bridge.get_timeline_text())
    
    # Cleanup
    sender.close()
    receiver.close()
    bridge.stop()

if __name__ == "__main__":
    main()
