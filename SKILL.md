---
name: antigravity-haiqu
description: Official Google Antigravity skill for developing, compiling, compressing, and benchmarking quantum algorithms on the Haiqu Quantum Platform using Haiqu SDK 1.6.0+ and AgenticOS. Provides end-to-end support for combinatorial optimization (QUBO and higher-order HUBO via qiskit_addon_opt_mapper.problems.OptimizationProblem), Linear-Ramp QAOA circuit generation, circuit state compression, cloud simulator and QPU execution, server-side bitflip local search postprocessing, CVaR expectation scoring, and SU(2)-equivariant variational quantum circuits.
---

# Antigravity Haiqu Skill

The **Antigravity Haiqu Skill** equips Google Antigravity agents with comprehensive capabilities to design, compile, compress, execute, and verify quantum algorithms on the **Haiqu Quantum Platform** using the official **Haiqu SDK (v1.6.0+)** and **Haiqu AgenticOS**.

---

## 1. Core Principles & Modern Architecture

> [!IMPORTANT]
> **Modern Modular Workflow vs. Deprecated Shortcuts**
> As of **Haiqu SDK 1.6.0** (released October 2026):
> - **Public Problem Type:** Haiqu uses `qiskit_addon_opt_mapper.problems.OptimizationProblem`.
> - **Native Higher-Order (HUBO):** The optimization stack natively supports higher-order terms (`higher_order={degree: {(vars): coeff}}`) without requiring manual reduction to quadratic form or extra slack qubits.
> - **Deprecated Surfaces:** The legacy `haiqu.sdk.optimization.QUBO` class and `haiqu.solve_qubo` shortcut are deprecated. Always use the modular workflow:
>   $$\text{OptimizationProblem} \longrightarrow \text{build\_lr\_qaoa\_circuit} \longrightarrow \text{state\_compression} \longrightarrow \text{run} \longrightarrow \text{postprocess}$$
> - **Zero-Hype Scientific Integrity:** Combinatorial optimization on NISQ hardware must be benchmarked against exact classical baselines (Google OR-Tools CP-SAT, branch-and-cut, or brute-force enumeration). Measure feasibility rates, approximation ratios, and CVaR tails without assuming unjustified quantum advantage.

---

## 2. Authentication & Initialization

The Haiqu SDK reads API access keys from environment variables or direct initialization:

```python
import os
from dotenv import load_dotenv
from haiqu.sdk import haiqu

load_dotenv()

# Option A: Login with explicit key
haiqu.login(api_access_key=os.getenv("HAIQU_API_KEY"))

# Option B: Login reading HAIQU_API_KEY from environment directly
haiqu.login()

# Initialize or attach to an experiment
haiqu.init("Elective Resource Optimization Experiment")
```

---

## 3. Combinatorial Optimization Workflow

### 3.1 Defining Problems with `OptimizationProblem`

Haiqu accepts unconstrained binary polynomial problems of arbitrary degree.

#### Quadratic Unconstrained Binary Optimization (QUBO):
```python
from qiskit_addon_opt_mapper.problems import OptimizationProblem

problem = OptimizationProblem("theatre_scheduling_qubo")
x = problem.binary_var_list(4)

# Define linear and quadratic interaction terms
problem.minimize(
    linear=[-2.5, -4.0, -1.8, -3.2],
    quadratic={
        (0, 1): 5.0,  # Mutual exclusion penalty
        (2, 3): 4.0
    }
)
```

#### Native Higher-Order Binary Optimization (HUBO):
No auxiliary variables or quadratization reductions required:
```python
hubo = OptimizationProblem("higher_order_model")
hubo.binary_var_list(3)

# Minimizes: -1.5 * x0 * x1 * x2
hubo.minimize(higher_order={3: {(0, 1, 2): -1.5}})
```

#### Handling Constrained Problems (Penalty Folding):
If linear or quadratic inequality/equality constraints are added to `OptimizationProblem`, they must be penalty-folded into an unconstrained polynomial prior to circuit construction:
```python
from haiqu.sdk.optimization import is_constrained, to_unconstrained_problem

if is_constrained(problem):
    # Folds constraints into quadratic penalties
    problem = to_unconstrained_problem(problem, penalty=25.0)
```

---

### 3.2 Compiling Linear-Ramp QAOA Circuits

Haiqu automatically builds optimized Linear-Ramp QAOA (LR-QAOA) circuits from unconstrained `OptimizationProblem` instances:

```python
# Builds synchronous LR-QAOA circuit immediately
circuit = haiqu.build_lr_qaoa_circuit(problem)

print(f"Circuit ID: {circuit.id}")
print(f"Qubits: {circuit.num_qubits}")
print(f"Circuit Depth: {circuit.depth}")
```

---

### 3.3 Haiqu State Compression

On noisy intermediate-scale quantum (NISQ) devices, deep circuits suffer from gate infidelities and decoherence. Haiqu provides proprietary **state compression** that compiles the circuit into an equivalent shallower ansatz:

