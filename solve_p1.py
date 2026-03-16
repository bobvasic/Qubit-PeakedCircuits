#!/usr/bin/env python3
"""Solve P1: Little Peak (4 qubits) - Find the peak bitstring via statevector simulation."""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

# Load the QASM file
qc = QuantumCircuit.from_qasm_file("/home/bob/Blue Qubit Hackathon/P1_little_peak.qasm")

print(f"Circuit: P1 Little Peak")
print(f"Qubits: {qc.num_qubits}")
print(f"Gates: {qc.size()}")
print(f"Depth: {qc.depth()}")
print()

# Use statevector simulator
sim = AerSimulator(method='statevector')
qc_copy = qc.copy()
qc_copy.save_statevector()
result = sim.run(qc_copy).result()
statevector = result.get_statevector()

# Get probabilities
probs = np.abs(np.array(statevector)) ** 2

# Find peak bitstring
peak_idx = np.argmax(probs)
peak_prob = probs[peak_idx]
peak_bitstring = format(peak_idx, f'0{qc.num_qubits}b')

print(f"=== RESULTS ===")
print(f"Peak bitstring: {peak_bitstring}")
print(f"Peak probability: {peak_prob:.6f}")
print()

# Show top 5 bitstrings
sorted_indices = np.argsort(probs)[::-1]
print("Top 5 bitstrings by probability:")
for i, idx in enumerate(sorted_indices[:5]):
    bs = format(idx, f'0{qc.num_qubits}b')
    print(f"  {i+1}. |{bs}⟩  P = {probs[idx]:.6f}")

print()
print(f">>> ANSWER FOR SUBMISSION: {peak_bitstring}")
