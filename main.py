"""Data Communications and Networking (DCN) Course Project.

Topic: Error Generation, Detection, and Comparative Performance Analysis
Author: Purva
Course: Data Communication and Computer Networks (DCN)

Interactive Console Interface for jury presentation, live demonstration,
and empirical analysis.
"""

import sys
import os
import time
from typing import List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.parity import add_parity, check_parity
from algorithms.two_dim_parity import encode_2d_parity, check_2d_parity, format_2d_matrix_display
from algorithms.checksum import add_checksum, verify_checksum_detailed
from algorithms.crc import crc_encode, crc_check_detailed, modulo2_divide, CRC_POLYNOMIALS
from algorithms.hamming import hamming_encode, hamming_check
from simulation.simulator import simulate, compare_all_techniques
from simulation.error_generator import (
    single_bit_error,
    multiple_bit_error,
    burst_error,
    manual_error,
    ber_channel_error
)
from visualization.plot_results import generate_all_plots
from experiments.experiment_runner import run_all_experiments
from experiments.metrics import compute_and_save_metrics


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


def binary_to_text(binary: str) -> str:
    """Convert an 8-bit aligned binary string back to ASCII text."""
    chars = []
    for i in range(0, len(binary) - (len(binary) % 8), 8):
        byte_chunk = binary[i:i + 8]
        chars.append(chr(int(byte_chunk, 2)))
    return "".join(chars)


def get_user_data_input() -> str:
    """Prompt user to supply data via binary, text, or random generation."""
    print("\n--- DATA INPUT SELECTION ---")
    print("  [1] Enter Custom Binary String (e.g. 110100110011)")
    print("  [2] Enter Plain Text String    (auto-converted to binary ASCII)")
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
        # Custom binary
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
# MENU OPTION 1: INTERACTIVE SINGLE TRANSMISSION WALKTHROUGH
# ======================================================================

