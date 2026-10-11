"""Parity Check Algorithm (1D Vertical Redundancy Check - VRC).

Supports both Even and Odd parity schemes.
In Even Parity, a redundant bit is appended such that the total number of 1s is even.
In Odd Parity, a redundant bit is appended such that the total number of 1s is odd.

DCN Characteristics:
- Detects all single-bit errors (100%).
- Detects all odd numbers of bit errors (3, 5, 7, ...).
- Completely FAILS to detect any even number of bit errors (2, 4, 6, ...) because parity remains unchanged.
- Minimum Hamming distance d_min = 2.
"""

from typing import Tuple, Dict, Any


def validate_binary(data: str) -> None:
    """Validate that the string consists only of '0' and '1' bits."""
    if not data or not all(c in "01" for c in data):
        raise ValueError(f"Input must be a non-empty binary string of '0' and '1', got: '{data}'")


def add_parity(data: str, mode: str = "even") -> str:
    """Append a parity bit to the binary data.

    Args:
        data: Binary string (e.g. '1011001').
        mode: 'even' or 'odd' parity.

    Returns:
        Frame with parity bit appended (length = len(data) + 1).
    """
    validate_binary(data)
    ones = data.count("1")

    if mode.lower() == "even":
        parity_bit = "0" if ones % 2 == 0 else "1"
    elif mode.lower() == "odd":
        parity_bit = "1" if ones % 2 == 0 else "0"
    else:
        raise ValueError(f"Invalid parity mode: {mode}. Must be 'even' or 'odd'.")

    return data + parity_bit


def check_parity(frame: str, mode: str = "even") -> Tuple[bool, Dict[str, Any]]:
    """Check whether a received frame satisfies the parity rule.

    Args:
        frame: Received frame string including parity bit.
        mode: 'even' or 'odd' parity.

    Returns:
        tuple (is_valid, details_dict)
    """
    validate_binary(frame)
    ones = frame.count("1")
    data_bits = frame[:-1]
    received_parity = frame[-1]

    if mode.lower() == "even":
        is_valid = (ones % 2 == 0)
        expected_parity = "0" if data_bits.count("1") % 2 == 0 else "1"
    elif mode.lower() == "odd":
        is_valid = (ones % 2 != 0)
        expected_parity = "1" if data_bits.count("1") % 2 == 0 else "0"
    else:
        raise ValueError(f"Invalid parity mode: {mode}. Must be 'even' or 'odd'.")

    details = {
        "mode": mode.lower(),
        "total_ones": ones,
        "data_bits": data_bits,
        "received_parity": received_parity,
        "expected_parity": expected_parity,
        "is_valid": is_valid,
        "parity_match": (received_parity == expected_parity)
    }

    return is_valid, details


# ==========================================
# BACKWARD COMPATIBLE WRAPPERS
# ==========================================

def add_even_parity(data: str) -> str:
    """Add even parity bit to data (backward-compatible function)."""
    return add_parity(data, mode="even")


def check_even_parity(frame: str) -> bool:
    """Check even parity of frame (backward-compatible function)."""
    is_valid, _ = check_parity(frame, mode="even")
    return is_valid