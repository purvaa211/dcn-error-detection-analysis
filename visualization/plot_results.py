"""Visualization Suite for DCN Error Detection and Analysis.

Generates ONLY the 4 essential DCN analytical charts and an all-in-one Master Dashboard:
1. Detection Rate vs Number of Bit Errors (Multi-Bit Analysis: Odd/Even Parity Phenomenon)
2. Detection Rate vs Burst Error Length (Impulse Noise Immunity)
3. Transmission Overhead vs Payload Size (Bandwidth Penalty Analysis)
4. Processing Time vs Payload Size (Computational Complexity Tradeoff)
5. Master Dashboard: 2x2 publication-ready comparison figure for jury presentation slides.

All graphs are saved non-blockingly to disk at high resolution (300 DPI).
"""

import os
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt

# Ensure output directory exists
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

TECH_COLORS = {
    "Parity": "#E63946",        # Red
    "2D-Parity": "#457B9D",     # Steel Blue
    "Checksum": "#F4A261",      # Sandy Orange
    "CRC": "#2A9D8F",           # Teal Green
    "Parity (Even)": "#E63946",
    "Checksum (8-bit)": "#F4A261",
    "CRC (degree 8)": "#2A9D8F"
}

TECH_MARKERS = {
    "Parity": "o",
    "2D-Parity": "s",
    "Checksum": "^",
    "CRC": "D"
}


def load_dataset(csv_path: str = "metrics_results.csv") -> Optional[pd.DataFrame]:
    """Load summary metrics from CSV file."""
    if not os.path.exists(csv_path):
        alt_path = os.path.join(os.path.dirname(OUTPUT_DIR), csv_path)
        if os.path.exists(alt_path):
            csv_path = alt_path
        else:
            print(f"[Error] Metrics file '{csv_path}' not found. Please run experiments first.")
            return None
    return pd.read_csv(csv_path)


def plot_detection_vs_errors(df: pd.DataFrame, ax: Optional[plt.Axes] = None, save: bool = True) -> str:
    """Chart 1: Detection Rate vs Number of Bit Errors (Odd/Even Parity Analysis)."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 5))

    sub = df[df["error_type"] == "multiple"].copy()
    if sub.empty:
        return ""

    ref_size = 128 if 128 in sub["data_size"].values else sub["data_size"].iloc[0]
    sub = sub[sub["data_size"] == ref_size].sort_values("error_amount")

    for tech in sub["technique"].unique():
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "o")
        ax.plot(
            t_data["error_amount"],
            t_data["detection_rate"],
            label=tech,
            color=color,
            marker=marker,
            linewidth=2,
            markersize=7
        )

    ax.set_title(f"Detection Rate vs Number of Bit Errors ({ref_size}-bit Payload)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Number of Bit Errors Injected", fontsize=10)
    ax.set_ylabel("Detection Rate (%)", fontsize=10)
    ax.set_ylim(-5, 105)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower right", framealpha=0.9)

    out_file = os.path.join(OUTPUT_DIR, "detection_rate_by_error_count.png")
    if standalone:
        plt.tight_layout()
        plt.savefig(out_file, dpi=300)
        plt.close()
    return out_file


def plot_detection_vs_burst(df: pd.DataFrame, ax: Optional[plt.Axes] = None, save: bool = True) -> str:
    """Chart 2: Detection Rate vs Burst Error Length."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 5))

    sub = df[df["error_type"] == "burst"].copy()
    if sub.empty:
        return ""

    ref_size = 128 if 128 in sub["data_size"].values else sub["data_size"].iloc[0]
    sub = sub[sub["data_size"] == ref_size].sort_values("error_amount")

    for tech in sub["technique"].unique():
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "s")
        ax.plot(
            t_data["error_amount"],
            t_data["detection_rate"],
            label=tech,
            color=color,
            marker=marker,
            linewidth=2,
            markersize=7
        )

    ax.set_title(f"Detection Rate vs Burst Error Span ({ref_size}-bit Payload)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Burst Length (bits)", fontsize=10)
    ax.set_ylabel("Detection Rate (%)", fontsize=10)
    ax.set_ylim(-5, 105)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower right", framealpha=0.9)

    out_file = os.path.join(OUTPUT_DIR, "burst_error_detection_rate.png")
    if standalone:
        plt.tight_layout()
        plt.savefig(out_file, dpi=300)
        plt.close()
    return out_file


