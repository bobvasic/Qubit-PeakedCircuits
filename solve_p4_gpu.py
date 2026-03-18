"""
P4 Golden Mountain Solver — for BlueQubit H100 GPU VM
Run this in the Jupyter notebook on the BlueQubit VM.

Strategy: Compute per-qubit <Zi> expectation values via high bond-dim MPS,
then reconstruct the peak bitstring from the signs.
"""

import bluequbit
import numpy as np
from qiskit import QuantumCircuit

# ── Load circuit ──
qc = QuantumCircuit.from_qasm_file('P4_golden_mountain.qasm')
print(f"P4: {qc.num_qubits} qubits, {qc.size()} gates")

bq = bluequbit.init()

# ── Approach 1: High bond-dim MPS on GPU ──
print("\n=== Approach 1: MPS GPU, bond_dim=4096 ===")
try:
    result = bq.run(qc, device='mps.gpu', shots=10000,
                    job_name='P4_gpu_bd4096',
                    options={'mps_bond_dimension': 4096})
    counts = result.get_counts()
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 bitstrings:")
    for bs, c in top:
        print(f"  {bs}: {c} ({c/100:.1f}%)")

    # Also extract marginals
    total = sum(counts.values())
    n = qc.num_qubits
    p1 = np.zeros(n)
    for bs, count in counts.items():
        for pos, bit in enumerate(bs):
            if bit == '1':
                p1[pos] += count
    p1 /= total
    candidate = ''.join('1' if p > 0.5 else '0' for p in p1)
    confidence = np.mean(np.abs(p1 - 0.5)) + 0.5
    print(f"\nMarginal candidate: {candidate}")
    print(f"Avg confidence: {confidence:.4f}")
    print(f"Strong bits (>0.7 or <0.3): {sum(1 for p in p1 if abs(p-0.5)>0.2)}/{n}")
except Exception as e:
    print(f"GPU MPS failed: {e}")

# ── Approach 2: Try quantum device ──
print("\n=== Approach 2: Quantum Device ===")
try:
    result_q = bq.run(qc, device='quantum', shots=10000,
                      job_name='P4_quantum')
    counts_q = result_q.get_counts()
    top_q = sorted(counts_q.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 bitstrings:")
    for bs, c in top_q:
        print(f"  {bs}: {c} ({c/100:.1f}%)")
except Exception as e:
    print(f"Quantum device failed: {e}")

# ── Approach 3: Multiple bond dims, marginal voting ──
print("\n=== Approach 3: Multi-BD Marginal Voting ===")
all_p1 = []
for bd in [1024, 2048, 4096]:
    print(f"\nRunning bd={bd}...")
    try:
        r = bq.run(qc, device='mps.gpu', shots=10000,
                   job_name=f'P4_marginal_bd{bd}',
                   options={'mps_bond_dimension': bd})
        counts = r.get_counts()
        total = sum(counts.values())
        n = qc.num_qubits
        p1 = np.zeros(n)
        for bs, count in counts.items():
            for pos, bit in enumerate(bs):
                if bit == '1':
                    p1[pos] += count
        p1 /= total
        all_p1.append(p1)

        # Check if this run alone has signal
        peak_bs, peak_c = max(counts.items(), key=lambda x: x[1])
        print(f"  Peak: {peak_bs} ({peak_c} counts)")
        print(f"  Unique bitstrings: {len(counts)}")
        print(f"  Strong bits: {sum(1 for p in p1 if abs(p-0.5)>0.2)}/{n}")
    except Exception as e:
        print(f"  bd={bd} failed: {e}")

if all_p1:
    avg_p1 = np.mean(all_p1, axis=0)
    final = ''.join('1' if p > 0.5 else '0' for p in avg_p1)
    conf = np.mean(np.abs(avg_p1 - 0.5)) + 0.5
    print(f"\n=== FINAL VOTED CANDIDATE ===")
    print(f"Bitstring: {final}")
    print(f"Confidence: {conf:.4f}")
    print(f"Strong bits: {sum(1 for p in avg_p1 if abs(p-0.5)>0.2)}/{n}")

    # Show per-qubit probabilities
    print("\nPer-qubit P(1):")
    for i, p in enumerate(avg_p1):
        marker = " ***" if abs(p - 0.5) > 0.2 else ""
        print(f"  q[{i:2d}]: {p:.4f}{marker}")
