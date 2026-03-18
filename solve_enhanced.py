#!/usr/bin/env python3
"""
Unified solver for BlueQubit Peaked Circuits Hackathon (P4-P10).

Escalating strategies:
1. Local MPS with increasing bond dimensions (512 → 4096)
2. Cloud MPS via BlueQubit API (bd=512, 1024)
3. Marginal reconstruction from multiple low-bd runs
4. Bit-flip local search from marginal candidate
5. Inverse circuit verification before final output

Usage: python solve_enhanced.py P8
       python solve_enhanced.py P8 --skip-cloud
       python solve_enhanced.py P8 --verify-only
"""
import sys
import os
import json
import time
import numpy as np
from pathlib import Path
from collections import Counter

# Setup
BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"
BQ_TOKEN = "eZAnt4RUMA0hN4DtkfExl6zU5CRmUpZL"

CIRCUITS = {
    "P4":  ("Golden Mountain",  "P4_golden_mountain.qasm",   48, 5096, "cross"),
    "P5":  ("Granite Summit",   "P5_granite_summit.qasm",    44, 1892, "heavy_hex"),
    "P6":  ("Titan Pinnacle",   "P6_titan_pinnacle.qasm",    62, 3494, "all_to_all"),
    "P7":  ("Heavy Hex 1275",   "P7_heavy_hex_1275.qasm",    45, 1275, "heavy_hex"),
    "P8":  ("Grid 888 iSwap",   "P8_grid_888_iswap.qasm",    40,  888, "grid"),
    "P9":  ("HQAP 1917",        "P9_hqap_1917.qasm",         56, 1917, "ring"),
    "P10": ("Heavy Hex 4020",   "P10_heavy_hex_4020.qasm",   49, 4020, "heavy_hex"),
}


def load_results():
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return {}


def save_results(results):
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))


def load_circuit(circuit_id):
    name, fname, n_q, n_2q, topo = CIRCUITS[circuit_id]
    fpath = BASE / fname
    from qiskit import QuantumCircuit
    qc = QuantumCircuit.from_qasm_file(str(fpath))
    return qc, name


def print_header(circuit_id):
    name, fname, n_q, n_2q, topo = CIRCUITS[circuit_id]
    print(f"\n{'='*60}")
    print(f"  Solving {circuit_id}: {name}")
    print(f"  {n_q} qubits | {n_2q} 2q gates | {topo} topology")
    print(f"{'='*60}")


# ─── Strategy 1: Local MPS with high bond dimensions ───────────────────

