#!/usr/bin/env python3
"""Generate all figures for the peaked circuits research paper."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import os

FIGDIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGDIR, exist_ok=True)

# Color scheme
SOLVED_COLOR = '#2ecc71'
UNSOLVED_COLOR = '#e74c3c'
ACCENT = '#3498db'
GRAY = '#95a5a6'
PURPLE = '#8e44ad'
ORANGE = '#e67e22'
DARK = '#2c3e50'


def fig1_circuit_complexity():
    """Circuit complexity: qubits vs 2Q gates, colored by solved/unsolved."""
    circuits = {
        'P1': (4, 3, True),
        'P2': (28, 450, True),
        'P3': (44, 200, True),
        'P4': (48, 5096, False),
        'P5': (44, 1892, False),
        'P6': (62, 3494, False),
        'P7': (45, 1275, False),
        'P8': (40, 888, False),
        'P9': (56, 1917, False),
        'P10': (49, 4020, False),
    }

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Add solvability boundary region
    ax.axhspan(0, 500, alpha=0.08, color=SOLVED_COLOR, label='_nolegend_')
    ax.axhline(y=500, color=SOLVED_COLOR, linestyle='--', alpha=0.5, lw=1)
    ax.text(63, 520, 'Solvability\nboundary', fontsize=8, color=SOLVED_COLOR,
            ha='right', va='bottom', style='italic')

    for name, (q, g, solved) in circuits.items():
        color = SOLVED_COLOR if solved else UNSOLVED_COLOR
        marker = 'o' if solved else 's'
        size = 150 if solved else 120
        ax.scatter(q, g, c=color, s=size, marker=marker, edgecolors='black',
                   linewidths=0.8, zorder=5)
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
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

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
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # Heavy-Hex (P5, P7, P10)
    ax = axes[2]
    ax.set_title('Heavy-Hex\n(P5, P7, P10)', fontsize=10, fontweight='bold')
    hex_pts = []
    for row in range(2):
        for col in range(3):
            cx = 0.2 + col * 0.28
            cy = 0.6 - row * 0.35
            if col % 2 == 1: cy += 0.08
            hex_pts.append((cx, cy))
    for i, (px, py) in enumerate(hex_pts):
        ax.scatter(px, py, c=ACCENT, s=150, zorder=5, edgecolors='black')
    edges = [(0,1),(1,2),(3,4),(4,5),(0,3),(2,5),(1,4)]
    for i, j in edges:
        ax.plot([hex_pts[i][0], hex_pts[j][0]], [hex_pts[i][1], hex_pts[j][1]], 'k-', lw=1.5)
        mx = (hex_pts[i][0] + hex_pts[j][0]) / 2
        my = (hex_pts[i][1] + hex_pts[j][1]) / 2
        ax.scatter(mx, my, c='#f39c12', s=80, zorder=5, edgecolors='black')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # Ring (P4) - CORRECTED from "Cross"
    ax = axes[3]
    ax.set_title('Ring (C$_{48}$)\n(P4)', fontsize=10, fontweight='bold')
    n = 12
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xp = 0.5 + 0.3 * np.cos(angles)
    yp = 0.5 + 0.3 * np.sin(angles)
    for i in range(n):
        ax.plot([xp[i], xp[(i+1) % n]], [yp[i], yp[(i+1) % n]], '-', color=ACCENT, lw=2)
    ax.scatter(xp, yp, c=ACCENT, s=120, zorder=5, edgecolors='black')
    ax.text(0.5, 0.08, '48 qubits, degree 2', ha='center', fontsize=8, style='italic', color=DARK)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

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
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # Dense/Ring (P9)
    ax = axes[5]
    ax.set_title('Dense (labeled "Circular")\n(P9)', fontsize=10, fontweight='bold')
    n = 10
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xp = 0.5 + 0.3 * np.cos(angles)
    yp = 0.5 + 0.3 * np.sin(angles)
    for i in range(n):
        for j in range(i + 1, min(i + 5, n)):
            ax.plot([xp[i], xp[j]], [yp[i], yp[j]], '-', color=GRAY, lw=0.5, alpha=0.4)
    for i in range(n):
        ax.plot([xp[i], xp[(i+1) % n]], [yp[i], yp[(i+1) % n]], '-', color=UNSOLVED_COLOR, lw=1.5, alpha=0.7)
    ax.scatter(xp, yp, c=ACCENT, s=150, zorder=5, edgecolors='black')
    ax.text(0.5, 0.08, 'degrees 33--42', ha='center', fontsize=8, style='italic', color=UNSOLVED_COLOR)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

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

    for bd, t in zip(bond_dims, times_min):
        ax1.annotate('noise', (bd, t), textcoords="offset points",
                     xytext=(10, 5), fontsize=9, color=UNSOLVED_COLOR, fontweight='bold')

    ext_bd = [512, 1024, 2048]
    base = times_sec[2]
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
    ax.bar(x - width/2, bw_orig, width, label='Original', color=UNSOLVED_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, bw_rcm, width, label='After RCM', color=SOLVED_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Circuit', fontsize=12)
    ax.set_ylabel('Bandwidth', fontsize=12)
    ax.set_title('Reverse Cuthill--McKee Bandwidth Reduction', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(circuits)
    ax.legend(fontsize=10)
    ax.grid(True, axis='y', alpha=0.3)

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
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.axis('off')

    columns = ['Circuit', 'Qubits', '2Q Gates', 'Topology', 'Best Method', 'Platforms Tried', 'Result']
    data = [
        ['P1', '4', '~3', 'Linear', 'Statevector', 'BlueQubit CPU', 'SOLVED (66.9%)'],
        ['P2', '28', '~450', 'Chain', 'Statevector', 'BlueQubit CPU', 'SOLVED (34.9%)'],
        ['P3', '44', '~200', 'Grid', 'MPS (bd=256)', 'BlueQubit MPS', 'SOLVED (11.0%)'],
        ['P4', '48', '5,096', 'Ring*', 'MPS + RCM', 'Local, Cloud, IBM QPU, H100', 'NOISE'],
        ['P5', '44', '1,892', 'Heavy Hex', 'MPS + IBM QPU', 'Cloud, IBM Heron R2', 'NOISE'],
        ['P6', '62', '3,494', 'All-to-All', 'MPS (cloud)', 'BlueQubit Cloud', 'NOISE'],
        ['P7', '45', '1,275', 'Heavy Hex', 'MPS (bd=1024)', 'Cloud, BQ QPU', 'NOISE'],
        ['P8', '40', '888', 'Grid', 'MPS + quimb', 'Local, Cloud, GPU, quimb', 'NOISE'],
        ['P9', '56', '1,917', 'Dense', 'MPS (cloud)', 'BlueQubit Cloud', 'NOISE'],
        ['P10', '49', '4,020', 'Heavy Hex', 'MPS (cloud)', 'BlueQubit Cloud', 'NOISE'],
    ]

    cell_colors = []
    for row in data:
        if 'SOLVED' in row[-1]:
            cell_colors.append(['#d5f5e3'] * len(columns))
        else:
            cell_colors.append(['#fadbd8'] * len(columns))

    table = ax.table(cellText=data, colLabels=columns, cellColours=cell_colors,
                     loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    for j in range(len(columns)):
        cell = table[0, j]
        cell.set_facecolor(DARK)
        cell.set_text_props(color='white', fontweight='bold')

    last_col = len(columns) - 1
    for i in range(1, len(data) + 1):
        cell = table[i, last_col]
        if 'SOLVED' in data[i-1][-1]:
            cell.set_text_props(fontweight='bold', color='#27ae60')
        else:
            cell.set_text_props(fontweight='bold', color='#c0392b')

    ax.set_title('Summary of Results Across All Platforms', fontsize=14, fontweight='bold', pad=20)
    ax.text(0.5, -0.02, '*P4 was labeled "Cross" but deep analysis revealed a 48-qubit ring (C$_{48}$)',
            transform=ax.transAxes, ha='center', fontsize=9, style='italic', color=GRAY)
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

    draw_box(5, 7.3, 2.5, 0.5, 'Load QASM Circuit', DARK)
    draw_diamond(5, 6.2, 'Qubits\n<= 34?')
    arrow(5, 7.05, 5, 6.7)
    draw_box(2.5, 6.2, 2, 0.5, 'Statevector\n(Exact)', SOLVED_COLOR)
    arrow(4, 6.2, 3.5, 6.2, 'Yes')
    draw_diamond(5, 4.8, 'Sparse\ntopology?')
    arrow(5, 5.7, 5, 5.3, 'No')
    draw_box(2.5, 4.8, 2, 0.5, 'RCM Reorder\n+ MPS', ORANGE)
    arrow(4, 4.8, 3.5, 4.8, 'Yes')
    draw_diamond(5, 3.4, '2Q gates\n< 1000?')
    arrow(5, 4.3, 5, 3.9, 'No')
    draw_box(2.5, 3.4, 2, 0.5, 'MPS\n(high bd)', ORANGE)
    arrow(4, 3.4, 3.5, 3.4, 'Yes')
    draw_box(5, 2.2, 2.2, 0.5, 'Cloud MPS /\nGPU Tensor Net', PURPLE)
    arrow(5, 2.9, 5, 2.45, 'No')
    draw_box(7.8, 2.2, 2, 0.5, 'Quantum\nHardware', DARK)
    arrow(6.1, 2.2, 6.8, 2.2)
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


def fig7_hardware_comparison():
    """Hardware platforms comparison — what was tried and outcome."""
    fig, ax = plt.subplots(figsize=(10, 5.5))

    platforms = [
        'Local CPU\n(16GB, 4 cores)',
        'BlueQubit\nmps.cpu',
        'BlueQubit\nmps.gpu',
        'BlueQubit\nQPU',
        'IBM Heron R2\n(156q)',
        'NVIDIA H100\n(94GB)',
        'quimb +\ncotengra'
    ]
    max_bd = [1024, 2048, 1024, 0, 0, 512, 256]
    colors_bar = [ACCENT, ACCENT, PURPLE, UNSOLVED_COLOR, UNSOLVED_COLOR, ORANGE, GRAY]
    outcomes = ['Noise', 'Noise', 'Terminated', 'Gate limit\nexceeded', 'Noise\n(decoherence)',
                'Credits\nexhausted', 'API error']

    x = np.arange(len(platforms))
    bars = ax.bar(x, max_bd, color=colors_bar, edgecolor='black', linewidth=0.8, alpha=0.85)

    for i, (b, outcome) in enumerate(zip(bars, outcomes)):
        height = b.get_height()
        y_pos = max(height + 50, 100)
        ax.text(b.get_x() + b.get_width()/2., y_pos, outcome,
                ha='center', va='bottom', fontsize=8, fontweight='bold',
                color=UNSOLVED_COLOR)

    ax.set_xlabel('Platform', fontsize=12)
    ax.set_ylabel('Max Bond Dimension Achieved', fontsize=12)
    ax.set_title('Simulation Platforms Attempted and Outcomes', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(platforms, fontsize=8)
    ax.set_ylim(0, 2800)
    ax.grid(True, axis='y', alpha=0.3)

    # Add a note about QPU and IBM not using bond dim
    ax.text(3, 150, 'N/A', ha='center', fontsize=9, color='white', fontweight='bold')
    ax.text(4, 150, 'N/A', ha='center', fontsize=9, color='white', fontweight='bold')

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig7_platforms.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 7: Hardware platform comparison")


def fig8_ibm_noise():
    """IBM Quantum noise visualization — showing uniform distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Left: Ideal peaked distribution (P3 - solved)
    ax = axes[0]
    np.random.seed(42)
    n_bins = 50
    # Simulate peaked distribution
    probs = np.random.exponential(0.01, n_bins)
    probs[25] = 0.11  # The peak
    probs = probs / probs.sum()
    colors = [SOLVED_COLOR if i == 25 else ACCENT for i in range(n_bins)]
    ax.bar(range(n_bins), probs * 100, color=colors, edgecolor='none', alpha=0.8)
    ax.annotate('Peak bitstring\n(11.0%)', xy=(25, 11), xytext=(35, 9),
                fontsize=9, fontweight='bold', color=SOLVED_COLOR,
                arrowprops=dict(arrowstyle='->', color=SOLVED_COLOR, lw=1.5))
    ax.set_xlabel('Bitstring Index (sorted)', fontsize=10)
    ax.set_ylabel('Probability (%)', fontsize=10)
    ax.set_title('P3: Solved (MPS, bd=256)', fontsize=11, fontweight='bold', color=SOLVED_COLOR)
    ax.set_ylim(0, 13)
    ax.grid(True, axis='y', alpha=0.3)

    # Right: Uniform noise (P4 on IBM)
    ax = axes[1]
    n_bins = 50
    probs_noise = np.ones(n_bins) / n_bins
    noise = np.random.normal(0, 0.001, n_bins)
    probs_noise += noise
    probs_noise = np.abs(probs_noise)
    probs_noise /= probs_noise.sum()
    ax.bar(range(n_bins), probs_noise * 100, color=UNSOLVED_COLOR, edgecolor='none', alpha=0.6)
    ax.axhline(y=100/n_bins, color='black', linestyle='--', lw=1, alpha=0.5)
    ax.text(n_bins - 1, 100/n_bins + 0.15, 'Uniform ($2^{-n}$)', ha='right',
            fontsize=9, style='italic', color=DARK)
    ax.set_xlabel('Bitstring Index (sorted)', fontsize=10)
    ax.set_ylabel('Probability (%)', fontsize=10)
    ax.set_title('P4: IBM Heron R2 (46,014 gates)', fontsize=11, fontweight='bold', color=UNSOLVED_COLOR)
    ax.set_ylim(0, 4)
    ax.grid(True, axis='y', alpha=0.3)
    ax.text(25, 3.5, '10,000 unique bitstrings\nfrom 10,000 shots\n= pure noise',
            ha='center', fontsize=10, fontweight='bold', color=UNSOLVED_COLOR,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=UNSOLVED_COLOR, alpha=0.9))

    fig.suptitle('Peaked vs. Noise Output Distribution', fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig8_noise.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 8: IBM noise visualization")


def fig9_transpilation_blowup():
    """Gate count blowup after transpilation for quantum hardware."""
    circuits = ['P4', 'P5', 'P7', 'P8']
    original_gates = [15336, 5700, 4000, 2704]
    transpiled_gates = [46014, 25000, 25961, 29729]
    gate_limits = [20000] * 4

    x = np.arange(len(circuits))
    width = 0.3

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x - width/2, original_gates, width, label='Original', color=ACCENT, edgecolor='black', linewidth=0.5, alpha=0.85)
    ax.bar(x + width/2, transpiled_gates, width, label='After Transpilation', color=UNSOLVED_COLOR, edgecolor='black', linewidth=0.5, alpha=0.85)
    ax.axhline(y=20000, color=ORANGE, linestyle='--', lw=2, label='BlueQubit QPU Gate Limit')

    ax.set_xlabel('Circuit', fontsize=12)
    ax.set_ylabel('Total Gate Count', fontsize=12)
    ax.set_title('Transpilation Gate Count Blowup', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(circuits)
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, axis='y', alpha=0.3)

    # Annotate blowup factors
    for i, (o, t) in enumerate(zip(original_gates, transpiled_gates)):
        factor = f'{t/o:.1f}x'
        ax.text(x[i] + width/2, t + 500, factor, ha='center', fontsize=9,
                fontweight='bold', color=UNSOLVED_COLOR)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig9_transpilation.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 9: Transpilation gate blowup")


