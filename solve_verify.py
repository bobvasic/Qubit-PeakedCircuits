#!/usr/bin/env python3
"""
Verification tool for peaked circuit solutions.

Uses the inverse circuit trick:
  1. Apply X gates for each '1' bit in the candidate bitstring
  2. Apply the inverse of the original circuit
  3. Measure — if candidate is correct, output concentrates on |0...0⟩

This works because: circuit|0⟩ = |peak⟩
  So: circuit⁻¹ · X(candidate) · |0⟩ should give |0⟩ if candidate == peak
"""
import sys
import json
import time
from pathlib import Path
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

BASE = Path("/home/bob/Blue Qubit Hackathon")
RESULTS_FILE = BASE / "results.json"

CIRCUITS = {
    "P4":  ("Golden Mountain",  "P4_golden_mountain.qasm"),
    "P5":  ("Granite Summit",   "P5_granite_summit.qasm"),
    "P6":  ("Titan Pinnacle",   "P6_titan_pinnacle.qasm"),
    "P7":  ("Heavy Hex 1275",   "P7_heavy_hex_1275.qasm"),
    "P8":  ("Grid 888 iSwap",   "P8_grid_888_iswap.qasm"),
    "P9":  ("HQAP 1917",        "P9_hqap_1917.qasm"),
    "P10": ("Heavy Hex 4020",   "P10_heavy_hex_4020.qasm"),
}


def load_circuit(circuit_id):
    """Load a circuit from QASM file."""
    name, fname = CIRCUITS[circuit_id]
    fpath = BASE / fname
    qc = QuantumCircuit.from_qasm_file(str(fpath))
    return qc, name


def verify_candidate(circuit_id, candidate_bitstring, bond_dim=256, shots=10000):
    """
    Verify a candidate bitstring using the inverse circuit trick.

    Returns (is_correct, zero_probability, counts_dict)
    """
    qc, name = load_circuit(circuit_id)
    n = qc.num_qubits

    if len(candidate_bitstring) != n:
        raise ValueError(f"Bitstring length {len(candidate_bitstring)} != {n} qubits")

    # Build verification circuit:
    # 1. Apply X gates to prepare |candidate⟩ from |0...0⟩
    # 2. Apply inverse of the original circuit
    # 3. Measure - should give |0...0⟩ if candidate is correct

    verify_qc = QuantumCircuit(n)

    # Qiskit bitstring convention: position 0 in string = qubit n-1 (MSB)
    for i, bit in enumerate(candidate_bitstring):
        if bit == '1':
            # Position i in string corresponds to qubit (n-1-i) in Qiskit
            verify_qc.x(n - 1 - i)

    # Append the inverse circuit
    verify_qc.compose(qc.inverse(), inplace=True)

    # Add measurements
    verify_qc.measure_all()

    # Simulate with MPS
    sim = AerSimulator(method='matrix_product_state')
    tc = transpile(verify_qc, sim)

    t0 = time.time()
    result = sim.run(
        tc,
        shots=shots,
        matrix_product_state_max_bond_dimension=bond_dim,
    ).result()
    elapsed = time.time() - t0

    counts = result.get_counts()
    zero_key = '0' * n
    zero_count = counts.get(zero_key, 0)
    zero_prob = zero_count / shots

    return zero_prob > 0.5, zero_prob, counts, elapsed


def verify_with_escalation(circuit_id, candidate_bitstring):
    """Verify with escalating bond dimensions for confidence."""
    print(f"\nVerifying {circuit_id}: {candidate_bitstring}")

    for bd in [256, 512, 1024]:
        try:
            is_correct, zero_prob, counts, elapsed = verify_candidate(
                circuit_id, candidate_bitstring, bond_dim=bd
            )

            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  bd={bd}: P(|0...0⟩) = {zero_prob:.4f} ({elapsed:.0f}s)")
            for bs, ct in sorted_counts:
                print(f"    |{bs}⟩ = {ct}")

            if is_correct:
                print(f"  VERIFIED CORRECT at bd={bd}!")
                return True
            elif zero_prob > 0.01:
                print(f"  Weak signal at bd={bd}, trying higher...")
            else:
                print(f"  No signal at bd={bd}")
                # Don't give up yet, higher bd might work
        except Exception as e:
            print(f"  ERROR at bd={bd}: {e}")
            if "memory" in str(e).lower():
                break

    print(f"  VERIFICATION FAILED - candidate may be incorrect")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_verify.py <circuit_id> [bitstring]")
        print("  If no bitstring given, uses results.json")
        sys.exit(1)

    circuit_id = sys.argv[1].upper()
    if circuit_id not in CIRCUITS:
        print(f"Unknown circuit: {circuit_id}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        candidate = sys.argv[2]
    else:
        results = json.loads(RESULTS_FILE.read_text())
        if circuit_id not in results or "peak_bitstring" not in results[circuit_id]:
            print(f"No result for {circuit_id} in results.json")
            sys.exit(1)
        candidate = results[circuit_id]["peak_bitstring"]

    ok = verify_with_escalation(circuit_id, candidate)
    sys.exit(0 if ok else 1)
