"""Experiment Runner for DCN Error Detection Algorithms.

Executes controlled Monte Carlo trials across:
- Techniques: VRC / Parity, LRC, Checksum, CRC
- Error Models: Clean transmission, Single-bit, Multiple-bit, Burst
- Configurable Data Sizes, Error Magnitudes, and Trial Counts

Keeps clean transmissions separate from corrupted trials.
"""

import random
import csv
import time
from typing import List, Dict, Any, Optional

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
            "errors_injected": sim_res["errors_injected"],
            "error_detected": sim_res["error_detected"],
            "is_valid": sim_res["is_valid"],
            "processing_time": sim_res["processing_time"],
            "overhead_bits": sim_res["overhead_bits"],
            "overhead_percentage": sim_res["overhead_percentage"]
        })

    return results


def run_all_experiments(
    techniques: Optional[List[str]] = None,
    data_sizes: Optional[List[int]] = None,
    multi_error_amounts: Optional[List[int]] = None,
    burst_lengths: Optional[List[int]] = None,
    include_clean: bool = True,
    trials: int = 50,
    output_file: str = "experiment_results.csv",
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """Execute all experimental sweeps based on configurable parameters.

    Args:
        techniques: List of techniques (default: VRC / Parity, LRC, Checksum, CRC).
        data_sizes: List of payload sizes in bits.
        multi_error_amounts: Multiple-bit error quantities to test.
        burst_lengths: Burst error lengths to test.
        include_clean: Whether to include clean transmission benchmark.
        trials: Number of trials per configuration.
        output_file: Destination CSV path.
        verbose: Print progress to console.
    """
    if techniques is None:
        techniques = ["VRC / Parity", "LRC", "Checksum", "CRC"]

    if data_sizes is None:
        data_sizes = [32, 64, 128, 256, 512, 1024]

    if multi_error_amounts is None:
        multi_error_amounts = [1, 2, 3, 4, 5, 6, 7, 8]

    if burst_lengths is None:
        burst_lengths = [2, 4, 6, 8, 12, 16]

    all_results: List[Dict[str, Any]] = []
    t_start = time.time()

    if verbose:
        print("\n" + "=" * 60)
        print(" RUNNING DCN BENCHMARK EXPERIMENTS")
        print(f" Techniques   : {', '.join(techniques)}")
        print(f" Data Sizes   : {data_sizes} bits")
        print(f" Multi-Errors : {multi_error_amounts} bits")
        print(f" Burst Spans  : {burst_lengths} bits")
        print(f" Trials/Config: {trials}")
        print("=" * 60)

    for tech in techniques:
        # 1. Clean transmission benchmark (separate from corrupted)
        if include_clean:
            for sz in data_sizes:
                res = run_single_config(
                    technique=tech,
                    error_type="clean",
                    data_size=sz,
                    error_amount=0,
                    trials=trials
                )
                all_results.extend(res)

        # 2. Single-bit error sweep across payload sizes
        for sz in data_sizes:
            res = run_single_config(
                technique=tech,
                error_type="single",
                data_size=sz,
                error_amount=1,
                trials=trials
            )
            all_results.extend(res)

        # 3. Multiple-bit errors across error magnitudes (using 128-bit payload as reference)
        ref_size = 128 if 128 in data_sizes else data_sizes[0]
        for err_cnt in multi_error_amounts:
            res = run_single_config(
                technique=tech,
                error_type="multiple",
                data_size=ref_size,
                error_amount=err_cnt,
                trials=trials
            )
            all_results.extend(res)

        # 4. Burst errors across burst lengths (using 128-bit payload as reference)
        for b_len in burst_lengths:
            res = run_single_config(
                technique=tech,
                error_type="burst",
                data_size=ref_size,
                error_amount=b_len,
                trials=trials
            )
            all_results.extend(res)

        if verbose:
            print(f"  [COMPLETED] {tech:<14} (All error models evaluated)")

    # Save to CSV
    fieldnames = [
        "technique",
        "error_type",
        "data_size",
        "error_amount",
        "trial",
        "errors_injected",
        "error_detected",
        "is_valid",
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
        print(f" Completed in {elapsed:.2f} seconds.")
        print(f" Total generated trial rows: {len(all_results):,}")
        print(f" Saved to: {output_file}")
        print("=" * 60 + "\n")

    return all_results


def main():
    run_all_experiments(trials=50)


if __name__ == "__main__":
    main()