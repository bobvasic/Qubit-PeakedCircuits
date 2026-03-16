#!/usr/bin/env python3
"""
BlueQubit Peaked Circuits Hackathon - Master Solver
Submits all 10 circuits to REAL quantum hardware via BlueQubit SDK.
Finds the peak bitstring for each circuit.
"""

import os
import sys
import time
import json
from pathlib import Path

# Load API key from .env file
env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

import bluequbit
from qiskit import QuantumCircuit

# Initialize BlueQubit client with real quantum hardware
bq = bluequbit.init()
print("BlueQubit client initialized successfully!")
print()

# Circuit files in order
CIRCUITS = [
    ("P1", "Little Peak",       "P1_little_peak.qasm",      4),
    ("P2", "Swift Rise",        "P2_swift_rise.qasm",       28),
    ("P3", "Sharp Peak",        "P3_sharp_peak.qasm",       44),
    ("P4", "Golden Mountain",   "P4_golden_mountain.qasm",  48),
    ("P5", "Granite Summit",    "P5_granite_summit.qasm",   44),
    ("P6", "Titan Pinnacle",    "P6_titan_pinnacle.qasm",   62),
    ("P7", "Heavy Hex 1275",    "P7_heavy_hex_1275.qasm",   45),
    ("P8", "Grid 888 iSwap",    "P8_grid_888_iswap.qasm",   None),  # custom gate
    ("P9", "HQAP 1917",         "P9_hqap_1917.qasm",        56),
    ("P10","Heavy Hex 4020",    "P10_heavy_hex_4020.qasm",   49),
]

BASE_DIR = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE_DIR / "results.json"

# Load existing results if any
results = {}
if RESULTS_FILE.exists():
    results = json.loads(RESULTS_FILE.read_text())

def load_circuit(filename):
    """Load a QASM circuit file into a Qiskit QuantumCircuit."""
    filepath = BASE_DIR / filename
    qc = QuantumCircuit.from_qasm_file(str(filepath))
    return qc

def submit_circuit(bq_client, circuit_id, name, filename, shots=1000):
    """Submit a single circuit to quantum hardware."""
    print(f"\n{'='*60}")
    print(f"  {circuit_id}: {name}")
    print(f"  File: {filename}")
    print(f"{'='*60}")

    try:
        qc = load_circuit(filename)
        print(f"  Qubits: {qc.num_qubits} | Gates: {qc.size()} | Depth: {qc.depth()}")

        # Add measurements if not present
        if qc.num_clbits == 0:
            qc.measure_all()

        # Estimate first
        print(f"  Estimating cost...")
        try:
            estimate = bq_client.estimate(qc, device="quantum")
            print(f"  Est. runtime: {estimate.estimated_runtime}ms | Est. cost: ${estimate.estimated_cost:.4f}")
            if estimate.warning_message:
                print(f"  Warning: {estimate.warning_message}")
        except Exception as e:
            print(f"  Estimate failed: {e}")

        # Submit to quantum hardware
        print(f"  Submitting to quantum device (shots={shots})...")
        job = bq_client.run(
            qc,
            device="quantum",
            shots=shots,
            job_name=f"hackathon_{circuit_id}",
            asynchronous=True
        )
        print(f"  Job submitted! ID: {job.job_id}")
        return job

    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def collect_results(bq_client, jobs_map):
    """Wait for all jobs and collect results."""
    print(f"\n{'='*60}")
    print(f"  COLLECTING RESULTS")
    print(f"{'='*60}")

    for circuit_id, (name, job) in jobs_map.items():
        if job is None:
            print(f"\n  {circuit_id} ({name}): SKIPPED (submission failed)")
            continue

        print(f"\n  Waiting for {circuit_id} ({name}) - Job: {job.job_id}...")
        try:
            result = bq_client.wait(job.job_id, timeout=600)

            if result.ok:
                counts = result.get_counts()
                if counts:
                    # Find peak bitstring (most frequent measurement)
                    peak_bitstring = max(counts, key=counts.get)
                    peak_count = counts[peak_bitstring]
                    total_shots = sum(counts.values()) if isinstance(list(counts.values())[0], int) else 1.0

                    print(f"  STATUS: COMPLETED")
                    print(f"  Peak bitstring: {peak_bitstring}")
                    print(f"  Peak count/prob: {peak_count}")
                    print(f"  Runtime: {result.run_time_ms}ms")

                    # Show top 5
                    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f"  Top 5:")
                    for bs, ct in sorted_counts:
                        print(f"    |{bs}⟩  = {ct}")

                    results[circuit_id] = {
                        "name": name,
                        "peak_bitstring": peak_bitstring,
                        "peak_value": peak_count,
                        "job_id": job.job_id,
                        "runtime_ms": result.run_time_ms,
                        "top5": sorted_counts[:5],
                    }
                else:
                    print(f"  STATUS: COMPLETED but no counts returned")
                    # Try statevector
                    if result.has_statevector:
                        import numpy as np
                        sv = result.get_statevector()
                        probs = np.abs(np.array(sv)) ** 2
                        peak_idx = np.argmax(probs)
                        n = result.num_qubits
                        peak_bitstring = format(peak_idx, f'0{n}b')
                        print(f"  Peak from statevector: {peak_bitstring} (P={probs[peak_idx]:.6f})")
                        results[circuit_id] = {
                            "name": name,
                            "peak_bitstring": peak_bitstring,
                            "peak_prob": float(probs[peak_idx]),
                            "job_id": job.job_id,
                        }
            else:
                print(f"  STATUS: FAILED - {result.error_message}")
                results[circuit_id] = {"name": name, "error": result.error_message}

        except Exception as e:
            print(f"  ERROR waiting: {e}")
            results[circuit_id] = {"name": name, "error": str(e)}

    # Save results
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to {RESULTS_FILE}")

def print_summary():
    """Print final summary of all answers."""
    print(f"\n{'='*60}")
    print(f"  FINAL ANSWERS FOR SUBMISSION")
    print(f"{'='*60}")
    for pid, pname, _, _ in CIRCUITS:
        if pid in results and "peak_bitstring" in results[pid]:
            r = results[pid]
            print(f"  {pid} ({pname}): {r['peak_bitstring']}")
        else:
            print(f"  {pid} ({pname}): NOT SOLVED")

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    # Determine which circuits to run
    if len(sys.argv) > 1:
        # Run specific circuits: python solve_all_quantum.py P1 P2 P3
        targets = [a.upper() for a in sys.argv[1:]]
    else:
        # Run all
        targets = [c[0] for c in CIRCUITS]

    # Phase 1: Submit all circuits
    jobs = {}
    for circuit_id, name, filename, qubits in CIRCUITS:
        if circuit_id not in targets:
            continue
        if circuit_id in results and "peak_bitstring" in results.get(circuit_id, {}):
            print(f"  {circuit_id} already solved: {results[circuit_id]['peak_bitstring']} - skipping")
            continue

        job = submit_circuit(bq, circuit_id, name, filename, shots=1000)
        if job:
            jobs[circuit_id] = (name, job)

    # Phase 2: Collect results
    if jobs:
        collect_results(bq, jobs)

    # Phase 3: Summary
    print_summary()
