#!/usr/bin/env python3
"""
Marginal analysis using BlueQubit CLOUD MPS (paid, fast).
Submits all runs async, collects results, extracts peak from marginals.
"""
import os, sys, json, time
import numpy as np
from pathlib import Path

env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        k, v = line.split("=", 1)
        os.environ[k] = v

import bluequbit
from qiskit import QuantumCircuit

bq = bluequbit.init()
BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

CIRCUITS = [
    ("P8",  "Grid 888 iSwap",  "P8_grid_888_iswap.qasm",   888),
    ("P7",  "Heavy Hex 1275",  "P7_heavy_hex_1275.qasm",  1275),
    ("P5",  "Granite Summit",  "P5_granite_summit.qasm",   1892),
    ("P9",  "HQAP 1917",      "P9_hqap_1917.qasm",        1917),
    ("P6",  "Titan Pinnacle",  "P6_titan_pinnacle.qasm",   3494),
    ("P10", "Heavy Hex 4020",  "P10_heavy_hex_4020.qasm",  4020),
    ("P4",  "Golden Mountain", "P4_golden_mountain.qasm",  5096),
]

targets = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else [c[0] for c in CIRCUITS]


def analyze_marginals(counts, n_qubits):
    total = sum(counts.values())
    p1 = np.zeros(n_qubits)
    for bitstring, count in counts.items():
        for pos, bit in enumerate(bitstring):
            if bit == '1':
                p1[pos] += count
    p1 /= total
    return p1


def marginals_to_bitstring(p1):
    return ''.join('1' if p > 0.5 else '0' for p in p1)


# ── Phase 1: Submit all jobs async ──
print("=" * 60)
print("  Submitting MPS jobs to BlueQubit cloud")
print("=" * 60)

pending = {}  # key -> {job_id, circuit_id, bond_dim, ...}

for cid, name, fname, two_q in CIRCUITS:
    if cid not in targets:
        continue

    fpath = BASE / fname
    if not fpath.exists():
        candidates = list(BASE.glob(f"{cid}*"))
        if candidates:
            fpath = candidates[0]

    qc = QuantumCircuit.from_qasm_file(str(fpath))
    n = qc.num_qubits
    if qc.num_clbits == 0:
        qc.measure_all()

    # Submit multiple bond dimensions
    bond_dims = [64, 128, 256]
    shots = 30000

    for bd in bond_dims:
        key = f"{cid}_bd{bd}"
        try:
            r = bq.run(
                qc, device="mps.cpu", shots=shots,
                job_name=f"marginal_{cid}_bd{bd}",
                asynchronous=True,
                options={"mps_bond_dimension": bd},
            )
            pending[key] = {
                "job_id": r.job_id, "cid": cid, "name": name,
                "n_qubits": n, "bond_dim": bd, "shots": shots,
            }
            print(f"  {key}: submitted (Job {r.job_id})")
        except Exception as e:
            print(f"  {key}: SUBMIT ERROR - {str(e)[:80]}")

print(f"\n  Total jobs submitted: {len(pending)}")

# ── Phase 2: Collect results and compute marginals ──
print(f"\n{'='*60}")
print("  Collecting results...")
print("=" * 60)

# Group marginals by circuit
circuit_marginals = {}  # cid -> list of p1 arrays

while pending:
    done_keys = []
    for key, info in list(pending.items()):
        try:
            r = bq.wait(info["job_id"], timeout=30)
            if r.ok:
                counts = r.get_counts()
                p1 = analyze_marginals(counts, info["n_qubits"])
                conf = np.mean(np.abs(p1 - 0.5))
                bs = marginals_to_bitstring(p1)

                sc = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top = sc[0][1]
                unique = len(counts)

                print(f"  {key}: conf={conf:.4f} top={top} unique={unique}/{info['shots']}")

                if info["cid"] not in circuit_marginals:
                    circuit_marginals[info["cid"]] = {"p1s": [], "name": info["name"], "n": info["n_qubits"]}
                circuit_marginals[info["cid"]]["p1s"].append(p1)
                done_keys.append(key)
            else:
                print(f"  {key}: FAILED - {r.error_message[:80]}")
                done_keys.append(key)
        except Exception as e:
            err = str(e)
            if "didn" in err.lower() or "complete" in err.lower():
                pass  # still running
            else:
                print(f"  {key}: ERROR - {err[:80]}")
                done_keys.append(key)

    for k in done_keys:
        del pending[k]

    if pending:
        remaining = list(pending.keys())
        print(f"  Waiting... {len(remaining)} jobs remaining: {', '.join(remaining[:5])}")
        time.sleep(60)

# ── Phase 3: Aggregate and save results ──
print(f"\n{'='*60}")
print("  RESULTS")
print("=" * 60)

results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}

for cid, data in circuit_marginals.items():
    p1s = data["p1s"]
    if not p1s:
        continue

    avg_p1 = np.mean(p1s, axis=0)
    bitstring = marginals_to_bitstring(avg_p1)
    conf = np.mean(np.abs(avg_p1 - 0.5))

    weak = sum(1 for p in avg_p1 if abs(p - 0.5) < 0.05)
    print(f"\n  {cid} ({data['name']}):")
    print(f"    Answer: {bitstring}")
    print(f"    Confidence: {conf:.4f} ({len(p1s)} runs averaged)")
    print(f"    Weak qubits (<0.05 from 0.5): {weak}/{data['n']}")

    results[cid] = {
        "name": data["name"],
        "peak_bitstring": bitstring,
        "peak_value": f"marginal_conf_{conf:.4f}",
        "device": "marginal_mps_cloud",
        "num_qubits": data["n"],
        "confidence": float(conf),
        "reliable": conf > 0.03 and weak < data["n"] * 0.3,
    }

RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

print(f"\n{'='*60}")
print("  ALL ANSWERS")
print("=" * 60)
for pid in ["P1","P2","P3","P4","P5","P6","P7","P8","P9","P10"]:
    r = results.get(pid, {})
    if "peak_bitstring" in r:
        c = r.get("confidence", "")
        d = r.get("device", "?")
        print(f"  {pid}: {r['peak_bitstring']} [{d}] conf={c}")
    else:
        print(f"  {pid}: NOT SOLVED")
