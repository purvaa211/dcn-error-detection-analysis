"""Internet Checksum Algorithm (RFC 1071 style).

Implements 1's complement addition with end-around carry.
Used across the TCP/IP stack (IPv4, TCP, UDP).

Procedure:
1. Divide data into k-bit words (typically 8-bit or 16-bit). Pad if necessary.
2. Sum all k-bit words using 1's complement arithmetic (wrap any carry back into sum).
3. Complement the result (bitwise NOT) to form the checksum word.
4. Transmitter sends data + checksum.
5. Receiver sums all words including checksum.
   - If transmission was error-free, 1's complement sum of (Data + ~Data) equals all 1s (0xFF or 0xFFFF).
   - Equivalently, complement of sum is 0.

DCN Characteristics:
- Detects all single-bit errors.
- Detects any odd number of bit errors.
- Detects most burst errors.
- Weakness: Compensating errors (where one bit flip in a column is canceled by
  an opposite bit flip in the same bit position in another word) go undetected.
"""

from typing import Tuple, Dict, Any, List


def pad_to_word_boundary(data: str, word_size: int = 8) -> Tuple[str, int]:
    """Pad data with trailing zeros so its bit length is a multiple of word_size."""
    remainder = len(data) % word_size
    if remainder != 0:
        padding_needed = word_size - remainder
        return data + ("0" * padding_needed), padding_needed
    return data, 0


def ones_complement_sum(words: List[int], word_size: int = 8) -> Tuple[int, List[Dict[str, Any]]]:
    """Perform 1's complement addition with end-around carry over integer words."""
    mask = (1 << word_size) - 1
    total = 0
    steps = []

    for idx, w in enumerate(words):
        raw_sum = total + w
        carry = raw_sum >> word_size
        wrapped_sum = (raw_sum & mask) + carry

        steps.append({
            "step": idx + 1,
            "word_val": w,
            "word_bin": format(w, f"0{word_size}b"),
            "previous_total": total,
            "carry": carry,
            "new_total": wrapped_sum
        })
        total = wrapped_sum

    # In case a lingering carry remains
    while total >> word_size:
        carry = total >> word_size
        total = (total & mask) + carry

    return total, steps


def calculate_checksum(
    data: str,
    word_size: int = 8
) -> Tuple[str, Dict[str, Any]]:
    """Compute the 1's complement checksum for a binary string.

    Args:
        data: Binary string payload.
        word_size: Word size in bits (8 or 16).

    Returns:
        tuple (checksum_binary_str, details_dict)
    """
    if not data or not all(c in "01" for c in data):
        raise ValueError("Data must be a non-empty binary string.")

    padded_data, pad_count = pad_to_word_boundary(data, word_size)
    num_blocks = len(padded_data) // word_size

    blocks = [
        int(padded_data[i * word_size:(i + 1) * word_size], 2)
        for i in range(num_blocks)
    ]

    total, steps = ones_complement_sum(blocks, word_size)
    mask = (1 << word_size) - 1
    checksum_val = (~total) & mask
    checksum_bin = format(checksum_val, f"0{word_size}b")

    details = {
        "word_size": word_size,
        "pad_count": pad_count,
        "blocks": blocks,
        "blocks_bin": [format(b, f"0{word_size}b") for b in blocks],
        "sum_before_complement": total,
        "sum_before_complement_bin": format(total, f"0{word_size}b"),
        "checksum_val": checksum_val,
        "checksum_bin": checksum_bin,
        "steps": steps
    }

    return checksum_bin, details


def add_checksum(data: str, word_size: int = 8) -> str:
    """Encode binary data by appending the calculated checksum.

    Args:
        data: Binary payload string.
        word_size: Checksum word size in bits (default: 8).

    Returns:
        Frame with checksum appended.
    """
    padded_data, _ = pad_to_word_boundary(data, word_size)
    checksum_bin, _ = calculate_checksum(padded_data, word_size)
    return padded_data + checksum_bin