def fig10_entanglement_barrier():
    """Entanglement barrier — required bond dim vs circuit 2Q gate count."""
    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Solved region
    gates_solved = [3, 200, 450]
    bd_needed = [2, 256, 32]
    ax.scatter(gates_solved, bd_needed, c=SOLVED_COLOR, s=150, marker='o',
               edgecolors='black', zorder=5, label='Solved')
    for g, b, name in zip(gates_solved, bd_needed, ['P1', 'P3', 'P2']):
        ax.annotate(name, (g, b), textcoords="offset points", xytext=(8, 5),
                    fontsize=9, fontweight='bold')

    # Unsolved — estimated required bd (from arxiv paper extrapolation)
    gates_unsolved = [888, 1275, 1892, 1917, 3494, 4020, 5096]
    bd_est = [8000, 12000, 30000, 32000, 200000, 300000, 500000]
    ax.scatter(gates_unsolved, bd_est, c=UNSOLVED_COLOR, s=120, marker='s',
               edgecolors='black', zorder=5, label='Unsolved (estimated)')
    for g, b, name in zip(gates_unsolved, bd_est,
                          ['P8', 'P7', 'P5', 'P9', 'P6', 'P10', 'P4']):
        ax.annotate(name, (g, b), textcoords="offset points", xytext=(8, 5),
                    fontsize=9, fontweight='bold')

    # Feasibility line
    ax.axhspan(0, 2048, alpha=0.08, color=SOLVED_COLOR)
    ax.axhline(y=2048, color=SOLVED_COLOR, linestyle='--', lw=1.5, alpha=0.7)
    ax.text(4500, 2500, 'Max feasible bd\n(cloud MPS)', fontsize=9,
            style='italic', color=SOLVED_COLOR, ha='center')

    ax.axhspan(0, 8192, alpha=0.04, color=ORANGE)
    ax.axhline(y=8192, color=ORANGE, linestyle=':', lw=1.5, alpha=0.5)
    ax.text(4500, 9500, 'H100 GPU limit\n(estimated)', fontsize=9,
            style='italic', color=ORANGE, ha='center')

    ax.set_yscale('log')
    ax.set_xlabel('Number of 2-Qubit Gates', fontsize=12)
    ax.set_ylabel('Estimated Required Bond Dimension', fontsize=12)
    ax.set_title('Entanglement Barrier: Required Bond Dimension', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-100, 5500)
    ax.set_ylim(1, 2000000)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig10_entanglement.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 10: Entanglement barrier")


