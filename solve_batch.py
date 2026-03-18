#!/usr/bin/env python3
"""
Batch solver for P4-P10.
- P7 → IBM Quantum (ibm_fez) with error mitigation (native heavy-hex)
- All others → BlueQubit MPS
"""
import os
import sys
import json
import time
from pathlib import Path

# Load API keys
env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

from qiskit import QuantumCircuit, transpile
import numpy as np

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

results = {}
if RESULTS_FILE.exists():
    results = json.loads(RESULTS_FILE.read_text())


def save_results():
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))


def solve_ibm(circuit_id, name, fname):
    """Run on IBM Quantum with Sampler + error mitigation."""
    print(f"\n{'='*60}")
    print(f"  {circuit_id}: {name} → IBM QUANTUM")
    print(f"{'='*60}")

    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    token = os.environ.get("IBM_QUANTUM_TOKEN")
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")

    fpath = BASE / fname
    if not fpath.exists():
        candidates = list(BASE.glob(f"{circuit_id}*"))
        if candidates:
            fpath = candidates[0]

    qc = QuantumCircuit.from_qasm_file(str(fpath))
    n = qc.num_qubits
    print(f"  Qubits: {n} | Gates: {qc.size()} | Depth: {qc.depth()}")

    # Add measurements
    qc.measure_all()

    # Transpile with high optimization
    print("  Transpiling (optimization_level=3)...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    tc = pm.run(qc)
    td = tc.depth()
    t2q = sum(1 for i in tc.data if i.operation.num_qubits == 2)
    print(f"  Transpiled: depth={td}, 2q_gates={t2q}")

    # Run with Sampler (supports error mitigation in V2)
    print("  Submitting to IBM Quantum (ibm_fez)...")
    sampler = SamplerV2(mode=backend)
    job = sampler.run([tc], shots=4096)
    print(f"  Job ID: {job.job_id()}")
    print("  Waiting for results...")

    result = job.result()
    pub_result = result[0]

    # Extract counts from SamplerV2 result
    counts = pub_result.data.meas.get_counts()
    if counts:
        # Sort by count
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        peak_bs = sorted_counts[0][0]
        peak_val = sorted_counts[0][1]

        print(f"  Peak: {peak_bs} (count: {peak_val}/4096)")
        print(f"  Top 10:")
        for bs, ct in sorted_counts[:10]:
            print(f"    |{bs}⟩ = {ct}")

        # Check if we have a real peak (not noise)
        if peak_val > 10:  # More than ~0.25% of shots
            results[circuit_id] = {
                "name": name,
                "peak_bitstring": peak_bs,
                "peak_value": peak_val,
                "device": "ibm_fez",
                "num_qubits": n,
                "job_id": job.job_id(),
                "transpiled_depth": td,
                "transpiled_2q_gates": t2q,
                "shots": 4096,
                "reliable": peak_val > 50,
            }
            save_results()
            return peak_bs
        else:
            print("  WARNING: No clear peak detected (noise dominated)")
            results[circuit_id] = {
                "name": name,
                "peak_bitstring": peak_bs,
                "peak_value": peak_val,
                "device": "ibm_fez",
                "num_qubits": n,
                "job_id": job.job_id(),
                "warning": "Possibly noise dominated",
                "reliable": False,
            }
            save_results()
            return None
    else:
        print("  ERROR: No counts returned")
        return None


def solve_mps(circuit_id, name, fname, bond_dim=256, shots=10000):
    """Run on BlueQubit MPS simulator."""
    print(f"\n{'='*60}")
    print(f"  {circuit_id}: {name} → BLUEQUBIT MPS (bond_dim={bond_dim})")
    print(f"{'='*60}")

    import bluequbit
    bq = bluequbit.init()

    fpath = BASE / fname
    if not fpath.exists():
        candidates = list(BASE.glob(f"{circuit_id}*"))
        if candidates:
            fpath = candidates[0]

    qc = QuantumCircuit.from_qasm_file(str(fpath))
    n = qc.num_qubits
    print(f"  Qubits: {n} | Gates: {qc.size()} | Depth: {qc.depth()}")

    if qc.num_clbits == 0:
        qc.measure_all()

    print(f"  Submitting to BlueQubit cloud (MPS, {shots} shots)...")
    t0 = time.time()

    result = bq.run(
        qc,
        device="mps.cpu",
        shots=shots,
        job_name=f"hackathon_{circuit_id}",
        asynchronous=False,
        options={"mps_bond_dimension": bond_dim},
    )

    elapsed = time.time() - t0

    if result.ok:
        counts = result.get_counts()
        if counts:
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            peak_bs = sorted_counts[0][0]
            peak_val = sorted_counts[0][1]

            print(f"  SOLVED! Peak: {peak_bs}")
            print(f"  Count: {peak_val}/{shots} ({peak_val/shots*100:.1f}%)")
            print(f"  Runtime: {elapsed:.0f}s | Cost: ${result.cost:.4f}")
            print(f"  Top 5:")
            for bs, ct in sorted_counts[:5]:
                print(f"    |{bs}⟩ = {ct}")

            results[circuit_id] = {
                "name": name,
                "peak_bitstring": peak_bs,
                "peak_value": peak_val,
                "device": "mps.cpu",
                "runtime_ms": int(elapsed * 1000),
                "cost": float(result.cost),
                "num_qubits": n,
                "bond_dim": bond_dim,
                "shots": shots,
            }
            save_results()
            return peak_bs
        else:
            print("  ERROR: No counts")
            return None
    else:
        print(f"  FAILED: {result.error_message}")
        results[circuit_id] = {"name": name, "error": result.error_message}
        save_results()
        return None


if __name__ == "__main__":
    # Parse CLI args: which circuits to solve
    targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else None

    # Strategy ordered by priority
    plan = [
        ("P7",  "Heavy Hex 1275",  "P7_heavy_hex_1275.qasm",  "ibm"),
        ("P8",  "Grid 888 iSwap",  "P8_grid_888_iswap.qasm",  "mps"),
        ("P5",  "Granite Summit",   "P5_granite_summit.qasm",  "mps"),
        ("P7",  "Heavy Hex 1275",  "P7_heavy_hex_1275.qasm",  "mps"),  # fallback
        ("P4",  "Golden Mountain",  "P4_golden_mountain.qasm", "mps"),
        ("P9",  "HQAP 1917",       "P9_hqap_1917.qasm",       "mps"),
        ("P6",  "Titan Pinnacle",   "P6_titan_pinnacle.qasm",  "mps"),
        ("P10", "Heavy Hex 4020",   "P10_heavy_hex_4020.qasm", "mps"),
    ]

    for circuit_id, name, fname, method in plan:
        if targets and circuit_id not in targets:
            continue

        # Skip if already solved reliably
        existing = results.get(circuit_id, {})
        if "peak_bitstring" in existing and existing.get("reliable", True):
            print(f"\n  {circuit_id} already solved: {existing['peak_bitstring']} - skipping")
            continue

        try:
            if method == "ibm":
                solve_ibm(circuit_id, name, fname)
            else:
                solve_mps(circuit_id, name, fname, bond_dim=256, shots=10000)
        except Exception as e:
            print(f"\n  {circuit_id} ERROR: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    all_ids = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
    for pid in all_ids:
        r = results.get(pid, {})
        if "peak_bitstring" in r:
            rel = "✓" if r.get("reliable", True) else "?"
            print(f"  {pid:4s}: {r['peak_bitstring']} [{r.get('device','?')}] {rel}")
        else:
            print(f"  {pid:4s}: NOT SOLVED")
