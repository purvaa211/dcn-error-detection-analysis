"""Metrics Processing Module for Error Detection Evaluation.

Aggregates raw Monte Carlo trial results into statistical performance indicators:
- Detection Rate (%) on Corrupted Transmissions
- Clean Transmission Integrity / False Alarm Rate
- Average Computational Latency (us)
- Redundancy Overhead (bits and %)

Maintains clean transmissions separate from corrupted trials.
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
                "errors_injected": int(row.get("errors_injected", 0)),
                "error_detected": row["error_detected"].strip().lower() == "true",
                "is_valid": row.get("is_valid", "true").strip().lower() == "true",
                "processing_time": float(row["processing_time"]),
                "overhead_bits": int(row["overhead_bits"]),
                "overhead_percentage": float(row["overhead_percentage"])
            })
    return results


def calculate_metrics(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group trial records and compute statistical metrics per configuration.

    Clean transmissions (0 errors injected) are evaluated for false alarms and accuracy,
    while corrupted transmissions are evaluated for detection rate.
    """
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
                "valid": 0,
                "processing_time": 0.0,
                "overhead_bits": 0,
                "overhead_percentage": 0.0
            }

        g = groups[key]
        g["total"] += 1
        if row["error_detected"]:
            g["detected"] += 1
        if row["is_valid"]:
            g["valid"] += 1
        g["processing_time"] += row["processing_time"]
        g["overhead_bits"] += row["overhead_bits"]
        g["overhead_percentage"] += row["overhead_percentage"]

    metrics = []
    for key, val in groups.items():
        technique, error_type, data_size, error_amount = key
        total = val["total"]
        detected = val["detected"]
        valid = val["valid"]
        undetected = total - detected

        is_clean = (error_type == "clean")

        if is_clean:
            # Clean transmission: detection rate is N/A; clean accuracy is valid / total
            detection_rate = 0.0
            undetected_rate = 0.0
            clean_accuracy = (valid / total) * 100.0 if total > 0 else 100.0
        else:
            detection_rate = (detected / total) * 100.0 if total > 0 else 0.0
            undetected_rate = (undetected / total) * 100.0 if total > 0 else 0.0
            clean_accuracy = 100.0

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
            "clean_accuracy": round(clean_accuracy, 2),
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
        print(f"Loading raw experimental data from {input_file}...")
    raw = load_raw_results(input_file)
    if verbose:
        print(f"Loaded {len(raw):,} trials. Aggregating performance metrics...")
    metrics = calculate_metrics(raw)
    save_metrics(metrics, output_file)
    if verbose:
        print(f"Aggregated {len(metrics)} experimental configurations to {output_file}.")
    return metrics


def main():
    compute_and_save_metrics()


if __name__ == "__main__":
    main()