```python
# Submit circuit for state compression
compression_job = haiqu.state_compression(circuit)
compressed_circuit = compression_job.result()

print(f"Original Depth: {circuit.depth} -> Compressed Depth: {compressed_circuit.depth}")
```

---

### 3.4 Hardware & Simulator Execution

Execute circuits across cloud backends (e.g. `aer_simulator` or connected QPU hardware):

```python
# Run circuit with shot allocation
job = haiqu.run(
    compressed_circuit,
    shots=1000,
    device_id="aer_simulator"  # or hardware backend ID
)

# Returns dictionary of sampled bitstrings and frequency counts
raw_counts = job.result()[0]
# e.g., {'1100': 420, '1010': 310, '0110': 270}
```

---

### 3.5 Classical Server-Side Postprocessing & CVaR

Haiqu provides server-side bitflip local search to refine QPU samples and escape local minima, alongside Conditional Value at Risk (CVaR) expectation metrics:

```python
from haiqu.sdk.optimization import cvar_expectation

# 1. Classical server-side bitflip local search (runs on Haiqu API)
# Returns (processed_costs, processed_counts)
processed_costs, processed_counts = haiqu.postprocess(
    counts=raw_counts,
    problem=problem,
    postprocess_iterations=5
)

best_bitstring = min(processed_costs, key=processed_costs.get)
print(f"Best solution: {best_bitstring} with energy: {processed_costs[best_bitstring]}")

# 2. CVaR Expectations over the sample distribution
# alpha=1.0: standard mean expectation value
# alpha=0.1: mean over the best 10% of samples (distribution tail)
mean_expectation = cvar_expectation(raw_counts, problem=problem, alpha=1.0)
cvar_10_tail = cvar_expectation(raw_counts, problem=problem, alpha=0.1)

print(f"Distribution Mean: {mean_expectation:.3f} | Best 10% CVaR: {cvar_10_tail:.3f}")
```

---

## 4. Variational QML & SU(2)-Equivariant Circuits

Haiqu SDK includes specialized equivariant ansatz compilers for geometric quantum machine learning and physics simulations:

```python
from haiqu.sdk.qml import (
    is_su2_equivariant,
    su2_equivariant_ansatz,
    su2_equivariant_2_qubit_gate,
    brickwork_pattern,
    VariationalProblem,
    NFTOptimizerOptions,
    ScipyOptimizerOptions
)
from qiskit.quantum_info import SparsePauliOp

# 1. Build an SU(2) equivariant ansatz
num_qubits = 4
ansatz = su2_equivariant_ansatz(num_qubits=num_qubits, reps=2)

# 2. Define Hamiltonian observable
observable = SparsePauliOp.from_list([("ZZZZ", 1.0), ("IIZZ", 0.5)])

# 3. Formulate Variational Problem
v_problem = VariationalProblem(ansatz, observable)

# 4. Run variational optimization using NFT or Scipy (COBYLA)
job = haiqu.variational_optimization(
    problem=v_problem,
    device_id="aer_simulator",
    shots=1000,
    optimizer_options=NFTOptimizerOptions(maxiter=100)
)

result = job.result()
print(f"Minimum loss: {result.min_loss}")
print(f"Optimal parameters: {result.optimal_parameters}")
```

---

## 5. Built-in Diagnostic & Verification Scripts

This skill includes turnkey automated scripts in `scripts/`:

### 5.1 Stack Health Verification
Verifies authentication, SDK version, circuit generation, simulator execution, state compression, and postprocessing:
```bash
python scripts/verify_haiqu_stack.py
```

### 5.2 Combinatorial Optimization Benchmark
Runs a full end-to-end QUBO/HUBO experiment comparing raw QAOA against postprocessed QAOA:
```bash
python scripts/run_qaoa_experiment.py --vars 6 --shots 1000
```

### 5.3 Circuit State Compression Utility
Submits an arbitrary Qiskit circuit to Haiqu's compression engine and reports depth reduction:
```bash
python scripts/compress_circuit.py --qubits 4 --depth 20
```

---

## 6. Antigravity Skill Guidelines for Agents

When implementing quantum algorithms with Haiqu:
1. **Never use deprecated APIs:** Avoid `from haiqu.sdk.optimization import QUBO` and `haiqu.solve_qubo`. Always import `OptimizationProblem` from `qiskit_addon_opt_mapper.problems`.
2. **Always evaluate constraint feasibility:** When solving real-world operational problems (e.g., healthcare scheduling, portfolio optimization), always decode bitstrings to check whether hard operational constraints are satisfied.
3. **Report both positive and negative findings:** NISQ QAOA often struggles with dense quadratic penalty landscapes. Documenting where quantum sampling requires postprocessing or where classical solvers (OR-Tools) dominate is essential for scientific integrity.
4. **Leverage state compression:** Always test `haiqu.state_compression` on deep circuits before QPU submission to reduce hardware noise and gate decoherence.
