
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_value_diagram(output="reliability_plot.png"):
    """
    Show the full value: Chaos in -> Guaranteed delivery out
    All the problems Data Bridge solves, not just ACKs.
    """
    plt.xkcd()
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # LEFT SIDE: The Chaos (Problems)
    ax.text(0.5, 5.5, 'THE PROBLEM', fontsize=14, fontweight='bold', ha='center', color='#c0392b')
    
    problems = [
        ('Packet Loss', 4.5, '#e74c3c'),
        ('Bit Corruption', 3.5, '#e74c3c'),
        ('Frame Sync Loss', 2.5, '#e74c3c'),
        ('Large Message Split', 1.5, '#e74c3c'),
    ]
    
    for text, y, color in problems:
        rect = patches.FancyBboxPatch((0, y-0.35), 1, 0.7, 
                                       boxstyle="round,pad=0.05", 
                                       facecolor='#fadbd8', edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(0.5, y, text, ha='center', va='center', fontsize=10, color=color)
    
    # CENTER: Data Bridge (Solution)
    center_x = 2.5
    rect = patches.FancyBboxPatch((1.8, 1), 1.4, 4.5, 
                                   boxstyle="round,pad=0.1", 
                                   facecolor='#d5f5e3', edgecolor='#27ae60', linewidth=3)
    ax.add_patch(rect)
    ax.text(center_x, 5.2, 'DATA', fontsize=11, ha='center', va='center', fontweight='bold', color='#27ae60')
    ax.text(center_x, 4.7, 'BRIDGE', fontsize=11, ha='center', va='center', fontweight='bold', color='#27ae60')
    
    solutions = [
        'ACK + Retry',
        'CRC32 Check',
        'COBS Framing',
        'Fragmentation',
    ]
    for i, sol in enumerate(solutions):
        ax.text(center_x, 4 - i*0.7, sol, ha='center', va='center', fontsize=9, color='#1e8449')
    
    # RIGHT SIDE: The Result
    ax.text(4.5, 5.5, 'THE RESULT', fontsize=14, fontweight='bold', ha='center', color='#27ae60')
    
    rect = patches.FancyBboxPatch((3.8, 2.3), 1.4, 1.4, 
                                   boxstyle="round,pad=0.1", 
                                   facecolor='#d5f5e3', edgecolor='#27ae60', linewidth=3)
    ax.add_patch(rect)
    ax.text(4.5, 3.2, '100%', fontsize=18, ha='center', va='center', fontweight='bold', color='#27ae60')
    ax.text(4.5, 2.6, 'Delivery', fontsize=11, ha='center', va='center', color='#27ae60')
    
    # Arrows
    ax.annotate('', xy=(1.7, 3), xytext=(1.1, 3),
                arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2))
    ax.annotate('', xy=(3.7, 3), xytext=(3.3, 3),
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=2))
    
    # Title
    ax.set_title('Data Bridge: Guaranteed Reliable Serial Communication', 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax.set_xlim(-0.3, 5.5)
    ax.set_ylim(0.5, 6.2)
    ax.axis('off')
    
    # Tagline
    ax.text(2.5, 0.7, 'Your data arrives intact, or you get a clear error. Never silent corruption.', 
            fontsize=10, ha='center', style='italic', color='#666')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

if __name__ == "__main__":
    create_value_diagram("reliability_plot.png")
