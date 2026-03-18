"""Check quantum hardware availability and estimate transpiled depths."""
import os
from pathlib import Path

# Load API keys
env_path = Path("/home/bob/Blue Qubit Hackathon/.env")
for line in env_path.read_text().strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        os.environ[key] = val

# ── 1. Check BlueQubit QPU ──
print("=" * 60)
print("  BLUEQUBIT QUANTUM DEVICE CHECK")
print("=" * 60)
try:
    import bluequbit
    bq = bluequbit.init()
    from qiskit import QuantumCircuit
    # Simple 2-qubit test circuit
    test_qc = QuantumCircuit(2)
    test_qc.h(0)
    test_qc.cx(0, 1)
    test_qc.measure_all()
    result = bq.run(test_qc, device="quantum", shots=10, asynchronous=False, job_name="hw_check")
    if result.ok:
        print("  BlueQubit QPU: ONLINE!")
        print(f"  Test result: {result.get_counts()}")
    else:
        print(f"  BlueQubit QPU: OFFLINE/ERROR - {result.error_message}")
except Exception as e:
    print(f"  BlueQubit QPU: ERROR - {e}")

# ── 2. Check IBM Quantum backends ──
print("\n" + "=" * 60)
print("  IBM QUANTUM BACKEND CHECK")
print("=" * 60)
try:
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    backends = service.backends()
    print(f"  Available backends: {len(backends)}")
    for b in backends:
        status = b.status()
        config = b.configuration()
        print(f"  {b.name}: {config.n_qubits}q, pending_jobs={status.pending_jobs}, "
              f"operational={status.operational}, status={status.status_msg}")
except Exception as e:
    print(f"  IBM Quantum: ERROR - {e}")

# ── 3. Estimate transpiled depths on IBM hardware ──
print("\n" + "=" * 60)
print("  TRANSPILED DEPTH ESTIMATES (IBM ibm_fez)")
print("=" * 60)
try:
    from qiskit import transpile
    backend = service.backend("ibm_fez")
    
    BASE = Path("/home/bob/Blue Qubit Hackathon")
    circuits = [
        ("P7",  "Heavy Hex 1275",  "P7_heavy_hex_1275.qasm",  45),
        ("P8",  "Grid 888 iSwap",  "P8_grid_888_iswap.qasm",  40),
        ("P5",  "Granite Summit",  "P5_granite_summit.qasm",   44),
        ("P4",  "Golden Mountain", "P4_golden_mountain.qasm",  48),
        ("P9",  "HQAP 1917",      "P9_hqap_1917.qasm",        56),
        ("P6",  "Titan Pinnacle",  "P6_titan_pinnacle.qasm",   62),
        ("P10", "Heavy Hex 4020",  "P10_heavy_hex_4020.qasm",  49),
    ]
    
    for pid, name, fname, nq in circuits:
        fpath = BASE / fname
        if not fpath.exists():
            candidates = list(BASE.glob(f"{pid}*"))
            if candidates:
                fpath = candidates[0]
        try:
            qc = QuantumCircuit.from_qasm_file(str(fpath))
            orig_depth = qc.depth()
            orig_2q = sum(1 for inst in qc.data if inst.operation.num_qubits == 2)
            
            # Transpile with optimization level 3
            qc.measure_all()
            tc = transpile(qc, backend=backend, optimization_level=3)
            t_depth = tc.depth()
            t_2q = sum(1 for inst in tc.data if inst.operation.num_qubits == 2)
            
            # Rule of thumb: IBM Heron can handle ~300-500 2q gate depth reliably
            feasible = "YES" if t_depth < 500 else ("MAYBE" if t_depth < 1000 else "NO")
            
            print(f"  {pid:4s} ({name:20s}): orig_depth={orig_depth:5d} -> transpiled_depth={t_depth:5d}, "
                  f"2q: {orig_2q:5d} -> {t_2q:5d}  [{feasible}]")
        except Exception as e:
            print(f"  {pid:4s} ({name:20s}): TRANSPILE ERROR - {e}")

except Exception as e:
    print(f"  Transpilation check failed: {e}")