def try_local_mps(circuit_id, bond_dims=None, shots=10000):
    """Try local MPS simulation with escalating bond dimensions."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits

    if bond_dims is None:
        _, _, n_q, n_2q, topo = CIRCUITS[circuit_id]
        if n_2q <= 1000:
            bond_dims = [512, 1024, 2048, 4096]
        elif n_2q <= 2000:
            bond_dims = [256, 512, 1024, 2048]
        elif n_2q <= 3500:
            bond_dims = [128, 256, 512, 1024]
        else:
            bond_dims = [128, 256, 512]

    qc_m = qc.copy()
    qc_m.measure_all()
    sim = AerSimulator(method='matrix_product_state')
    tc = transpile(qc_m, sim)

    best_bitstring = None
    best_count = 0

    for bd in bond_dims:
        print(f"\n  [Local MPS] bond_dim={bd}, shots={shots}")
        t0 = time.time()
        try:
            result = sim.run(
                tc,
                shots=shots,
                matrix_product_state_max_bond_dimension=bd,
            ).result()
            elapsed = time.time() - t0

            counts = result.get_counts()
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            peak_bs, peak_val = sorted_counts[0]
            unique = len(counts)

            print(f"    Time: {elapsed:.0f}s | Peak: {peak_val}/{shots} ({peak_val*100/shots:.1f}%)")
            print(f"    Unique: {unique}/{shots}")
            for bs, ct in sorted_counts[:3]:
                print(f"    |{bs}⟩ = {ct}")

            if peak_val > best_count:
                best_count = peak_val
                best_bitstring = peak_bs

            # Strong peak found — done!
            if peak_val > shots * 0.01:  # >1% concentration
                print(f"    *** PEAK FOUND: {peak_bs} ({peak_val*100/shots:.1f}%) ***")
                return peak_bs, peak_val, "local_mps", bd

            # Moderate signal — keep going to higher bd
            if peak_val > 5:
                print(f"    Weak signal detected, trying higher bond dim...")

        except Exception as e:
            elapsed = time.time() - t0
            print(f"    ERROR after {elapsed:.0f}s: {e}")
            if "memory" in str(e).lower() or "std::bad_alloc" in str(e):
                print(f"    Out of memory — stopping local MPS escalation")
                break

    if best_count > 5:
        print(f"\n  [Local MPS] Best candidate: {best_bitstring} (count={best_count})")
        return best_bitstring, best_count, "local_mps_weak", 0
    return None, 0, None, 0


# ─── Strategy 2: Cloud MPS via BlueQubit ────────────────────────────────

def try_cloud_mps(circuit_id, bond_dims=None, shots=30000):
    """Try BlueQubit cloud MPS with high bond dimension."""
    import bluequbit
    from qiskit import QuantumCircuit

    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits
    qc_m = qc.copy()
    qc_m.measure_all()

    bq = bluequbit.init(BQ_TOKEN)

    if bond_dims is None:
        bond_dims = [512, 1024]

    best_bitstring = None
    best_count = 0

    for bd in bond_dims:
        print(f"\n  [Cloud MPS] bond_dim={bd}, shots={shots}")
        t0 = time.time()
        try:
            result = bq.run(
                qc_m,
                device="mps.cpu",
                job_name=f"hackathon_{circuit_id}_bd{bd}",
                asynchronous=False,
                shots=shots,
                options={"mps_bond_dimension": bd},
                timeout=1800,
            )
            elapsed = time.time() - t0

            if result.ok:
                counts = result.get_counts()
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                peak_bs, peak_val = sorted_counts[0]
                unique = len(counts)

                print(f"    Time: {elapsed:.0f}s | Cost: ${result.cost:.4f}")
                print(f"    Peak: {peak_val}/{shots} ({peak_val*100/shots:.1f}%)")
                print(f"    Unique: {unique}/{shots}")
                for bs, ct in sorted_counts[:3]:
                    print(f"    |{bs}⟩ = {ct}")

                if peak_val > best_count:
                    best_count = peak_val
                    best_bitstring = peak_bs

                if peak_val > shots * 0.01:
                    print(f"    *** PEAK FOUND: {peak_bs} ({peak_val*100/shots:.1f}%) ***")
                    return peak_bs, peak_val, "cloud_mps", bd
            else:
                print(f"    Cloud error: {result.error_message}")

        except Exception as e:
            print(f"    ERROR: {e}")

    if best_count > 5:
        return best_bitstring, best_count, "cloud_mps_weak", 0
    return None, 0, None, 0


# ─── Strategy 3: Marginal reconstruction ────────────────────────────────

def try_marginals(circuit_id, bond_dims=None, shots_per_run=20000, n_runs=5):
    """Reconstruct peak from per-qubit marginal probabilities."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits

    if bond_dims is None:
        _, _, n_q, n_2q, topo = CIRCUITS[circuit_id]
        if n_2q <= 2000:
            bond_dims = [128, 256, 512]
        else:
            bond_dims = [64, 128, 256]

    qc_m = qc.copy()
    qc_m.measure_all()
    sim = AerSimulator(method='matrix_product_state')
    tc = transpile(qc_m, sim)

    all_p1 = []
    all_counts = Counter()

    print(f"\n  [Marginals] Running {n_runs} runs at bond_dims={bond_dims}")

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

                # Aggregate counts across runs
                for bs, ct in counts.items():
                    all_counts[bs] += ct

                # Per-qubit marginals
                total = sum(counts.values())
                p1 = np.zeros(n)
                for bitstring, count in counts.items():
                    for pos, bit in enumerate(bitstring):
                        if bit == '1':
                            p1[pos] += count
                p1 /= total

                conf = np.mean(np.abs(p1 - 0.5))
                all_p1.append(p1)

                top_bs, top_ct = max(counts.items(), key=lambda x: x[1])
                print(f"    bd={bd} run={run_idx}: conf={conf:.4f} top={top_ct} t={elapsed:.0f}s")

            except Exception as e:
                print(f"    bd={bd} run={run_idx}: ERROR - {str(e)[:60]}")
                if "memory" in str(e).lower():
                    break

    if not all_p1:
        return None, 0, None, 0

    # Method A: Most frequent bitstring across all runs
    sorted_agg = all_counts.most_common(5)
    agg_best_bs, agg_best_ct = sorted_agg[0]
    print(f"\n    Aggregate top bitstrings:")
    for bs, ct in sorted_agg[:5]:
        print(f"      |{bs}⟩ = {ct}")

    # Method B: Marginal reconstruction
    avg_p1 = np.mean(all_p1, axis=0)
    marginal_bs = ''.join('1' if p > 0.5 else '0' for p in avg_p1)
    conf = np.mean(np.abs(avg_p1 - 0.5))

    # Identify weak qubits
    weak_positions = [i for i in range(n) if abs(avg_p1[i] - 0.5) < 0.05]
    print(f"\n    Marginal bitstring: {marginal_bs}")
    print(f"    Confidence: {conf:.4f}")
    if weak_positions:
        print(f"    Weak qubits ({len(weak_positions)}): {weak_positions}")

    # Return whichever has better support
    if agg_best_ct > 1:
        return agg_best_bs, agg_best_ct, "marginal_aggregate", 0
    return marginal_bs, conf, "marginal_reconstruct", 0


