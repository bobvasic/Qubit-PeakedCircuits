#!/usr/bin/env python3
"""Solve remaining circuits P4-P10 with optimized MPS settings."""

import os, sys, json
from pathlib import Path

env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

import bluequbit
from qiskit import QuantumCircuit

bq = bluequbit.init()
print("BlueQubit client initialized!")

BASE_DIR = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE_DIR / "results.json"
results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}

# Remaining circuits with optimized MPS bond dimensions
# Lower bond_dim = faster but less accurate. For peaked circuits, peak should still show.
REMAINING = [
    # (id, name, file, bond_dim, shots)
    ("P5",  "Granite Summit",   "P5_granite_summit.qasm",   128, 10000),
    ("P7",  "Heavy Hex 1275",   "P7_heavy_hex_1275.qasm",   128, 10000),
    ("P8",  "Grid 888 iSwap",   "P8_grid_888_iswap.qasm",   128, 10000),
    ("P9",  "HQAP 1917",        "P9_hqap_1917.qasm",         64, 10000),
    ("P4",  "Golden Mountain",  "P4_golden_mountain.qasm",    64, 10000),
    ("P6",  "Titan Pinnacle",   "P6_titan_pinnacle.qasm",     64, 10000),
    ("P10", "Heavy Hex 4020",   "P10_heavy_hex_4020.qasm",    64, 10000),
]

targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else [c[0] for c in REMAINING]

for cid, name, fname, bond_dim, shots in REMAINING:
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
    print(f"  Device: mps.cpu | Bond dim: {bond_dim} | Shots: {shots}")

    if qc.num_clbits == 0:
        qc.measure_all()

    try:
        print(f"  Submitting to BlueQubit cloud (async)...")
        job = bq.run(
            qc,
            device="mps.cpu",
            shots=shots,
            job_name=f"hackathon_{cid}",
            options={"mps_bond_dimension": bond_dim},
            asynchronous=True
        )
        print(f"  Job submitted! ID: {job.job_id}")
        print(f"  Waiting for completion (timeout=1800s)...")

        result = bq.wait(job.job_id, timeout=1800)

        if result.ok:
            counts = result.get_counts()
            if counts:
                peak = max(counts, key=counts.get)
                top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"  SOLVED! Peak: {peak} (count: {counts[peak]})")
                print(f"  Runtime: {result.run_time_ms}ms")
                for bs, ct in top5:
                    print(f"    |{bs}> = {ct}")
                results[cid] = {
                    "name": name, "peak_bitstring": peak,
                    "peak_value": counts[peak], "device": "mps.cpu",
                    "bond_dim": bond_dim, "runtime_ms": result.run_time_ms,
                    "num_qubits": n,
                }
        else:
            print(f"  FAILED: {result.error_message}")
            results[cid] = {"name": name, "error": result.error_message}

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
