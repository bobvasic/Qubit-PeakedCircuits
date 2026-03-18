# Peaked Circuits Solver

Systematic exploration of classical and quantum simulation methods for solving [BlueQubit's Peaked Circuit Challenge](https://www.bluequbit.io/quantum-computing-hackathon) — finding hidden bitstrings in quantum circuits designed to demonstrate verifiable quantum advantage.

**Outcome:** 3/10 circuits solved. The remaining 7 circuits (40–62 qubits, 888–5,096 entangling gates) defeated every accessible simulation method, including MPS up to bond dimension 2,048, IBM Quantum hardware, and GPU tensor networks.

## The Challenge

Peaked circuits are quantum circuits where a single bitstring $x^*$ dominates the output distribution: $|\langle x^* | U | 0^n \rangle|^2 \gg 2^{-n}$. Given a circuit $U$, find that peak.

| # | Circuit | Qubits | 2Q Gates | Gate Type | Topology | Result |
|---|---------|--------|----------|-----------|----------|--------|
| P1 | Little Peak | 4 | ~3 | — | Linear | **Solved** (66.9%) |
| P2 | Swift Rise | 28 | ~450 | — | Chain | **Solved** (34.9%) |
| P3 | Sharp Peak | 44 | ~200 | — | Grid | **Solved** (11.0%) |
| P4 | Golden Mountain | 48 | 5,096 | CZ | Cross | Noise |
| P5 | Granite Summit | 44 | 1,892 | CZ | Heavy Hex | Noise |
| P6 | Titan Pinnacle | 62 | 3,494 | CZ | All-to-All | Noise |
| P7 | Heavy Hex 1275 | 45 | 1,275 | CZ | Heavy Hex | Noise |
| P8 | Grid 888 iSwap | 40 | 888 | iSWAP | Grid | Noise |
| P9 | HQAP 1917 | 56 | 1,917 | RZZ | Dense* | Noise |
| P10 | Heavy Hex 4020 | 49 | 4,020 | CZ | Heavy Hex | Noise |

*\*P9 was labeled "Circular" but coupling map analysis revealed a densely connected graph (node degrees 33–42, 1,069 edges).*

## Methods Attempted

Eight distinct simulation strategies were deployed, escalating from exact classical to approximate to quantum hardware:

| Method | Tool | Applied To | Outcome |
|--------|------|------------|---------|
| Exact statevector | BlueQubit `cpu` | P1, P2 | Solved both |
| MPS simulation | Qiskit Aer + BlueQubit `mps.cpu` | P3–P10 | Solved P3; noise for P4–P10 at $\chi$ up to 2,048 |
| RCM qubit reordering | NetworkX | P4–P10 | P4 bandwidth 47→2 (23.5x); still noise |
| Cloud GPU tensor network | BlueQubit `mps.gpu` | P8 | Job terminated (cost/time limit) |
| Marginal reconstruction | Custom voting scheme | P8 | Confidence → 0.5 (no signal) |
| Inverse circuit verification | Custom $U^\dagger$ tool | — | Built but no valid candidates to verify |
| IBM Quantum hardware | ibm_fez (Heron r2, 156q) | P5 | Pure decoherence noise |
| quimb / cotengra | Alternative tensor networks | P8 | API incompatibility (failed) |

## Key Findings

- **The solvability boundary sits between ~200 and ~888 two-qubit gates** on 40+ qubit circuits. Below that threshold, MPS at moderate bond dimension captures the peak; above it, entanglement exceeds any feasible $\chi$.
- **Topology alone doesn't determine tractability.** P4's cross topology reduced to bandwidth 2 via RCM (essentially 1D), yet 5,096 CZ gates still generated unmanageable entanglement.
- **Current quantum hardware can't help either.** IBM's 156-qubit Heron r2 produced pure noise on a 44-qubit / 1,892-gate circuit — the depth exceeds coherence limits.
- **Low-bond-dimension marginals don't converge.** Per-qubit probabilities averaged to ~0.5 (maximum entropy), providing zero signal about the true peak.

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install qiskit qiskit-aer bluequbit numpy

export BLUEQUBIT_API_TOKEN="your_token"

# Solve specific circuits
python solve_all_cloud.py P1 P2 P3

# Solve all via cloud
python solve_all_cloud.py
```

## Project Structure

```
├── P1_little_peak.qasm        # Circuit definitions (OpenQASM 2.0)
├── ...
├── P10_heavy_hex_4020.qasm
│
├── solve_all_cloud.py          # Cloud solver (statevector + MPS)
├── solve_all_quantum.py        # BlueQubit QPU solver
├── solve_ibm_quantum.py        # IBM Quantum (ibm_fez) solver
├── solve_enhanced.py           # Unified solver with adaptive bond dims
├── solve_marginals.py          # Marginal probability reconstruction
├── solve_verify.py             # Inverse circuit verification
├── solve_batch.py              # Batch cloud job submission
├── solve_cloud_async.py        # Async cloud job management
├── analyze_remaining.py        # Circuit topology analysis + RCM
│
├── auto_collect.py             # Cloud job status monitor
├── check_jobs.py               # Job status checker
├── results.json                # Final results and metadata
│
└── paper/
    ├── main.tex                # LaTeX source (11-page research paper)
    ├── main.pdf                # Compiled paper
    ├── generate_figures.py     # Figure generation script
    └── figures/                # 6 generated figure PDFs
```

## Research Paper

A full 11-page technical paper is available in [`paper/main.pdf`](paper/main.pdf), covering all methods, performance data, entanglement analysis, and 21 references. To regenerate:

```bash
pip install matplotlib
python paper/generate_figures.py
cd paper && pdflatex main.tex && pdflatex main.tex
```

## Tech Stack

- **[BlueQubit SDK](https://app.bluequbit.io/sdk-docs/)** — cloud quantum simulation and QPU access
- **[Qiskit](https://qiskit.org/) + [Qiskit Aer](https://github.com/Qiskit/qiskit-aer)** — circuit loading, transpilation, local MPS simulation
- **[IBM Quantum](https://quantum.ibm.com/)** — Heron r2 quantum hardware (ibm_fez)
- **[NetworkX](https://networkx.org/)** — coupling map analysis and RCM reordering
- **[quimb](https://quimb.readthedocs.io/) + [cotengra](https://cotengra.readthedocs.io/)** — tensor network contraction (experimental)
- **Python 3.10+**

## License

MIT