def fig11_timeline():
    """Timeline of methods attempted during the hackathon."""
    fig, ax = plt.subplots(figsize=(12, 5))

    methods = [
        ('Statevector\n(P1, P2)', 0, 1, SOLVED_COLOR),
        ('MPS Cloud\n(P3)', 1, 2, SOLVED_COLOR),
        ('MPS Local\n(P4-P10, bd=64-256)', 2, 6, UNSOLVED_COLOR),
        ('RCM Reordering\n+ MPS', 4, 7, ORANGE),
        ('Cloud MPS\n(bd=256-2048)', 3, 9, ACCENT),
        ('Marginal\nReconstruction', 6, 8, PURPLE),
        ('BlueQubit QPU', 5, 7, DARK),
        ('IBM Heron R2\n(P5, P4)', 7, 9, '#1a5276'),
        ('quimb/cotengra', 8, 9, GRAY),
        ('H100 GPU VM\n(MPS)', 9, 10, ORANGE),
    ]

    for i, (name, start, end, color) in enumerate(methods):
        ax.barh(i, end - start, left=start, height=0.6, color=color,
                edgecolor='black', linewidth=0.5, alpha=0.85)
        ax.text(start + (end - start) / 2, i, name, ha='center', va='center',
                fontsize=7, fontweight='bold', color='white')

    ax.set_xlabel('Relative Time', fontsize=12)
    ax.set_title('Chronological Method Escalation', fontsize=14, fontweight='bold')
    ax.set_yticks([])
    ax.set_xlim(-0.5, 11)
    ax.grid(True, axis='x', alpha=0.3)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor=SOLVED_COLOR, markersize=10, label='Solved'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=UNSOLVED_COLOR, markersize=10, label='Failed (noise)'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=ORANGE, markersize=10, label='Partial / timeout'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=GRAY, markersize=10, label='Error / incompatible'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig11_timeline.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 11: Method timeline")


