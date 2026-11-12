"""Visualization Suite for DCN Error Detection and Analysis System.

Generates the four required analytical graphs using the Warm Ivory + Forest Green palette:
1. Detection Rate by Error Type and Technique (Grouped Bar Chart)
2. Detection Rate versus Error Magnitude (Multi-Bit Curve showing Parity Limitation)
3. Processing Time versus Data Size (Computational Latency Curve)
4. Transmission Overhead versus Data Size (Bandwidth Penalty Curve)

Aesthetic Guidelines:
- Clean warm ivory / white canvas (#FFFFFF / #FAF8F5).
- Forest green primary data series (#315C49).
- Muted olive and earthy complementary series (#7F9078, #B45309, #A84A48).
- Subtle, unobtrusive gridlines (#E2DFD6).
- Clear typography, legible annotations, and professional layout.
"""

import os
from typing import Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Elegant Warm Ivory + Forest Green / Earth Engineering Palette
TECH_COLORS = {
    "VRC / Parity": "#A84A48",  # Muted Crimson
    "LRC": "#7F9078",           # Muted Olive
    "Checksum": "#B45309",      # Warm Amber / Terracotta
    "CRC": "#315C49"            # Forest Green (Primary)
}

TECH_MARKERS = {
    "VRC / Parity": "o",
    "LRC": "s",
    "Checksum": "^",
    "CRC": "D"
}


def apply_academic_styling(ax, title: str, xlabel: str, ylabel: str):
    """Apply consistent, professional styling across all charts."""
    ax.set_facecolor("#FFFFFF")
    ax.figure.patch.set_facecolor("#FAF9F5")

    ax.set_title(title, fontsize=12, fontweight="bold", color="#244638", pad=12)
    ax.set_xlabel(xlabel, fontsize=10, fontweight="bold", color="#292D2A", labelpad=8)
    ax.set_ylabel(ylabel, fontsize=10, fontweight="bold", color="#292D2A", labelpad=8)

    ax.tick_params(colors="#292D2A", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D5CFBF")
    ax.spines["bottom"].set_color("#D5CFBF")
    ax.grid(True, linestyle="--", alpha=0.45, color="#D5CFBF")


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
    """Graph 1: Detection Rate by Error Type and Technique (Grouped Bar Chart)."""
    corrupted_df = df[df["error_type"].isin(["single", "multiple", "burst"])].copy()
    if corrupted_df.empty:
        return ""

    grouped = corrupted_df.groupby(["error_type", "technique"])["detection_rate"].mean().unstack("technique")

    order = [t for t in ["single", "multiple", "burst"] if t in grouped.index]
    grouped = grouped.reindex(order)

    display_labels = {
        "single": "Single-Bit Error",
        "multiple": "Multiple-Bit Errors",
        "burst": "Burst Errors"
    }
    grouped.index = [display_labels.get(idx, idx) for idx in grouped.index]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    apply_academic_styling(
        ax,
        title="Detection Rate by Error Type and Technique",
        xlabel="Physical Channel Error Model",
        ylabel="Detection Rate (%)"
    )

    techs = [t for t in ["VRC / Parity", "LRC", "Checksum", "CRC"] if t in grouped.columns]
    x = np.arange(len(grouped.index))
    width = 0.18

    for i, tech in enumerate(techs):
        vals = grouped[tech]
        color = TECH_COLORS.get(tech, "#333333")
        rects = ax.bar(
            x + i * width - (len(techs) - 1) * width / 2,
            vals,
            width,
            label=tech,
            color=color,
            edgecolor="#FFFFFF",
            linewidth=0.8,
            alpha=0.92
        )

        for rect in rects:
            height = rect.get_height()
            if not np.isnan(height):
                ax.annotate(
                    f"{height:.1f}%",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color="#292D2A"
                )

    ax.set_xticks(x)
    ax.set_xticklabels(grouped.index, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", framealpha=0.95, facecolor="#FFFFFF", edgecolor="#D5CFBF", fontsize=9)

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
    apply_academic_styling(
        ax,
        title=f"Detection Rate vs Error Magnitude ({ref_size}-bit Payload)",
        xlabel="Number of Injected Bit Errors",
        ylabel="Detection Rate (%)"
    )

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

    ax.set_ylim(-5, 108)
    ax.set_xticks(sorted(sub["error_amount"].unique()))
    ax.legend(loc="lower right", framealpha=0.95, facecolor="#FFFFFF", edgecolor="#D5CFBF", fontsize=9)

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
    apply_academic_styling(
        ax,
        title="Processing Time vs Data Size",
        xlabel="Payload Size (bits)",
        ylabel="Processing Latency (µs)"
    )

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

    ax.set_xticks(sorted(sub["data_size"].unique()))
    ax.legend(loc="upper left", framealpha=0.95, facecolor="#FFFFFF", edgecolor="#D5CFBF", fontsize=9)

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
    apply_academic_styling(
        ax,
        title="Transmission Overhead vs Data Size",
        xlabel="Payload Size (bits)",
        ylabel="Overhead Ratio (%)"
    )

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

    ax.set_xticks(sorted(sub["data_size"].unique()))
    ax.legend(loc="upper right", framealpha=0.95, facecolor="#FFFFFF", edgecolor="#D5CFBF", fontsize=9)

    target_dir = output_dir or OUTPUT_DIR
    out_file = os.path.join(target_dir, "overhead_vs_data_size.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    return out_file


def generate_all_plots(csv_path: str = "metrics_results.csv", output_dir: Optional[str] = None, verbose: bool = True) -> List[str]:
    """Generate the four analytical graphs with Warm Ivory / Forest Green styling."""
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
