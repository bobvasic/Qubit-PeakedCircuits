#!/usr/bin/env python3
"""
Two-phase solver:
1. Submit all unsolved circuits to BlueQubit cloud MPS (bond_dim=512) asynchronously
2. Poll every 15 min for QPU availability; if online, submit all unsolved to QPU

Usage: python solve_cloud_async.py
"""
import os
import sys
import json
import time
from pathlib import Path

env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

import bluequbit
from qiskit import QuantumCircuit

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"
JOBS_FILE = BASE / "pending_jobs.json"

CIRCUITS = [
    ("P8",  "Grid 888 iSwap",  "P8_grid_888_iswap.qasm"),
    ("P7",  "Heavy Hex 1275",  "P7_heavy_hex_1275.qasm"),
    ("P5",  "Granite Summit",  "P5_granite_summit.qasm"),
    ("P4",  "Golden Mountain", "P4_golden_mountain.qasm"),
    ("P9",  "HQAP 1917",      "P9_hqap_1917.qasm"),
    ("P6",  "Titan Pinnacle",  "P6_titan_pinnacle.qasm"),
    ("P10", "Heavy Hex 4020",  "P10_heavy_hex_4020.qasm"),
]


def load_results():
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return {}


def save_results(results):
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))


def load_jobs():
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text())
    return {}


def save_jobs(jobs):
    JOBS_FILE.write_text(json.dumps(jobs, indent=2, default=str))


def is_solved(results, cid):
    r = results.get(cid, {})
    return "peak_bitstring" in r and r.get("reliable", True)


def load_circuit(fname):
    fpath = BASE / fname
    if not fpath.exists():
        pid = fname.split("_")[0]
        candidates = list(BASE.glob(f"{pid}*"))
        if candidates:
            fpath = candidates[0]
    return QuantumCircuit.from_qasm_file(str(fpath))


def check_qpu_online(bq):
    """Quick check if QPU is online."""
    try:
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()
        result = bq.run(qc, device="quantum", shots=10, asynchronous=False,
                        job_name="qpu_ping", timeout=120)
        return result.ok
    except Exception as e:
        if "offline" in str(e).lower() or "TERMINATED" in str(e):
            return False
        return False


def submit_mps_async(bq, circuit_id, name, fname, bond_dim=512, shots=10000):
    """Submit circuit to BlueQubit MPS asynchronously."""
    qc = load_circuit(fname)
    n = qc.num_qubits
    if qc.num_clbits == 0:
        qc.measure_all()

    print(f"  Submitting {circuit_id} ({name}, {n}q) → MPS bond_dim={bond_dim}...")
    result = bq.run(
        qc,
        device="mps.cpu",
        shots=shots,
        job_name=f"hackathon_{circuit_id}_bd{bond_dim}",
        asynchronous=True,
        options={"mps_bond_dimension": bond_dim},
    )
    job_id = result.job_id
    print(f"    Job ID: {job_id}")
    return job_id


def submit_qpu(bq, circuit_id, name, fname, shots=4096):
    """Submit circuit to BlueQubit QPU asynchronously."""
    qc = load_circuit(fname)
    n = qc.num_qubits
    if qc.num_clbits == 0:
        qc.measure_all()

    print(f"  Submitting {circuit_id} ({name}, {n}q) → QPU ({shots} shots)...")
    result = bq.run(
        qc,
        device="quantum",
        shots=shots,
        job_name=f"hackathon_{circuit_id}_qpu",
        asynchronous=True,
    )
    job_id = result.job_id
    print(f"    Job ID: {job_id}")
    return job_id


