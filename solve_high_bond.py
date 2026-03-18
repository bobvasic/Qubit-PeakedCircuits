#!/usr/bin/env python3
"""
Try MPS with progressively higher bond dimensions locally.
Tests bond_dim = 512, 1024, 2048 to find the threshold where the peak emerges.
"""
import sys
import time
import json
from pathlib import Path
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

results = {}
if RESULTS_FILE.exists():
    results = json.loads(RESULTS_FILE.read_text())

# Circuit to solve (from CLI arg or default P8)
circuit_id = sys.argv[1].upper() if len(sys.argv) > 1 else "P8"
bond_dims = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [512, 1024, 2048]

CIRCUITS = {
    "P4":  ("Golden Mountain",  "P4_golden_mountain.qasm"),
    "P5":  ("Granite Summit",   "P5_granite_summit.qasm"),
    "P6":  ("Titan Pinnacle",   "P6_titan_pinnacle.qasm"),
    "P7":  ("Heavy Hex 1275",   "P7_heavy_hex_1275.qasm"),
    "P8":  ("Grid 888 iSwap",   "P8_grid_888_iswap.qasm"),
    "P9":  ("HQAP 1917",        "P9_hqap_1917.qasm"),
    "P10": ("Heavy Hex 4020",   "P10_heavy_hex_4020.qasm"),
}

if circuit_id not in CIRCUITS:
    print(f"Unknown circuit: {circuit_id}")
    sys.exit(1)

name, fname = CIRCUITS[circuit_id]
fpath = BASE / fname
if not fpath.exists():
    candidates = list(BASE.glob(f"{circuit_id}*"))
    if candidates:
        fpath = candidates[0]

qc = QuantumCircuit.from_qasm_file(str(fpath))
n = qc.num_qubits
two_q = sum(1 for i in qc.data if i.operation.num_qubits == 2)
print(f"{circuit_id}: {name}")
print(f"  Qubits: {n} | Depth: {qc.depth()} | 2q gates: {two_q}")
qc.measure_all()

for bd in bond_dims:
    print(f"\n--- Bond dimension: {bd} ---")
    sim = AerSimulator(method='matrix_product_state')
    tc = transpile(qc, sim)
    
    t0 = time.time()
    try:
        result = sim.run(
            tc,
            shots=10000,
            matrix_product_state_max_bond_dimension=bd,
        ).result()
        elapsed = time.time() - t0
        
        counts = result.get_counts()
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        peak_bs = sorted_counts[0][0]
        peak_val = sorted_counts[0][1]
        unique = len(counts)
        
        print(f"  Time: {elapsed:.0f}s")
        print(f"  Peak: {peak_bs} (count: {peak_val}/10000, {peak_val/100:.1f}%)")
        print(f"  Unique bitstrings: {unique}/10000")
        print(f"  Top 5:")
        for bs, ct in sorted_counts[:5]:
            print(f"    |{bs}⟩ = {ct}")
        
        # If we found a real peak (>1% of shots), save it
        if peak_val > 100:
            print(f"\n  *** PEAK FOUND! {peak_bs} with {peak_val/100:.1f}% probability ***")
            results[circuit_id] = {
                "name": name,
                "peak_bitstring": peak_bs,
                "peak_value": peak_val,
                "device": f"local_mps_bd{bd}",
                "num_qubits": n,
                "bond_dim": bd,
                "shots": 10000,
            }
            RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
            break
        elif peak_val > 10:
            print(f"\n  Possible weak signal at bond_dim={bd}. Trying higher...")
        else:
            print(f"\n  No peak detected at bond_dim={bd}.")
            
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  ERROR after {elapsed:.0f}s: {e}")
        if "memory" in str(e).lower():
            print("  Out of memory. Cannot increase bond dimension further.")
            break
