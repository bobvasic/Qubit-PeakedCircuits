#!/usr/bin/env python3
"""Generate all figures for the peaked circuits research paper."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

FIGDIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGDIR, exist_ok=True)

# Color scheme
SOLVED_COLOR = '#2ecc71'
UNSOLVED_COLOR = '#e74c3c'
ACCENT = '#3498db'
GRAY = '#95a5a6'


def fig1_circuit_complexity():
    """Circuit complexity: qubits vs 2Q gates, colored by solved/unsolved."""
    circuits = {
        'P1': (4, 3, True),      # ~3 2Q gates estimated
        'P2': (28, 450, True),   # estimated from depth/chain
        'P3': (44, 200, True),   # estimated from depth/grid
        'P4': (48, 5096, False),
        'P5': (44, 1892, False),
        'P6': (62, 3494, False),
        'P7': (45, 1275, False),
        'P8': (40, 888, False),
        'P9': (56, 1917, False),
        'P10': (49, 4020, False),
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    for name, (q, g, solved) in circuits.items():
        color = SOLVED_COLOR if solved else UNSOLVED_COLOR
        marker = 'o' if solved else 's'
        ax.scatter(q, g, c=color, s=120, marker=marker, edgecolors='black',
                   linewidths=0.8, zorder=5)
        offset_x = 1.2
        offset_y = 80 if g > 500 else 30
        ax.annotate(name, (q, g), textcoords="offset points",
                    xytext=(8, 5), fontsize=9, fontweight='bold')

    ax.set_xlabel('Number of Qubits', fontsize=12)
    ax.set_ylabel('Number of 2-Qubit Gates', fontsize=12)
    ax.set_title('Circuit Complexity Landscape', fontsize=14, fontweight='bold')

    solved_patch = mpatches.Patch(color=SOLVED_COLOR, label='Solved (P1--P3)')
    unsolved_patch = mpatches.Patch(color=UNSOLVED_COLOR, label='Unsolved (P4--P10)')
    ax.legend(handles=[solved_patch, unsolved_patch], loc='upper left', fontsize=10)

    ax.set_xlim(0, 68)
    ax.set_ylim(-200, 5500)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig1_complexity.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 1: Circuit complexity landscape")


def fig2_topologies():
    """Topology schematics for the different coupling maps."""
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    axes = axes.flatten()

    # Linear/Chain (P1, P2)
    ax = axes[0]
    ax.set_title('Linear / Chain\n(P1, P2)', fontsize=10, fontweight='bold')
    n = 6
    x = np.linspace(0.1, 0.9, n)
    y = np.ones(n) * 0.5
    for i in range(n - 1):
        ax.plot([x[i], x[i+1]], [y[i], y[i+1]], 'k-', lw=1.5)
    ax.scatter(x, y, c=ACCENT, s=200, zorder=5, edgecolors='black')
    for i in range(n):
        ax.text(x[i], y[i], str(i), ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Grid (P3, P8)
    ax = axes[1]
    ax.set_title('Grid\n(P3, P8)', fontsize=10, fontweight='bold')
    rows, cols = 3, 4
    for r in range(rows):
        for c in range(cols):
            cx, cy = 0.15 + c * 0.22, 0.7 - r * 0.25
            ax.scatter(cx, cy, c=ACCENT, s=200, zorder=5, edgecolors='black')
            if c < cols - 1:
                ax.plot([cx, cx + 0.22], [cy, cy], 'k-', lw=1.5)
            if r < rows - 1:
                ax.plot([cx, cx], [cy, cy - 0.25], 'k-', lw=1.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Heavy-Hex (P5, P7, P10)
    ax = axes[2]
    ax.set_title('Heavy-Hex\n(P5, P7, P10)', fontsize=10, fontweight='bold')
    # Simplified heavy-hex: hexagons with bridge qubits
    hex_pts = []
    for row in range(2):
        for col in range(3):
            cx = 0.2 + col * 0.28
            cy = 0.6 - row * 0.35
            if col % 2 == 1:
                cy += 0.08
            hex_pts.append((cx, cy))
    for i, (px, py) in enumerate(hex_pts):
        ax.scatter(px, py, c=ACCENT, s=150, zorder=5, edgecolors='black')
    # Connect in heavy-hex pattern
    edges = [(0,1),(1,2),(3,4),(4,5),(0,3),(2,5),(1,4)]
    for i, j in edges:
        ax.plot([hex_pts[i][0], hex_pts[j][0]],
                [hex_pts[i][1], hex_pts[j][1]], 'k-', lw=1.5)
        # Bridge qubit
        mx = (hex_pts[i][0] + hex_pts[j][0]) / 2
        my = (hex_pts[i][1] + hex_pts[j][1]) / 2
        ax.scatter(mx, my, c='#f39c12', s=80, zorder=5, edgecolors='black')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Cross (P4)
    ax = axes[3]
    ax.set_title('Cross\n(P4)', fontsize=10, fontweight='bold')
    cx, cy = 0.5, 0.5
    arm_len = 4
    positions = [(cx, cy)]
    for dx, dy in [(0.08, 0), (-0.08, 0), (0, 0.08), (0, -0.08)]:
        for k in range(1, arm_len + 1):
            positions.append((cx + dx * k, cy + dy * k))
    for px, py in positions:
        ax.scatter(px, py, c=ACCENT, s=100, zorder=5, edgecolors='black')
    # Draw arms
    for dx, dy in [(0.08, 0), (-0.08, 0), (0, 0.08), (0, -0.08)]:
        for k in range(arm_len):
            x1, y1 = cx + dx * k, cy + dy * k
            x2, y2 = cx + dx * (k + 1), cy + dy * (k + 1)
            ax.plot([x1, x2], [y1, y2], 'k-', lw=1.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # All-to-All (P6)
    ax = axes[4]
    ax.set_title('All-to-All\n(P6)', fontsize=10, fontweight='bold')
    n = 8
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xp = 0.5 + 0.3 * np.cos(angles)
    yp = 0.5 + 0.3 * np.sin(angles)
    for i in range(n):
        for j in range(i + 1, n):
            ax.plot([xp[i], xp[j]], [yp[i], yp[j]], '-', color=GRAY, lw=0.5, alpha=0.5)
    ax.scatter(xp, yp, c=ACCENT, s=150, zorder=5, edgecolors='black')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Dense/Ring (P9)
    ax = axes[5]
    ax.set_title('Dense (labeled "Circular")\n(P9)', fontsize=10, fontweight='bold')
    n = 10
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xp = 0.5 + 0.3 * np.cos(angles)
    yp = 0.5 + 0.3 * np.sin(angles)
    # Draw many connections (dense, not just ring)
    for i in range(n):
        for j in range(i + 1, min(i + 5, n)):
            ax.plot([xp[i], xp[j]], [yp[i], yp[j]], '-', color=GRAY, lw=0.5, alpha=0.4)
    # Ring edges highlighted
    for i in range(n):
        ax.plot([xp[i], xp[(i+1) % n]], [yp[i], yp[(i+1) % n]], '-',
                color=UNSOLVED_COLOR, lw=1.5, alpha=0.7)
    ax.scatter(xp, yp, c=ACCENT, s=150, zorder=5, edgecolors='black')
    ax.text(0.5, 0.08, 'degrees 33--42', ha='center', fontsize=8, style='italic', color=UNSOLVED_COLOR)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig2_topologies.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 2: Topology schematics")


def fig3_mps_scaling():
    """MPS bond dimension scaling — time vs bond dimension for P4 reordered."""
    bond_dims = [64, 128, 256]
    times_sec = [279, 2282, 15691]
    times_min = [t / 60 for t in times_sec]

    fig, ax1 = plt.subplots(figsize=(7, 5))

    color1 = ACCENT
    ax1.semilogy(bond_dims, times_min, 'o-', color=color1, lw=2, markersize=8, label='Runtime')
    ax1.set_xlabel('Bond Dimension', fontsize=12)
    ax1.set_ylabel('Runtime (minutes)', fontsize=12, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    # Annotate all returned noise
    for bd, t in zip(bond_dims, times_min):
        ax1.annotate('noise', (bd, t), textcoords="offset points",
                     xytext=(10, 5), fontsize=9, color=UNSOLVED_COLOR, fontweight='bold')

    # Add extrapolated points
    ext_bd = [512, 1024, 2048]
    # Roughly cubic scaling: t ~ bd^3
    base = times_sec[2]  # 15691 at bd=256
    ext_times = [base * (b / 256) ** 2.5 for b in ext_bd]
    ext_min = [t / 60 for t in ext_times]
    ax1.semilogy(ext_bd, ext_min, 's--', color=color1, alpha=0.4, markersize=6)
    ax1.annotate('extrapolated', (512, ext_min[0]), textcoords="offset points",
                 xytext=(10, -10), fontsize=8, color=GRAY, style='italic')

    ax1.set_title('MPS Runtime Scaling (P4, RCM-reordered)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks([64, 128, 256, 512, 1024, 2048])
    ax1.set_xticklabels(['64', '128', '256', '512', '1024', '2048'])

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig3_mps_scaling.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 3: MPS bond dimension scaling")


def fig4_rcm_bandwidth():
    """RCM bandwidth reduction before/after bar chart."""
    circuits = ['P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']
    bw_orig = [47, 43, 61, 12, 8, 55, 11]
    bw_rcm = [2, 38, 50, 6, 9, 53, 6]

    x = np.arange(len(circuits))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width/2, bw_orig, width, label='Original', color=UNSOLVED_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, bw_rcm, width, label='After RCM', color=SOLVED_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Circuit', fontsize=12)
    ax.set_ylabel('Bandwidth', fontsize=12)
    ax.set_title('Reverse Cuthill--McKee Bandwidth Reduction', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(circuits)
    ax.legend(fontsize=10)
    ax.grid(True, axis='y', alpha=0.3)

    # Annotate improvement factors
    for i, (o, r) in enumerate(zip(bw_orig, bw_rcm)):
        if o > r:
            factor = f'{o/r:.1f}x'
            ax.annotate(factor, (x[i] + width/2, r + 1), ha='center',
                        fontsize=8, fontweight='bold', color='#27ae60')

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig4_rcm_bandwidth.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 4: RCM bandwidth reduction")


def fig5_results_summary():
    """Results summary table as a figure."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('off')

    columns = ['Circuit', 'Qubits', '2Q Gates', 'Topology', 'Method', 'Result']
    data = [
        ['P1', '4', '~3', 'Linear', 'Statevector', 'SOLVED (66.9%)'],
        ['P2', '28', '~450', 'Chain', 'Statevector', 'SOLVED (34.9%)'],
        ['P3', '44', '~200', 'Grid', 'MPS (bd=256)', 'SOLVED (11.0%)'],
        ['P4', '48', '5,096', 'Cross', 'MPS + RCM', 'NOISE'],
        ['P5', '44', '1,892', 'Heavy Hex', 'MPS + IBM QPU', 'NOISE'],
        ['P6', '62', '3,494', 'All-to-All', 'MPS (cloud)', 'NOISE'],
        ['P7', '45', '1,275', 'Heavy Hex', 'MPS (bd=1024)', 'NOISE'],
        ['P8', '40', '888', 'Grid', 'MPS + GPU + quimb', 'NOISE'],
        ['P9', '56', '1,917', 'Dense', 'MPS (cloud)', 'NOISE'],
        ['P10', '49', '4,020', 'Heavy Hex', 'MPS (cloud)', 'NOISE'],
    ]

    cell_colors = []
    for row in data:
        if 'SOLVED' in row[-1]:
            cell_colors.append([SOLVED_COLOR + '40'] * len(columns))
        else:
            cell_colors.append([UNSOLVED_COLOR + '30'] * len(columns))

    table = ax.table(cellText=data, colLabels=columns, cellColours=cell_colors,
                     loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Style header
    for j in range(len(columns)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')

    # Bold the result column
    last_col = len(columns) - 1
    for i in range(1, len(data) + 1):
        cell = table[i, last_col]
        if 'SOLVED' in data[i-1][-1]:
            cell.set_text_props(fontweight='bold', color='#27ae60')
        else:
            cell.set_text_props(fontweight='bold', color='#c0392b')

    ax.set_title('Summary of Results', fontsize=14, fontweight='bold', pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig5_results.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 5: Results summary table")


def fig6_method_flowchart():
    """Strategy decision flowchart."""
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    def draw_box(x, y, w, h, text, color=ACCENT, fontsize=9):
        rect = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                        boxstyle="round,pad=0.1",
                                        facecolor=color, edgecolor='black',
                                        linewidth=1.5, alpha=0.85)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color='white', wrap=True)

    def draw_diamond(x, y, text, color='#f39c12'):
        diamond = plt.Polygon([(x, y+0.5), (x+1, y), (x, y-0.5), (x-1, y)],
                              facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.85)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')

    def arrow(x1, y1, x2, y2, text=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
        if text:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx + 0.15, my, text, fontsize=8, color='#666')

    # Start
    draw_box(5, 7.3, 2.5, 0.5, 'Load QASM Circuit', '#2c3e50')

    # Decision: qubits <= 34?
    draw_diamond(5, 6.2, 'Qubits\n<= 34?')
    arrow(5, 7.05, 5, 6.7)

    # Yes -> Statevector
    draw_box(2.5, 6.2, 2, 0.5, 'Statevector\n(Exact)', SOLVED_COLOR)
    arrow(4, 6.2, 3.5, 6.2, 'Yes')

    # No -> check topology
    draw_diamond(5, 4.8, 'Sparse\ntopology?')
    arrow(5, 5.7, 5, 5.3, 'No')

    # Yes -> RCM + MPS
    draw_box(2.5, 4.8, 2, 0.5, 'RCM Reorder\n+ MPS', '#e67e22')
    arrow(4, 4.8, 3.5, 4.8, 'Yes')

    # No -> check gates
    draw_diamond(5, 3.4, '2Q gates\n< 1000?')
    arrow(5, 4.3, 5, 3.9, 'No')

    # Yes -> MPS high bd
    draw_box(2.5, 3.4, 2, 0.5, 'MPS\n(high bd)', '#e67e22')
    arrow(4, 3.4, 3.5, 3.4, 'Yes')

    # No -> cloud/hardware
    draw_box(5, 2.2, 2.2, 0.5, 'Cloud MPS /\nGPU Tensor Net', '#8e44ad')
    arrow(5, 2.9, 5, 2.45, 'No')

    # Also try hardware
    draw_box(7.8, 2.2, 2, 0.5, 'Quantum\nHardware', '#2c3e50')
    arrow(6.1, 2.2, 6.8, 2.2)

    # Result
    draw_diamond(5, 1.0, 'Peak\nfound?')
    arrow(5, 1.95, 5, 1.5)

    draw_box(2.5, 1.0, 1.5, 0.4, 'Submit', SOLVED_COLOR)
    arrow(4, 1.0, 3.25, 1.0, 'Yes')

    draw_box(7.5, 1.0, 2, 0.4, 'Increase bd /\nTry alternatives', UNSOLVED_COLOR)
    arrow(6, 1.0, 6.5, 1.0, 'No')

    ax.set_title('Method Selection Strategy', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig6_flowchart.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 6: Method decision flowchart")


if __name__ == '__main__':
    print("Generating figures...")
    fig1_circuit_complexity()
    fig2_topologies()
    fig3_mps_scaling()
    fig4_rcm_bandwidth()
    fig5_results_summary()
    fig6_method_flowchart()
    print("All figures generated in", FIGDIR)
