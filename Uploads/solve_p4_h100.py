import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import time

qc = QuantumCircuit.from_qasm_file('P4_golden_mountain.qasm')
n = qc.num_qubits
qc.measure_all()
sim = AerSimulator(method='matrix_product_state')
tc = transpile(qc, sim)
print(f'Loaded P4: {n} qubits, {qc.size()} gates')

results_all = {}
all_p1 = []

for bd in [512, 1024, 2048, 4096, 8192]:
    print(f"\n{'='*60}")
    print(f"MPS bond_dim={bd}")
    print(f"{'='*60}")
    t0 = time.time()
    result = sim.run(tc, shots=10000, matrix_product_state_max_bond_dimension=bd).result()
    counts = result.get_counts()
    elapsed = time.time() - t0
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    unique = len(counts)
    peak_bs, peak_c = top[0]
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Unique bitstrings: {unique}/10000")
    print(f"  Top 5:")
    for bs, c in top:
        print(f"    {bs}: {c} ({c/100:.1f}%)")
    total = sum(counts.values())
    p1 = np.zeros(n)
    for bs, count in counts.items():
        for pos, bit in enumerate(bs):
            if bit == '1':
                p1[pos] += count
    p1 /= total
    all_p1.append(p1)
    candidate = ''.join('1' if p > 0.5 else '0' for p in p1)
    strong = sum(1 for p in p1 if abs(p - 0.5) > 0.2)
    conf = np.mean(np.abs(p1 - 0.5)) + 0.5
    print(f"  Marginal candidate: {candidate}")
    print(f"  Confidence: {conf:.4f}")
    print(f"  Strong bits: {strong}/{n}")
    results_all[bd] = {'top': top, 'unique': unique, 'elapsed': elapsed,
                       'candidate': candidate, 'confidence': conf, 'strong': strong, 'p1': p1.copy()}
    if peak_c > 100:
        print(f"\n*** PEAK FOUND at bd={bd}: {peak_bs} ({peak_c/100:.1f}%) ***")
        break

print(f"\n{'='*60}")
print("AGGREGATE MARGINAL ANALYSIS")
print(f"{'='*60}")
avg_p1 = np.mean(all_p1, axis=0)
final = ''.join('1' if p > 0.5 else '0' for p in avg_p1)
strong_total = sum(1 for p in avg_p1 if abs(p - 0.5) > 0.2)
conf_total = np.mean(np.abs(avg_p1 - 0.5)) + 0.5
print(f"Final candidate: {final}")
print(f"Overall confidence: {conf_total:.4f}")
print(f"Strong bits: {strong_total}/{n}")

print("\nDONE. Copy all output above and send it back.")
