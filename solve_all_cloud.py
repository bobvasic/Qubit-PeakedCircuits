#!/usr/bin/env python3
"""
BlueQubit Peaked Circuits Hackathon - Cloud Simulator Solver
Tiered approach: cpu for <=34 qubits, mps.cpu for larger circuits.
All execution happens on BlueQubit's cloud infrastructure.
"""

import os
import sys
import json
from pathlib import Path

# Load API key
env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

import bluequbit
from qiskit import QuantumCircuit

bq = bluequbit.init()
print("BlueQubit client initialized!")

CIRCUITS = [
    ("P1",  "Little Peak",      "P1_little_peak.qasm"),
    ("P2",  "Swift Rise",       "P2_swift_rise.qasm"),
    ("P3",  "Sharp Peak",       "P3_sharp_peak.qasm"),
    ("P4",  "Golden Mountain",  "P4_golden_mountain.qasm"),
    ("P5",  "Granite Summit",   "P5_granite_summit.qasm"),
    ("P6",  "Titan Pinnacle",   "P6_titan_pinnacle.qasm"),
    ("P7",  "Heavy Hex 1275",   "P7_heavy_hex_1275.qasm"),
    ("P8",  "Grid 888 iSwap",   "P8_grid_888_iswap.qasm"),
    ("P9",  "HQAP 1917",        "P9_hqap_1917.qasm"),
    ("P10", "Heavy Hex 4020",   "P10_heavy_hex_4020.qasm"),
]

BASE_DIR = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE_DIR / "results.json"

results = {}
if RESULTS_FILE.exists():
    results = json.loads(RESULTS_FILE.read_text())


def pick_device(num_qubits):
    """Choose the best device based on qubit count."""
    if num_qubits <= 34:
        return "cpu", None, None       # exact statevector
    elif num_qubits <= 36:
        return "gpu", None, None       # exact statevector (GPU)
    else:
        return "mps.cpu", 256, 10000   # MPS with bond_dim=256, 10k shots


def solve_circuit(bq_client, circuit_id, name, filename):
    """Load, submit, wait, and extract peak bitstring for one circuit."""
    print(f"\n{'='*60}")
    print(f"  {circuit_id}: {name}")
    print(f"{'='*60}")

    filepath = BASE_DIR / filename
    try:
        qc = QuantumCircuit.from_qasm_file(str(filepath))
    except Exception as e:
        print(f"  QASM load error: {e}")
        return None

    n = qc.num_qubits
    device, bond_dim, shots = pick_device(n)
    print(f"  Qubits: {n} | Gates: {qc.size()} | Depth: {qc.depth()}")
    print(f"  Device: {device} | Bond dim: {bond_dim} | Shots: {shots}")

    # Add measurements for MPS (needs shots)
    if shots and qc.num_clbits == 0:
        qc.measure_all()

    try:
        # Build run kwargs
        kwargs = {
            "device": device,
            "job_name": f"hackathon_{circuit_id}",
            "asynchronous": False,   # wait for completion
        }
        if shots:
            kwargs["shots"] = shots
        if bond_dim:
            kwargs["options"] = {"mps_bond_dimension": bond_dim}

        print(f"  Submitting to BlueQubit cloud...")
        result = bq_client.run(qc, **kwargs)

        if result.ok:
            counts = result.get_counts()
            if counts:
                peak_bs = max(counts, key=counts.get)
                peak_val = counts[peak_bs]
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

                print(f"  SOLVED! Peak: {peak_bs} (value: {peak_val})")
                print(f"  Runtime: {result.run_time_ms}ms | Cost: ${result.cost:.4f}")
                print(f"  Top 5:")
                for bs, ct in sorted_counts:
                    print(f"    |{bs}⟩ = {ct}")

                results[circuit_id] = {
                    "name": name,
                    "peak_bitstring": peak_bs,
                    "peak_value": peak_val,
                    "device": device,
                    "runtime_ms": result.run_time_ms,
                    "cost": result.cost,
                    "num_qubits": n,
                }
                return peak_bs
            else:
                # No counts = statevector mode (cpu/gpu)
                if result.has_statevector:
                    import numpy as np
                    sv = result.get_statevector()
                    probs = np.abs(np.array(sv)) ** 2
                    peak_idx = np.argmax(probs)
                    peak_bs = format(peak_idx, f'0{n}b')
                    peak_prob = probs[peak_idx]

                    sorted_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:5]
                    print(f"  SOLVED! Peak: {peak_bs} (P={peak_prob:.6f})")
                    print(f"  Runtime: {result.run_time_ms}ms | Cost: ${result.cost:.4f}")
                    print(f"  Top 5:")
                    for idx in sorted_indices:
                        bs = format(idx, f'0{n}b')
                        print(f"    |{bs}⟩ P={probs[idx]:.6f}")

                    results[circuit_id] = {
                        "name": name,
                        "peak_bitstring": peak_bs,
                        "peak_prob": float(peak_prob),
                        "device": device,
                        "runtime_ms": result.run_time_ms,
                        "cost": result.cost,
                        "num_qubits": n,
                    }
                    return peak_bs
        else:
            print(f"  FAILED: {result.error_message}")
            results[circuit_id] = {"name": name, "error": result.error_message}
            return None

    except Exception as e:
        print(f"  ERROR: {e}")
        results[circuit_id] = {"name": name, "error": str(e)}
        return None


if __name__ == "__main__":
    targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else [c[0] for c in CIRCUITS]

    for circuit_id, name, filename in CIRCUITS:
        if circuit_id not in targets:
            continue
        if circuit_id in results and "peak_bitstring" in results.get(circuit_id, {}):
            print(f"\n  {circuit_id} already solved: {results[circuit_id]['peak_bitstring']} - skipping")
            continue
        solve_circuit(bq, circuit_id, name, filename)
        # Save after each circuit
        RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

    # Final summary
    print(f"\n{'='*60}")
    print(f"  FINAL ANSWERS FOR SUBMISSION")
    print(f"{'='*60}")
    total_cost = 0
    for pid, pname, _ in CIRCUITS:
        if pid in results and "peak_bitstring" in results[pid]:
            r = results[pid]
            cost = r.get("cost", 0) or 0
            total_cost += cost
            print(f"  {pid:4s} ({pname:20s}): {r['peak_bitstring']}")
        else:
            err = results.get(pid, {}).get("error", "not attempted")
            print(f"  {pid:4s} ({pname:20s}): NOT SOLVED ({err})")
    print(f"\n  Total cost: ${total_cost:.4f}")