def run_interactive_walkthrough() -> None:
    """Execute step-by-step interactive simulation."""
    data = get_user_data_input()

    print("\n--- ERROR DETECTION TECHNIQUE ---")
    print("  [1] Even Parity (1D VRC - Vertical Redundancy Check)")
    print("  [2] Odd Parity  (1D VRC)")
    print("  [3] Two-Dimensional (2D) Parity Matrix (LRC + VRC)")
    print("  [4] Internet Checksum (8-bit RFC 1071)")
    print("  [5] Internet Checksum (16-bit RFC 1071)")
    print("  [6] CRC-8 (ATM polynomial: x^8 + x^2 + x + 1)")
    print("  [7] CRC-16-CCITT (HDLC / Bluetooth: x^16 + x^12 + x^5 + 1)")
    print("  [8] CRC-32 (IEEE 802.3 Ethernet standard)")
    print("  [9] Custom CRC Generator Polynomial")
    print("  [10] Hamming Code (7,4) (Forward Error Detection & Correction)")

    tech_choice = input("\nSelect technique [1-10] (default 6): ").strip()
    tech_map = {
        "1": "Parity-Even",
        "2": "Parity-Odd",
        "3": "2D-Parity",
        "4": "Checksum-8",
        "5": "Checksum-16",
        "6": "CRC-8",
        "7": "CRC-16-CCITT",
        "8": "CRC-32",
        "9": "CRC",
        "10": "Hamming"
    }
    technique = tech_map.get(tech_choice, "CRC-8")

    custom_crc = "100000111"
    if technique == "CRC":
        custom_crc = input("Enter binary generator polynomial (e.g. 1101 or 100000111): ").strip()
        if not custom_crc or not all(c in "01" for c in custom_crc):
            custom_crc = "100000111"

    print("\n--- ERROR GENERATION MODEL ---")
    print("  [1] Clean Transmission (No error introduced)")
    print("  [2] Single-Bit Error (Random bit flip)")
    print("  [3] Multiple-Bit Error (Specify bit count k)")
    print("  [4] Burst Error (Contiguous span of noise)")
    print("  [5] Manual Error Injection (Pick exact bit indices to flip - Jury Demo)")
    print("  [6] Channel Noise (Bit Error Rate probability)")

    err_choice = input("\nSelect error model [1-6] (default 3): ").strip()

    err_type = "multiple"
    err_amount: any = 2

    if err_choice == "1":
        err_type = "none"
        err_amount = 0
    elif err_choice == "2":
        err_type = "single"
        err_amount = 1
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
        val = input("Enter 0-based bit indices separated by commas (e.g. 2, 5): ").strip()
        err_amount = [int(p.strip()) for p in val.split(",") if p.strip().isdigit()]
        if not err_amount:
            err_amount = [2, 4]
    elif err_choice == "6":
        err_type = "ber"
        val = input("Enter Bit Error Rate probability (e.g. 0.05): ").strip()
        try:
            err_amount = float(val)
        except ValueError:
            err_amount = 0.05

    # Run simulation
    sim = simulate(
        data=data,
        technique=technique,
        error_type=err_type,
        error_amount=err_amount,
        crc_generator=custom_crc
    )

    # Display results cleanly
    print("\n" + "=" * 72)
    print("                 END-TO-END TRANSMISSION REPORT")
    print("=" * 72)

    print("\n[STAGE 1: TRANSMITTER / SENDER]")
    print(f"  Payload Data     : {sim['original_data']} ({sim['payload_length']} bits)")
    print(f"  Technique Used   : {sim['technique']}")
    print(f"  Protected Frame  : {sim['protected_frame']} ({len(sim['protected_frame'])} bits)")
    print(f"  Redundancy Added : {sim['overhead_bits']} bit(s)")
    print(f"  Channel Overhead : {sim['overhead_percentage']:.2f}%")
    print(f"  Encoding Latency : {sim['encoding_time'] * 1e6:.2f} us")

    print("\n[STAGE 2: PHYSICAL CHANNEL IMPAIRMENTS]")
    print(f"  Error Model      : {sim['error_type'].upper()}")
    print(f"  Injected Errors  : {sim['errors_injected']} bit(s)")
    print(f"  Corrupted Indices: {sim['flipped_indices']}")
    print(f"  Original Frame   : {sim['protected_frame']}")
    print(f"  Corrupted Frame  : {sim['corrupted_frame']}")
    pointer_str = highlight_corrupted_bits(sim['protected_frame'], sim['corrupted_frame'], sim['flipped_indices'])
    print(f"  Error Location   : {pointer_str}")

    print("\n[STAGE 3: RECEIVER VERIFICATION & DIAGNOSTICS]")
    print(f"  Verification Time: {sim['checking_time'] * 1e6:.2f} us")
    print(f"  Total Latency    : {sim['processing_time'] * 1e6:.2f} us")

    # Diagnostic details
    if "CRC" in sim["technique"]:
        rem = sim["diagnostics"].get("syndrome_remainder", "")
        print(f"  CRC Remainder    : R = '{rem}' (Expected: {'0' * len(rem)})")
    elif "Checksum" in sim["technique"]:
        sum_hex = sim["diagnostics"].get("final_sum_hex", "")
        exp_hex = sim["diagnostics"].get("expected_sum_hex", "")
        print(f"  Checksum Sum     : {sum_hex} (Expected: {exp_hex})")
    elif "2D" in sim["technique"]:
        fr = sim["diagnostics"].get("failed_rows", [])
        fc = sim["diagnostics"].get("failed_cols", [])
        print(f"  Failed Rows      : {fr}")
        print(f"  Failed Columns   : {fc}")

    print("\n[STAGE 4: VERDICT & DCN THEORETICAL ANALYSIS]")
    if sim["errors_injected"] == 0:
        print("  Status: [CLEAN FRAME - ACCEPTED (ACK)]")
    elif sim["error_detected"]:
        print("  Status: [ERROR DETECTED - FRAME REJECTED (NAK)]")
    else:
        print("  Status: [ERROR MISSED - UNDETECTED TRANSMISSION CORRUPTION!]")

    print(f"\n  DCN Explanation  : {sim['explanation']}")
    print("=" * 72)


