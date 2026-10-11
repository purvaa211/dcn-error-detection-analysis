"""Metrics Processing Module for Error Detection Evaluation.

Aggregates raw Monte Carlo trial results into statistical performance indicators:
- Detection Rate (%)
- Undetected Error Rate (%)
- Average Computational Latency (μs)
- Redundancy Overhead (bits and %)
"""

import csv
from typing import List, Dict, Any


def load_raw_results(filename: str = "experiment_results.csv") -> List[Dict[str, Any]]:
    """Load raw trial logs from CSV file."""
    results = []
    with open(filename, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            results.append({
                "technique": row["technique"],
                "error_type": row["error_type"],
                "data_size": int(row["data_size"]),
                "error_amount": int(row["error_amount"]),
                "trial": int(row["trial"]),
                "error_detected": row["error_detected"].strip().lower() == "true",
                "processing_time": float(row["processing_time"]),
                "overhead_bits": int(row["overhead_bits"]),
                "overhead_percentage": float(row["overhead_percentage"])
            })
    return results


def calculate_metrics(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group trial records and compute statistical metrics per configuration."""
    groups: Dict[tuple, Dict[str, Any]] = {}

    for row in results:
        key = (
            row["technique"],
            row["error_type"],
            row["data_size"],
            row["error_amount"]
        )

        if key not in groups:
            groups[key] = {
                "total": 0,
                "detected": 0,
                "processing_time": 0.0,
                "overhead_bits": 0,
                "overhead_percentage": 0.0
            }

        g = groups[key]
        g["total"] += 1
        if row["error_detected"]:
            g["detected"] += 1
        g["processing_time"] += row["processing_time"]
        g["overhead_bits"] += row["overhead_bits"]
        g["overhead_percentage"] += row["overhead_percentage"]

    metrics = []
    for key, val in groups.items():
        technique, error_type, data_size, error_amount = key
        total = val["total"]
        detected = val["detected"]
        undetected = total - detected

        detection_rate = (detected / total) * 100.0 if total > 0 else 0.0
        undetected_rate = (undetected / total) * 100.0 if total > 0 else 0.0
        avg_time = val["processing_time"] / total if total > 0 else 0.0
        avg_overhead_bits = val["overhead_bits"] / total if total > 0 else 0.0
        avg_overhead_pct = val["overhead_percentage"] / total if total > 0 else 0.0

        metrics.append({
            "technique": technique,
            "error_type": error_type,
            "data_size": data_size,
            "error_amount": error_amount,
            "total_trials": total,
            "detected": detected,
            "undetected": undetected,
            "detection_rate": round(detection_rate, 2),
            "undetected_rate": round(undetected_rate, 2),
            "average_processing_time": avg_time,
            "average_processing_time_us": round(avg_time * 1e6, 2),
            "average_overhead_bits": avg_overhead_bits,
            "average_overhead_percentage": round(avg_overhead_pct, 4)
        })

    return metrics


def save_metrics(metrics: List[Dict[str, Any]], filename: str = "metrics_results.csv") -> None:
    """Save processed summary metrics to CSV."""
    if not metrics:
        return

    fieldnames = list(metrics[0].keys())
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)


def compute_and_save_metrics(
    input_file: str = "experiment_results.csv",
    output_file: str = "metrics_results.csv",
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """Load raw results, calculate metrics, and save to CSV."""
    if verbose:
        print(f"Loading experimental results from {input_file}...")
    raw = load_raw_results(input_file)
    if verbose:
        print(f"Loaded {len(raw):,} raw trials. Aggregating metrics...")
    metrics = calculate_metrics(raw)
    save_metrics(metrics, output_file)
    if verbose:
        print(f"Aggregated {len(metrics)} experimental configurations to {output_file}.")
    return metrics


def main():
    compute_and_save_metrics()


if __name__ == "__main__":
    main()