# ─── Strategy 4: Bit-flip local search ──────────────────────────────────

def try_bitflip_search(circuit_id, start_bitstring, max_rounds=3):
    """Flip each bit and check if it improves the count."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits

    print(f"\n  [Bit-flip] Starting from: {start_bitstring}")

    # Use inverse circuit to score candidates efficiently
    def score_candidate(candidate, bd=256, shots=4000):
        """Score a candidate using inverse circuit — higher P(|0⟩) = better."""
        verify_qc = QuantumCircuit(n)
        for i, bit in enumerate(candidate):
            if bit == '1':
                verify_qc.x(n - 1 - i)
        verify_qc.compose(qc.inverse(), inplace=True)
        verify_qc.measure_all()

        sim = AerSimulator(method='matrix_product_state')
        tc = transpile(verify_qc, sim)
        result = sim.run(
            tc, shots=shots,
            matrix_product_state_max_bond_dimension=bd,
        ).result()
        counts = result.get_counts()
        zero_key = '0' * n
        return counts.get(zero_key, 0) / shots

    current = start_bitstring
    current_score = score_candidate(current)
    print(f"    Initial score (P(|0⟩)): {current_score:.4f}")

    if current_score > 0.5:
        print(f"    Already good! Skipping bit-flip search.")
        return current, current_score, "bitflip_verified", 0

    for round_idx in range(max_rounds):
        improved = False
        print(f"    Round {round_idx + 1}:")

        for bit_pos in range(n):
            flipped = list(current)
            flipped[bit_pos] = '1' if flipped[bit_pos] == '0' else '0'
            flipped = ''.join(flipped)

            new_score = score_candidate(flipped)
            if new_score > current_score + 0.005:
                print(f"      Flip bit {bit_pos}: {current_score:.4f} → {new_score:.4f} ✓")
                current = flipped
                current_score = new_score
                improved = True

        if not improved:
            print(f"      No improvement in round {round_idx + 1}")
            break

        print(f"    After round {round_idx + 1}: score={current_score:.4f}")
        if current_score > 0.5:
            print(f"    *** HIGH CONFIDENCE ***")
            break

    return current, current_score, "bitflip", 0


# ─── Verification ────────────────────────────────────────────────────────

def verify_candidate(circuit_id, candidate):
    """Verify using inverse circuit trick at high bond dim."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits

    print(f"\n  [Verify] Checking: {candidate}")

    for bd in [256, 512, 1024, 2048]:
        try:
            verify_qc = QuantumCircuit(n)
            for i, bit in enumerate(candidate):
                if bit == '1':
                    verify_qc.x(n - 1 - i)
            verify_qc.compose(qc.inverse(), inplace=True)
            verify_qc.measure_all()

            sim = AerSimulator(method='matrix_product_state')
            tc = transpile(verify_qc, sim)

            t0 = time.time()
            result = sim.run(
                tc, shots=10000,
                matrix_product_state_max_bond_dimension=bd,
            ).result()
            elapsed = time.time() - t0

            counts = result.get_counts()
            zero_key = '0' * n
            zero_count = counts.get(zero_key, 0)
            zero_prob = zero_count / 10000

            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"    bd={bd}: P(|0⟩)={zero_prob:.4f} ({elapsed:.0f}s)")
            for bs, ct in sorted_counts:
                tag = " ← all-zeros" if bs == zero_key else ""
                print(f"      |{bs}⟩ = {ct}{tag}")

            if zero_prob > 0.5:
                print(f"    *** VERIFIED at bd={bd}! ***")
                return True, zero_prob
            elif zero_prob > 0.01:
                print(f"    Weak signal, trying higher bd...")
            else:
                # No signal at all — might be wrong answer
                # But keep trying in case bd is too low
                pass

        except Exception as e:
            print(f"    bd={bd}: ERROR - {e}")
            if "memory" in str(e).lower():
                break

    return False, 0.0


# ─── Main solver ─────────────────────────────────────────────────────────