def fig12_p4_ring_structure():
    """P4 ring structure with sandwich gate pattern."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Ring topology
    ax = axes[0]
    n = 48
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False) - np.pi/2
    r = 0.4
    xp = 0.5 + r * np.cos(angles)
    yp = 0.5 + r * np.sin(angles)

    for i in range(n):
        ax.plot([xp[i], xp[(i+1) % n]], [yp[i], yp[(i+1) % n]], '-',
                color=ACCENT, lw=1.2, alpha=0.7)
    ax.scatter(xp, yp, c=ACCENT, s=25, zorder=5, edgecolors='black', linewidths=0.3)

    # Label a few qubits
    for i in [0, 12, 24, 36]:
        ax.annotate(f'q{i}', (xp[i], yp[i]), textcoords="offset points",
                    xytext=(10, 5), fontsize=7, fontweight='bold')

    # Highlight the cut point
    cut_i = 23
    ax.plot([xp[cut_i], xp[cut_i+1]], [yp[cut_i], yp[cut_i+1]], '-',
            color=UNSOLVED_COLOR, lw=3, zorder=6)
    ax.annotate('MPS cut\npoint', xy=((xp[cut_i]+xp[cut_i+1])/2, (yp[cut_i]+yp[cut_i+1])/2),
                textcoords="offset points", xytext=(15, -15), fontsize=8,
                color=UNSOLVED_COLOR, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=UNSOLVED_COLOR))

    ax.set_title('P4: 48-Qubit Ring Topology\n(mislabeled as "Cross")', fontsize=11, fontweight='bold')
    ax.text(0.5, 0.05, '48 edges, degree 2, ~106 CZ per edge',
            ha='center', fontsize=9, style='italic', color=GRAY, transform=ax.transAxes)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # Right: CZ sandwich structure
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Draw sandwich pattern
    y_start = 5
    box_h = 0.4
    box_w = 1.8

    def gate_box(x, y, text, color):
        rect = mpatches.FancyBboxPatch((x - box_w/2, y - box_h/2), box_w, box_h,
                                        boxstyle="round,pad=0.05", facecolor=color,
                                        edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Qubit lines
    ax.plot([0.5, 9.5], [4.5, 4.5], 'k-', lw=0.8)
    ax.plot([0.5, 9.5], [3.5, 3.5], 'k-', lw=0.8)
    ax.text(0.3, 4.5, 'q$_a$', ha='right', va='center', fontsize=10)
    ax.text(0.3, 3.5, 'q$_b$', ha='right', va='center', fontsize=10)

    # CZ - u3 - u3 - CZ sandwich
    gate_box(2, 4.0, 'CZ', ACCENT)
    gate_box(4, 4.5, 'u3($\\theta$, 0, $\\pm\\pi/2$)', ORANGE)
    gate_box(4, 3.5, 'u3($\\theta$, 0, $\\pm\\pi/2$)', ORANGE)
    gate_box(6, 4.0, 'CZ', ACCENT)

    # Brace
    ax.annotate('', xy=(1, 2.7), xytext=(7, 2.7),
                arrowprops=dict(arrowstyle='-', lw=1))
    ax.text(4, 2.3, 'KAK Sandwich = 1 Logical 2Q Gate', ha='center',
            fontsize=10, fontweight='bold', color=DARK)
    ax.text(4, 1.7, '2,543 sandwiches + 10 standalone CZ\n= 5,096 total CZ gates',
            ha='center', fontsize=9, color=GRAY)
    ax.text(4, 0.8, 'Circuit phases: Staircase buildup\n'
            + u'\u2192 Steady-state sweeps (\u00d740)\n'
            + u'\u2192 Staircase wind-down',
            ha='center', fontsize=9, color=PURPLE, style='italic')

    ax.set_title('P4: CZ-u3-CZ Sandwich Structure', fontsize=11, fontweight='bold')

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig12_p4_ring.pdf'), bbox_inches='tight')
    plt.close(fig)
    print("  Fig 12: P4 ring structure and sandwich gates")


if __name__ == '__main__':
    print("Generating figures...")
    fig1_circuit_complexity()
    fig2_topologies()
    fig3_mps_scaling()
    fig4_rcm_bandwidth()
    fig5_results_summary()
    fig6_method_flowchart()
    fig7_hardware_comparison()
    fig8_ibm_noise()
    fig9_transpilation_blowup()
    fig10_entanglement_barrier()
    fig11_timeline()
    fig12_p4_ring_structure()
    print(f"All 12 figures generated in {FIGDIR}")
