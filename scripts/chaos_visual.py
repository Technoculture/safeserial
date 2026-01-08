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
import argparse
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

from chaos_monkey import ChaosMonkey

# Config
CHAOS_CONFIG = {
    'drop_rate': 0.10,     # 10% drop rate - should still recover!
    'corrupt_rate': 0.05,  # 5% corruption - CRC will catch it
    'baud_rate': 115200,   # Emulate standard UART speed
}

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
    
    # Format timeline from ChaosMonkey (returns list of chars)
    timeline_chars = bridge.get_timeline_text()
    timeline_text = Text()
    for e in timeline_chars:
        if e == 'O':
            timeline_text.append("█", style="green")
        elif e == 'D':
            timeline_text.append("█", style="red")
        elif e == 'C':
            timeline_text.append("█", style="yellow")
        elif e == 'R':
            timeline_text.append("█", style="blue")
            
    text.append_text(timeline_text)
    
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
    # Map CLI args to ChaosMonkey args
    # Note: ChaosMonkey has more modes than exposed in this CLI, but we set the basic ones.
    # We could expose more, but let's keep it simple for now, relying on defaults for burst/etc.
    bridge = ChaosMonkey(
        drop_rate=args.drop,
        corrupt_rate=args.corrupt,
        baud_rate=args.baud
    )
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
