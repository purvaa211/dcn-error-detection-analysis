"""Data Communication and Computer Networks (DCN) Project.

Error Generation, Detection, and Comparative Performance Analysis System.
Author: Purva
Subject: Data Communication and Computer Networks (DCN)

Interactive Console Interface.
"""

import sys
import os
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.parity import add_vrc, check_vrc, format_vrc_working
from algorithms.lrc import add_lrc, check_lrc, format_lrc_working
from algorithms.checksum import add_checksum, verify_checksum_detailed, format_checksum_working
from algorithms.crc import crc_encode, crc_check_detailed, format_crc_working, CRC_POLYNOMIALS
from simulation.simulator import simulate, compare_all_techniques
from simulation.error_generator import (
    clean_transmission,
    single_bit_error,
    multiple_bit_error,
    burst_error,
    manual_error
)
from experiments.experiment_runner import run_all_experiments
from experiments.metrics import compute_and_save_metrics
from visualization.plot_results import generate_all_plots


# ======================================================================
# HELPER UTILITIES: INPUT PARSING & VISUAL FORMATTING
# ======================================================================

def clear_screen() -> None:
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Display project header banner."""
    print("=" * 72)
    print("     DATA COMMUNICATION AND COMPUTER NETWORKS (DCN) PROJECT")
    print("      ERROR GENERATION, DETECTION & ANALYSIS SYSTEM")
    print("=" * 72)


def text_to_binary(text: str) -> str:
    """Convert an ASCII text string to an 8-bit binary representation."""
    return "".join(format(ord(c), "08b") for c in text)


def get_user_data_input() -> str:
    """Prompt user to supply data via binary, text, or random generation."""
    print("\n--- DATA INPUT SELECTION ---")
    print("  [1] Enter Custom Binary String (e.g. 110100110011)")
    print("  [2] Enter Plain Text String    (auto-converted to 8-bit binary ASCII)")
    print("  [3] Generate Random Binary Bits")

    choice = input("\nEnter choice [1-3] (default 1): ").strip()

    if choice == "2":
        user_txt = input("Enter text string: ").strip()
        if not user_txt:
            user_txt = "DCN"
        bin_data = text_to_binary(user_txt)
        print(f" -> ASCII Text: '{user_txt}'")
        print(f" -> Converted Binary ({len(bin_data)} bits): {bin_data}")
        return bin_data

    elif choice == "3":
        length_input = input("Enter number of bits to generate [8-256] (default 16): ").strip()
        bit_len = int(length_input) if length_input.isdigit() else 16
        bit_len = max(8, min(bit_len, 512))
        import random
        bin_data = "".join(random.choice("01") for _ in range(bit_len))
        print(f" -> Generated Random Binary ({bit_len} bits): {bin_data}")
        return bin_data

    else:
        while True:
            raw_bin = input("Enter binary string (0s and 1s): ").strip()
            if not raw_bin:
                raw_bin = "1011011011001100"
                print(f" -> Using default binary: {raw_bin}")
                return raw_bin
            if all(c in "01" for c in raw_bin):
                return raw_bin
            print(" [!] Invalid input. String must only contain '0' and '1'. Please retry.")


def highlight_corrupted_bits(original: str, corrupted: str, flipped_indices: List[int]) -> str:
    """Produce a terminal pointer string showing exactly where errors occurred."""
    markers = [" "] * len(corrupted)
    for idx in flipped_indices:
        if 0 <= idx < len(markers):
            markers[idx] = "^"
    return "".join(markers)


# ======================================================================
# 1. SIMULATE DATA TRANSMISSION
# ======================================================================

def run_simulate_transmission() -> None:
    """Option 1: Simulate data transmission pipeline."""
    print("\n" + "=" * 72)
    print(" 1. SIMULATE DATA TRANSMISSION")
    print("=" * 72)

    # 1. Input Data
    data = get_user_data_input()

    # 2. Detection Technique
    print("\n--- SELECT DETECTION TECHNIQUE ---")
    print("  [1] VRC / Parity (Vertical Redundancy Check)")
    print("  [2] LRC          (Longitudinal Redundancy Check)")
    print("  [3] Checksum     (Internet Checksum - 8-bit)")
    print("  [4] CRC          (Cyclic Redundancy Check - CRC-8)")

    tech_choice = input("\nSelect technique [1-4] (default 4): ").strip()
    tech_map = {
        "1": "VRC / Parity",
        "2": "LRC",
        "3": "Checksum",
        "4": "CRC"
    }
    technique = tech_map.get(tech_choice, "CRC")

    # 3. Error Model (Exactly 5 models)
    print("\n--- SELECT ERROR GENERATION MODEL ---")
    print("  [1] Clean transmission       (Zero error introduced)")
    print("  [2] Single-bit error         (Random isolated bit flip)")
    print("  [3] Multiple-bit error       (Specify number of bit flips)")
    print("  [4] Burst error              (Contiguous span of noise)")
    print("  [5] Manual error injection   (Select exact bit positions to flip)")

    err_choice = input("\nSelect error model [1-5] (default 2): ").strip()
    err_type = "single"
    err_amount: any = 1

    if err_choice == "1":
        err_type = "clean"
        err_amount = 0
    elif err_choice == "3":
        err_type = "multiple"
        val = input("Enter number of bit errors to inject (default 2): ").strip()
        err_amount = int(val) if val.isdigit() else 2
    elif err_choice == "4":
        err_type = "burst"
        val = input("Enter burst length in bits (default 4): ").strip()
        err_amount = int(val) if val.isdigit() else 4
    elif err_choice == "5":
        err_type = "manual"
        val = input("Enter 0-based bit positions to flip separated by commas (e.g. 2, 5): ").strip()
        err_amount = [int(p.strip()) for p in val.split(",") if p.strip().isdigit()]
        if not err_amount:
            err_amount = [2]
    else:
        err_type = "single"
        err_amount = 1

    # Execute simulation
    sim = simulate(
        data=data,
        technique=technique,
        error_type=err_type,
        error_amount=err_amount
    )

    # Display Sender -> Channel -> Receiver Pipeline
    print("\n" + "=" * 72)
    print("                 END-TO-END TRANSMISSION REPORT")
    print("=" * 72)

    print("\n[STAGE 1: SENDER / TRANSMITTER]")
    print(f"  Input Payload    : {sim['original_data']} ({sim['payload_length']} bits)")
    print(f"  Technique Applied: {sim['technique']}")
    print(f"  Protected Frame  : {sim['protected_frame']} ({len(sim['protected_frame'])} bits)")
    print(f"  Redundancy Added : {sim['overhead_bits']} bit(s)")
    print(f"  Channel Overhead : {sim['overhead_percentage']:.2f}%")
    print(f"  Encoding Latency : {sim['encoding_time'] * 1e6:.2f} us")

    print("\n[STAGE 2: CHANNEL (ERROR INJECTION)]")
    print(f"  Error Model Used : {sim['error_type'].upper()}")
    print(f"  Errors Injected  : {sim['errors_injected']} bit(s)")
    print(f"  Error Positions  : {sim['flipped_indices']}")
    print(f"  Protected Frame  : {sim['protected_frame']}")
    print(f"  Corrupted Frame  : {sim['corrupted_frame']}")
    pointer_str = highlight_corrupted_bits(sim['protected_frame'], sim['corrupted_frame'], sim['flipped_indices'])
    print(f"  Error Locations  : {pointer_str}")

    print("\n[STAGE 3: RECEIVER & VERIFICATION]")
    print(f"  Received Frame   : {sim['corrupted_frame']}")
    print(f"  Checking Latency : {sim['checking_time'] * 1e6:.2f} us")
    print(f"  Total Proc. Time : {sim['processing_time'] * 1e6:.2f} us")

    # Diagnostic details
    if "CRC" in sim["technique"]:
        rem = sim["diagnostics"].get("syndrome_remainder", "")
        print(f"  CRC Remainder    : R = '{rem}' (Expected: {'0' * len(rem)})")
    elif "Checksum" in sim["technique"]:
        sum_hex = sim["diagnostics"].get("final_sum_hex", "")
        exp_hex = sim["diagnostics"].get("expected_sum_hex", "")
        print(f"  Checksum Sum     : {sum_hex} (Expected: {exp_hex})")
    elif "LRC" in sim["technique"]:
        rec = sim["diagnostics"].get("received_lrc", "")
        exp = sim["diagnostics"].get("expected_lrc", "")
        fc = sim["diagnostics"].get("failed_columns", [])
        print(f"  Received LRC     : {rec}")
        print(f"  Computed LRC     : {exp}")
        print(f"  Failed Column(s) : {fc}")
    elif "VRC" in sim["technique"]:
        rec = sim["diagnostics"].get("received_parity", "")
        exp = sim["diagnostics"].get("expected_parity", "")
        print(f"  Received Parity  : {rec}")
        print(f"  Computed Parity  : {exp}")

    print("\n[STAGE 4: FINAL DETECTION RESULT]")
    if sim["errors_injected"] == 0:
        print("  Verdict: [CLEAN TRANSMISSION - FRAME ACCEPTED]")
    elif sim["error_detected"]:
        print("  Verdict: [ERROR DETECTED - FRAME REJECTED]")
    else:
        print("  Verdict: [ERROR MISSED - UNDETECTED CORRUPTION]")

    print(f"\n  DCN Explanation  : {sim['explanation']}")
    print("=" * 72)


# ======================================================================
# 2. COMPARE ERROR DETECTION TECHNIQUES
# ======================================================================

def run_compare_techniques() -> None:
    """Option 2: Compare all four techniques on same input and equivalent errors."""
    print("\n" + "=" * 72)
    print(" 2. COMPARE ERROR DETECTION TECHNIQUES")
    print("=" * 72)

    data = get_user_data_input()

    print("\n--- SELECT ERROR SCENARIO TO TEST ON ALL FOUR TECHNIQUES ---")
    print("  [1] Clean transmission")
    print("  [2] Single-bit error       (1 bit flip)")
    print("  [3] Two-bit error          (2 bit flips -> Classic Parity Failure Test)")
    print("  [4] Four-bit error         (4 bit flips)")
    print("  [5] Burst error            (span of 6 bits)")
    print("  [6] Manual error injection (select bit positions to flip)")

    choice = input("\nSelect scenario [1-6] (default 3): ").strip()
    if choice == "1":
        err_type, err_amount = "clean", 0
    elif choice == "2":
        err_type, err_amount = "single", 1
    elif choice == "4":
        err_type, err_amount = "multiple", 4
    elif choice == "5":
        err_type, err_amount = "burst", 6
    elif choice == "6":
        val = input("Enter comma-separated bit positions to flip: ").strip()
        pos = [int(p) for p in val.split(",") if p.strip().isdigit()]
        err_type, err_amount = "manual", pos if pos else [1, 3]
    else:
        err_type, err_amount = "multiple", 2

    # Run all 4 techniques on the exact same input & equivalent error pattern
    results = compare_all_techniques(data, error_type=err_type, error_amount=err_amount)

    print("\n" + "=" * 80)
    print(f" COMPARATIVE EVALUATION MATRIX ({len(data)}-bit Input)")
    print(f" Scenario: {err_type.upper()} error (magnitude: {err_amount})")
    print("=" * 80)

    header = f"{'Technique':<16} | {'Overhead':<14} | {'Proc. Time':<12} | {'Detection Result':<18} | {'Verdict'}"
    print(header)
    print("-" * 80)

    for r in results:
        tech = r["technique"]
        ovh = f"{r['overhead_bits']}b ({r['overhead_percentage']:.1f}%)"
        time_us = f"{r['processing_time'] * 1e6:.2f} us"
        if r["errors_injected"] == 0:
            det_str = "CLEAN [VALID]"
            verdict = "Accepted"
        elif r["error_detected"]:
            det_str = "YES [DETECTED]"
            verdict = "Rejected"
        else:
            det_str = "NO  [MISSED!]"
            verdict = "Undetected Error"

        print(f"{tech:<16} | {ovh:<14} | {time_us:<12} | {det_str:<18} | {verdict}")

    print("=" * 80)
    print("\nKEY OBSERVATIONS:")
    print(" - VRC / Parity fails whenever an even number of bits flip (d_min = 2).")
    print(" - LRC catches errors across different columns but fails on same-column pairs.")
    print(" - Checksum detects most errors with low CPU latency but is vulnerable to compensating flips.")
    print(" - CRC provides mathematically guaranteed detection for burst errors <= degree.\n")


# ======================================================================
# 3. VIEW ALGORITHM WORKING
# ======================================================================

def run_view_algorithm_working() -> None:
    """Option 3: Show step-by-step VRC, LRC, Checksum, and CRC calculations."""
    print("\n" + "=" * 72)
    print(" 3. VIEW ALGORITHM WORKING")
    print("=" * 72)

    print("  [1] VRC / Parity Step-by-Step Working")
    print("  [2] LRC          Step-by-Step Working")
    print("  [3] Checksum     Step-by-Step Working")
    print("  [4] CRC          Step-by-Step Working (Modulo-2 Division)")
    print("  [5] View All Four Algorithms")

    c = input("\nSelect algorithm to view [1-5] (default 5): ").strip()
    data = input("Enter binary string to calculate (default: 1101001100101101): ").strip()
    if not data or not all(b in "01" for b in data):
        data = "1101001100101101"

    print(f"\nUsing Input Data ({len(data)} bits): {data}\n")

    if c == "1" or c == "5":
        print(format_vrc_working(data, mode="even"))
        print()

    if c == "2" or c == "5":
        _, lrc_info = calculate_lrc(data, block_size=8)
        print(format_lrc_working(lrc_info))
        print()

    if c == "3" or c == "5":
        print(format_checksum_working(data, word_size=8))
        print()

    if c == "4" or c == "5":
        print(format_crc_working(data, generator="100000111"))
        print()


# ======================================================================
# 4. RUN EXPERIMENTS AND VIEW GRAPHS
# ======================================================================

def run_experiments_and_graphs() -> None:
    """Option 4: Configure experiments, generate datasets, and create 4 graphs."""
    print("\n" + "=" * 72)
    print(" 4. RUN EXPERIMENTS AND VIEW GRAPHS")
    print("=" * 72)

    print("Configure Experiment Parameters:")

    # Trial count
    trials_in = input("  Trials per configuration [default: 50]: ").strip()
    trials = int(trials_in) if trials_in.isdigit() and int(trials_in) > 0 else 50

    # Data sizes
    sizes_in = input("  Data sizes in bits comma-separated [default: 32, 64, 128, 256, 512, 1024]: ").strip()
    if sizes_in:
        sizes = [int(s.strip()) for s in sizes_in.split(",") if s.strip().isdigit()]
    else:
        sizes = [32, 64, 128, 256, 512, 1024]
    if not sizes:
        sizes = [32, 64, 128, 256, 512, 1024]

    # Error magnitudes for multiple-bit errors
    mag_in = input("  Multiple-bit error magnitudes comma-separated [default: 1, 2, 3, 4, 5, 6, 7, 8]: ").strip()
    if mag_in:
        mags = [int(m.strip()) for m in mag_in.split(",") if m.strip().isdigit()]
    else:
        mags = [1, 2, 3, 4, 5, 6, 7, 8]
    if not mags:
        mags = [1, 2, 3, 4, 5, 6, 7, 8]

    # Burst lengths
    burst_in = input("  Burst lengths in bits comma-separated [default: 2, 4, 6, 8, 12, 16]: ").strip()
    if burst_in:
        bursts = [int(b.strip()) for b in burst_in.split(",") if b.strip().isdigit()]
    else:
        bursts = [2, 4, 6, 8, 12, 16]
    if not bursts:
        bursts = [2, 4, 6, 8, 12, 16]

    print("\nExecuting experiment suite...")
    run_all_experiments(
        data_sizes=sizes,
        multi_error_amounts=mags,
        burst_lengths=bursts,
        trials=trials,
        verbose=True
    )

    print("Aggregating metrics (keeping clean transmissions separate from corrupted trials)...")
    compute_and_save_metrics(verbose=True)

    print("Generating the four required analytical graphs...")
    charts = generate_all_plots()

    open_q = input("\nPreview generated graphs in windows? [y/N]: ").strip().lower()
    if open_q == "y":
        import matplotlib.pyplot as plt
        for chart_path in charts:
            if os.path.exists(chart_path):
                img = plt.imread(chart_path)
                plt.figure(figsize=(10, 6))
                plt.imshow(img)
                plt.axis("off")
                plt.title(f"{os.path.basename(chart_path)} (Close window to see next)")
                plt.show()


# ======================================================================
# MAIN INTERACTIVE LOOP
# ======================================================================

def main_menu() -> None:
    """Main interactive driver with exactly the 5 required menu options."""
    while True:
        print_banner()
        print("  1. Simulate Data Transmission")
        print("  2. Compare Error Detection Techniques")
        print("  3. View Algorithm Working")
        print("  4. Run Experiments and View Graphs")
        print("  5. Exit")
        print("=" * 72)

        choice = input("\nEnter your choice [1-5]: ").strip()

        if choice == "1":
            run_simulate_transmission()
        elif choice == "2":
            run_compare_techniques()
        elif choice == "3":
            run_view_algorithm_working()
        elif choice == "4":
            run_experiments_and_graphs()
        elif choice == "5":
            print("\nExiting DCN Error Detection System. Thank you!\n")
            break
        else:
            print(" [!] Invalid option. Please enter a number between 1 and 5.")

        input("\nPress Enter to return to main menu...")
        clear_screen()


if __name__ == "__main__":
    try:
        main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram terminated.")