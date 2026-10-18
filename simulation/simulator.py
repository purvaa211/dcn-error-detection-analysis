"""Simulation Engine for DCN Error Detection and Analysis.

Coordinates the complete 3-stage communication pipeline:
[1. Transmitter / Sender] -> Encodes payload with redundant check bits.
[2. Physical Channel]     -> Injects errors (Clean, Single-bit, Multiple-bit, Burst, Manual).
[3. Receiver]             -> Performs integrity verification and error detection.
"""

import time
import random
from typing import Dict, Any, List, Optional, Union, Tuple

from algorithms.parity import add_vrc, check_vrc, add_parity, check_parity
from algorithms.lrc import add_lrc, check_lrc
from algorithms.checksum import add_checksum, verify_checksum_detailed
from algorithms.crc import crc_encode, crc_check_detailed, CRC_POLYNOMIALS
from simulation.error_generator import (
    clean_transmission,
    single_bit_error,
    multiple_bit_error,
    burst_error,
    consecutive_burst_error,
    multiple_burst_error,
    manual_error
)


def simulate(
    data: str,
    technique: str = "CRC",
    error_type: str = "single",
    error_amount: Union[int, float, List[int]] = 1,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    forced_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Execute a single end-to-end transmission simulation.

    Args:
        data: Original binary payload (e.g. '10110011').
        technique: 'VRC', 'VRC / Parity', 'Parity', 'LRC', 'Checksum', 'CRC'.
        error_type: 'clean', 'single', 'multiple', 'burst', 'manual'.
        error_amount: Integer count for multiple/burst, or list of indices for manual.
        crc_generator: CRC generator polynomial if custom or standard name.
        checksum_word_size: Word size in bits for Checksum (8 or 16).
        forced_indices: If provided, corrupt these exact indices for synchronized testing.

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

    if tech_normalized in ("VRC", "VRC / Parity", "Parity", "Parity-Even", "Even Parity"):
        protected_frame = add_vrc(data, mode="even")
        tech_name = "VRC / Parity"
        redundancy_bits = 1

    elif tech_normalized in ("LRC", "Longitudinal Redundancy Check"):
        protected_frame = add_lrc(data, block_size=8)
        tech_name = "LRC"
        redundancy_bits = len(protected_frame) - len(data)

    elif tech_normalized in ("Checksum", "Checksum-8", "Internet Checksum"):
        protected_frame = add_checksum(data, word_size=checksum_word_size)
        tech_name = f"Checksum ({checksum_word_size}-bit)"
        redundancy_bits = checksum_word_size

    elif tech_normalized.startswith("CRC") or tech_normalized in ("Cyclic Redundancy Check",):
        gen_to_use = crc_generator
        if tech_normalized in CRC_POLYNOMIALS:
            gen_to_use = CRC_POLYNOMIALS[tech_normalized]["generator"]
        elif tech_normalized == "CRC":
            gen_to_use = crc_generator

        protected_frame = crc_encode(data, generator=gen_to_use)
        tech_name = f"CRC ({len(gen_to_use) - 1}-bit)"
        redundancy_bits = len(gen_to_use) - 1

    else:
        # Fallback to VRC
        protected_frame = add_vrc(data, mode="even")
        tech_name = tech_normalized
        redundancy_bits = 1

    encoding_time = time.perf_counter() - t_enc_start

    # ==========================================
    # STAGE 2: PHYSICAL TRANSMISSION CHANNEL
    # ==========================================
    flipped_indices: List[int] = []
    corrupted_frame = protected_frame

    if forced_indices is not None:
        # Corrupt the specified bit positions
        corrupted_frame, flipped_indices = manual_error(
            protected_frame, positions=forced_indices, return_indices=True
        )
    elif error_type in ("clean", "none", "0"):
        corrupted_frame, flipped_indices = clean_transmission(
            protected_frame, return_indices=True
        )
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
    elif error_type in ("consecutive_burst", "consecutive"):
        span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
        corrupted_frame, flipped_indices = consecutive_burst_error(
            protected_frame, burst_length=span, return_indices=True
        )
    elif error_type in ("multiple_burst", "multi_burst"):
        if isinstance(error_amount, dict):
            num_b = int(error_amount.get("num_bursts", 2))
            b_len = int(error_amount.get("burst_length", 3))
        elif isinstance(error_amount, (list, tuple)) and len(error_amount) >= 2:
            num_b = int(error_amount[0])
            b_len = int(error_amount[1])
        else:
            num_b = 2
            b_len = int(error_amount) if isinstance(error_amount, (int, float)) else 3
        corrupted_frame, flipped_indices = multiple_burst_error(
            protected_frame, num_bursts=num_b, burst_length=b_len, return_indices=True
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
    else:
        raise ValueError(f"Invalid error_type: '{error_type}'. Supported: clean, single, multiple, burst, consecutive_burst, multiple_burst, manual.")

    actual_errors_injected = len(flipped_indices)

    # ==========================================
    # STAGE 3: RECEIVER VERIFICATION
    # ==========================================
    t_chk_start = time.perf_counter()
    diag_details: Dict[str, Any] = {}
    is_valid = True

    if tech_name == "VRC / Parity":
        is_valid, diag_details = check_vrc(corrupted_frame, mode="even")

    elif tech_name == "LRC":
        is_valid, diag_details = check_lrc(corrupted_frame, block_size=8)

    elif "Checksum" in tech_name:
        is_valid, diag_details = verify_checksum_detailed(corrupted_frame, word_size=checksum_word_size)

    elif tech_name.startswith("CRC"):
        gen_to_use = crc_generator
        if tech_normalized in CRC_POLYNOMIALS:
            gen_to_use = CRC_POLYNOMIALS[tech_normalized]["generator"]
        is_valid, diag_details = crc_check_detailed(corrupted_frame, generator=gen_to_use)

    checking_time = time.perf_counter() - t_chk_start

    # ==========================================
    # STAGE 4: ANALYSIS & EXPLANATION
    # ==========================================
    error_detected = not is_valid
    total_time = encoding_time + checking_time

    overhead_bits = redundancy_bits
    overhead_pct = (overhead_bits / len(data)) * 100 if len(data) > 0 else 0.0

    error_cause, error_introduction = _get_error_cause_and_mechanism(
        error_type=error_type,
        errors_injected=actual_errors_injected,
        flipped_indices=flipped_indices,
        frame_len=len(protected_frame)
    )

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
        "error_cause": error_cause,
        "error_introduction": error_introduction,
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


def _get_error_cause_and_mechanism(
    error_type: str,
    errors_injected: int,
    flipped_indices: List[int],
    frame_len: int
) -> Tuple[str, str]:
    """Provide realistic physical layer noise etiology and injection mechanism."""
    err_norm = error_type.lower().strip()

    if err_norm in ("clean", "none", "0") or errors_injected == 0:
        cause = "Ideal transmission environment. Complete absence of thermal noise, cross-talk, and electromagnetic interference on the transmission medium."
        mechanism = "Transparent channel transmission without bit alteration (0 bit flips). Frame integrity is fully preserved."
        return cause, mechanism

    if err_norm == "single":
        cause = "Microscopic thermal white noise (Gaussian background disturbance) or a brief localized voltage transient on physical media (copper, optical receiver, or wireless RF)."
        pos_str = str(flipped_indices[0]) if flipped_indices else "random"
        mechanism = f"Inverted exactly 1 isolated bit (0 ↔ 1) at frame bit position {pos_str}."
        return cause, mechanism

    if err_norm == "multiple":
        cause = "Inductive crosstalk from adjacent cable pairs, high-frequency atmospheric noise, or multi-user interference causing independent random bit flips."
        mechanism = f"Inverted {errors_injected} independent bit positions scattered across the frame at indices: {flipped_indices}."
        return cause, mechanism

    if err_norm == "burst":
        span = (max(flipped_indices) - min(flipped_indices) + 1) if flipped_indices else errors_injected
        cause = "Transient impulse noise event such as an electrostatic discharge (ESD), lightning strike, relay contact arcing, or sudden power bus switching transient."
        mechanism = f"Textbook burst error spanning {span} bits from index {min(flipped_indices)} to {max(flipped_indices)}. Endpoints are guaranteed inverted, with intermediate bits flipped probabilistically (total {errors_injected} bits altered)."
        return cause, mechanism

    if err_norm in ("consecutive_burst", "consecutive"):
        cause = "Sustained electromagnetic interference (EMI) pulse, temporary physical cable disconnection/vibration, deep signal fade dip in wireless propagation, or transceiver clock sync dropout."
        start = min(flipped_indices) if flipped_indices else 0
        end = max(flipped_indices) if flipped_indices else 0
        mechanism = f"Solid consecutive burst corruption: 100% of contiguous bits inverted continuously across a span of {errors_injected} bit(s) from index {start} to {end}: {flipped_indices}."
        return cause, mechanism

    if err_norm in ("multiple_burst", "multi_burst"):
        cause = "Periodic impulse noise, recurring motor commutator arcing, mechanical vibration on connectors, or multipath reflection echoes creating multiple distinct interference clusters."
        mechanism = f"Multiple separated burst episodes injected across the frame, corrupting {errors_injected} bits across positions: {flipped_indices} separated by uncorrupted bit intervals."
        return cause, mechanism

    if err_norm == "manual":
        cause = "Controlled deterministic test harness simulating targeted edge-case vulnerabilities, synchronized bit alterations, or synthetic corruption patterns."
        mechanism = f"Manual injection of deterministic bit flips directly at user-selected positions: {flipped_indices}."
        return cause, mechanism

    cause = "Channel disturbance causing binary signal level inversion."
    mechanism = f"Inverted {errors_injected} bit(s) at positions: {flipped_indices}."
    return cause, mechanism


def _generate_explanation(
    tech_name: str,
    error_type: str,
    errors_injected: int,
    error_detected: bool,
    diag_details: Dict[str, Any]
) -> str:
    """Produce clear DCN textbook rationale for jury presentation."""
    if errors_injected == 0:
        return "Clean transmission. Frame integrity verified with 0 bit errors."

    err_norm = error_type.lower().strip()

    if "VRC" in tech_name or "Parity" in tech_name:
        if err_norm in ("consecutive_burst", "consecutive"):
            if errors_injected % 2 == 1:
                return (
                    f"VRC DETECTED consecutive burst: The burst corrupted an odd count of consecutive bits ({errors_injected}), "
                    f"which altered overall frame parity."
                )
            else:
                return (
                    f"VRC MISSED consecutive burst: The burst corrupted an even count of consecutive bits ({errors_injected}). "
                    f"In 1D parity, even bit flips cancel out, leaving parity invariant (d_min = 2)."
                )

        if errors_injected % 2 == 1:
            return (
                f"VRC DETECTED error: An odd number of bit errors ({errors_injected}) occurred, "
                f"which changed the overall parity."
            )
        else:
            return (
                f"VRC MISSED error: An even number of bit errors ({errors_injected}) occurred. "
                f"In 1D parity, even bit flips cancel out, leaving parity invariant (d_min = 2)."
            )

    elif tech_name == "LRC":
        failed_cols = diag_details.get("failed_columns", [])
        if error_detected:
            return (
                f"LRC DETECTED error: Column parity failed on column(s) {failed_cols}."
            )
        else:
            return "LRC MISSED error: Even number of bit errors occurred in the exact same column position(s)."

    elif "Checksum" in tech_name:
        if error_detected:
            sum_hex = diag_details.get("final_sum_hex", "")
            return f"Checksum DETECTED error: 1's complement sum ({sum_hex}) does not equal 0xFF (all 1s)."
        else:
            return "Checksum MISSED error: Compensating errors occurred in complementary positions."

    elif "CRC" in tech_name:
        rem = diag_details.get("syndrome_remainder", "")
        if error_detected:
            return f"CRC DETECTED error: Modulo-2 division remainder is non-zero (R = '{rem}')."
        else:
            return "CRC MISSED error: Error polynomial E(x) is divisible by generator G(x)."

    return "Verification completed."


def compare_all_techniques(
    data: str,
    error_type: str = "multiple",
    error_amount: Union[int, float, List[int]] = 2
) -> List[Dict[str, Any]]:
    """Run all four techniques on the same input under equivalent error conditions.

    Ensures the identical data payload bit positions are corrupted across
    VRC, LRC, Checksum, and CRC.
    """
    data_len = len(data)

    # Determine corrupted payload bit indices so all 4 techniques face the EXACT same errors
    payload_corrupted_indices: List[int] = []

    if error_type == "clean":
        payload_corrupted_indices = []
    elif error_type == "single":
        payload_corrupted_indices = [random.randrange(data_len)]
    elif error_type == "multiple":
        count = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 2, data_len))
        payload_corrupted_indices = sorted(random.sample(range(data_len), count))
    elif error_type == "burst":
        span = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 4, data_len))
        start = random.randint(0, data_len - span)
        payload_corrupted_indices = [start, start + span - 1]
        for p in range(start + 1, start + span - 1):
            if random.random() < 0.5:
                payload_corrupted_indices.append(p)
        payload_corrupted_indices = sorted(payload_corrupted_indices)
    elif error_type in ("consecutive_burst", "consecutive"):
        span = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 4, data_len))
        max_start = data_len - span
        start = random.randint(0, max_start) if max_start > 0 else 0
        payload_corrupted_indices = list(range(start, start + span))
    elif error_type in ("multiple_burst", "multi_burst"):
        num_b = 2
        b_len = int(error_amount) if isinstance(error_amount, (int, float)) else 3
        _, payload_corrupted_indices = multiple_burst_error(
            "0" * data_len, num_bursts=num_b, burst_length=b_len, return_indices=True
        )
    elif error_type == "manual":
        if isinstance(error_amount, list):
            positions = error_amount
        elif isinstance(error_amount, int):
            positions = [error_amount]
        else:
            positions = [int(p.strip()) for p in str(error_amount).split(",") if p.strip().isdigit()]
        payload_corrupted_indices = sorted([p for p in positions if 0 <= p < data_len])
        if not payload_corrupted_indices:
            payload_corrupted_indices = [0]

    techniques = [
        "VRC / Parity",
        "LRC",
        "Checksum",
        "CRC"
    ]

    results = []
    for tech in techniques:
        res = simulate(
            data=data,
            technique=tech,
            error_type=error_type,
            error_amount=error_amount,
            forced_indices=payload_corrupted_indices if error_type != "clean" else []
        )
        results.append(res)

    return results