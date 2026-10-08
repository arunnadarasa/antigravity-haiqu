#!/usr/bin/env python3
"""
CLI runner for parameterized QAOA optimization experiments on Haiqu.
"""
import argparse
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run QAOA experiment with Haiqu SDK")
    parser.add_argument("--vars", type=int, default=4, help="Number of binary decision variables")
    parser.add_argument("--shots", type=int, default=500, help="Shot budget for circuit execution")
    parser.add_argument("--device", type=str, default="aer_simulator", help="Target device ID")
    parser.add_argument("--postprocess-iters", type=int, default=3, help="Iterations of bitflip search")
    parser.add_argument("--compress", action="store_true", help="Apply state compression to the circuit")
    args = parser.parse_args()

    from haiqu.sdk import haiqu
    from qiskit_addon_opt_mapper.problems import OptimizationProblem
    from haiqu.sdk.optimization import cvar_expectation

    api_key = os.getenv("HAIQU_API_KEY")
    if api_key:
        haiqu.login(api_access_key=api_key)
    else:
        haiqu.login()

    print(f"Creating OptimizationProblem with {args.vars} binary variables...")
    prob = OptimizationProblem("parameterized_qaoa_experiment")
    prob.binary_var_list(args.vars)

    # Generate synthetic random weights
    import random
    random.seed(42)
    linear = [round(random.uniform(-5.0, 5.0), 2) for _ in range(args.vars)]
    quadratic = {}
    for i in range(args.vars):
        for j in range(i + 1, args.vars):
            if random.random() > 0.5:
                quadratic[(i, j)] = round(random.uniform(-3.0, 3.0), 2)

    prob.minimize(linear=linear, quadratic=quadratic)
    print(f"Objective defined: {len(linear)} linear terms, {len(quadratic)} quadratic terms.")

    t0 = time.perf_counter()
    circuit = haiqu.build_lr_qaoa_circuit(prob)
    print(f"LR-QAOA circuit compiled in {time.perf_counter() - t0:.2f}s (Depth: {circuit.depth}, Qubits: {circuit.num_qubits})")

    target_circuit = circuit
    if args.compress:
        print("Applying Haiqu State Compression...")
        t_comp = time.perf_counter()
        comp_job = haiqu.state_compression(circuit)
        target_circuit = comp_job.result()
        print(f"Compressed circuit in {time.perf_counter() - t_comp:.2f}s (New Depth: {target_circuit.depth})")

    print(f"Executing {args.shots} shots on {args.device}...")
    t_run = time.perf_counter()
    job = haiqu.run(target_circuit, shots=args.shots, device_id=args.device)
    raw_counts = job.result()[0]
    print(f"Execution complete in {time.perf_counter() - t_run:.2f}s. Sampled {len(raw_counts)} unique states.")

    print(f"Running server-side classical postprocessing ({args.postprocess_iters} iterations)...")
    costs, proc_counts = haiqu.postprocess(counts=raw_counts, problem=prob, postprocess_iterations=args.postprocess_iters)
    best_bs = min(costs, key=costs.get)

    cvar_10 = cvar_expectation(raw_counts, problem=prob, alpha=0.1)
    cvar_mean = cvar_expectation(raw_counts, problem=prob, alpha=1.0)

    print("\n" + "=" * 50)
    print("EXPERIMENT SUMMARY")
    print("=" * 50)
    print(f"Optimal Bitstring:        {best_bs}")
    print(f"Best Energy/Cost:         {costs[best_bs]:.4f}")
    print(f"CVaR @ 10% (Tail):        {cvar_10:.4f}")
    print(f"Distribution Mean:        {cvar_mean:.4f}")
    print(f"States after Bitflip:     {len(proc_counts)}")
    print("=" * 50)

if __name__ == "__main__":
    main()