# ======================================================================
# MENU OPTION 2: MULTI-TECHNIQUE COMPARISON SIDE-BY-SIDE
# ======================================================================

def run_multi_technique_comparison() -> None:
    """Run all primary error detection techniques against the same scenario."""
    print("\n--- MULTI-TECHNIQUE COMPARATIVE DEMONSTRATION ---")
    data = get_user_data_input()

    print("\nSelect Error Injection Scenario:")
    print("  [1] Single-Bit Error       (k = 1)")
    print("  [2] Two-Bit Error          (k = 2  -> Critical Test for Parity!)")
    print("  [3] Four-Bit Error         (k = 4)")
    print("  [4] Burst Error            (span = 6 bits)")
    print("  [5] Custom Manual Flip     (user-specified indices)")

    choice = input("\nSelect scenario [1-5] (default 2): ").strip()
    if choice == "1":
        err_type, err_amount = "single", 1
    elif choice == "3":
        err_type, err_amount = "multiple", 4
    elif choice == "4":
        err_type, err_amount = "burst", 6
    elif choice == "5":
        val = input("Enter comma-separated bit indices to flip: ").strip()
        pos = [int(p) for p in val.split(",") if p.strip().isdigit()]
        err_type, err_amount = "manual", pos if pos else [1, 3]
    else:
        err_type, err_amount = "multiple", 2

    results = compare_all_techniques(data, error_type=err_type, error_amount=err_amount)

    print("\n" + "=" * 78)
    print(f" COMPARATIVE EVALUATION MATRIX ON {len(data)}-BIT PAYLOAD")
    print(f" Scenario: {err_type.upper()} error (magnitude: {err_amount})")
    print("=" * 78)

    header = f"{'Technique':<20} | {'Overhead':<10} | {'Error Detected?':<16} | {'Verdict'}"
    print(header)
    print("-" * 78)

    for r in results:
        tech = r["technique"]
        ovh = f"{r['overhead_bits']}b ({r['overhead_percentage']:.1f}%)"
        detected_str = "YES [DETECTED]" if r["error_detected"] else "NO  [MISSED!]"
        verdict = "Rejected (NAK)" if r["error_detected"] else "UNDETECTED ERROR"

        print(f"{tech:<20} | {ovh:<10} | {detected_str:<16} | {verdict}")

    print("=" * 78)
    print("\nKEY OBSERVATIONS FOR JURY:")
    print(" 1. Single Parity Check fails whenever an EVEN number of bits flip (d_min = 2).")
    print(" 2. 2D Parity Matrix successfully detects all 1, 2, and 3-bit errors (d_min = 4).")
    print(" 3. Checksum provides good protection but can be fooled by compensating errors.")
    print(" 4. CRC provides mathematically guaranteed detection for burst lengths <= degree.\n")


# ======================================================================
# MENU OPTION 3: CRC DIVISION STEP-BY-STEP TRACE
# ======================================================================

def run_crc_trace() -> None:
    """Display educational modulo-2 division breakdown."""
    print("\n--- CRC MODULO-2 DIVISION BREAKDOWN ---")
    data = input("Enter binary data (default: 110101): ").strip()
    if not data or not all(c in "01" for c in data):
        data = "110101"

    print("\nSelect Generator Polynomial:")
    print("  [1] CRC-8 (ATM): 100000111")
    print("  [2] CRC-4 (ITU): 10011")
    print("  [3] Custom Generator")

    c = input("Choice [1-3] (default 2 for clean trace): ").strip()
    if c == "1":
        gen = "100000111"
    elif c == "3":
        gen = input("Enter generator: ").strip()
        if not gen or not all(b in "01" for b in gen):
            gen = "10011"
    else:
        gen = "10011"

    degree = len(gen) - 1
    padded = data + ("0" * degree)
    quotient, remainder, steps = modulo2_divide(padded, gen, track_steps=True)

    print("\n" + "=" * 60)
    print(" CRC MODULO-2 (XOR) DIVISION TRACE")
    print("=" * 60)
    print(f" Data Payload        : {data}")
    print(f" Generator Polynomial: {gen} (Degree = {degree})")
    print(f" Zero-Padded Dividend: {padded}")
    print("-" * 60)

    for s in steps[:10]:  # Limit first 10 steps for clarity
        q = s["quotient_bit"]
        print(f" Step {s['index']+1:<2}: Dividend chunk = {s['before_xor']} | XOR with {s['generator']} -> {s['after_xor']}")

    if len(steps) > 10:
        print(f" ... ({len(steps) - 10} additional division steps completed)")

    print("-" * 60)
    print(f" Quotient Bits       : {quotient}")
    print(f" Calculated Remainder: {remainder} (FCS / CRC Checksum)")
    print(f" Transmitted Frame   : {data + remainder}")
    print("=" * 60 + "\n")


