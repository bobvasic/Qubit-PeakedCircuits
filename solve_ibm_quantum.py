#!/usr/bin/env python3
"""
Solve remaining peaked circuits using IBM Quantum hardware (free Open Plan).
Uses IBM Heron r2 156-qubit QPU via qiskit-ibm-runtime.
"""

import os, sys, json
from pathlib import Path

# Load tokens
env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

BASE_DIR = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE_DIR / "results.json"
results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}

# Connect to IBM Quantum
print("Connecting to IBM Quantum...")
try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["IBM_QUANTUM_TOKEN"])
except Exception:
    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform",
        token=os.environ["IBM_QUANTUM_TOKEN"],
        overwrite=True
    )
    service = QiskitRuntimeService(channel="ibm_quantum_platform")

# Get the best available backend
backend = service.least_busy(simulator=False, min_num_qubits=62, operational=True)
print(f"Backend: {backend.name} ({backend.num_qubits} qubits)")

CIRCUITS = [
    ("P4",  "Golden Mountain",  "P4_golden_mountain.qasm"),
    ("P5",  "Granite Summit",   "P5_granite_summit.qasm"),
    ("P6",  "Titan Pinnacle",   "P6_titan_pinnacle.qasm"),
    ("P7",  "Heavy Hex 1275",   "P7_heavy_hex_1275.qasm"),
    ("P8",  "Grid 888 iSwap",   "P8_grid_888_iswap.qasm"),
    ("P9",  "HQAP 1917",        "P9_hqap_1917.qasm"),
    ("P10", "Heavy Hex 4020",   "P10_heavy_hex_4020.qasm"),
]

targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else [c[0] for c in CIRCUITS]

# Transpile and submit
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

for cid, name, fname in CIRCUITS:
    if cid not in targets:
        continue
    if cid in results and "peak_bitstring" in results.get(cid, {}):
        print(f"\n  {cid} already solved: {results[cid]['peak_bitstring']} - skipping")
        continue

    print(f"\n{'='*60}")
    print(f"  {cid}: {name}")
    print(f"{'='*60}")

    try:
        qc = QuantumCircuit.from_qasm_file(str(BASE_DIR / fname))
    except Exception as e:
        print(f"  QASM load error: {e}")
        results[cid] = {"name": name, "error": str(e)}
        RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
        continue

    n = qc.num_qubits
    print(f"  Qubits: {n} | Gates: {qc.size()} | Depth: {qc.depth()}")

    # Add measurements
    if qc.num_clbits == 0:
        qc.measure_all()

    # Transpile for hardware
    print(f"  Transpiling for {backend.name}...")
    try:
        transpiled = pm.run(qc)
        print(f"  Transpiled: {transpiled.size()} gates, depth {transpiled.depth()}")
    except Exception as e:
        print(f"  Transpilation error: {e}")
        results[cid] = {"name": name, "error": f"transpile: {e}"}
        RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
        continue

    # Run on QPU
    print(f"  Submitting to {backend.name} (1000 shots)...")
    try:
        sampler = Sampler(mode=backend)
        job = sampler.run([transpiled], shots=1000)
        print(f"  Job ID: {job.job_id()}")
        print(f"  Waiting for results...")
        result = job.result()

        # Extract counts
        pub_result = result[0]
        counts = pub_result.data.meas.get_counts()

        peak = max(counts, key=counts.get)
        top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

        print(f"  SOLVED! Peak: {peak} (count: {counts[peak]}/1000)")
        for bs, ct in top5:
            print(f"    |{bs}> = {ct}")

        results[cid] = {
            "name": name,
            "peak_bitstring": peak,
            "peak_value": counts[peak],
            "device": backend.name,
            "num_qubits": n,
            "job_id": job.job_id(),
        }

    except Exception as e:
        print(f"  ERROR: {e}")
        results[cid] = {"name": name, "error": str(e)}

    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

# Summary
print(f"\n{'='*60}")
print(f"  CURRENT STATUS")
print(f"{'='*60}")
ALL = [("P1","Little Peak"),("P2","Swift Rise"),("P3","Sharp Peak"),
       ("P4","Golden Mountain"),("P5","Granite Summit"),("P6","Titan Pinnacle"),
       ("P7","Heavy Hex 1275"),("P8","Grid 888 iSwap"),("P9","HQAP 1917"),
       ("P10","Heavy Hex 4020")]
for pid, pname in ALL:
    if pid in results and "peak_bitstring" in results[pid]:
        print(f"  {pid:4s} ({pname:20s}): {results[pid]['peak_bitstring']}")
    else:
        err = results.get(pid, {}).get("error", "not attempted")
        print(f"  {pid:4s} ({pname:20s}): PENDING ({err})")
