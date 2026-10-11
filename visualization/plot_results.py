"""Visualization Suite for DCN Error Detection and Analysis.

Generates ONLY the four required analytical graphs:
1. Detection Rate by Error Type and Technique (Grouped Bar Chart)
2. Detection Rate versus Error Magnitude (Multi-Bit Curve showing Parity Limitation)
3. Processing Time versus Data Size (Computational Latency Curve)
4. Transmission Overhead versus Data Size (Bandwidth Penalty Curve)

Ensures graphs use the latest experiment results, not stale data.
Keeps clean transmissions separate from corrupted trials.
"""

import os
from typing import Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

TECH_COLORS = {
    "VRC / Parity": "#E63946",  # Red
    "LRC": "#457B9D",           # Steel Blue
    "Checksum": "#F4A261",      # Sandy Orange
    "CRC": "#2A9D8F"            # Teal Green
}

TECH_MARKERS = {
    "VRC / Parity": "o",
    "LRC": "s",
    "Checksum": "^",
    "CRC": "D"
}


def load_dataset(csv_path: str = "metrics_results.csv") -> Optional[pd.DataFrame]:
    """Load latest metrics dataset."""
    if not os.path.exists(csv_path):
        alt_path = os.path.join(os.path.dirname(OUTPUT_DIR), csv_path)
        if os.path.exists(alt_path):
            csv_path = alt_path
        else:
            print(f"[Error] Metrics file '{csv_path}' not found. Please run experiments first.")
            return None
    return pd.read_csv(csv_path)


