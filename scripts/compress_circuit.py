#!/usr/bin/env python3
"""
CLI utility to compress quantum circuits using Haiqu State Compression.
"""
import argparse
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Benchmark Haiqu State Compression")
    parser.add_argument("--qubits", type=int, default=4, help="Number of qubits")
    parser.add_argument("--depth", type=int, default=15, help="Approximate target depth")
    args = parser.parse_args()

    from haiqu.sdk import haiqu
    from qiskit.circuit.random import random_circuit

    api_key = os.getenv("HAIQU_API_KEY")
    if api_key:
        haiqu.login(api_access_key=api_key)
    else:
        haiqu.login()

    print(f"Generating synthetic {args.qubits}-qubit circuit with target depth {args.depth}...")
    qc = random_circuit(num_qubits=args.qubits, depth=args.depth, measure=False, seed=42)
    original_depth = qc.depth()
    print(f"Original Qiskit Circuit: {qc.num_qubits} qubits, depth={original_depth}, gates={len(qc.data)}")

    print("Submitting to Haiqu State Compression service...")
    t0 = time.perf_counter()
    job = haiqu.state_compression(qc)
    compressed_circuit = job.result()
    latency = time.perf_counter() - t0

    comp_depth = compressed_circuit.depth
    reduction_pct = ((original_depth - comp_depth) / original_depth) * 100 if original_depth > 0 else 0

    print("\n" + "=" * 50)
    print("HAIQU STATE COMPRESSION BENCHMARK")
    print("=" * 50)
    print(f"Original Depth:      {original_depth}")
    print(f"Compressed Depth:    {comp_depth}")
    print(f"Depth Reduction:     {reduction_pct:.1f}%")
    print(f"Service Latency:     {latency:.2f}s")
    print("=" * 50)

if __name__ == "__main__":
    main()
