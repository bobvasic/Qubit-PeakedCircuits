"""Analyze P3 circuit to identify which 28 qubits are data qubits vs ancilla."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Load circuit
qc = QuantumCircuit.from_qasm_file("/home/bob/Blue Qubit Hackathon/P3_sharp_peak.qasm")
print(f"Total qubits: {qc.num_qubits}")

# Add measurements to all qubits
qc.measure_all()

# Run MPS simulation with many shots
sim = AerSimulator(method='matrix_product_state')
from qiskit import transpile
tc = transpile(qc, sim)
result = sim.run(tc, shots=10000, matrix_product_state_max_bond_dimension=256).result()
counts = result.get_counts()

# Get top bitstring
top_bitstring = max(counts, key=counts.get)
print(f"Top bitstring ({len(top_bitstring)} bits): {top_bitstring}")
print(f"Top count: {counts[top_bitstring]}/10000")

# Analyze each qubit position - check if it's always the same value
n = len(top_bitstring)
qubit_values = {i: {'0': 0, '1': 0} for i in range(n)}

for bitstring, count in counts.items():
    for i, bit in enumerate(bitstring):
        qubit_values[i][bit] += count

# Identify qubits that are NOT deterministic (data qubits)
# and qubits that are always the same (ancilla)
deterministic = []
variable = []
for i in range(n):
    total = qubit_values[i]['0'] + qubit_values[i]['1']
    p0 = qubit_values[i]['0'] / total
    p1 = qubit_values[i]['1'] / total
    dominant = '0' if p0 > p1 else '1'
    dominance = max(p0, p1)
    
    if dominance > 0.999:  # essentially always the same
        deterministic.append((i, dominant, dominance))
    else:
        variable.append((i, dominant, dominance))

print(f"\nDeterministic qubits (ancilla): {len(deterministic)}")
for pos, val, dom in deterministic:
    print(f"  Position {pos}: always '{val}' ({dom*100:.1f}%)")

print(f"\nVariable qubits (data): {len(variable)}")
for pos, val, dom in variable:
    print(f"  Position {pos}: dominant '{val}' ({dom*100:.1f}%)")

# Extract just the data qubit values from top bitstring
if len(variable) == 28:
    data_bits = ''.join([top_bitstring[pos] for pos, _, _ in variable])
    print(f"\n28-bit answer (variable qubits only): {data_bits}")
else:
    # Try different thresholds
    for threshold in [0.999, 0.99, 0.98, 0.95]:
        det = [i for i in range(n) if max(qubit_values[i]['0'], qubit_values[i]['1']) / 10000 > threshold]
        var = [i for i in range(n) if i not in det]
        print(f"\nThreshold {threshold}: {len(det)} deterministic, {len(var)} variable")
        if len(var) == 28:
            data_bits = ''.join([top_bitstring[i] for i in var])
            print(f"  28-bit answer: {data_bits}")
