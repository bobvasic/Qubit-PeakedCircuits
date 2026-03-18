#!/usr/bin/env python3
"""Monitor and collect results from BlueQubit cloud jobs."""
import json
import sys
from pathlib import Path

import bluequbit

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"
JOBS_FILE = BASE / "cloud_jobs.json"

bq = bluequbit.init("eZAnt4RUMA0hN4DtkfExl6zU5CRmUpZL")

jobs = json.loads(JOBS_FILE.read_text())
results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}

wait_mode = "--wait" in sys.argv

for jname, jid in sorted(jobs.items()):
    pid = jname.split("_")[0]
    try:
        if wait_mode:
            r = bq.wait(jid, timeout=7200)
        else:
            r = bq.get(jid)

        status = r.run_status
        print(f"{jname:25s} ({jid}): {status}", end="")

        if r.ok:
            counts = r.get_counts()
            sc = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            peak_bs, peak_val = sc[0]
            unique = len(counts)
            print(f" | peak={peak_val}/10000 ({peak_val/100:.1f}%) unique={unique}")
            for bs, ct in sc[:5]:
                print(f"  |{bs}> = {ct}")

            # Save if it's the best result for this problem
            existing = results.get(pid, {})
            existing_val = existing.get("peak_value", 0)
            if isinstance(existing_val, str):
                existing_val = 0
            if peak_val > existing_val:
                results[pid] = {
                    "name": jname,
                    "peak_bitstring": peak_bs,
                    "peak_value": peak_val,
                    "device": "mps.cpu",
                    "num_qubits": len(peak_bs),
                    "bond_dim": int(jname.split("bd")[-1]),
                    "shots": 10000,
                    "job_id": jid,
                    "reliable": peak_val > 100,
                }
                RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
                print(f"  ** Saved as best for {pid}")
        else:
            print(f" | cost=${r.cost}")
    except Exception as e:
        print(f"{jname:25s} ({jid}): ERROR - {str(e)[:80]}")

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
for pid in ["P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
    r = results.get(pid, {})
    bs = r.get("peak_bitstring", "NOT SOLVED")
    val = r.get("peak_value", "?")
    rel = "VERIFIED" if r.get("reliable") else "unverified"
    print(f"  {pid}: {bs[:50]}{'...' if len(str(bs))>50 else ''} (val={val}, {rel})")
