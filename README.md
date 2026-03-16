# Peaked Circuits Solver

Quantum computing toolkit for solving [BlueQubit's Peaked Circuit Challenge](https://www.bluequbit.io/quantum-computing-hackathon) — finding hidden bitstrings in quantum circuits designed to demonstrate verifiable quantum advantage.

## The Challenge

Peaked circuits are quantum circuits engineered so that one bitstring appears with significantly higher measurement probability than all others. Given a circuit, find that peak.

| # | Circuit | Qubits | Depth | Topology |
|---|---------|--------|-------|----------|
| P1 | Little Peak | 4 | 2 | Linear |
| P2 | Swift Rise | 28 | 90 | Chain |
| P3 | Sharp Peak | 44 | 19 | Grid |
| P4 | Golden Mountain | 48 | 437 | Cross |
| P5 | Granite Summit | 44 | — | Heavy Hex |
| P6 | Titan Pinnacle | 62 | — | All-to-All |
| P7 | Heavy Hex 1275 | 45 | — | Heavy Hex |
| P8 | Grid 888 iSwap | — | — | Grid |
| P9 | HQAP 1917 | 56 | — | Circular |
| P10 | Heavy Hex 4020 | 49 | — | Heavy Hex |

## Approach

**Tiered execution** based on circuit size:

- **Statevector** (`cpu`) — exact solution for circuits up to 34 qubits
- **Tensor Network** (`mps.cpu`) — approximate simulation for 34–62 qubits
- **Quantum Hardware** (`quantum`) — real QPU execution via BlueQubit

All execution runs on [BlueQubit's cloud infrastructure](https://app.bluequbit.io).

## Quick Start

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install qiskit qiskit-aer bluequbit numpy

# Set your API key
export BLUEQUBIT_API_TOKEN="your_token"

# Solve specific circuits
python solve_all_cloud.py P1 P2 P3

# Solve all
python solve_all_cloud.py
```

## Project Structure

```
├── P1_little_peak.qasm      # Circuit files (OpenQASM 2.0)
├── ...
├── P10_heavy_hex_4020.qasm
├── solve_all_cloud.py        # Cloud simulator solver (cpu + mps)
├── solve_all_quantum.py      # Real quantum hardware solver
├── solve_remaining.py        # Batch solver for large circuits
├── results.json              # Computed peak bitstrings
└── .env                      # API key (gitignored)
```

## Results

See `results.json` for computed answers and metadata.

## Tech Stack

- **[BlueQubit SDK](https://app.bluequbit.io/sdk-docs/)** — cloud quantum execution
- **[Qiskit](https://qiskit.org/)** — circuit loading and manipulation
- **Python 3.10+**

## License

MIT
