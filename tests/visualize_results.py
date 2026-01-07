
import matplotlib.pyplot as plt
import sys
import re

def parse_log(log_content):
    events = []
    chaos_events = []
    
    # Simple discrete time model: each log line is a tick? 
    # Or just index events. Let's index events.
    
    event_idx = 0
    completed_items = 0
    
    for line in log_content.splitlines():
        event_idx += 1
        
        if "[CHAOS] DROPPED" in line:
            chaos_events.append((event_idx, "DROP"))
        elif "[CHAOS] CORRUPTED" in line:
            chaos_events.append((event_idx, "CORRUPT"))
        elif "Completed Item" in line:
            completed_items += 1
            events.append((event_idx, completed_items))
            
    return events, chaos_events

def plot_results(log_content, output_file="reliability_plot.png"):
    data_events, chaos_events = parse_log(log_content)
    
    if not data_events:
        print("No data events found to plot")
        return

    x_data = [x[0] for x in data_events]
    y_data = [x[1] for x in data_events]
    
    plt.figure(figsize=(10, 6))
    
    # Plot Successful Transfers
    plt.plot(x_data, y_data, label=f"Successful API Calls ({y_data[-1]} Total)", color='green', linewidth=2)
    
    # Plot Chaos
    drops_x = [x[0] for x in chaos_events if x[1] == "DROP"]
    drops_y = [0] * len(drops_x) # Plot at bottom
    
    corrupt_x = [x[0] for x in chaos_events if x[1] == "CORRUPT"]
    corrupt_y = [0] * len(corrupt_x)
    
    if drops_x:
        plt.scatter(drops_x, [y_data[-1] * 0.05] * len(drops_x), marker='x', color='red', label='Packet Drops', alpha=0.6)
        
    if corrupt_x:
        plt.scatter(corrupt_x, [y_data[-1] * 0.1] * len(corrupt_x), marker='*', color='orange', label='Bit Corruption', alpha=0.6, s=100)

    plt.title("System Resilience: Valid Transfers vs Injected Faults")
    plt.xlabel("Test Event Timeline")
    plt.ylabel("Cumulative Successful Transactions")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Generated plot: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize_results.py <logfile>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        content = f.read()
        
    plot_results(content)
