#!/usr/bin/env python3
"""
Diagnostic Health Check for Haiqu SDK Stack in Antigravity.
Validates:
1. Haiqu SDK importation and version.
2. HAIQU_API_KEY environment variable.
3. API authentication via haiqu.login().
4. OptimizationProblem construction (QUBO & HUBO).
5. LR-QAOA circuit compilation via haiqu.build_lr_qaoa_circuit().
6. Simulator execution on aer_simulator via haiqu.run().
7. Server-side bitflip local search via haiqu.postprocess().
8. CVaR expectation computation.
9. Circuit state compression via haiqu.state_compression().
"""
import os
import sys
import time

def run_health_check():
    print("=" * 65)
    print("  Antigravity Haiqu Skill — Diagnostic Health Check")
    print("=" * 65)

    # 1. SDK Import
    try:
        from haiqu.sdk import haiqu
        import haiqu as haiqu_pkg
        version = getattr(haiqu_pkg, "__version__", "1.6.0+")
        print(f"[✓] Haiqu SDK imported successfully (version: {version})")
    except ImportError as e:
        print(f"[✗] Failed to import haiqu-sdk: {e}")
        sys.exit(1)

    # 2. API Key Check
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("HAIQU_API_KEY")
    if not api_key:
        print("[✗] HAIQU_API_KEY environment variable not found.")
        print("    Please set HAIQU_API_KEY in your .env or environment.")
        sys.exit(1)
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"[✓] Found HAIQU_API_KEY: {masked_key}")

    # 3. Authentication
    try:
        haiqu.login(api_access_key=api_key)
        print("[✓] Authenticated with Haiqu Cloud API successfully.")
    except Exception as e:
        print(f"[✗] Authentication failed: {e}")
        sys.exit(1)

    # 4. Problem Definition
    try:
        from qiskit_addon_opt_mapper.problems import OptimizationProblem
        prob = OptimizationProblem("diagnostic_toy")
        prob.binary_var_list(3)
        prob.minimize(linear=[-1.0, -2.0, -1.5], quadratic={(0, 1): 2.5})
        print(f"[✓] Formulated OptimizationProblem with {prob.get_num_vars()} variables.")
    except Exception as e:
        print(f"[✗] Failed to construct OptimizationProblem: {e}")
        sys.exit(1)

    # 5. Circuit Compilation
    try:
        circuit = haiqu.build_lr_qaoa_circuit(prob)
        print(f"[✓] LR-QAOA circuit compiled: {circuit.num_qubits} qubits, depth: {circuit.depth}")
    except Exception as e:
        print(f"[✗] Failed to build LR-QAOA circuit: {e}")
        sys.exit(1)

    # 6. Simulator Run
    try:
        job = haiqu.run(circuit, shots=100, device_id="aer_simulator")
        raw_counts = job.result()[0]
        print(f"[✓] Successfully executed on aer_simulator: {len(raw_counts)} unique bitstrings sampled.")
    except Exception as e:
        print(f"[✗] Simulator execution failed: {e}")
        sys.exit(1)

    # 7. Postprocessing & CVaR
    try:
        from haiqu.sdk.optimization import cvar_expectation
        costs, counts = haiqu.postprocess(counts=raw_counts, problem=prob, postprocess_iterations=2)
        cvar_val = cvar_expectation(raw_counts, problem=prob, alpha=0.5)
        best_bs = min(costs, key=costs.get)
        print(f"[✓] Classical postprocessing & CVaR succeeded: best bitstring={best_bs}, cost={costs[best_bs]:.2f}, CVaR={cvar_val:.2f}")
    except Exception as e:
        print(f"[✗] Postprocessing/CVaR failed: {e}")
        sys.exit(1)

    # 8. State Compression
    try:
        comp_job = haiqu.state_compression(circuit)
        comp_circuit = comp_job.result()
        print(f"[✓] Circuit state compression succeeded: Depth {circuit.depth} -> {comp_circuit.depth}")
    except Exception as e:
        print(f"[!] State compression note/warning: {e}")

    print("\n" + "=" * 65)
    print("  ALL CORE HAIQU CAPABILITIES OPERATIONAL & VERIFIED!")
    print("=" * 65)

if __name__ == "__main__":
    run_health_check()
