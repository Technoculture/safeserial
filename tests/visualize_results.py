import matplotlib.pyplot as plt
import numpy as np

def create_compelling_plot(output="reliability_plot.png"):
    """
    Single striking visualization: One corrupted byte can kill a patient.
    Simple, clear, memorable.
    """
    plt.xkcd()
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # The story: A 512-byte medical record transmitted
    # Show what happens with and without CRC protection
    
    # Large center visualization
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'One Corrupted Byte in 512', fontsize=20, ha='center', 
            fontweight='bold', color='#2c3e50')
    
    # LEFT: What the sensor sent
    ax.text(1.5, 7.8, 'SENT:', fontsize=14, ha='center', color='#34495e', fontweight='bold')
    
    # Show the medical reading
    ax.text(1.5, 6.5, '{"dose": 31.9,', fontsize=16, ha='center', 
            family='monospace', color='#27ae60')
    ax.text(1.5, 5.8, ' "unit": "mg"}', fontsize=16, ha='center',
            family='monospace', color='#27ae60')
    
    ax.text(1.5, 4.5, '31.9 mg', fontsize=28, ha='center', 
            fontweight='bold', color='#27ae60')
    ax.text(1.5, 3.8, 'Safe Dose', fontsize=12, ha='center', color='#27ae60')
    
    # Arrow
    ax.annotate('', xy=(4.5, 5.5), xytext=(2.8, 5.5),
                arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=3))
    ax.text(3.65, 6.2, 'Serial Link\n(noisy)', fontsize=10, ha='center', color='#95a5a6')
    
    # CENTER: The corruption
    ax.text(5, 5.5, '0x33 → 0x32', fontsize=14, ha='center', 
            family='monospace', color='#e74c3c', fontweight='bold')
    ax.text(5, 4.8, '(1 bit flip)', fontsize=10, ha='center', color='#e74c3c')
    
    # Arrow
    ax.annotate('', xy=(7.2, 5.5), xytext=(5.5, 5.5),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=3))
    
    # RIGHT: What was received
    ax.text(8.5, 7.8, 'RECEIVED:', fontsize=14, ha='center', color='#34495e', fontweight='bold')
    
    ax.text(8.5, 6.5, '{"dose": 21.9,', fontsize=16, ha='center',
            family='monospace', color='#e74c3c')
    ax.text(8.5, 5.8, ' "unit": "mg"}', fontsize=16, ha='center',
            family='monospace', color='#7f8c8d')
    
    ax.text(8.5, 4.5, '21.9 mg', fontsize=28, ha='center',
            fontweight='bold', color='#e74c3c')
    ax.text(8.5, 3.8, 'WRONG DOSE', fontsize=12, ha='center', color='#e74c3c', fontweight='bold')
    
    # The consequence
    ax.text(5, 2.3, 'Patient receives 31% less medication', fontsize=14, 
            ha='center', color='#c0392b', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#fadbd8', edgecolor='#e74c3c', linewidth=2))
    
    # The solution
    ax.text(5, 1.0, 'Data Bridge: CRC32 detects this. Automatic retry. 100% accuracy.', 
            fontsize=13, ha='center', color='#27ae60', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#d4efdf', edgecolor='#27ae60', linewidth=2))
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created: {output}")

if __name__ == "__main__":
    create_compelling_plot("reliability_plot.png")
