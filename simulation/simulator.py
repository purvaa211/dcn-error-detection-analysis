"""Simulation Engine for DCN Error Detection and Analysis.

Coordinates the complete 3-stage communication pipeline:
[1. Transmitter / Sender] -> Encodes payload with redundant check bits.
[2. Physical Channel]     -> Injects errors (Single-bit, Multiple-bit, Burst, Manual, BER).
[3. Receiver]             -> Performs integrity verification and error detection.
"""

import time
from typing import Dict, Any, List, Optional, Union

from algorithms.parity import add_parity, check_parity, add_even_parity, check_even_parity
from algorithms.two_dim_parity import encode_2d_parity, check_2d_parity, format_2d_matrix_display
from algorithms.checksum import add_checksum, verify_checksum_detailed, check_checksum
from algorithms.crc import crc_encode, crc_check, crc_check_detailed, CRC_POLYNOMIALS
from algorithms.hamming import hamming_encode, hamming_check
from simulation.error_generator import (
    single_bit_error,
    multiple_bit_error,
    burst_error,
    manual_error,
    ber_channel_error
)


def simulate(
    data: str,
    technique: str = "CRC",
    error_type: str = "single",
    error_amount: Union[int, float, List[int]] = 1,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8
) -> Dict[str, Any]:
    """Execute a single end-to-end transmission simulation.

    Args:
        data: Original binary payload (e.g. '10110011').
        technique: 'Parity', 'Parity-Even', 'Parity-Odd', '2D-Parity',
                   'Checksum', 'Checksum-8', 'Checksum-16',
                   'CRC', 'CRC-8', 'CRC-16-CCITT', 'CRC-16-ANSI', 'CRC-32', 'Hamming'.
        error_type: 'none', 'single', 'multiple', 'burst', 'manual', 'ber'.
        error_amount: Integer count for multiple/burst, float for BER, or list of indices for manual.
        crc_generator: CRC generator polynomial if custom or standard name.
        checksum_word_size: Word size in bits for Checksum (8 or 16).

    Returns:
        Comprehensive dictionary containing frames, timings, overheads, and diagnostic report.
    """
    if not data or not all(c in "01" for c in data):
        raise ValueError(f"Data must be a non-empty binary string, got: '{data}'")

    tech_normalized = technique.strip()

    # ==========================================
    # STAGE 1: SENDER / TRANSMITTER ENCODING
    # ==========================================
    t_enc_start = time.perf_counter()
    encoding_meta: Dict[str, Any] = {}

    if tech_normalized in ("Parity", "Parity-Even", "Even Parity"):
        protected_frame = add_parity(data, mode="even")
        tech_name = "Parity (Even)"
        redundancy_bits = 1

    elif tech_normalized in ("Parity-Odd", "Odd Parity"):
        protected_frame = add_parity(data, mode="odd")
        tech_name = "Parity (Odd)"
        redundancy_bits = 1

    elif tech_normalized in ("2D-Parity", "2D Parity", "LRC"):
        protected_frame, matrix_info = encode_2d_parity(data, col_size=8)
        encoding_meta = matrix_info
        tech_name = "2D Matrix Parity"
        redundancy_bits = len(protected_frame) - len(data)

    elif tech_normalized in ("Checksum", "Checksum-8", "Internet Checksum"):
        protected_frame = add_checksum(data, word_size=checksum_word_size)
        tech_name = f"Checksum ({checksum_word_size}-bit)"
        redundancy_bits = checksum_word_size

    elif tech_normalized in ("Checksum-16",):
        protected_frame = add_checksum(data, word_size=16)
        tech_name = "Checksum (16-bit)"
        redundancy_bits = 16

    elif tech_normalized.startswith("CRC") or tech_normalized in ("Cyclic Redundancy Check",):
        gen_to_use = crc_generator
        if tech_normalized in CRC_POLYNOMIALS:
            gen_to_use = CRC_POLYNOMIALS[tech_normalized]["generator"]
        elif tech_normalized == "CRC":
            gen_to_use = crc_generator

        protected_frame = crc_encode(data, generator=gen_to_use)
        tech_name = f"CRC (degree {len(gen_to_use) - 1})"
        redundancy_bits = len(gen_to_use) - 1

    elif tech_normalized in ("Hamming", "Hamming(7,4)"):
        protected_frame = hamming_encode(data)
        tech_name = "Hamming (7,4)"
        redundancy_bits = len(protected_frame) - len(data)

    else:
        raise ValueError(f"Unsupported detection technique: '{technique}'")

    encoding_time = time.perf_counter() - t_enc_start

    # ==========================================
    # STAGE 2: PHYSICAL TRANSMISSION CHANNEL
    # ==========================================
    flipped_indices: List[int] = []
    corrupted_frame = protected_frame

    if error_type == "none":
        corrupted_frame = protected_frame
        flipped_indices = []

    elif error_type == "single":
        corrupted_frame, flipped_indices = single_bit_error(
            protected_frame, return_indices=True
        )

    elif error_type == "multiple":
        count = int(error_amount) if isinstance(error_amount, (int, float)) else 2
        corrupted_frame, flipped_indices = multiple_bit_error(
            protected_frame, number_of_errors=count, return_indices=True
        )

    elif error_type == "burst":
        span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
        corrupted_frame, flipped_indices = burst_error(
            protected_frame, burst_length=span, mode="textbook", return_indices=True
        )

    elif error_type == "manual":
        if isinstance(error_amount, list):
            positions = error_amount
        elif isinstance(error_amount, int):
            positions = [error_amount]
        else:
            positions = [int(p.strip()) for p in str(error_amount).split(",") if p.strip().isdigit()]
        corrupted_frame, flipped_indices = manual_error(
            protected_frame, positions=positions, return_indices=True
        )

    elif error_type == "ber":
        ber_rate = float(error_amount) if isinstance(error_amount, (int, float)) else 0.05
        corrupted_frame, flipped_indices = ber_channel_error(
            protected_frame, bit_error_rate=ber_rate, return_indices=True
        )

    else:
        raise ValueError(f"Invalid error_type: '{error_type}'")

    actual_errors_injected = len(flipped_indices)

    # ==========================================
    # STAGE 3: RECEIVER VERIFICATION
    # ==========================================
    t_chk_start = time.perf_counter()
    diag_details: Dict[str, Any] = {}
    is_valid = True

    if tech_name == "Parity (Even)":
        is_valid, diag_details = check_parity(corrupted_frame, mode="even")

    elif tech_name == "Parity (Odd)":
        is_valid, diag_details = check_parity(corrupted_frame, mode="odd")

    elif tech_name == "2D Matrix Parity":
        is_valid, diag_details = check_2d_parity(corrupted_frame, col_size=8)

    elif "Checksum" in tech_name:
        w_size = 16 if "16-bit" in tech_name else checksum_word_size
        is_valid, diag_details = verify_checksum_detailed(corrupted_frame, word_size=w_size)

    elif tech_name.startswith("CRC"):
        gen_to_use = crc_generator
        if tech_normalized in CRC_POLYNOMIALS:
            gen_to_use = CRC_POLYNOMIALS[tech_normalized]["generator"]
        is_valid, diag_details = crc_check_detailed(corrupted_frame, generator=gen_to_use)

    elif tech_name == "Hamming (7,4)":
        is_valid, diag_details = hamming_check(corrupted_frame)

    checking_time = time.perf_counter() - t_chk_start

    # ==========================================
    # STAGE 4: ANALYSIS & EXPLANATION
    # ==========================================
    # If errors were actually injected, was an error detected?
    error_detected = not is_valid
    total_time = encoding_time + checking_time

    overhead_bits = redundancy_bits
    overhead_pct = (overhead_bits / len(data)) * 100 if len(data) > 0 else 0.0

    # Build DCN explanation
    explanation = _generate_explanation(
        tech_name=tech_name,
        error_type=error_type,
        errors_injected=actual_errors_injected,
        error_detected=error_detected,
        diag_details=diag_details
    )

    return {
        "original_data": data,
        "payload_length": len(data),
        "technique": tech_name,
        "protected_frame": protected_frame,
        "corrupted_frame": corrupted_frame,
        "flipped_indices": flipped_indices,
        "errors_injected": actual_errors_injected,
        "error_type": error_type,
        "is_valid": is_valid,
        "error_detected": error_detected,
        "overhead_bits": overhead_bits,
        "overhead_percentage": overhead_pct,
        "encoding_time": encoding_time,
        "checking_time": checking_time,
        "processing_time": total_time,
        "diagnostics": diag_details,
        "explanation": explanation
    }


