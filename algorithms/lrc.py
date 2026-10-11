"""Longitudinal Redundancy Check (LRC) Algorithm.

In Longitudinal Redundancy Check (LRC), data bits are organized into a table
of rows (typically 8-bit blocks / characters).
A parity bit is calculated for each column across all rows.
The resulting row of parity bits is called the LRC Block (or Block Check Character - BCC).

DCN Characteristics:
- Redundancy: 1 block (typically 8 bits) per frame.
- Detects all single-bit errors.
- Detects multiple-bit errors as long as an odd number of bits flip in any column.
- Catches 2-bit errors if they occur in different columns (unlike 1D VRC).
- Weakness: Fails if an even number of bits flip in the exact same column position.
- Detects burst errors of length <= block width (8 bits).
"""

from typing import Tuple, Dict, Any, List, Union


def pad_to_block_boundary(data: str, block_size: int = 8) -> Tuple[str, int]:
    """Pad binary data with trailing zeros so length is a multiple of block_size."""
    remainder = len(data) % block_size
    if remainder != 0:
        padding_needed = block_size - remainder
        return data + ("0" * padding_needed), padding_needed
    return data, 0


def calculate_lrc(data: str, block_size: int = 8) -> Tuple[str, Dict[str, Any]]:
    """Compute the LRC block (column-wise even parity) for a binary string.

    Args:
        data: Binary payload string.
        block_size: Width of each row in bits (default: 8).

    Returns:
        tuple (lrc_block_str, details_dict)
    """
    if not data or not all(c in "01" for c in data):
        raise ValueError("Data must be a non-empty binary string.")

    padded_data, pad_count = pad_to_block_boundary(data, block_size)
    num_blocks = len(padded_data) // block_size

    blocks: List[str] = [
        padded_data[i * block_size:(i + 1) * block_size]
        for i in range(num_blocks)
    ]

    col_ones_counts = []
    lrc_bits = []

    for c in range(block_size):
        ones = sum(1 for b in blocks if b[c] == "1")
        col_ones_counts.append(ones)
        # Even parity for each column
        lrc_bits.append("0" if ones % 2 == 0 else "1")

    lrc_block = "".join(lrc_bits)

    details = {
        "block_size": block_size,
        "num_blocks": num_blocks,
        "pad_count": pad_count,
        "blocks": blocks,
        "col_ones_counts": col_ones_counts,
        "lrc_block": lrc_block
    }

    return lrc_block, details


def add_lrc(data: str, block_size: int = 8) -> str:
    """Encode data by appending the calculated LRC parity block.

    Args:
        data: Binary payload string.
        block_size: Column width in bits (default: 8).

    Returns:
        Protected frame (padded data + LRC block).
    """
    padded_data, _ = pad_to_block_boundary(data, block_size)
    lrc_block, _ = calculate_lrc(padded_data, block_size)
    return padded_data + lrc_block


def check_lrc(frame: str, block_size: int = 8) -> Tuple[bool, Dict[str, Any]]:
    """Verify received frame using Longitudinal Redundancy Check (LRC).

    Splits the frame into data blocks and the trailing LRC block,
    recalculates column parities, and compares with received LRC.

    Args:
        frame: Received bit sequence.
        block_size: Block width in bits (default: 8).

    Returns:
        tuple (is_valid, details_dict)
    """
    if len(frame) < block_size * 2 or len(frame) % block_size != 0:
        return False, {
            "is_valid": False,
            "error_message": f"Frame length {len(frame)} is not a valid multiple of block size {block_size}"
        }

    num_total_blocks = len(frame) // block_size
    num_data_blocks = num_total_blocks - 1

    data_payload = frame[:num_data_blocks * block_size]
    received_lrc = frame[num_data_blocks * block_size:]

    data_blocks = [
        data_payload[i * block_size:(i + 1) * block_size]
        for i in range(num_data_blocks)
    ]

    expected_lrc_bits = []
    col_counts = []
    failed_columns = []

    for c in range(block_size):
        ones = sum(1 for b in data_blocks if b[c] == "1")
        col_counts.append(ones)
        exp_bit = "0" if ones % 2 == 0 else "1"
        expected_lrc_bits.append(exp_bit)
        if exp_bit != received_lrc[c]:
            failed_columns.append(c)

    expected_lrc = "".join(expected_lrc_bits)
    is_valid = (expected_lrc == received_lrc)

    details = {
        "is_valid": is_valid,
        "block_size": block_size,
        "num_data_blocks": num_data_blocks,
        "data_blocks": data_blocks,
        "received_lrc": received_lrc,
        "expected_lrc": expected_lrc,
        "col_counts": col_counts,
        "failed_columns": failed_columns
    }

    return is_valid, details


def format_lrc_working(data_or_details: Union[str, Dict[str, Any]], block_size: int = 8) -> str:
    """Format step-by-step LRC table for educational display.
    
    Accepts either a binary string payload or an existing details dictionary.
    """
    if isinstance(data_or_details, str):
        _, details = calculate_lrc(data_or_details, block_size=block_size)
    else:
        details = data_or_details

    blocks = details.get("blocks", details.get("data_blocks", []))
    block_size = details.get("block_size", block_size)
    lrc_block = details.get("lrc_block", details.get("expected_lrc", ""))
    counts = details.get("col_ones_counts", details.get("col_counts", []))
    failed_cols = set(details.get("failed_columns", []))

    lines = []
    lines.append("=" * 60)
    lines.append(" LONGITUDINAL REDUNDANCY CHECK (LRC) CALCULATION")
    lines.append("=" * 60)
    lines.append(f" Block size (column width): {block_size} bits | Number of blocks: {len(blocks)}")
    lines.append("-" * 60)

    header = "       " + " ".join(f"C{c}" for c in range(block_size))
    lines.append(header)
    lines.append("     +" + "-" * (block_size * 3 + 1))

    for idx, b in enumerate(blocks):
        row_str = "  ".join(b)
        lines.append(f" B{idx:<2} | {row_str}")

    lines.append("     +" + "-" * (block_size * 3 + 1))

    if counts:
        ones_str = " ".join(f"{cnt:>2}" for cnt in counts)
        lines.append(f" 1s  | {ones_str}  (Total count of 1s per column)")

    lrc_str = "  ".join(lrc_block)
    lines.append(f" LRC | {lrc_str}  (Column Parity: 0 if even, 1 if odd)")

    if "received_lrc" in details:
        rec_str = "  ".join(details["received_lrc"])
        lines.append(f" RX  | {rec_str}  (Received LRC)")
        status = " ".join(" ^" if c in failed_cols else "  " for c in range(block_size))
        lines.append(f" MIS | {status}")

    lines.append("=" * 60)
    return "\n".join(lines)
