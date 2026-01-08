#!/usr/bin/env python3
"""
Chaos Visualization - Tests DataBridge ARQ Reliability

Usage:
    uv run --project bindings/python python scripts/chaos_visual.py
    
    # Cross-language examples:
    python scripts/chaos_visual.py --sender node --receiver python
    python scripts/chaos_visual.py --sender cpp --receiver cpp --items 50
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
import subprocess
import shutil
import re
import signal
from typing import Union
from collections import deque

try:
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn
    console = Console()
except ImportError:
    print("ERROR: 'rich' is required. Run: uv add rich --project bindings/python")
    sys.exit(1)

from chaos_monkey import ChaosMonkey

# --- Paths (Mirrors verify_reliability.py) ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
TEST_BIN = os.path.join(BUILD_DIR, "tests", "reliability_test")

NODE_BINDING_ROOT = os.path.join(PROJECT_ROOT, "bindings", "node")
NODE_SENDER = os.path.join(NODE_BINDING_ROOT, "scripts", "sender.js")
NODE_RECEIVER = os.path.join(NODE_BINDING_ROOT, "scripts", "receiver.js")

PYTHON_BINDING_ROOT = os.path.join(PROJECT_ROOT, "bindings", "python")
PYTHON_SENDER = os.path.join(PYTHON_BINDING_ROOT, "scripts", "sender.py")
PYTHON_RECEIVER = os.path.join(PYTHON_BINDING_ROOT, "scripts", "receiver.py")

# --- Helper Functions ---

def get_agent_command(lang, role, port, item_count=20):
    if lang == "cpp":
        args = [TEST_BIN, port, role]
        if role == "sender": args.append(str(item_count))
        return args, PROJECT_ROOT
    elif lang == "node":
        script = NODE_SENDER if role == "sender" else NODE_RECEIVER
        args = ["node", script, port]
        if role == "sender": args.append(str(item_count))
        return args, PROJECT_ROOT
    elif lang == "python":
        script = PYTHON_SENDER if role == "sender" else PYTHON_RECEIVER
        uv = shutil.which("uv")
        args = [uv, "run", "--project", PYTHON_BINDING_ROOT, "python", script, port]
        if role == "sender": args.append(str(item_count))
        return args, PROJECT_ROOT
    elif lang == "internal":
        return None, None
    raise ValueError(f"Unknown language: {lang}")

def build_display(bridge, status_msg, elapsed, total_items, current_items, last_log):
    stats = bridge.stats
    lines = []
    lines.append(f"[cyan]Time:[/] {elapsed:.1f}s")
    lines.append(f"[cyan]Status:[/] {status_msg}")
    lines.append(f"[dim]{last_log}[/]")
    lines.append("")
    lines.append(f"[green]OK:[/] {stats['ok']}  [blue]RETRY:[/] {stats['retries']}  [red]DROP:[/] {stats['drop']}  [yellow]CORRUPT:[/] {stats['corrupt']}")
    lines.append(f"[dim]Detailed: PktDrop={stats['dropped_packets']} BitFlip={stats['corrupted_bits']} Burst={stats['burst_corruptions']} Ins={stats['inserted_bytes']} Del={stats['deleted_bytes']} Latency={stats['latency_spikes']} Disc={stats['disconnects']}[/]")
    lines.append("")
    lines.append("[bold]Timeline:[/] [green]█=OK[/] [blue]█=RETRY[/] [red]█=DROP[/] [yellow]█=CORRUPT[/]")
    
    text = Text()
    for line in lines:
        text.append_text(Text.from_markup(line + "\n"))
    
    # Timeline
    timeline_chars = bridge.get_timeline_text()
    timeline_text = Text()
    for e in timeline_chars:
        if e == 'O': timeline_text.append("█", style="green")
        elif e == 'D': timeline_text.append("█", style="red")
        elif e == 'C': timeline_text.append("█", style="yellow")
        elif e == 'R': timeline_text.append("█", style="blue")
    text.append_text(timeline_text)
    
    # Progress Bar
    pct = 0
    if total_items > 0:
        pct = min(100, int(current_items / total_items * 100))
        
    bar_width = 40
    filled = int(bar_width * pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    text.append_text(Text.from_markup(f"\n\n[bold]Progress:[/] {pct}% [{bar}] ({current_items}/{total_items} items)"))
    
    return Panel(text, title="[bold blue]DataBridge ARQ Chaos Test[/]", border_style="blue")

def main():
    parser = argparse.ArgumentParser(description="DataBridge ARQ Chaos Test")
    parser.add_argument("--sender", choices=["internal", "cpp", "node", "python"], default="internal", help="Sender type")
    parser.add_argument("--receiver", choices=["internal", "cpp", "node", "python"], default="internal", help="Receiver type")
    parser.add_argument("--items", type=int, default=50, help="Number of items to send")
    parser.add_argument("--drop", type=float, default=0.1, help="Packet drop rate")
    parser.add_argument("--corrupt", type=float, default=0.05, help="Packet corruption rate")
    parser.add_argument("--baud", type=int, default=115200, help="Simulated baud rate")
    
    # Advanced Chaos Options
    parser.add_argument("--burst", type=float, default=0.01, help="Burst corruption rate")
    parser.add_argument("--insert", type=float, default=0.005, help="Byte insertion rate")
    parser.add_argument("--delete", type=float, default=0.005, help="Byte deletion rate")
    parser.add_argument("--latency", type=float, default=0.01, help="Latency spike rate")
    parser.add_argument("--disconnect", type=float, default=0.001, help="Disconnect rate")
    
    # Ignored legacy args for compatibility if any wrapper passes them
    parser.add_argument("--len", type=int, default=4096, help="Ignored in external mode")

    args = parser.parse_args()

    # In internal mode, we force symmetry if one is internal
    if args.sender == "internal" and args.receiver != "internal":
        args.receiver = "internal" # Mixed internal/external not supported easily yet
    if args.receiver == "internal" and args.sender != "internal":
        args.sender = "internal"

    console.print(Panel.fit("[bold blue]Cross-Language Chaos Visualizer[/]"))
    console.print(f"[yellow]Config: {args.sender.upper()} -> {args.receiver.upper()} | {args.drop*100:.0f}% Drop, {args.corrupt*100:.0f}% Corrupt[/]")
    console.print(f"[yellow]Advanced: Burst={args.burst*100:.1f}%, Ins/Del={args.insert*100:.1f}%, Latency={args.latency*100:.1f}%, Disc={args.disconnect*100:.1f}%[/]\n")

    # Start Bridge
    bridge = ChaosMonkey(
        drop_rate=args.drop, 
        corrupt_rate=args.corrupt, 
        baud_rate=args.baud,
        burst_corrupt_rate=args.burst,
        insert_rate=args.insert,
        delete_rate=args.delete,
        latency_spike_rate=args.latency,
        disconnect_rate=args.disconnect
    )
    bridge.start()
    console.print(f"[cyan]Bridge Active:[/] {bridge.port_a} <-> {bridge.port_b}")

    sender_proc = None
    recv_proc = None
    
    # State for UI
    ui_state = {
        "status": "Initializing...",
        "items_sent": 0,
        "items_recv": 0,
        "last_log": "",
        "complete": False
    }

    def monitor_stream(stream, prefix):
        """Reads stdout from agents and updates stats."""
        for line in iter(stream.readline, ''):
            line = line.strip()
            if not line: continue
            
            ui_state["last_log"] = f"{prefix}: {line[-50:]}" # tail log
            
            # Simple heuristic parsing (matches standardize logs from verify_reliability agents)
            # Node/Py: [RECEIVER] Got: Packet-X (Total: N)
            # C++: [RECEIVER] Completed Item X (Total: N)
            if "Total:" in line:
                try:
                    # Extract number after Total:
                    match = re.search(r"Total:\s*(\d+)", line)
                    if match:
                        ui_state["items_recv"] = int(match.group(1))
                except: pass
            
            if "TEST COMPLETE" in line:
                ui_state["status"] = "Sender Finished"

    try:
        if args.sender == "internal":
            # --- INTERNAL MODE (Python Only, High Fidelity) ---
            import data_bridge
            
            sender = data_bridge.DataBridge()
            receiver = data_bridge.DataBridge()
            
            recv_list = []
            def on_recv(d):
                recv_list.append(d)
                ui_state["items_recv"] += 1
                ui_state["last_log"] = f"RX: {len(d)} bytes"
            
            sender.open(bridge.port_a, 115200)
            receiver.open(bridge.port_b, 115200, on_recv)
            
            # Generate dummy payload packets
            payloads = [f"Ticket-{i}".encode() for i in range(args.items)]
            
            def internal_send():
                for i, p in enumerate(payloads):
                    ui_state["status"] = f"Sending Item {i+1}/{args.items}"
                    try:
                        sender.send(p)
                        ui_state["items_sent"] += 1
                    except Exception as e:
                        ui_state["last_log"] = f"Send Err: {e}"
                    time.sleep(0.05)
                ui_state["status"] = "Internal Send Complete"
                
            t = threading.Thread(target=internal_send)
            t.start()
            
            # Loop UI
            start_time = time.time()
            with Live(console=console, refresh_per_second=10) as live:
                while ui_state["items_recv"] < args.items:
                    elapsed = time.time() - start_time
                    live.update(build_display(bridge, ui_state["status"], elapsed, args.items, ui_state["items_recv"], ui_state["last_log"]))
                    
                    if elapsed > args.items * 2: # Timeout
                        ui_state["status"] = "TIMEOUT"
                        break
                    time.sleep(0.1)
            
            t.join()
            sender.close()
            receiver.close()

        else:
            # --- EXTERNAL MODE (Subprocesses) ---
            
            # Launch Receiver
            rcmd, rcwd = get_agent_command(args.receiver, "receiver", bridge.port_b)
            recv_proc = subprocess.Popen(rcmd, cwd=rcwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, preexec_fn=os.setsid)
            t_recv = threading.Thread(target=monitor_stream, args=(recv_proc.stdout, f"[{args.receiver.upper()}]"))
            t_recv.daemon = True
            t_recv.start()
            
            # Launch Sender
            scmd, scwd = get_agent_command(args.sender, "sender", bridge.port_a, args.items)
            sender_proc = subprocess.Popen(scmd, cwd=scwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, preexec_fn=os.setsid)
            t_send = threading.Thread(target=monitor_stream, args=(sender_proc.stdout, f"[{args.sender.upper()}]"))
            t_send.daemon = True
            t_send.start()
            
            ui_state["status"] = "Running external agents..."
            
            start_time = time.time()
            with Live(console=console, refresh_per_second=10) as live:
                while True:
                    elapsed = time.time() - start_time
                    
                    # Update UI
                    live.update(build_display(bridge, ui_state["status"], elapsed, args.items, ui_state["items_recv"], ui_state["last_log"]))
                    
                    # Exit conditions
                    if ui_state["items_recv"] >= args.items:
                        ui_state["status"] = "SUCCESS"
                        break
                        
                    if sender_proc.poll() is not None:
                        if sender_proc.returncode != 0:
                            ui_state["status"] = "SENDER FAILED"
                            break
                        # Sender done, wait a bit for receiver
                    
                    if elapsed > (args.items * 1.5) + 10:
                        ui_state["status"] = "TIMEOUT"
                        break
                        
                    time.sleep(0.1)
            
            # Cleanup
            if sender_proc: os.killpg(os.getpgid(sender_proc.pid), signal.SIGTERM)
            if recv_proc: os.killpg(os.getpgid(recv_proc.pid), signal.SIGTERM)
            
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
        console.print(f"\n[bold]Final Status: {ui_state['status']}[/]")

if __name__ == "__main__":
    main()
