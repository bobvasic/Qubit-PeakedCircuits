#!/usr/bin/env python3
"""Auto-collect results from BlueQubit cloud jobs. Run this overnight."""
import json
import time
import sys
from pathlib import Path

import bluequbit

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

bq = bluequbit.init("eZAnt4RUMA0hN4DtkfExl6zU5CRmUpZL")

jobs = json.loads((BASE / "cloud_jobs.json").read_text())
results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}

print(f"Monitoring {len(jobs)} jobs. Will check every 5 minutes.")
print(f"Press Ctrl+C to stop.\n")

while True:
    pending = 0
    running = 0
    done = 0

    for jname, jid in sorted(jobs.items()):
        pid = jname.split("_")[0]
        try:
            r = bq.get(jid)
            status = r.run_status

            if status in ("PENDING", "QUEUED"):
                pending += 1
            elif status == "RUNNING":
                running += 1
            elif r.ok:
                done += 1
                counts = r.get_counts()
                sc = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                peak_bs, peak_val = sc[0]

                if peak_val > 1:
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
                        }
                        RESULTS_FILE.write_text(json.dumps(results, indent=2))
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] *** {pid} SOLVED! peak={peak_val} bs={peak_bs}")
                else:
                    done += 1
            else:
                done += 1
        except Exception as e:
            pass

    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] pending={pending} running={running} done={done}")

    if pending == 0 and running == 0:
        print("All jobs finished!")
        break

    time.sleep(300)  # Check every 5 min

# Print final summary
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")
results = json.loads(RESULTS_FILE.read_text())
for pid in ["P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
    r = results.get(pid, {})
    bs = r.get("peak_bitstring", "NOT SOLVED")
    val = r.get("peak_value", "?")
    print(f"  {pid}: {bs}")
    print(f"       value={val}")