def check_checksum(frame: str, word_size: int = 8) -> bool:
    """Verify frame integrity using 1's complement checksum (backward compatible).

    Returns:
        True if checksum verification passes (no error detected), False otherwise.
    """
    is_valid, _ = verify_checksum_detailed(frame, word_size)
    return is_valid


def verify_checksum_detailed(
    frame: str,
    word_size: int = 8
) -> Tuple[bool, Dict[str, Any]]:
    """Verify frame with full step-by-step diagnostics for jury presentation.

    Args:
        frame: Received bit sequence including checksum.
        word_size: Word size in bits (default: 8).

    Returns:
        tuple (is_valid, details_dict)
    """
    if len(frame) < word_size * 2 or len(frame) % word_size != 0:
        return False, {
            "is_valid": False,
            "error": f"Frame length {len(frame)} is not a valid multiple of word size {word_size}"
        }

    num_blocks = len(frame) // word_size
    blocks = [
        int(frame[i * word_size:(i + 1) * word_size], 2)
        for i in range(num_blocks)
    ]

    total, steps = ones_complement_sum(blocks, word_size)
    mask = (1 << word_size) - 1

    # In 1's complement arithmetic, sum + ~sum = all 1s (e.g. 0xFF for 8-bit, 0xFFFF for 16-bit)
    is_valid = (total == mask)

    complement_result = (~total) & mask

    details = {
        "word_size": word_size,
        "num_blocks": num_blocks,
        "blocks": blocks,
        "blocks_bin": [format(b, f"0{word_size}b") for b in blocks],
        "final_sum": total,
        "final_sum_hex": hex(total),
        "expected_sum": mask,
        "expected_sum_hex": hex(mask),
        "complement_result": complement_result,
        "is_valid": is_valid,
        "steps": steps
    }

    return is_valid, details


def format_checksum_working(data: str, word_size: int = 8) -> str:
    """Format step-by-step Internet Checksum calculation for educational display."""
    checksum_bin, details = calculate_checksum(data, word_size)
    blocks_bin = details["blocks_bin"]
    steps = details["steps"]
    mask = (1 << word_size) - 1

    lines = [
        "=" * 60,
        f" INTERNET CHECKSUM ({word_size}-BIT) STEP-BY-STEP CALCULATION",
        "=" * 60,
        f" Original Data: {data} ({len(data)} bits)",
        f" Word Size    : {word_size} bits | Divided into {len(blocks_bin)} block(s)",
        "-" * 60
    ]

    for idx, b in enumerate(blocks_bin):
        lines.append(f"  Word {idx+1}: {b} (0x{int(b, 2):02X})")

    lines.append("-" * 60)
    lines.append(" 1's Complement Summation (with end-around carry wrap):")

    for s in steps:
        step_num = s["step"]
        w_bin = s["word_bin"]
        p_tot = format(s["previous_total"], f"0{word_size}b")
        c = s["carry"]
        n_tot = format(s["new_total"], f"0{word_size}b")
        lines.append(f"  Step {step_num}: Sum so far = {p_tot} + Word {step_num} ({w_bin})")
        if c > 0:
            lines.append(f"          Carry generated = {c} -> wrapped back to sum")
        lines.append(f"          New Sum = {n_tot} (0x{s['new_total']:02X})")

    tot_val = details["sum_before_complement"]
    chk_val = details["checksum_val"]
    lines.append("-" * 60)
    lines.append(f" Final Sum before complement : {format(tot_val, f'0{word_size}b')} (0x{tot_val:02X})")
    lines.append(f" Bitwise 1's Complement (NOT): {checksum_bin} (0x{chk_val:02X})")
    lines.append(f" Checksum to Transmit        : {checksum_bin}")
    lines.append(f" Transmitted Frame           : {data + checksum_bin}")
    lines.append("=" * 60)

    return "\n".join(lines)