def plot_detection_by_error_type(df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """Graph 1: Detection Rate by Error Type and Technique (Grouped Bar Chart).

    Clean transmissions are excluded from detection rate calculations
    to avoid skewing error detection statistics.
    """
    # Filter to only corrupted trials
    corrupted_df = df[df["error_type"].isin(["single", "multiple", "burst"])].copy()
    if corrupted_df.empty:
        return ""

    # Aggregate overall detection rate by technique and error_type
    grouped = corrupted_df.groupby(["error_type", "technique"])["detection_rate"].mean().unstack("technique")

    # Order error types logically
    order = [t for t in ["single", "multiple", "burst"] if t in grouped.index]
    grouped = grouped.reindex(order)

    # Rename index for display
    display_labels = {
        "single": "Single-Bit Error",
        "multiple": "Multiple-Bit Errors",
        "burst": "Burst Errors"
    }
    grouped.index = [display_labels.get(idx, idx) for idx in grouped.index]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    techs = [t for t in ["VRC / Parity", "LRC", "Checksum", "CRC"] if t in grouped.columns]
    x = np.arange(len(grouped.index))
    width = 0.18

    for i, tech in enumerate(techs):
        vals = grouped[tech]
        color = TECH_COLORS.get(tech, "#333333")
        rects = ax.bar(x + i * width - (len(techs) - 1) * width / 2, vals, width, label=tech, color=color, alpha=0.9)

        # Value annotations
        for rect in rects:
            height = rect.get_height()
            if not np.isnan(height):
                ax.annotate(f"{height:.1f}%",
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_title("Detection Rate by Error Type and Technique", fontsize=12, fontweight="bold")
    ax.set_xlabel("Error Model", fontsize=10, fontweight="bold")
    ax.set_ylabel("Detection Rate (%)", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(grouped.index, fontsize=10)
    ax.set_ylim(0, 115)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9)

    target_dir = output_dir or OUTPUT_DIR
    out_file = os.path.join(target_dir, "detection_rate_by_error_type.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    return out_file


def plot_detection_vs_error_magnitude(df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """Graph 2: Detection Rate versus Error Magnitude (Multiple-Bit Errors)."""
    sub = df[df["error_type"] == "multiple"].copy()
    if sub.empty:
        return ""

    ref_size = 128 if 128 in sub["data_size"].values else sub["data_size"].iloc[0]
    sub = sub[sub["data_size"] == ref_size].sort_values("error_amount")

    fig, ax = plt.subplots(figsize=(8.5, 5))

    techs = [t for t in ["VRC / Parity", "LRC", "Checksum", "CRC"] if t in sub["technique"].values]

    for tech in techs:
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "o")
        ax.plot(
            t_data["error_amount"],
            t_data["detection_rate"],
            label=tech,
            color=color,
            marker=marker,
            linewidth=2.2,
            markersize=7
        )

    ax.set_title(f"Detection Rate vs Error Magnitude ({ref_size}-bit Payload)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Number of Bit Errors", fontsize=10, fontweight="bold")
    ax.set_ylabel("Detection Rate (%)", fontsize=10, fontweight="bold")
    ax.set_ylim(-5, 108)
    ax.set_xticks(sorted(sub["error_amount"].unique()))
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower right", framealpha=0.9)

    target_dir = output_dir or OUTPUT_DIR
    out_file = os.path.join(target_dir, "detection_rate_vs_error_magnitude.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    return out_file


def plot_processing_time_vs_data_size(df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """Graph 3: Processing Time versus Data Size."""
    sub = df[df["error_type"] == "single"].copy()
    if sub.empty:
        return ""

    sub = sub.sort_values("data_size")
    fig, ax = plt.subplots(figsize=(8.5, 5))

    techs = [t for t in ["VRC / Parity", "LRC", "Checksum", "CRC"] if t in sub["technique"].values]

    for tech in techs:
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "D")
        latencies_us = t_data["average_processing_time"] * 1e6

        ax.plot(
            t_data["data_size"],
            latencies_us,
            label=tech,
            color=color,
            marker=marker,
            linewidth=2.2,
            markersize=7
        )

    ax.set_title("Processing Time vs Data Size", fontsize=12, fontweight="bold")
    ax.set_xlabel("Payload Size (bits)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Processing Latency (us)", fontsize=10, fontweight="bold")
    ax.set_xticks(sorted(sub["data_size"].unique()))
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left", framealpha=0.9)

    target_dir = output_dir or OUTPUT_DIR
    out_file = os.path.join(target_dir, "processing_time_vs_data_size.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    return out_file


def plot_overhead_vs_data_size(df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """Graph 4: Transmission Overhead versus Data Size."""
    sub = df[df["error_type"] == "single"].copy()
    if sub.empty:
        return ""

    sub = sub.sort_values("data_size")
    fig, ax = plt.subplots(figsize=(8.5, 5))

    techs = [t for t in ["VRC / Parity", "LRC", "Checksum", "CRC"] if t in sub["technique"].values]

    for tech in techs:
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "^")

        ax.plot(
            t_data["data_size"],
            t_data["average_overhead_percentage"],
            label=tech,
            color=color,
            marker=marker,
            linewidth=2.2,
            markersize=7
        )

    ax.set_title("Transmission Overhead vs Data Size", fontsize=12, fontweight="bold")
    ax.set_xlabel("Payload Size (bits)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Overhead Percentage (%)", fontsize=10, fontweight="bold")
    ax.set_xticks(sorted(sub["data_size"].unique()))
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    target_dir = output_dir or OUTPUT_DIR
    out_file = os.path.join(target_dir, "overhead_vs_data_size.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    return out_file


def generate_all_plots(csv_path: str = "metrics_results.csv", output_dir: Optional[str] = None, verbose: bool = True) -> List[str]:
    """Generate the four analytical graphs.

    Args:
        csv_path: Path to metrics results CSV.
        output_dir: Target directory for generated PNG images (defaults to visualization/).
        verbose: Whether to print console progress.

    Returns:
        List of generated file paths.
    """
    df = load_dataset(csv_path)
    if df is None:
        return []

    target_dir = output_dir or OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)

    generated: List[str] = []

    f1 = plot_detection_by_error_type(df, output_dir=target_dir)
    if f1:
        generated.append(f1)

    f2 = plot_detection_vs_error_magnitude(df, output_dir=target_dir)
    if f2:
        generated.append(f2)

    f3 = plot_processing_time_vs_data_size(df, output_dir=target_dir)
    if f3:
        generated.append(f3)

    f4 = plot_overhead_vs_data_size(df, output_dir=target_dir)
    if f4:
        generated.append(f4)

    if verbose:
        for f in generated:
            print(f"  -> {os.path.basename(f)}")

    return generated


def main():
    generate_all_plots()


if __name__ == "__main__":
    main()