def plot_overhead_vs_payload(df: pd.DataFrame, ax: Optional[plt.Axes] = None, save: bool = True) -> str:
    """Chart 3: Transmission Redundancy Overhead vs Payload Size."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 5))

    sub = df[df["error_type"] == "single"].copy()
    if sub.empty:
        return ""

    sub = sub.sort_values("data_size")

    for tech in sub["technique"].unique():
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "^")
        ax.plot(
            t_data["data_size"],
            t_data["average_overhead_percentage"],
            label=tech,
            color=color,
            marker=marker,
            linewidth=2,
            markersize=7
        )

    ax.set_title("Transmission Overhead vs Payload Size", fontsize=11, fontweight="bold")
    ax.set_xlabel("Data Payload Size (bits)", fontsize=10)
    ax.set_ylabel("Overhead Percentage (%)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    out_file = os.path.join(OUTPUT_DIR, "transmission_overhead.png")
    if standalone:
        plt.tight_layout()
        plt.savefig(out_file, dpi=300)
        plt.close()
    return out_file


def plot_latency_vs_payload(df: pd.DataFrame, ax: Optional[plt.Axes] = None, save: bool = True) -> str:
    """Chart 4: Computational Latency vs Payload Size."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 5))

    sub = df[df["error_type"] == "single"].copy()
    if sub.empty:
        return ""

    sub = sub.sort_values("data_size")

    for tech in sub["technique"].unique():
        t_data = sub[sub["technique"] == tech]
        color = TECH_COLORS.get(tech, "#333333")
        marker = TECH_MARKERS.get(tech, "D")

        # Convert to microseconds for readability
        latencies_us = t_data["average_processing_time"] * 1e6
        ax.plot(
            t_data["data_size"],
            latencies_us,
            label=tech,
            color=color,
            marker=marker,
            linewidth=2,
            markersize=7
        )

    ax.set_title("Execution Latency vs Payload Size", fontsize=11, fontweight="bold")
    ax.set_xlabel("Data Payload Size (bits)", fontsize=10)
    ax.set_ylabel("Processing Latency (us)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left", framealpha=0.9)

    out_file = os.path.join(OUTPUT_DIR, "processing_time.png")
    if standalone:
        plt.tight_layout()
        plt.savefig(out_file, dpi=300)
        plt.close()
    return out_file


def generate_master_dashboard(df: pd.DataFrame) -> str:
    """Generate a combined 2x2 presentation dashboard containing all 4 key analysis charts."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Comparative Evaluation of DCN Error Detection Algorithms\n(Parity vs 2D-Parity vs Checksum vs CRC)",
        fontsize=14,
        fontweight="bold",
        y=0.98
    )

    plot_detection_vs_errors(df, ax=axes[0, 0])
    plot_detection_vs_burst(df, ax=axes[0, 1])
    plot_overhead_vs_payload(df, ax=axes[1, 0])
    plot_latency_vs_payload(df, ax=axes[1, 1])

    dashboard_file = os.path.join(OUTPUT_DIR, "dcn_performance_dashboard.png")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(dashboard_file, dpi=300)
    plt.close()
    return dashboard_file


def generate_all_plots(csv_path: str = "metrics_results.csv", show_interactive: bool = False) -> list:
    """Generate all essential analytical plots and the Master Dashboard.

    Returns:
        List of generated image file paths.
    """
    df = load_dataset(csv_path)
    if df is None:
        return []

    print("\n" + "=" * 60)
    print(" GENERATING DCN ANALYTICAL VISUALIZATIONS")
    print("=" * 60)

    generated = []

    # 1. Detection vs Multiple Bit Errors
    f1 = plot_detection_vs_errors(df)
    if f1:
        generated.append(f1)
        print(f" [Chart 1] Multi-Bit Detection Curve      -> {os.path.basename(f1)}")

    # 2. Detection vs Burst Errors
    f2 = plot_detection_vs_burst(df)
    if f2:
        generated.append(f2)
        print(f" [Chart 2] Burst Noise Immunity Curve      -> {os.path.basename(f2)}")

    # 3. Transmission Overhead
    f3 = plot_overhead_vs_payload(df)
    if f3:
        generated.append(f3)
        print(f" [Chart 3] Bandwidth Overhead Tradeoff     -> {os.path.basename(f3)}")

    # 4. Processing Latency
    f4 = plot_latency_vs_payload(df)
    if f4:
        generated.append(f4)
        print(f" [Chart 4] Computational Latency (us)      -> {os.path.basename(f4)}")

    # 5. Master Dashboard (All-in-One 2x2 figure)
    f5 = generate_master_dashboard(df)
    if f5:
        generated.append(f5)
        print(f" [Master]  All-in-One Presentation Board   -> {os.path.basename(f5)}")

    print("=" * 60)
    print(f" Total figures generated: {len(generated)} (High Resolution 300 DPI)")
    print(f" Saved in: {OUTPUT_DIR}")
    print("=" * 60 + "\n")

    if show_interactive:
        # If user explicitly wants to open the dashboard
        img = plt.imread(f5)
        plt.figure(figsize=(12, 8))
        plt.imshow(img)
        plt.axis("off")
        plt.title("DCN Analysis Dashboard (Close window to continue)")
        plt.show()

    return generated


def main():
    generate_all_plots()


if __name__ == "__main__":
    main()