# ======================================================================
# MENU OPTION 4: 2D PARITY MATRIX VISUALIZER
# ======================================================================

def run_2d_parity_visualizer() -> None:
    """Display 2D parity matrix in visual table format."""
    print("\n--- 2D PARITY MATRIX (LRC + VRC) VISUALIZER ---")
    data = input("Enter binary string (default 16 bits): ").strip()
    if not data or not all(c in "01" for c in data):
        data = "1100101011110000"

    print(f"\nEncoding payload ({len(data)} bits) into 8-bit rows...")
    frame, enc_info = encode_2d_parity(data, col_size=8)

    print("\n[TRANSMITTED 2D MATRIX]")
    print(format_2d_matrix_display(enc_info))

    inject = input("\nInject a single-bit error to test matrix localization? [Y/n]: ").strip().lower()
    if inject != "n":
        pos_str = input(f"Enter bit index to flip [0 to {len(frame)-1}] (default 3): ").strip()
        flip_pos = int(pos_str) if pos_str.isdigit() and int(pos_str) < len(frame) else 3
        corrupted = list(frame)
        corrupted[flip_pos] = "1" if corrupted[flip_pos] == "0" else "0"
        corrupted_frame = "".join(corrupted)

        is_valid, chk_info = check_2d_parity(corrupted_frame, col_size=8)
        print("\n[RECEIVED CORRUPTED 2D MATRIX]")
        print(format_2d_matrix_display(chk_info))

        print("\nDIAGNOSIS:")
        print(f"  Integrity Status : {'VALID' if is_valid else 'ERROR DETECTED!'}")
        print(f"  Flipped Bit Index: {flip_pos}")
        print(f"  Failed Row(s)    : {chk_info['failed_rows']}")
        print(f"  Failed Column(s) : {chk_info['failed_cols']}")
        if chk_info.get("single_error_coord"):
            r, c = chk_info["single_error_coord"]
            print(f"  -> Error localized at Matrix Coordinates: Row {r}, Column {c}!")
            print("  -> 2D Parity can correct this error by inverting the bit at (Row, Col)!")


# ======================================================================
# MENU OPTION 5: GENERATE ESSENTIAL VISUALIZATIONS
# ======================================================================

def run_visualization_suite() -> None:
    """Generate the 4 essential DCN charts plus Master Dashboard."""
    print("\nGenerating focused DCN analytical visualizations...")
    files = generate_all_plots()

    open_dash = input("\nOpen Master Dashboard image in window? [y/N]: ").strip().lower()
    if open_dash == "y":
        import matplotlib.pyplot as plt
        dash_path = os.path.join(PROJECT_ROOT, "visualization", "dcn_performance_dashboard.png")
        if os.path.exists(dash_path):
            img = plt.imread(dash_path)
            plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.axis("off")
            plt.title("DCN Analysis Dashboard (Close window to return)")
            plt.show()


# ======================================================================
# MENU OPTION 6: RUN STATISTICAL BENCHMARK EXPERIMENTS
# ======================================================================

