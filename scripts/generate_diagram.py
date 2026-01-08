import matplotlib.pyplot as plt

def create_multi_example_plot(output="reliability_plot.png"):
    """
    Multiple compelling examples of medical data corruption.
    """
    plt.xkcd()
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'Serial Data Corruption: Silent but Deadly', fontsize=18, 
            ha='center', fontweight='bold', color='#2c3e50')
    ax.text(7, 8.9, '512-byte medical records × unreliable serial link', 
            fontsize=11, ha='center', color='#7f8c8d')
    
    # Define examples
    examples = [
        {
            'sent': '{"dose": 31.9}',
            'received': '{"dose": 319}',
            'sent_val': '31.9 mg',
            'recv_val': '319 mg',
            'error': '0x33 0x31 → 0x33 0x31 0x39',
            'consequence': '10x OVERDOSE',
            'y': 7.2
        },
        {
            'sent': '{"rate": 120}',
            'received': '{"rate": 12}',
            'sent_val': '120 bpm',
            'recv_val': '12 bpm',
            'error': 'Lost byte: "0"',
            'consequence': 'FALSE BRADYCARDIA ALARM',
            'y': 5.2
        },
        {
            'sent': '{"temp": 98.6}',
            'received': '{"temp": 9.86}',
            'sent_val': '98.6°F',
            'recv_val': '9.86°F',
            'error': '0x38 → . inserted',
            'consequence': 'HYPOTHERMIA ALERT',
            'y': 3.2
        },
        {
            'sent': '{"bp": "120/80"}',
            'received': '(no data)',
            'sent_val': '120/80',
            'recv_val': '???',
            'error': 'Packet lost (USB glitch)',
            'consequence': 'MISSING VITALS',
            'y': 1.2
        },
    ]
    
    for ex in examples:
        y = ex['y']
        
        # Sent
        ax.text(1.2, y + 0.4, 'SENT:', fontsize=9, color='#7f8c8d', fontweight='bold')
        ax.text(1.2, y, ex['sent_val'], fontsize=14, fontweight='bold', color='#27ae60')
        
        # Arrow with corruption note
        ax.annotate('', xy=(5.5, y + 0.1), xytext=(3, y + 0.1),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))
        ax.text(4.2, y + 0.5, ex['error'], fontsize=8, ha='center', 
                color='#e74c3c', family='monospace')
        
        # Received
        ax.text(6, y + 0.4, 'RECEIVED:', fontsize=9, color='#7f8c8d', fontweight='bold')
        ax.text(6, y, ex['recv_val'], fontsize=14, fontweight='bold', color='#e74c3c')
        
        # Consequence
        ax.text(9.5, y + 0.1, ex['consequence'], fontsize=11, ha='center',
                fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', 
                         edgecolor='#e74c3c', linewidth=1.5))
        
        # Separator line
        if y > 1.5:
            ax.axhline(y - 0.7, color='#ecf0f1', linewidth=1, linestyle='-')
    
    # Headers
    ax.text(1.5, 8.4, 'Original', fontsize=11, ha='center', color='#27ae60', fontweight='bold')
    ax.text(6.2, 8.4, 'Corrupted', fontsize=11, ha='center', color='#e74c3c', fontweight='bold')
    ax.text(9.5, 8.4, 'Consequence', fontsize=11, ha='center', color='#c0392b', fontweight='bold')
    
    # Solution box
    ax.add_patch(plt.Rectangle((11.5, 2.5), 2.3, 5.5, 
                                facecolor='#d4efdf', edgecolor='#27ae60', 
                                linewidth=2, transform=ax.transData))
    ax.text(12.65, 7.5, 'DATA', fontsize=14, ha='center', fontweight='bold', color='#27ae60')
    ax.text(12.65, 7.0, 'BRIDGE', fontsize=14, ha='center', fontweight='bold', color='#27ae60')
    ax.text(12.65, 6.2, '───', fontsize=10, ha='center', color='#27ae60')
    ax.text(12.65, 5.5, 'CRC32', fontsize=10, ha='center', color='#1e8449')
    ax.text(12.65, 5.0, 'ACK/Retry', fontsize=10, ha='center', color='#1e8449')
    ax.text(12.65, 4.5, 'Auto-', fontsize=10, ha='center', color='#1e8449')
    ax.text(12.65, 4.0, 'Reconnect', fontsize=10, ha='center', color='#1e8449')
    ax.text(12.65, 3.2, '───', fontsize=10, ha='center', color='#27ae60')
    ax.text(12.65, 2.7, '100%', fontsize=16, ha='center', fontweight='bold', color='#27ae60')
    
    # Footer
    ax.text(7, 0.3, 'Every bit matters. Data Bridge ensures they all arrive correctly.', 
            fontsize=12, ha='center', style='italic', color='#34495e')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

if __name__ == "__main__":
    from pathlib import Path
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    create_multi_example_plot(str(docs_dir / "reliability_plot.png"))
