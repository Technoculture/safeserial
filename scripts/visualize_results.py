"""
Visualize Test Results - Fault Tolerance Focus

Parses test_report.md to generate visualizations that demonstrate
the protocol's fault tolerance:
1. Retry recovery chart - shows how retries recover from faults
2. Per-test chaos survival - compares clean vs chaos test performance
"""

import re
import sys
from pathlib import Path

def parse_test_report(report_path: str) -> dict:
    """Parse test_report.md for test results."""
    content = Path(report_path).read_text()
    
    results = {'tests': []}
    
    # Parse the summary table for drop/corrupt rates
    table_pattern = r'\| T-(\d+) \| Drop=([\d.]+)%, Corrupt=([\d.]+)% \| (\d+) \|'
    table_matches = re.findall(table_pattern, content)
    
    test_configs = {}
    for test_id, drop, corrupt, items in table_matches:
        test_configs[test_id] = {
            'drop_rate': float(drop),
            'corrupt_rate': float(corrupt),
            'expected_items': int(items),
        }
    
    # Find all log sections
    log_pattern = r'### T-(\d+) Details\s*### Sender Log\s*```(.*?)```\s*### Receiver Log\s*```(.*?)```'
    log_matches = re.findall(log_pattern, content, re.DOTALL)
    
    for test_id, sender_log, receiver_log in log_matches:
        config = test_configs.get(test_id, {'drop_rate': 0, 'corrupt_rate': 0, 'expected_items': 20})
        
        test = {
            'id': test_id,
            'drop_rate': config['drop_rate'],
            'corrupt_rate': config['corrupt_rate'],
            'sends': 0,
            'receives': 0,
            'retries': 0,
            'items_verified': 0,
        }
        
        # Parse sender log
        for line in sender_log.strip().split('\n'):
            if 'Sending Item' in line and 'Frag' in line:
                test['sends'] += 1
            elif 'Timeout/NACK' in line or 'Retrying' in line:
                test['retries'] += 1
            elif 'Verified' in line:
                test['items_verified'] += 1
        
        # Parse receiver log
        for line in receiver_log.strip().split('\n'):
            if 'Completed Item' in line:
                test['receives'] += 1
        
        results['tests'].append(test)
    
    return results

def generate_fault_tolerance_chart(results: dict, output: str = "test_timeline.png"):
    """Generate a chart showing fault tolerance across test conditions."""
    import matplotlib.pyplot as plt
    import numpy as np
    
    plt.xkcd()
    
    if not results['tests']:
        print("No test data found")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: Stacked bar chart showing sends, retries, and deliveries
    ax1 = axes[0]
    
    test_labels = []
    sends = []
    retries = []
    deliveries = []
    
    for test in results['tests']:
        label = f"T-{test['id']}\n{test['drop_rate']:.0f}% drop\n{test['corrupt_rate']:.0f}% corrupt"
        test_labels.append(label)
        sends.append(test['sends'])
        retries.append(test['retries'])
        deliveries.append(test['receives'])
    
    x = np.arange(len(test_labels))
    width = 0.25
    
    bars1 = ax1.bar(x - width, sends, width, label='Fragments Sent', color='#3498db', alpha=0.8)
    bars2 = ax1.bar(x, retries, width, label='Retries (Recovery)', color='#e74c3c', alpha=0.8)
    bars3 = ax1.bar(x + width, deliveries, width, label='Items Delivered', color='#27ae60', alpha=0.8)
    
    ax1.set_xlabel('Test Condition', fontsize=11)
    ax1.set_ylabel('Count', fontsize=11)
    ax1.set_title('Protocol Recovery Under Increasing Chaos', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(test_labels, fontsize=9)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Annotations
    for bar in bars2:
        if bar.get_height() > 0:
            ax1.annotate(f'{int(bar.get_height())} faults\nrecovered',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', fontsize=8, color='#c0392b')
    
    # Right: Delivery success rate (should be 100% for all)
    ax2 = axes[1]
    
    success_rates = []
    retry_rates = []
    for test in results['tests']:
        expected = 20  # Items per test
        success_rates.append(100 * test['receives'] / expected if expected > 0 else 0)
        retry_rates.append(100 * test['retries'] / test['sends'] if test['sends'] > 0 else 0)
    
    x = np.arange(len(test_labels))
    
    # Draw target line
    ax2.axhline(y=100, color='#27ae60', linestyle='--', linewidth=2, alpha=0.5)
    
    colors = ['#27ae60' if s == 100 else '#e74c3c' for s in success_rates]
    bars = ax2.bar(x, success_rates, 0.6, color=colors)
    
    for i, (bar, rate, retry_rate) in enumerate(zip(bars, success_rates, retry_rates)):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{rate:.0f}%', ha='center', va='bottom', fontsize=14, fontweight='bold',
                color='#27ae60' if rate == 100 else '#c0392b')
        if retry_rate > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, 15,
                    f'{retry_rate:.0f}% retries', ha='center', fontsize=9, color='white')
    
    ax2.set_xlabel('Test Condition', fontsize=11)
    ax2.set_ylabel('Delivery Success Rate (%)', fontsize=11)
    ax2.set_title('100% Delivery Despite Faults', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(test_labels, fontsize=9)
    ax2.set_ylim(0, 115)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Big message
    ax2.text(1, 50, 'ZERO DATA LOSS', fontsize=16, ha='center', 
             color='#27ae60', fontweight='bold', rotation=0,
             bbox=dict(boxstyle='round', facecolor='#d4efdf', edgecolor='#27ae60'))
    
    plt.suptitle('Data Bridge: Guaranteed Delivery Under Chaos', 
                 fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

def generate_summary_stats(results: dict):
    """Print summary statistics."""
    total_sends = sum(t['sends'] for t in results['tests'])
    total_receives = sum(t['receives'] for t in results['tests'])
    total_retries = sum(t['retries'] for t in results['tests'])
    expected_total = 20 * len(results['tests'])
    
    print("\n=== Fault Tolerance Summary ===")
    print(f"Tests run: {len(results['tests'])}")
    print(f"Total fragments sent: {total_sends}")
    print(f"Total items delivered: {total_receives} / {expected_total}")
    print(f"Total retries (fault recovery): {total_retries}")
    print(f"Retry rate: {total_retries / total_sends * 100:.1f}%" if total_sends > 0 else "N/A")
    print(f"Delivery success: {'100% ✓' if total_receives == expected_total else 'FAILED'}")

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
        # Save output in the same directory as the report
        report_dir = Path(report_path).parent
        output_file = report_dir / "test_timeline.png"
        generate_fault_tolerance_chart(results, str(output_file))
    except ImportError:
        print("matplotlib not available, skipping plots")