def run_benchmark_experiments() -> None:
    """Run Monte Carlo simulation trials and update CSV metrics."""
    print("\n--- STATISTICAL BENCHMARK CONFIGURATION ---")
    print("  [1] Fast Demo Mode (50 trials/config  ~ 1 second)  [Recommended for Live Presentation]")
    print("  [2] Full Batch Mode (500 trials/config ~ 6 seconds)")

    c = input("\nSelect mode [1-2] (default 1): ").strip()
    trials = 500 if c == "2" else 50

    run_all_experiments(trials=trials, verbose=True)
    compute_and_save_metrics(verbose=True)
    print("Regenerating analytical charts from new metrics...")
    generate_all_plots()
    print("All benchmark datasets and figures updated successfully!\n")


# ======================================================================
# MENU OPTION 7: DCN THEORETICAL QUICK REFERENCE & VIVA GUIDE
# ======================================================================

def show_theory_guide() -> None:
    """Display comprehensive DCN theoretical reference guide."""
    print("\n" + "=" * 72)
    print("     DCN ERROR DETECTION THEORY & JURY Q&A REFERENCE GUIDE")
    print("=" * 72)

    print("""
1. VERTICAL REDUNDANCY CHECK (VRC / 1D PARITY):
   - Redundancy  : 1 bit per data unit.
   - Hamming Dist: d_min = 2.
   - Capability  : Detects all single-bit and odd numbers of errors.
   - Limitation  : Fails 100% on any even number of bit errors (2, 4, 6...).

2. TWO-DIMENSIONAL PARITY (2D LRC + VRC):
   - Redundancy  : R + C + 1 bits (matrix boundary).
   - Hamming Dist: d_min = 4.
   - Capability  : Detects all 1, 2, and 3-bit errors.
   - Localization: Locates single-bit error by row/column intersection -> FEC!

3. INTERNET CHECKSUM (RFC 1071):
   - Arithmetic  : 1's complement addition with end-around carry.
   - Standard    : TCP, UDP, IPv4 headers.
   - Capability  : Detects all odd-bit errors, high burst detection.
   - Limitation  : Vulnerable to compensating errors (e.g. transposition).

4. CYCLIC REDUNDANCY CHECK (CRC):
   - Mathematical: Modulo-2 polynomial division over GF(2).
   - Capability  : Detects 100% burst errors of length <= generator degree r.
                   Detects 1 - (1/2)^(r-1) of bursts of length r + 1.
                   Detects 1 - (1/2)^r of bursts of length > r + 1.
   - Industry Use: IEEE 802.3 Ethernet (CRC-32), Bluetooth (CRC-16), ATM (CRC-8).
""")
    print("=" * 72)
    input("Press Enter to return to main menu...")


# ======================================================================
# MAIN INTERACTIVE LOOP
# ======================================================================

def main_menu() -> None:
    """Main interactive driver."""
    while True:
        print_banner()
        print("  [1] Interactive Transmission Walkthrough (Sender -> Channel -> Receiver)")
        print("  [2] Multi-Technique Comparison on Same Input (Side-by-Side Live Demo)")
        print("  [3] Step-by-Step CRC Modulo-2 Division Trace")
        print("  [4] 2D Parity Matrix Grid Visualizer (Row + Column Check)")
        print("  [5] Generate Essential Analytical Visualizations & Dashboard")
        print("  [6] Run Statistical Benchmark Suite (Regenerate CSV Datasets)")
        print("  [7] DCN Theoretical Quick Reference & Jury Viva Guide")
        print("  [8] Exit")
        print("=" * 72)

        choice = input("\nEnter your choice [1-8]: ").strip()

        if choice == "1":
            run_interactive_walkthrough()
        elif choice == "2":
            run_multi_technique_comparison()
        elif choice == "3":
            run_crc_trace()
        elif choice == "4":
            run_2d_parity_visualizer()
        elif choice == "5":
            run_visualization_suite()
        elif choice == "6":
            run_benchmark_experiments()
        elif choice == "7":
            show_theory_guide()
        elif choice == "8":
            print("\nThank you for using the DCN Error Detection System. Good luck with the jury!\n")
            break
        else:
            print(" [!] Invalid option. Please enter a number between 1 and 8.")

        input("\nPress Enter to continue...")
        clear_screen()


if __name__ == "__main__":
    try:
        main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram terminated.")