def _generate_explanation(
    tech_name: str,
    error_type: str,
    errors_injected: int,
    error_detected: bool,
    diag_details: Dict[str, Any]
) -> str:
    """Produce clear DCN textbook rationale for jury presentation."""
    if errors_injected == 0:
        return "Clean frame transmitted. Integrity verified with zero bit errors."

    if "Parity" in tech_name and "2D" not in tech_name:
        if errors_injected % 2 == 1:
            return (
                f"Parity DETECTED the error: An odd number of bit flips ({errors_injected}) "
                f"inverted the total count of 1s, violating the parity condition."
            )
        else:
            return (
                f"Parity MISSED the error: An even number of bit flips ({errors_injected}) "
                f"occurred. In 1D parity, even errors cancel each other out, leaving parity unchanged."
            )

    elif "2D Matrix Parity" in tech_name:
        failed_r = diag_details.get("failed_rows", [])
        failed_c = diag_details.get("failed_cols", [])
        if error_detected:
            return (
                f"2D Parity DETECTED error: Row parity failed on {len(failed_r)} row(s), "
                f"Column parity failed on {len(failed_c)} column(s)."
            )
        else:
            return "2D Parity missed error: Symmetrical 4-bit rectangular pattern cancelled out row/col parities."

    elif "Checksum" in tech_name:
        if error_detected:
            sum_hex = diag_details.get("final_sum_hex", "")
            return f"Checksum DETECTED error: 1's complement sum ({sum_hex}) did not equal 0xFF (all 1s)."
        else:
            return "Checksum MISSED error: Compensating errors occurred in complementary positions."

    elif "CRC" in tech_name:
        rem = diag_details.get("syndrome_remainder", "")
        if error_detected:
            return f"CRC DETECTED error: Modulo-2 division remainder is non-zero (R = '{rem}')."
        else:
            return "CRC missed error: Error pattern polynomial E(x) is a multiple of generator G(x)."

    elif "Hamming" in tech_name:
        if error_detected:
            err_pos = diag_details.get("detected_errors", [])
            return f"Hamming code DETECTED errors at position(s): {err_pos}. Forward correction attempted."
        return "Hamming code passed."

    return "Verification completed."


def compare_all_techniques(
    data: str,
    error_type: str = "multiple",
    error_amount: Union[int, float, List[int]] = 2
) -> List[Dict[str, Any]]:
    """Run all primary DCN error detection techniques on the same error scenario.

    Allows side-by-side comparative evaluation for jury demonstration.
    """
    techniques = [
        "Parity-Even",
        "2D-Parity",
        "Checksum-8",
        "CRC-8",
        "CRC-16-CCITT"
    ]

    results = []
    for tech in techniques:
        res = simulate(
            data=data,
            technique=tech,
            error_type=error_type,
            error_amount=error_amount
        )
        results.append(res)

    return results