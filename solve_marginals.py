#!/usr/bin/env python3
"""
RADICAL APPROACH: Extract peak bitstring from per-qubit marginal probabilities.

Even when MPS can't find the peak bitstring directly (all counts=1),
the per-qubit marginals still carry signal about the correct answer.
Each qubit position shows a bias toward the correct bit value.

We run multiple MPS simulations at low bond dimensions (fast!) and
aggregate the marginal statistics to reconstruct the peak bitstring.
"""
import sys
import json
import time
import numpy as np
from pathlib import Path
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

CIRCUITS = {
    "P4":  ("Golden Mountain",  "P4_golden_mountain.qasm"),
    "P5":  ("Granite Summit",   "P5_granite_summit.qasm"),
    "P6":  ("Titan Pinnacle",   "P6_titan_pinnacle.qasm"),
    "P7":  ("Heavy Hex 1275",   "P7_heavy_hex_1275.qasm"),
    "P8":  ("Grid 888 iSwap",   "P8_grid_888_iswap.qasm"),
    "P9":  ("HQAP 1917",        "P9_hqap_1917.qasm"),
    "P10": ("Heavy Hex 4020",   "P10_heavy_hex_4020.qasm"),
}


def analyze_marginals(counts, n_qubits):
    """Extract per-qubit marginal probabilities from counts dict.
    
    Returns: array of shape (n_qubits,) with P(qubit_i = 1) for each qubit.
    Qiskit convention: bitstring is MSB first, so position 0 = qubit n-1.
    """
    total = sum(counts.values())
    p1 = np.zeros(n_qubits)
    
    for bitstring, count in counts.items():
        for pos, bit in enumerate(bitstring):
            if bit == '1':
                p1[pos] += count
    
    p1 /= total
    return p1


def marginals_to_bitstring(p1):
    """Convert marginal probabilities to a bitstring using majority vote."""
    return ''.join('1' if p > 0.5 else '0' for p in p1)


def marginal_confidence(p1):
    """Return average confidence (distance from 0.5) across all qubits."""
    return np.mean(np.abs(p1 - 0.5))


def solve_circuit_marginals(circuit_id, name, fname, bond_dims=[64, 128, 256],
                             shots_per_run=20000, n_runs=3):
    """Solve a circuit using marginal analysis with multiple MPS runs."""
    fpath = BASE / fname
    if not fpath.exists():
        candidates = list(BASE.glob(f"{circuit_id}*"))
        if candidates:
            fpath = candidates[0]
    
    qc = QuantumCircuit.from_qasm_file(str(fpath))
    n = qc.num_qubits
    two_q = sum(1 for i in qc.data if i.operation.num_qubits == 2)
    print(f"\n{'='*60}")
    print(f"  {circuit_id}: {name} ({n}q, {two_q} 2q gates)")
    print(f"{'='*60}")
    
    qc.measure_all()
    sim = AerSimulator(method='matrix_product_state')
    tc = transpile(qc, sim)
    
    # Accumulate marginals across multiple bond dimensions and runs
    all_p1 = []
    
    for bd in bond_dims:
        for run_idx in range(n_runs):
            t0 = time.time()
            try:
                result = sim.run(
                    tc,
                    shots=shots_per_run,
                    matrix_product_state_max_bond_dimension=bd,
                    seed_simulator=42 + run_idx * 1000 + bd,
                ).result()
                elapsed = time.time() - t0
                
                counts = result.get_counts()
                p1 = analyze_marginals(counts, n)
                conf = marginal_confidence(p1)
                bitstring = marginals_to_bitstring(p1)
                
                # Find actual peak in counts
                sorted_c = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_count = sorted_c[0][1]
                unique = len(counts)
                
                print(f"  bd={bd:4d} run={run_idx}: conf={conf:.4f} "
                      f"top_count={top_count} unique={unique}/{shots_per_run} "
                      f"time={elapsed:.0f}s")
                
                all_p1.append(p1)
                
            except Exception as e:
                print(f"  bd={bd:4d} run={run_idx}: ERROR - {str(e)[:80]}")
    
    if not all_p1:
        print("  No successful runs!")
        return None
    
    # Aggregate: weighted average of marginals (higher bond dim = more weight)
    # Simple average for now
    avg_p1 = np.mean(all_p1, axis=0)
    final_bitstring = marginals_to_bitstring(avg_p1)
    final_conf = marginal_confidence(avg_p1)
    
    print(f"\n  RESULT: {final_bitstring}")
    print(f"  Avg confidence: {final_conf:.4f}")
    print(f"  Per-qubit P(1): min={avg_p1.min():.3f} max={avg_p1.max():.3f}")
    
    # Show qubits with low confidence (close to 0.5)
    weak = [(i, avg_p1[i]) for i in range(n) if abs(avg_p1[i] - 0.5) < 0.1]
    if weak:
        print(f"  WARNING: {len(weak)} qubits with confidence < 0.1:")
        for pos, p in weak:
            print(f"    Position {pos}: P(1)={p:.3f}")
    
    return final_bitstring, final_conf, avg_p1


if __name__ == "__main__":
    targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else list(CIRCUITS.keys())
    
    results = {}
    if RESULTS_FILE.exists():
        results = json.loads(RESULTS_FILE.read_text())
    
    for cid in targets:
        if cid not in CIRCUITS:
            print(f"Unknown circuit: {cid}")
            continue
        
        name, fname = CIRCUITS[cid]
        
        # Use different strategies based on circuit size
        two_q = {
            "P4": 5096, "P5": 1892, "P6": 3494, 
            "P7": 1275, "P8": 888, "P9": 1917, "P10": 4020
        }.get(cid, 0)
        
        if two_q <= 1300:
            # Smaller circuits: can use higher bond dims
            bond_dims = [128, 256]
            shots = 30000
            runs = 3
        elif two_q <= 2000:
            bond_dims = [64, 128]
            shots = 20000
            runs = 3
        else:
            # Large circuits: stick to low bond dims, more runs
            bond_dims = [32, 64, 128]
            shots = 15000
            runs = 2
        
        result = solve_circuit_marginals(cid, name, fname,
                                         bond_dims=bond_dims,
                                         shots_per_run=shots,
                                         n_runs=runs)
        
        if result:
            bitstring, conf, avg_p1 = result
            results[cid] = {
                "name": name,
                "peak_bitstring": bitstring,
                "peak_value": f"marginal_conf_{conf:.4f}",
                "device": "marginal_analysis",
                "num_qubits": len(bitstring),
                "confidence": float(conf),
                "reliable": conf > 0.05,  # even small bias is useful
            }
            RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  FINAL RESULTS")
    print(f"{'='*60}")
    for pid in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
        r = results.get(pid, {})
        if "peak_bitstring" in r:
            conf = r.get("confidence", "n/a")
            rel = "✓" if r.get("reliable", True) else "?"
            dev = r.get("device", "?")
            bs = r["peak_bitstring"]
            print(f"  {pid:4s}: {bs[:45]}{'...' if len(bs)>45 else ''} [{dev}] conf={conf} {rel}")
        else:
            print(f"  {pid:4s}: NOT SOLVED")
