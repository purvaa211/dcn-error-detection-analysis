"""Data Communication and Computer Networks (DCN) Project.

Error Generation, Detection, and Comparative Performance Analysis System.
Author: Purva
Subject: Data Communication and Computer Networks (DCN)

Interactive Console Interface.
"""

import sys
import os
import random
import shutil
import tempfile
from typing import List, Dict, Any, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.parity import add_vrc, check_vrc, format_vrc_working
from algorithms.lrc import add_lrc, check_lrc, calculate_lrc, format_lrc_working
from algorithms.checksum import add_checksum, verify_checksum_detailed, format_checksum_working
from algorithms.crc import crc_encode, crc_check_detailed, format_crc_working, CRC_POLYNOMIALS
from algorithms.hamming import format_hamming_working
from core.traffic_analysis import (
    parse_pcap_file,
    extract_packet_payload_details,
    evaluate_traffic_error_detection,
    compare_all_traffic_techniques,
    generate_sample_pcap
)
from simulation.simulator import simulate, compare_all_techniques
from simulation.error_generator import (
    clean_transmission,
    single_bit_error,
    multiple_bit_error,
    burst_error,
    consecutive_burst_error,
    multiple_burst_error,
    manual_error
)
from experiments.experiment_runner import run_all_experiments
from experiments.metrics import compute_and_save_metrics
from visualization.plot_results import generate_all_plots


# ======================================================================
# SESSION STATE MANAGEMENT
# ======================================================================

SESSION_DATA: str = "1011011011001100"


