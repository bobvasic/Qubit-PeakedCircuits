#!/usr/bin/env python3
"""Solve P2: Swift Rise (28 qubits) - Find the peak bitstring via statevector simulation."""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np
import time

print("Loading P2 circuit...")
qc = QuantumCircuit.from_qasm_file("/home/bob/Blue Qubit Hackathon/P2_swift_rise.qasm")

print(f"Circuit: P2 Swift Rise")
print(f"Qubits: {qc.num_qubits}")
print(f"Gates: {qc.size()}")
print(f"Depth: {qc.depth()}")
print(f"Memory needed: ~{2**qc.num_qubits * 16 / 1e9:.1f} GB")
print()

# Use statevector simulator
print("Running statevector simulation (28 qubits, ~4GB RAM)...")
start = time.time()
sim = AerSimulator(method='statevector')
qc_copy = qc.copy()
qc_copy.save_statevector()
result = sim.run(qc_copy).result()
statevector = result.get_statevector()
elapsed = time.time() - start
print(f"Simulation completed in {elapsed:.1f}s")
print()

# Get probabilities
probs = np.abs(np.array(statevector)) ** 2

# Find peak bitstring
peak_idx = np.argmax(probs)
peak_prob = probs[peak_idx]
peak_bitstring = format(peak_idx, f'0{qc.num_qubits}b')

print(f"=== RESULTS ===")
print(f"Peak bitstring: {peak_bitstring}")
print(f"Peak probability: {peak_prob:.8f}")
print()

# Show top 10 bitstrings
sorted_indices = np.argsort(probs)[::-1]
print("Top 10 bitstrings by probability:")
for i, idx in enumerate(sorted_indices[:10]):
    bs = format(idx, f'0{qc.num_qubits}b')
    print(f"  {i+1}. |{bs}⟩  P = {probs[idx]:.8f}")

print()
print(f">>> ANSWER FOR SUBMISSION: {peak_bitstring}")