def solve(circuit_id, skip_cloud=False, verify_only=False):
    """Main solving pipeline with escalating strategies."""
    print_header(circuit_id)
    results = load_results()

    # If verify-only mode, just verify existing result
    if verify_only:
        if circuit_id in results and "peak_bitstring" in results[circuit_id]:
            candidate = results[circuit_id]["peak_bitstring"]
            verified, prob = verify_candidate(circuit_id, candidate)
            return candidate if verified else None
        else:
            print("  No existing result to verify")
            return None

    best_candidate = None
    best_score = 0
    best_method = None

    # Strategy 1: Local MPS
    print("\n" + "─" * 40)
    print("  Strategy 1: Local MPS (high bond dim)")
    print("─" * 40)
    bs, score, method, bd = try_local_mps(circuit_id)
    if bs and score > best_score:
        best_candidate, best_score, best_method = bs, score, method

    # If we got a strong peak, verify and finish
    if best_score > 100:  # >1% of 10000 shots
        verified, vprob = verify_candidate(circuit_id, best_candidate)
        if verified:
            save_result(results, circuit_id, best_candidate, best_score, best_method, verified=True)
            return best_candidate

    # Strategy 2: Cloud MPS
    if not skip_cloud:
        print("\n" + "─" * 40)
        print("  Strategy 2: Cloud MPS (BlueQubit)")
        print("─" * 40)
        bs, score, method, bd = try_cloud_mps(circuit_id)
        if bs and score > best_score:
            best_candidate, best_score, best_method = bs, score, method

        if best_score > 300:  # >1% of 30000
            verified, vprob = verify_candidate(circuit_id, best_candidate)
            if verified:
                save_result(results, circuit_id, best_candidate, best_score, best_method, verified=True)
                return best_candidate

    # Strategy 3: Marginal reconstruction
    print("\n" + "─" * 40)
    print("  Strategy 3: Marginal Reconstruction")
    print("─" * 40)
    bs, score, method, _ = try_marginals(circuit_id)
    if bs:
        # Verify marginal candidate
        verified, vprob = verify_candidate(circuit_id, bs)
        if verified:
            save_result(results, circuit_id, bs, vprob, "marginal_verified", verified=True)
            return bs

        # If marginal wasn't verified, try bit-flip search
        print("\n" + "─" * 40)
        print("  Strategy 4: Bit-flip Local Search")
        print("─" * 40)
        bs2, score2, method2, _ = try_bitflip_search(circuit_id, bs)
        if score2 > 0.01:
            verified, vprob = verify_candidate(circuit_id, bs2)
            if verified:
                save_result(results, circuit_id, bs2, vprob, "bitflip_verified", verified=True)
                return bs2

    # If nothing verified, save the best candidate we have with a warning
    if best_candidate:
        print(f"\n  WARNING: No candidate was verified. Best: {best_candidate}")
        print(f"  Method: {best_method}, Score: {best_score}")
        save_result(results, circuit_id, best_candidate, best_score, best_method, verified=False)
        return best_candidate
    elif bs:
        print(f"\n  WARNING: No candidate was verified. Marginal: {bs}")
        save_result(results, circuit_id, bs, 0, "marginal_unverified", verified=False)
        return bs

    print(f"\n  FAILED: No candidate found for {circuit_id}")
    return None


def save_result(results, circuit_id, bitstring, score, method, verified=False):
    """Save result to results.json."""
    name = CIRCUITS[circuit_id][0]
    n_q = CIRCUITS[circuit_id][2]
    results[circuit_id] = {
        "name": name,
        "peak_bitstring": bitstring,
        "peak_value": score,
        "device": method,
        "num_qubits": n_q,
        "verified": verified,
    }
    save_results(results)

    print(f"\n{'='*60}")
    print(f"  RESULT for {circuit_id}: {name}")
    print(f"  Bitstring: {bitstring}")
    print(f"  Method: {method}")
    print(f"  Verified: {'YES' if verified else 'NO'}")
    print(f"{'='*60}")
    print(f"\n  >>> COPY FOR SUBMISSION: {bitstring}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_enhanced.py <circuit_id> [--skip-cloud] [--verify-only]")
        print("       python solve_enhanced.py P8")
        print("       python solve_enhanced.py all")
        sys.exit(1)

    args = sys.argv[1:]
    skip_cloud = "--skip-cloud" in args
    verify_only = "--verify-only" in args
    circuit_ids = [a.upper() for a in args if not a.startswith("--")]

    if "ALL" in circuit_ids:
        # Priority order
        circuit_ids = ["P8", "P7", "P5", "P9", "P6", "P10", "P4"]

    for cid in circuit_ids:
        if cid not in CIRCUITS:
            print(f"Unknown circuit: {cid}")
            continue
        solve(cid, skip_cloud=skip_cloud, verify_only=verify_only)