def clear_screen() -> None:
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Display project header banner with current session data."""
    print("=" * 72)
    print("     DATA COMMUNICATION AND COMPUTER NETWORKS (DCN) PROJECT")
    print("      ERROR GENERATION, DETECTION & ANALYSIS SYSTEM")
    print("=" * 72)
    print(f"  Current Session Data : {SESSION_DATA} ({len(SESSION_DATA)} bits)")
    print("=" * 72)


def text_to_binary(text: str) -> str:
    """Convert an ASCII text string to an 8-bit binary representation."""
    return "".join(format(ord(c), "08b") for c in text)


def parse_user_data(user_input: str, default: str = "1011011011001100") -> str:
    """Parse raw user input into a validated binary string."""
    cleaned = user_input.strip()
    if not cleaned:
        return default

    # 1. Direct binary string
    if all(c in "01" for c in cleaned):
        return cleaned

    # 2. Random generation request ('r' or 'random')
    if cleaned.lower() in ("r", "random"):
        return "".join(random.choice("01") for _ in range(16))

    # 3. Plain text string -> convert to 8-bit ASCII binary
    bin_str = text_to_binary(cleaned)
    print(f"  -> Converted ASCII '{cleaned}' to {len(bin_str)}-bit binary.")
    return bin_str


def setup_initial_data() -> None:
    """Prompt user once at startup to set or generate session data."""
    global SESSION_DATA
    print("\n--- INITIAL DATA SETUP ---")
    print("Enter binary string, plain text, 'r' for random 16 bits,")
    print("or press Enter to use default [1011011011001100]:")
    raw = input("Input > ").strip()
    SESSION_DATA = parse_user_data(raw, default="1011011011001100")
    print(f"Active Session Data: {SESSION_DATA} ({len(SESSION_DATA)} bits)\n")


def prompt_change_session_data() -> None:
    """Explicitly change the session data when the user requests it."""
    global SESSION_DATA
    print(f"\nCurrent Session Data: {SESSION_DATA} ({len(SESSION_DATA)} bits)")
    raw = input("Enter new binary, text, or 'r' for random [Enter to keep]: ").strip()
    if raw:
        SESSION_DATA = parse_user_data(raw, default=SESSION_DATA)
        print(f"Session data updated: {SESSION_DATA} ({len(SESSION_DATA)} bits)")
    else:
        print("Session data unchanged.")


def check_and_offer_data_change(current: str) -> str:
    """Offer a fast prompt to change session data or press Enter to keep."""
    global SESSION_DATA
    print(f"\nCurrent Data: {current} ({len(current)} bits)")
    ans = input("Change data? [y/N]: ").strip().lower()
    if ans == "y":
        raw = input("Enter new binary, text, or 'r' for random: ").strip()
        SESSION_DATA = parse_user_data(raw, default=current)
        print(f"Updated Data: {SESSION_DATA} ({len(SESSION_DATA)} bits)")
        return SESSION_DATA
    return current


def highlight_corrupted_bits(corrupted_len: int, flipped_indices: List[int]) -> str:
    """Produce a terminal pointer string showing exactly where errors occurred."""
    markers = [" "] * corrupted_len
    for idx in flipped_indices:
        if 0 <= idx < corrupted_len:
            markers[idx] = "^"
    return "".join(markers)


# ======================================================================
# SIMPLIFIED ERROR SELECTION (EXACTLY 5 MODELS, NO PRESET SCENARIOS)
# ======================================================================

def get_error_model_selection(payload_len: int) -> Tuple[str, any, List[int]]:
    """Prompt user to select from seven physical error models and their parameters.

    Returns:
        tuple (error_type, error_amount, positions)
    """
    print("\nSelect Error Model:")
    print("  1. Clean transmission")
    print("  2. Single-bit error")
    print("  3. Multiple-bit error")
    print("  4. Burst error (textbook)")
    print("  5. Consecutive burst corruption (solid contiguous burst)")
    print("  6. Multiple burst errors (separated burst episodes)")
    print("  7. Manual error injection")

    choice = input("\nChoice [1-7] (default 1): ").strip()

    # Model 1: Clean transmission
    if choice == "1" or not choice:
        return "clean", 0, []

    # Model 2: Single-bit error
    elif choice == "2":
        pos_in = input(f"Bit position [0 to {payload_len - 1}] (Enter for random): ").strip()
        if pos_in.isdigit() and 0 <= int(pos_in) < payload_len:
            pos = int(pos_in)
        else:
            pos = random.randrange(payload_len)
            print(f"  -> Random position selected: {pos}")
        return "single", 1, [pos]

    # Model 3: Multiple-bit error
    elif choice == "3":
        num_in = input(f"Number of bits to flip [1 to {payload_len}] (default 2): ").strip()
        k = int(num_in) if num_in.isdigit() and 1 <= int(num_in) <= payload_len else 2

        pos_in = input(f"Positions [0 to {payload_len - 1}, comma-separated] (Enter for random): ").strip()
        if pos_in:
            parsed = [int(p.strip()) for p in pos_in.split(",") if p.strip().isdigit() and 0 <= int(p.strip()) < payload_len]
            parsed = sorted(list(set(parsed)))
            if parsed:
                positions = parsed
            else:
                positions = sorted(random.sample(range(payload_len), min(k, payload_len)))
        else:
            positions = sorted(random.sample(range(payload_len), min(k, payload_len)))
            print(f"  -> Random positions selected: {positions}")

        return "multiple", len(positions), positions

    # Model 4: Burst error
    elif choice == "4":
        len_in = input(f"Burst length in bits [2 to {payload_len}] (default 4): ").strip()
        burst_len = int(len_in) if len_in.isdigit() and 2 <= int(len_in) <= payload_len else min(4, payload_len)

        max_start = payload_len - burst_len
        start_in = input(f"Starting position [0 to {max_start}] (Enter for random): ").strip()
        if start_in.isdigit() and 0 <= int(start_in) <= max_start:
            start = int(start_in)
        else:
            start = random.randint(0, max_start) if max_start > 0 else 0
            print(f"  -> Random start selected: {start}")

        # Textbook burst: first & last bit inverted, intermediate bits 50% random
        end = start + burst_len - 1
        flipped = [start, end]
        for p in range(start + 1, end):
            if random.random() < 0.5:
                flipped.append(p)
        flipped = sorted(list(set(flipped)))
        return "burst", burst_len, flipped

    # Model 5: Consecutive burst corruption
    elif choice == "5":
        len_in = input(f"Consecutive burst length in bits [2 to {payload_len}] (default 4): ").strip()
        span = int(len_in) if len_in.isdigit() and 1 <= int(len_in) <= payload_len else min(4, payload_len)

        max_start = payload_len - span
        start_in = input(f"Starting position [0 to {max_start}] (Enter for random): ").strip()
        if start_in.isdigit() and 0 <= int(start_in) <= max_start:
            start = int(start_in)
        else:
            start = random.randint(0, max_start) if max_start > 0 else 0
            print(f"  -> Random start selected: {start}")

        flipped = list(range(start, start + span))
        return "consecutive_burst", span, flipped

    # Model 6: Multiple burst errors
    elif choice == "6":
        max_bursts = max(2, payload_len // 4)
        num_in = input(f"Number of separate bursts [2 to {max_bursts}] (default 2): ").strip()
        num_bursts = int(num_in) if num_in.isdigit() and 1 <= int(num_in) <= max_bursts else 2

        len_in = input("Burst length per episode in bits (default 3): ").strip()
        burst_len = int(len_in) if len_in.isdigit() and 1 <= int(len_in) <= payload_len // num_bursts else 3

        _, flipped = multiple_burst_error("0" * payload_len, num_bursts=num_bursts, burst_length=burst_len, return_indices=True)
        print(f"  -> Multiple burst positions selected: {flipped}")
        return "multiple_burst", (num_bursts, burst_len), flipped

    # Model 7: Manual error injection
    elif choice == "7":
        while True:
            pos_in = input(f"Enter bit positions to flip [0 to {payload_len - 1}, comma-separated]: ").strip()
            parsed = [int(p.strip()) for p in pos_in.split(",") if p.strip().isdigit() and 0 <= int(p.strip()) < payload_len]
            parsed = sorted(list(set(parsed)))
            if parsed:
                return "manual", parsed, parsed
            print(f"  [!] Please enter valid integers between 0 and {payload_len - 1}.")

    else:
        return "clean", 0, []


# ======================================================================
# 1. SIMULATE TRANSMISSION
# ======================================================================

def run_simulate_transmission() -> None:
    """Option 1: Simulate data transmission pipeline using session data."""
    global SESSION_DATA
    print("\n" + "=" * 72)
    print(" 1. SIMULATE TRANSMISSION")
    print("=" * 72)

    data = check_and_offer_data_change(SESSION_DATA)

    # 1. Detection Technique
    print("\nSelect Detection Technique:")
    print("  [1] VRC / Parity (Vertical Redundancy Check)")
    print("  [2] LRC          (Longitudinal Redundancy Check)")
    print("  [3] Checksum     (1's Complement - 8-bit)")
    print("  [4] CRC          (Cyclic Redundancy Check - CRC-8)")
    print("  [5] Hamming      (Hamming (7,4) Error-Correcting Code)")

    tech_choice = input("\nChoice [1-5] (default 4): ").strip()
    tech_map = {
        "1": "VRC / Parity",
        "2": "LRC",
        "3": "Checksum",
        "4": "CRC",
        "5": "Hamming (7,4)"
    }
    technique = tech_map.get(tech_choice, "CRC")

    # 2. Error Model
    err_type, err_amount, chosen_positions = get_error_model_selection(len(data))

    # Execute simulation
    sim = simulate(
        data=data,
        technique=technique,
        error_type=err_type,
        error_amount=err_amount,
        forced_indices=chosen_positions if err_type != "clean" else []
    )

    # Display Sender -> Channel -> Receiver Pipeline
    print("\n" + "=" * 72)
    print("                 TRANSMISSION REPORT")
    print("=" * 72)

    print("\n[STAGE 1: SENDER / TRANSMITTER]")
    print(f"  Input Payload    : {sim['original_data']} ({sim['payload_length']} bits)")
    print(f"  Technique Applied: {sim['technique']}")
    print(f"  Protected Frame  : {sim['protected_frame']} ({len(sim['protected_frame'])} bits)")
    print(f"  Redundancy Added : {sim['overhead_bits']} bit(s)")
    print(f"  Channel Overhead : {sim['overhead_percentage']:.2f}%")
    print(f"  Encoding Latency : {sim['encoding_time'] * 1e6:.2f} us")

    print("\n[STAGE 2: CHANNEL (ERROR INJECTION)]")
    print(f"  Error Model Used : {sim['error_type'].upper().replace('_', ' ')}")
    print(f"  Physical Cause   : {sim.get('error_cause', 'N/A')}")
    print(f"  Intro Mechanism  : {sim.get('error_introduction', 'N/A')}")
    print(f"  Errors Injected  : {sim['errors_injected']} bit(s)")
    print(f"  Error Positions  : {sim['flipped_indices']}")
    print(f"  Protected Frame  : {sim['protected_frame']}")
    print(f"  Corrupted Frame  : {sim['corrupted_frame']}")
    pointer_str = highlight_corrupted_bits(len(sim['corrupted_frame']), sim['flipped_indices'])
    print(f"  Error Locations  : {pointer_str}")

    print("\n[STAGE 3: RECEIVER & VERIFICATION]")
    print(f"  Received Frame   : {sim['corrupted_frame']}")
    print(f"  Checking Latency : {sim['checking_time'] * 1e6:.2f} us")
    print(f"  Total Proc. Time : {sim['processing_time'] * 1e6:.2f} us")

    # Diagnostics
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
    elif "Hamming" in sim["technique"]:
        syndromes = sim["diagnostics"].get("syndromes", [])
        corr_pos = sim["diagnostics"].get("corrected_positions", [])
        corr_frame = sim["diagnostics"].get("corrected_frame", "")
        dec_payload = sim["diagnostics"].get("decoded_payload", "")
        print(f"  Block Syndromes  : {syndromes}")
        print(f"  Error Positions  : {corr_pos if corr_pos else 'None (Clean)'}")
        print(f"  Corrected Frame  : {corr_frame}")
        print(f"  Decoded Payload  : {dec_payload}")

    print("\n[STAGE 4: FINAL DETECTION RESULT]")
    if "Hamming" in sim["technique"]:
        verdict = sim.get("hamming_verdict", "")
        if not verdict:
            if sim["errors_injected"] == 0:
                verdict = "[CLEAN TRANSMISSION]"
            elif sim["diagnostics"].get("successfully_corrected"):
                verdict = "[ERROR DETECTED AND CORRECTED]"
            else:
                verdict = "[ERROR DETECTED - NOT CORRECTABLE / MISCORRECTED]"
        print(f"  Verdict: {verdict}")
    elif sim["errors_injected"] == 0:
        print("  Verdict: [CLEAN TRANSMISSION - FRAME ACCEPTED]")
    elif sim["error_detected"]:
        print("  Verdict: [ERROR DETECTED - FRAME REJECTED]")
    else:
        print("  Verdict: [ERROR MISSED - UNDETECTED CORRUPTION]")

    print(f"\n  Explanation      : {sim['explanation']}")
    print("=" * 72)


# ======================================================================
# 2. COMPARE DETECTION TECHNIQUES
# ======================================================================

def run_compare_techniques() -> None:
    """Option 2: Compare all four techniques on same input and equivalent errors."""
    global SESSION_DATA
    print("\n" + "=" * 72)
    print(" 2. COMPARE DETECTION TECHNIQUES")
    print("=" * 72)

    data = check_and_offer_data_change(SESSION_DATA)

    # Prompt error model only once (no preset scenario choices)
    err_type, err_amount, chosen_positions = get_error_model_selection(len(data))

    if err_type != "clean":
        print(f"\n  Error injection mapping: Corrupting payload bit positions {chosen_positions}")
        print("  Identical payload corruption is applied across VRC, LRC, Checksum, and CRC.")

    # Run all 4 techniques with exact same payload corruption
    results = compare_all_techniques(
        data=data,
        error_type=err_type,
        error_amount=chosen_positions if err_type != "clean" else 0
    )

    print("\n" + "=" * 80)
    print(f" COMPARATIVE EVALUATION MATRIX ({len(data)}-bit Input)")
    print(f" Error Model: {err_type.upper()} | Flipped Bit Positions: {chosen_positions}")
    print("=" * 80)

    header = f"{'Technique':<16} | {'Redundant Bits':<16} | {'Proc. Time':<12} | {'Detection Result':<18} | {'Final Verdict'}"
    print(header)
    print("-" * 80)

    for r in results:
        tech = r["technique"]
        ovh = f"{r['overhead_bits']} bit(s) ({r['overhead_percentage']:.1f}%)"
        time_us = f"{r['processing_time'] * 1e6:.2f} us"
        if "Hamming" in tech:
            if r["errors_injected"] == 0:
                det_str = "CLEAN [VALID]"
                verdict = "[CLEAN TRANSMISSION]"
            elif r.get("hamming_verdict") == "[ERROR DETECTED AND CORRECTED]" or r.get("diagnostics", {}).get("successfully_corrected"):
                det_str = "CORRECTED"
                verdict = "[ERROR DETECTED AND CORRECTED]"
            else:
                det_str = "MISCORRECTED"
                verdict = "[NOT CORRECTABLE / MISCORRECTED]"
        elif r["errors_injected"] == 0:
            det_str = "CLEAN [VALID]"
            verdict = "Frame Accepted"
        elif r["error_detected"]:
            det_str = "YES [DETECTED]"
            verdict = "Frame Rejected"
        else:
            det_str = "NO  [MISSED!]"
            verdict = "Undetected Error"

        print(f"{tech:<16} | {ovh:<16} | {time_us:<12} | {det_str:<18} | {verdict}")

    print("=" * 80)


# ======================================================================
# 3. VIEW ALGORITHM WORKING
# ======================================================================

def run_view_algorithm_working() -> None:
    """Option 3: Show step-by-step VRC, LRC, Checksum, and CRC calculations."""
    global SESSION_DATA
    print("\n" + "=" * 72)
    print(" 3. VIEW ALGORITHM WORKING")
    print("=" * 72)

    data = check_and_offer_data_change(SESSION_DATA)

    print("\nSelect Algorithm to View:")
    print("  [1] VRC / Parity Working")
    print("  [2] LRC          Working")
    print("  [3] Checksum     Working (1's Complement)")
    print("  [4] CRC          Working (Modulo-2 Division)")
    print("  [5] Hamming      Working (Hamming (7,4) Code)")
    print("  [6] View All Five Algorithms")

    c = input("\nChoice [1-6] (default 6): ").strip()
    if not c:
        c = "6"

    print(f"\nCalculating for Data ({len(data)} bits): {data}\n")

    if c in ("1", "6"):
        print(format_vrc_working(data, mode="even"))
        print()

    if c in ("2", "6"):
        print(format_lrc_working(data, block_size=8))
        print()

    if c in ("3", "6"):
        print(format_checksum_working(data, word_size=8))
        print()

    if c in ("4", "6"):
        print(format_crc_working(data, generator="100000111"))
        print()

    if c in ("5", "6"):
        print(format_hamming_working(data))
        print()


# ======================================================================
# 4. RUN EXPERIMENTS AND VIEW GRAPHS (SAFE STAGING & CONFIRMATION)
# ======================================================================

def run_experiments_and_graphs() -> None:
    """Option 4: Configure benchmark settings, generate datasets and 4 graphs.

    Uses safe staging: files are generated in an isolated temporary location first.
    The user is prompted to confirm before replacing the existing results on disk.
    If the user declines, new results are discarded and previous results are preserved.
    """
    print("\n" + "=" * 72)
    print(" 4. RUN EXPERIMENTS AND VIEW GRAPHS")
    print("=" * 72)

    print("Configure Benchmark Settings (press Enter to accept default):")

    # Data sizes
    sizes_in = input("  Data sizes in bits [default: 32, 64, 128, 256, 512, 1024]: ").strip()
    if sizes_in:
        sizes = [int(s.strip()) for s in sizes_in.split(",") if s.strip().isdigit()]
    else:
        sizes = [32, 64, 128, 256, 512, 1024]
    if not sizes:
        sizes = [32, 64, 128, 256, 512, 1024]

    # Error magnitudes for multiple-bit errors
    mag_in = input("  Multiple-bit error magnitudes [default: 1, 2, 3, 4, 5, 6, 7, 8]: ").strip()
    if mag_in:
        mags = [int(m.strip()) for m in mag_in.split(",") if m.strip().isdigit()]
    else:
        mags = [1, 2, 3, 4, 5, 6, 7, 8]
    if not mags:
        mags = [1, 2, 3, 4, 5, 6, 7, 8]

    # Burst lengths
    burst_in = input("  Burst lengths in bits [default: 2, 4, 6, 8, 12, 16]: ").strip()
    if burst_in:
        bursts = [int(b.strip()) for b in burst_in.split(",") if b.strip().isdigit()]
    else:
        bursts = [2, 4, 6, 8, 12, 16]
    if not bursts:
        bursts = [2, 4, 6, 8, 12, 16]

    # Trial count
    trials_in = input("  Trials per configuration [default: 1000]: ").strip()
    trials = int(trials_in) if trials_in.isdigit() and int(trials_in) > 0 else 1000

    # 1. Setup isolated temporary staging directory
    staging_dir = tempfile.mkdtemp(prefix="dcn_exp_staging_")
    staging_exp_csv = os.path.join(staging_dir, "experiment_results.csv")
    staging_metrics_csv = os.path.join(staging_dir, "metrics_results.csv")
    staging_viz_dir = os.path.join(staging_dir, "visualization")
    os.makedirs(staging_viz_dir, exist_ok=True)

    expected_charts = [
        "detection_rate_by_error_type.png",
        "detection_rate_vs_error_magnitude.png",
        "processing_time_vs_data_size.png",
        "overhead_vs_data_size.png"
    ]

    try:
        print("\nExecuting benchmark experiments...")
        run_all_experiments(
            data_sizes=sizes,
            multi_error_amounts=mags,
            burst_lengths=bursts,
            trials=trials,
            output_file=staging_exp_csv,
            verbose=True
        )

        print("Aggregating metrics...")
        compute_and_save_metrics(
            input_file=staging_exp_csv,
            output_file=staging_metrics_csv,
            verbose=False
        )

        print("Generating analytical graphs...")
        generate_all_plots(
            csv_path=staging_metrics_csv,
            output_dir=staging_viz_dir,
            verbose=True
        )

        # Validate that all files were generated properly
        valid_exp = os.path.exists(staging_exp_csv) and os.path.getsize(staging_exp_csv) > 0
        valid_metrics = os.path.exists(staging_metrics_csv) and os.path.getsize(staging_metrics_csv) > 0
        valid_charts = all(
            os.path.exists(os.path.join(staging_viz_dir, c)) and os.path.getsize(os.path.join(staging_viz_dir, c)) > 0
            for c in expected_charts
        )

        if not (valid_exp and valid_metrics and valid_charts):
            print("\n[Error] Benchmark generation failed. Existing files preserved.")
            return

        # 2. Confirmation prompt before applying
        print()
        while True:
            resp = input("New experiment results have been generated. Do you want to apply these changes and replace the existing results? (y/n): ").strip().lower()
            if resp in ("y", "yes"):
                target_exp_csv = os.path.join(PROJECT_ROOT, "experiment_results.csv")
                target_metrics_csv = os.path.join(PROJECT_ROOT, "metrics_results.csv")
                target_viz_dir = os.path.join(PROJECT_ROOT, "visualization")
                os.makedirs(target_viz_dir, exist_ok=True)

                shutil.copy2(staging_exp_csv, target_exp_csv)
                shutil.copy2(staging_metrics_csv, target_metrics_csv)
                for c in expected_charts:
                    shutil.copy2(os.path.join(staging_viz_dir, c), os.path.join(target_viz_dir, c))

                print("Results and graphs updated.")
                break
            elif resp in ("n", "no"):
                print("Changes discarded. Previous results and graphs preserved.")
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


# ======================================================================
# MAIN INTERACTIVE LOOP
# ======================================================================


# ======================================================================
# NETWORK TRAFFIC ANALYSIS & PACKET ERROR DETECTION (CLI)
# ======================================================================

def run_traffic_cli_analysis() -> None:
    """Option T: Inspect Wireshark PCAP packets, extract payloads, and run error detection."""
    global SESSION_DATA
    print("\n" + "=" * 72)
    print(" NETWORK TRAFFIC ANALYSIS & PACKET ERROR DETECTION")
    print("=" * 72)

    sample_path = os.path.join(PROJECT_ROOT, "samples", "sample_capture.pcap")
    if not os.path.exists(sample_path):
        generate_sample_pcap(sample_path)

    print(f"\nEnter path to PCAP / PCAPNG capture file")
    print(f"[Press Enter to use bundled demonstration: samples/sample_capture.pcap]:")
    raw_path = input("Path > ").strip()
    pcap_path = raw_path if raw_path else sample_path

    if not os.path.exists(pcap_path):
        print(f" [!] File not found at '{pcap_path}'. Using bundled sample capture.")
        pcap_path = sample_path

    print(f"\nReading and auditing packets with Scapy...")
    res = parse_pcap_file(pcap_path)
    if not res.get("success"):
        print(f" [!] Error: {res.get('error')}")
        return

    packets = res["packets"]
    summary = res["summary"]

    print("\n" + "-" * 72)
    print(f" CAPTURE SUMMARY: {os.path.basename(pcap_path)}")
    print(f" Total Packets: {summary['total_packets']} | With Payload: {summary['packets_with_payload']}")
    cs = summary['checksum_summary']
    print(f" Checksum Audit: {cs.get('valid', 0)} Valid, {cs.get('mismatch', 0)} Mismatch, {cs.get('offload', 0)} Offload/Other")
    print("-" * 72)

    header = f"{'#':<4} | {'Protocol':<12} | {'Source -> Destination':<32} | {'Size':<6} | {'Payload':<10} | {'Checksum Audit'}"
    print(header)
    print("-" * 90)

    for p in packets:
        src = f"{p['src_ip']}:{p['src_port']}" if p['src_port'] else p['src_ip']
        dst = f"{p['dst_ip']}:{p['dst_port']}" if p['dst_port'] else p['dst_ip']
        flow = f"{src} -> {dst}"
        flow = flow[:30]
        pay_str = f"{p['payload_size_bytes']} B" if p['has_payload'] else "0 B"
        chk_label = p['checksum_label']
        print(f"{p['packet_number']:<4} | {p['protocol']:<12} | {flow:<32} | {p['packet_size_bytes']:<6} | {pay_str:<10} | {chk_label}")

    print("-" * 90)
    print(" Note: IPv6 headers have no checksum (RFC 8200). Outgoing TCP/UDP checksums may reflect NIC offloading.")

    sel = input(f"\nSelect Packet Number to inspect [1-{len(packets)}] (Enter to cancel): ").strip()
    if not sel or not sel.isdigit():
        return

    pkt_num = int(sel)
    if pkt_num < 1 or pkt_num > len(packets):
        print(" [!] Invalid packet number.")
        return

    idx = pkt_num - 1
    details = extract_packet_payload_details(pcap_path, idx)
    if not details.get("success"):
        print(f" [!] Error: {details.get('error')}")
        return

    meta = details["metadata"]
    print("\n" + "=" * 72)
    print(f" PACKET #{pkt_num} DETAILS ({meta['protocol']})")
    print(f" Flow: {meta['src_ip']} -> {meta['dst_ip']} | Length: {meta['packet_size_bytes']} bytes")
    print(f" Checksum Details: {meta['checksum_details']}")
    print("=" * 72)

    if not details["has_payload"]:
        print(f"\n [!] {details.get('reason')}\n")
        return

    print(f"\nPayload Size: {details['byte_length']} bytes ({details['bit_length']} bits)")
    print(f"Hex Dump: {details['hex_dump'][:60]}...")
    print(f"ASCII   : {details['ascii_preview'][:60]}...")
    print(f"Binary  : {details['binary_string'][:64]}...")

    bin_data = details["binary_string"]

    print("\nChoose Error Detection Action:")
    print("  [1] Set this Packet Payload as Active Session Data for Simulator")
    print("  [2] Run Canonical Error Detection on this Packet")
    print("  [3] Compare All 5 Techniques Side-by-Side on this Packet")
    print("  [0] Return to Main Menu")

    action = input("\nChoice [1-3] (default 2): ").strip()

    if action == "1":
        SESSION_DATA = bin_data
        print(f"\n[+] Active Session Data updated to Packet #{pkt_num} payload ({len(bin_data)} bits).")
        return

    elif action in ("2", ""):
        print("\nSelect Technique:")
        print("  [1] VRC / Parity Check")
        print("  [2] LRC")
        print("  [3] 1's Complement Checksum")
        print("  [4] CRC (CRC-8 Modulo-2 Division)")
        print("  [5] Hamming (7,4) Code")

        tc = input("\nChoice [1-5] (default 4): ").strip()
        tmap = {"1": "VRC / Parity", "2": "LRC", "3": "Checksum", "4": "CRC", "5": "Hamming (7,4)"}
        tech = tmap.get(tc, "CRC")

        print("\nIntroduce Controlled Transmission Error?")
        print("  [0] No (Verify Clean Reference Frame)")
        print("  [1] Single-Bit Error")
        print("  [2] Multiple-Bit Error (2 bits)")
        print("  [3] Burst Error (4-bit span)")

        ec = input("\nChoice [0-3] (default 1): ").strip()
        inject = ec in ("1", "2", "3")
        err_type = "single" if ec == "1" else ("multiple" if ec == "2" else ("burst" if ec == "3" else "clean"))
        err_amt = 1 if ec == "1" else (2 if ec == "2" else 4)

        sim = evaluate_traffic_error_detection(
            binary_payload=bin_data,
            technique=tech,
            inject_error=inject,
            error_type=err_type,
            error_amount=err_amt
        )

        print("\n" + "=" * 72)
        print(" PACKET ERROR DETECTION REPORT")
        print("=" * 72)
        print(f" Technique Applied: {sim['technique']}")
        print(f" Payload Size     : {sim['payload_bits']} bits")
        print(f" Redundant Bits   : +{sim['overhead_bits']} bits ({sim['overhead_percentage']}%)")
        print(f" Errors Injected  : {sim['errors_injected']} bit(s) at positions {sim['flipped_indices']}")
        print(f" Final Verdict    : {sim['verdict']}")
        print(f" Processing Time  : {sim['processing_time_us']} us")
        print(f"\n Explanation      : {sim['explanation']}")
        print("=" * 72)

    elif action == "3":
        print("\nIntroduce Controlled Transmission Error for Comparison?")
        print("  [0] No (Clean Baseline)")
        print("  [1] Single-Bit Error")
        print("  [2] Multiple-Bit Error (2 bits)")
        print("  [3] Burst Error (4-bit span)")

        ec = input("\nChoice [0-3] (default 1): ").strip()
        inject = ec in ("1", "2", "3")
        err_type = "single" if ec == "1" else ("multiple" if ec == "2" else ("burst" if ec == "3" else "clean"))
        err_amt = 1 if ec == "1" else (2 if ec == "2" else 4)

        comp = compare_all_traffic_techniques(
            binary_payload=bin_data,
            inject_error=inject,
            error_type=err_type,
            error_amount=err_amt
        )

        print("\n" + "=" * 80)
        print(f" PACKET #{pkt_num} SYNCHRONIZED COMPARATIVE ANALYSIS ({len(bin_data)} bits)")
        print(f" Error Model: {err_type.upper()} | Flipped Bit Indices: {comp['forced_indices']}")
        print("=" * 80)

        header = f"{'Technique':<16} | {'Redundant Bits':<16} | {'Proc. Time':<12} | {'Detection Result':<18} | {'Final Verdict'}"
        print(header)
        print("-" * 80)

        for r in comp["results"]:
            tech = r["technique"]
            ovh = f"+{r['overhead_bits']} bits ({r['overhead_percentage']}%)"
            time_us = f"{r['processing_time_us']} us"
            if not inject or r["errors_injected"] == 0:
                det_str = "CLEAN [VALID]"
                verdict = "Reference Accepted"
            elif "Hamming" in tech:
                if "CORRECTED" in r.get("verdict", ""):
                    det_str = "CORRECTED (FEC)"
                    verdict = "[ERROR CORRECTED]"
                else:
                    det_str = "MISCORRECTED"
                    verdict = "[NOT CORRECTABLE]"
            elif r["error_detected"]:
                det_str = "YES [DETECTED]"
                verdict = "Frame Rejected"
            else:
                det_str = "NO  [MISSED!]"
                verdict = "Undetected Error"

            print(f"{tech:<16} | {ovh:<16} | {time_us:<12} | {det_str:<18} | {verdict}")

        print("=" * 80)

def main_menu() -> None:
    """Main interactive driver with exactly the five required options."""
    # 1. Setup session data once at startup
    print_banner()
    setup_initial_data()
    clear_screen()

    # 2. Main loop
    while True:
        print_banner()
        print("  1. Simulate Transmission")
        print("  2. Compare Detection Techniques")
        print("  3. View Algorithm Working")
        print("  4. Run Experiments and View Graphs")
        print("  5. Exit")
        print("  [C] Change Session Data")
        print("  [T] Network Traffic Analysis (PCAP Packet Inspection & Error Detection)")
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
            print("\nExiting.\n")
            break
        elif choice.lower() == "c":
            prompt_change_session_data()
        elif choice.lower() == "t":
            run_traffic_cli_analysis()
        else:
            print(" [!] Invalid option. Please enter a number between 1 and 5.")

        input("\nPress Enter to return to main menu...")
        clear_screen()


if __name__ == "__main__":
    try:
        main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram terminated.")