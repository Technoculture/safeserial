
import matplotlib.pyplot as plt
import sys
import re
import numpy as np

def parse_logs(log_content):
    events = []
    
    # Matches float_ts: msg
    pattern = re.compile(r"(\d+\.\d+): (.*)")
    
    base_time = None
    
    # Track cycle count and item offsets
    cycle_count = -1
    item_offset = 0
    
    lines = log_content.splitlines()
    for line in lines:
        m = pattern.search(line)
        if not m: continue
        
        ts = float(m.group(1))
        msg = m.group(2)
        
        if base_time is None: base_time = ts
        rel_ts = ts - base_time
        
        # Detect new cycle to offset item IDs
        if "Starting stress test" in msg:
            cycle_count += 1
            item_offset = cycle_count * 20
        
        # Extract events
        if "Sending Item" in msg:
            m_item = re.search(r"Item (\d+)", msg)
            if m_item:
                idx = int(m_item.group(1)) + item_offset
                events.append({"ts": rel_ts, "type": "START", "id": idx})
        elif "Verified" in msg or "Sent Successfully" in msg:
            m_item = re.search(r"Item (\d+)", msg)
            if m_item:
                idx = int(m_item.group(1)) + item_offset
                events.append({"ts": rel_ts, "type": "SUCCESS", "id": idx})
        elif "Timeout/NACK" in msg:
            m_item = re.search(r"Item (\d+)", msg)
            if m_item:
                idx = int(m_item.group(1)) + item_offset
                events.append({"ts": rel_ts, "type": "RETRY", "id": idx})
        elif "DROPPED" in msg:
             # Associate with the likely current item offset
             events.append({"ts": rel_ts, "type": "DROP", "id": item_offset}) 
        elif "CORRUPTED" in msg:
             events.append({"ts": rel_ts, "type": "CORRUPT", "id": item_offset})

    return events

def plot_xkcd(events, output="reliability_plot.png"):
    plt.xkcd()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    success_ts = [e["ts"] for e in events if e["type"] == "SUCCESS"]
    success_id = [e["id"] for e in events if e["type"] == "SUCCESS"]
    
    retry_ts = [e["ts"] for e in events if e["type"] == "RETRY"]
    retry_id = [e["id"] for e in events if e["type"] == "RETRY"]
    
    drop_ts = [e["ts"] for e in events if e["type"] == "DROP"]
    drop_id = [e["id"] for e in events if e["type"] == "DROP"]
    
    corrupt_ts = [e["ts"] for e in events if e["type"] == "CORRUPT"]
    corrupt_id = [e["id"] for e in events if e["type"] == "CORRUPT"]

    print(f"Plotting: {len(success_ts)} Success markers found.")

    if success_ts:
        ax.plot(success_ts, success_id, 'g-', alpha=0.3)
        ax.scatter(success_ts, success_id, color='green', marker='o', s=50, label="Confirmed Delivery", zorder=5)
    
    if retry_ts:
        ax.scatter(retry_ts, retry_id, color='orange', marker='x', s=100, label="Protocol Healing", zorder=4)
    
    # Offset chaos markers slightly to be visible even if many on same item
    if drop_ts:
        ax.scatter(drop_ts, [i + 0.5 for i in drop_id], color='red', marker='v', s=80, label="Packet Loss", alpha=0.6)
    
    if corrupt_ts:
        ax.scatter(corrupt_ts, [i - 0.5 for i in corrupt_id], color='purple', marker='*', s=120, label="Bit Inversion", alpha=0.6)

    ax.set_title("Data Bridge Reliability Timeline")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Transaction Sequence (Cumulative)")
    ax.legend(loc='upper left', frameon=False)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    with open(sys.argv[1], 'r') as f: content = f.read()
    events = parse_logs(content)
    if not events:
        print("No events found in logs!")
        sys.exit(0)
        
    plot_xkcd(events, "reliability_plot.png")
