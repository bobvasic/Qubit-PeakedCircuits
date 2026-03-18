"""Quick analysis of remaining circuits P4-P10."""
from qiskit import QuantumCircuit
from pathlib import Path

BASE = Path("/home/bob/Blue Qubit Hackathon")

circuits = [
    ("P4", "Golden Mountain", "P4_golden_mountain.qasm"),
    ("P5", "Granite Summit", "P5_granite_summit.qasm"),
    ("P6", "Titan Pinnacle", "P6_titan_pinnacle.qasm"),
    ("P7", "Heavy Hex 1275", "P7_heavy_hex_1275.qasm"),
    ("P8", "Grid 888 iSwap", "P8_grid_888_iswap.qasm"),
    ("P9", "HQAP 1917", "P9_hqap_1917.qasm"),
    ("P10", "Heavy Hex 4020", "P10_heavy_hex_4020.qasm"),
]

for pid, name, fname in circuits:
    fpath = BASE / fname
    if not fpath.exists():
        # Try alternate names
        candidates = list(BASE.glob(f"{pid}*"))
        if candidates:
            fpath = candidates[0]
            fname = fpath.name
        else:
            print(f"{pid:4s} ({name:20s}): FILE NOT FOUND")
            continue
    try:
        qc = QuantumCircuit.from_qasm_file(str(fpath))
        n = qc.num_qubits
        g = qc.size()
        d = qc.depth()
        # Count 2-qubit gates
        two_q = sum(1 for inst in qc.data if inst.operation.num_qubits == 2)
        print(f"{pid:4s} ({name:20s}): {n:3d}q, depth={d:5d}, gates={g:6d}, 2q_gates={two_q:5d}, file={fname}")
    except Exception as e:
        print(f"{pid:4s} ({name:20s}): ERROR loading {fname}: {e}")
