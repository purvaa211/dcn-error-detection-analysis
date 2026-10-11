"""Experiment Runner for Empirical Evaluation of DCN Error Detection Algorithms.

Executes controlled Monte-Carlo trials across:
- Techniques: Parity (1D), 2D Parity Matrix, Internet Checksum, CRC-8, CRC-16
- Error Models: Single-bit, Multiple-bit (1 to 8 errors), Burst errors (2 to 16 span)
- Payload Sizes: 32, 64, 128, 256, 512, 1024 bits

Supports both Quick Demo Mode (fast execution for live jury) and Full Benchmark Mode.
"""

import random
import csv
import time
from typing import List, Dict, Any

from simulation.simulator import simulate

random.seed(42)


def generate_binary_data(size: int) -> str:
    """Generate random binary payload of specified bit size."""
    return "".join(random.choice("01") for _ in range(size))


def run_single_config(
    technique: str,
    error_type: str,
    data_size: int,
    error_amount: int,
    trials: int
) -> List[Dict[str, Any]]:
    """Run specified number of Monte Carlo trials for a single configuration."""
    results = []

    for trial_idx in range(1, trials + 1):
        data = generate_binary_data(data_size)

        sim_res = simulate(
            data=data,
            technique=technique,
            error_type=error_type,
            error_amount=error_amount
        )

        results.append({
            "technique": technique,
            "error_type": error_type,
            "data_size": data_size,
            "error_amount": error_amount,
            "trial": trial_idx,
            "error_detected": sim_res["error_detected"],
            "processing_time": sim_res["processing_time"],
            "overhead_bits": sim_res["overhead_bits"],
            "overhead_percentage": sim_res["overhead_percentage"]
        })

    return results


def run_all_experiments(
    trials: int = 100,
    output_file: str = "experiment_results.csv",
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """Execute all experimental sweeps across techniques, error models, and payload sizes.

    Args:
        trials: Number of Monte Carlo trials per configuration (default: 100 for fast run).
        output_file: CSV destination path.
        verbose: Whether to print progress to console.
    """
    techniques = [
        "Parity",
        "2D-Parity",
        "Checksum",
        "CRC"
    ]

    data_sizes = [32, 64, 128, 256, 512, 1024]

    # Test both odd and even error amounts (1 through 8) to clearly show Parity's behavior
    multi_error_amounts = [1, 2, 3, 4, 5, 6, 7, 8]

    # Burst error lengths
    burst_lengths = [2, 4, 6, 8, 12, 16]

    all_results: List[Dict[str, Any]] = []
    t_start = time.time()

    if verbose:
        print("\n" + "=" * 60)
        print(" RUNNING DCN ERROR DETECTION BENCHMARK SUITE")
        print(f" Trials per configuration: {trials}")
        print("=" * 60)

    for tech in techniques:
        # 1. Single bit error sweep across payload sizes
        for sz in data_sizes:
            res = run_single_config(
                technique=tech,
                error_type="single",
                data_size=sz,
                error_amount=1,
                trials=trials
            )
            all_results.extend(res)

        # 2. Multiple bit errors (using 128-bit payload as reference)
        for err_cnt in multi_error_amounts:
            res = run_single_config(
                technique=tech,
                error_type="multiple",
                data_size=128,
                error_amount=err_cnt,
                trials=trials
            )
            all_results.extend(res)

        # 3. Burst errors (using 128-bit payload as reference)
        for b_len in burst_lengths:
            res = run_single_config(
                technique=tech,
                error_type="burst",
                data_size=128,
                error_amount=b_len,
                trials=trials
            )
            all_results.extend(res)

        if verbose:
            print(f"  [COMPLETED] {tech:<12} (all error models & sizes)")

    # Save to CSV
    fieldnames = [
        "technique",
        "error_type",
        "data_size",
        "error_amount",
        "trial",
        "error_detected",
        "processing_time",
        "overhead_bits",
        "overhead_percentage"
    ]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    elapsed = time.time() - t_start
    if verbose:
        print("=" * 60)
        print(f" Benchmark completed in {elapsed:.2f} seconds.")
        print(f" Total trial data points: {len(all_results):,}")
        print(f" Saved to: {output_file}")
        print("=" * 60 + "\n")

    return all_results


def main():
    """CLI entry point for running experiments."""
    run_all_experiments(trials=100)


if __name__ == "__main__":
    main()