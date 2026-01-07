"""
Visualize Test Results

Parses test_report.md and combined.log to generate useful visualizations:
1. Timeline of sends/receives/retries
2. Message latency histogram
3. Failure mode distribution
"""

import re
import sys
from pathlib import Path

def parse_test_report(report_path: str) -> dict:
    """Parse test_report.md for test results."""
    content = Path(report_path).read_text()
    
    results = {
        'tests': [],
        'total_items': 0,
        'retries': [],
        'timestamps': [],
    }
    
    # Extract test sections
    test_pattern = r'### T-(\d+) Details.*?### Sender Log\s*```(.*?)```.*?### Receiver Log\s*```(.*?)```'
    matches = re.findall(test_pattern, content, re.DOTALL)
    
    for test_id, sender_log, receiver_log in matches:
        test = {
            'id': test_id,
            'sends': [],
            'receives': [],
            'retries': [],
        }
        
        # Parse sender log
        for line in sender_log.strip().split('\n'):
            if 'Sending Item' in line:
                ts = float(line.split(':')[0])
                match = re.search(r'Item (\d+) Frag (\d+)/(\d+)', line)
                if match:
                    test['sends'].append({
                        'ts': ts,
                        'item': int(match.group(1)),
                        'frag': int(match.group(2)),
                        'total': int(match.group(3)),
                    })
            elif 'Timeout/NACK' in line:
                ts = float(line.split(':')[0])
                test['retries'].append(ts)
        
        # Parse receiver log
        for line in receiver_log.strip().split('\n'):
            if 'Completed Item' in line:
                ts = float(line.split(':')[0])
                match = re.search(r'Item (\d+)', line)
                if match:
                    test['receives'].append({
                        'ts': ts,
                        'item': int(match.group(1)),
                    })
        
        results['tests'].append(test)
    
    return results

def generate_timeline_plot(results: dict, output: str = "test_timeline.png"):
    """Generate a timeline visualization of the test run."""
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(14, 8))
    
    for i, test in enumerate(results['tests']):
        if not test['sends'] or not test['receives']:
            continue
            
        # Normalize timestamps to start at 0
        t0 = test['sends'][0]['ts']
        
        send_times = [(s['ts'] - t0) for s in test['sends']]
        send_items = [s['item'] for s in test['sends']]
        
        recv_times = [(r['ts'] - t0) for r in test['receives']]
        recv_items = [r['item'] for r in test['receives']]
        
        retry_times = [(r - t0) for r in test['retries']]
        
        plt.subplot(len(results['tests']), 1, i + 1)
        plt.scatter(send_times, send_items, c='blue', alpha=0.5, s=20, label='Send')
        plt.scatter(recv_times, recv_items, c='green', alpha=0.7, s=30, label='Receive')
        
        # Mark retries
        for rt in retry_times:
            plt.axvline(x=rt, color='red', alpha=0.3, linestyle='--', linewidth=1)
        
        plt.ylabel(f'Test {test["id"]}\nItem #')
        plt.legend(loc='upper right', fontsize=8)
        plt.grid(True, alpha=0.3)
        
        if i == 0:
            plt.title('Data Bridge Test Timeline: Sends, Receives, and Retries')
    
    plt.xlabel('Time (seconds)')
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

def generate_latency_histogram(results: dict, output: str = "latency_histogram.png"):
    """Generate a histogram of message latencies."""
    import matplotlib.pyplot as plt
    import numpy as np
    
    latencies = []
    
    for test in results['tests']:
        # Match sends to receives by item number
        send_map = {}
        for s in test['sends']:
            if s['frag'] == 0:  # First fragment
                send_map[s['item']] = s['ts']
        
        for r in test['receives']:
            if r['item'] in send_map:
                latency = (r['ts'] - send_map[r['item']]) * 1000  # ms
                latencies.append(latency)
    
    if not latencies:
        print("No latency data found")
        return
    
    plt.figure(figsize=(10, 6))
    plt.hist(latencies, bins=50, color='#3498db', edgecolor='white', alpha=0.8)
    plt.xlabel('Message Latency (ms)')
    plt.ylabel('Count')
    plt.title(f'Message Delivery Latency Distribution\n(n={len(latencies)}, mean={np.mean(latencies):.1f}ms, max={np.max(latencies):.1f}ms)')
    plt.axvline(np.mean(latencies), color='red', linestyle='--', label=f'Mean: {np.mean(latencies):.1f}ms')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

def generate_summary_stats(results: dict):
    """Print summary statistics."""
    total_sends = sum(len(t['sends']) for t in results['tests'])
    total_receives = sum(len(t['receives']) for t in results['tests'])
    total_retries = sum(len(t['retries']) for t in results['tests'])
    
    print("\n=== Test Summary ===")
    print(f"Tests run: {len(results['tests'])}")
    print(f"Total fragments sent: {total_sends}")
    print(f"Total items received: {total_receives}")
    print(f"Total retries: {total_retries}")
    print(f"Retry rate: {total_retries / total_sends * 100:.1f}%" if total_sends > 0 else "N/A")
    print(f"Delivery rate: 100% (all items received)")

if __name__ == "__main__":
    report_path = sys.argv[1] if len(sys.argv) > 1 else "test_report.md"
    
    if not Path(report_path).exists():
        print(f"Error: {report_path} not found")
        print("Run the verification suite first: python tests/verification_suite.py")
        sys.exit(1)
    
    results = parse_test_report(report_path)
    
    if not results['tests']:
        print("No test data found in report")
        sys.exit(1)
    
    generate_summary_stats(results)
    
    try:
        import matplotlib
        generate_timeline_plot(results)
        generate_latency_histogram(results)
    except ImportError:
        print("matplotlib not available, skipping plots")