def check_job_result(bq, job_id, circuit_id, name, device_label):
    """Check if an async job is complete and extract results."""
    try:
        result = bq.wait(job_id, timeout=10)
        if result.ok:
            counts = result.get_counts()
            if counts:
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                peak_bs = sorted_counts[0][0]
                peak_val = sorted_counts[0][1]
                total = sum(counts.values())

                print(f"  {circuit_id} [{device_label}]: peak={peak_bs} "
                      f"({peak_val}/{total}, {peak_val/total*100:.1f}%)")

                # Check if it's a real peak
                reliable = peak_val > max(10, total * 0.005)  # >0.5% of shots
                if not reliable:
                    print(f"    WARNING: Likely noise (peak count too low)")

                return {
                    "name": name,
                    "peak_bitstring": peak_bs,
                    "peak_value": peak_val,
                    "device": device_label,
                    "num_qubits": len(peak_bs),
                    "job_id": job_id,
                    "shots": total,
                    "reliable": reliable,
                }
        else:
            print(f"  {circuit_id} [{device_label}]: FAILED - {result.error_message}")
    except Exception as e:
        err = str(e)
        if "RUNNING" in err or "PENDING" in err or "timeout" in err.lower():
            print(f"  {circuit_id} [{device_label}]: still running...")
            return "RUNNING"
        else:
            print(f"  {circuit_id} [{device_label}]: ERROR - {err[:100]}")
    return None


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bq = bluequbit.init()
    results = load_results()
    pending = load_jobs()

    # ── Phase 1: Submit MPS jobs for all unsolved circuits ──
    print("=" * 60)
    print("  PHASE 1: Submit MPS jobs (bond_dim=512)")
    print("=" * 60)

    for cid, name, fname in CIRCUITS:
        if is_solved(results, cid):
            print(f"  {cid}: already solved ✓")
            continue
        mps_key = f"{cid}_mps512"
        if mps_key not in pending:
            try:
                job_id = submit_mps_async(bq, cid, name, fname, bond_dim=512)
                pending[mps_key] = {
                    "job_id": job_id,
                    "circuit_id": cid,
                    "name": name,
                    "fname": fname,
                    "device": "mps.cpu_bd512",
                    "submitted": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                }
                save_jobs(pending)
            except Exception as e:
                print(f"  {cid}: submit error - {e}")
        else:
            print(f"  {cid}: MPS job already pending ({pending[mps_key]['job_id']})")

    # ── Phase 2: Poll loop — check MPS results + QPU availability ──
    print(f"\n{'='*60}")
    print("  PHASE 2: Poll for results + QPU availability (every 15 min)")
    print("=" * 60)

    qpu_online = False
    qpu_submitted = False
    poll_count = 0
    MAX_POLLS = 20  # 20 × 15 min = 5 hours max

    while poll_count < MAX_POLLS:
        poll_count += 1
        now = time.strftime("%H:%M:%S UTC", time.gmtime())
        print(f"\n--- Poll #{poll_count} at {now} ---")

        results = load_results()
        all_solved = True

        # Check all pending jobs
        completed_keys = []
        for key, job_info in list(pending.items()):
            cid = job_info["circuit_id"]
            if is_solved(results, cid):
                completed_keys.append(key)
                continue

            all_solved = False
            res = check_job_result(bq, job_info["job_id"], cid,
                                   job_info["name"], job_info["device"])
            if res == "RUNNING":
                continue
            elif res and isinstance(res, dict):
                if res.get("reliable", False):
                    results[cid] = res
                    save_results(results)
                    completed_keys.append(key)
                    print(f"    *** {cid} SOLVED! ***")
                else:
                    print(f"    {cid}: result unreliable, keeping job tracked")
                    # Store unreliable result but don't mark as solved
                    results[cid] = res
                    save_results(results)
                    completed_keys.append(key)
            elif res is None:
                completed_keys.append(key)  # Failed, remove from pending

        for k in completed_keys:
            if k in pending:
                del pending[k]
                save_jobs(pending)

        # Check if all circuits are solved
        unsolved = [cid for cid, _, _ in CIRCUITS if not is_solved(results, cid)]
        if not unsolved:
            print("\n  ALL CIRCUITS SOLVED!")
            break

        print(f"\n  Unsolved: {', '.join(unsolved)}")

        # Check QPU availability
        if not qpu_submitted:
            print("  Checking QPU availability...")
            if check_qpu_online(bq):
                print("  *** QPU IS ONLINE! Submitting all unsolved circuits ***")
                qpu_online = True
                for cid, name, fname in CIRCUITS:
                    if is_solved(results, cid):
                        continue
                    qpu_key = f"{cid}_qpu"
                    if qpu_key not in pending:
                        try:
                            job_id = submit_qpu(bq, cid, name, fname, shots=4096)
                            pending[qpu_key] = {
                                "job_id": job_id,
                                "circuit_id": cid,
                                "name": name,
                                "fname": fname,
                                "device": "quantum",
                                "submitted": time.strftime("%Y-%m-%d %H:%M:%S UTC",
                                                           time.gmtime()),
                            }
                            save_jobs(pending)
                        except Exception as e:
                            print(f"    {cid} QPU submit error: {e}")
                qpu_submitted = True
            else:
                print("  QPU still offline.")

        # If no more pending jobs and still unsolved, nothing to wait for
        if not pending:
            print("\n  No more pending jobs. Remaining circuits need QPU or higher bond dim.")
            if not qpu_online:
                print("  Will continue polling for QPU...")

        # Wait 15 minutes before next poll
        remaining_unsolved = [cid for cid, _, _ in CIRCUITS if not is_solved(results, cid)]
        if remaining_unsolved and (pending or not qpu_online):
            print(f"  Sleeping 15 minutes until next poll...")
            time.sleep(900)
        else:
            break

    # ── Final summary ──
    results = load_results()
    print(f"\n{'='*60}")
    print("  FINAL RESULTS")
    print("=" * 60)
    all_ids = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
    for pid in all_ids:
        r = results.get(pid, {})
        if "peak_bitstring" in r:
            rel = "✓" if r.get("reliable", True) else "?"
            print(f"  {pid:4s}: {r['peak_bitstring'][:40]}{'...' if len(r.get('peak_bitstring',''))>40 else ''} "
                  f"[{r.get('device','?')}] {rel}")
        else:
            print(f"  {pid:4s}: NOT SOLVED")
