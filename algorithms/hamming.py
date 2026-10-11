"""Hamming Code (7, 4) Error Detection and Correction.

Encodes 4 data bits into a 7-bit codeword by inserting 3 parity bits at
power-of-2 bit positions (1, 2, 4).

Bit layout (1-indexed):
Position 1: P1 (covers 1, 3, 5, 7)
Position 2: P2 (covers 2, 3, 6, 7)
Position 3: D1
Position 4: P3 (covers 4, 5, 6, 7)
Position 5: D2
Position 6: D3
Position 7: D4

Receiver computes Syndrome:
S = (S3 * 4) + (S2 * 2) + S1
If S == 0: No error.
If S != 0: S directly indicates the 1-based index of the corrupted bit!
The receiver can detect AND correct the single-bit error.
"""

from typing import Tuple, Dict, Any, List


def encode_hamming_block(nibble: str) -> str:
    """Encode a 4-bit binary nibble into a 7-bit Hamming codeword."""
    if len(nibble) != 4 or not all(c in "01" for c in nibble):
        raise ValueError("Nibble must be exactly 4 binary bits.")

    d1, d2, d3, d4 = int(nibble[0]), int(nibble[1]), int(nibble[2]), int(nibble[3])

    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4

    # 1-indexed: P1, P2, D1, P3, D2, D3, D4
    codeword = f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}"
    return codeword


def check_hamming_block(block: str) -> Tuple[bool, int, str]:
    """Check a 7-bit Hamming block.

    Returns:
        tuple (is_valid, error_position_1_indexed, corrected_nibble)
    """
    if len(block) != 7:
        raise ValueError("Hamming block must be exactly 7 bits.")

    b = [int(c) for c in block]
    # b[0]=P1, b[1]=P2, b[2]=D1, b[3]=P3, b[4]=D2, b[5]=D3, b[6]=D4

    s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s3 = b[3] ^ b[4] ^ b[5] ^ b[6]

    syndrome = (s3 << 2) | (s2 << 1) | s1

    if syndrome == 0:
        return True, 0, f"{b[2]}{b[4]}{b[5]}{b[6]}"

    # Error detected at syndrome index (1 to 7)
    corrupted = list(b)
    err_pos = syndrome - 1
    if 0 <= err_pos < 7:
        corrupted[err_pos] ^= 1

    corrected_nibble = f"{corrupted[2]}{corrupted[4]}{corrupted[5]}{corrupted[6]}"
    return False, syndrome, corrected_nibble


def hamming_encode(data: str) -> str:
    """Encode an arbitrary length binary string using Hamming(7,4) blocks.

    Pads data to multiple of 4 bits.
    """
    remainder = len(data) % 4
    if remainder != 0:
        data = data + ("0" * (4 - remainder))

    encoded_blocks = []
    for i in range(0, len(data), 4):
        nibble = data[i:i + 4]
        encoded_blocks.append(encode_hamming_block(nibble))

    return "".join(encoded_blocks)


def hamming_check(frame: str) -> Tuple[bool, Dict[str, Any]]:
    """Check a multi-block Hamming frame."""
    if len(frame) % 7 != 0:
        return False, {"is_valid": False, "error": "Frame length not multiple of 7"}

    num_blocks = len(frame) // 7
    all_valid = True
    errors = []
    corrected_data = []

    for blk_idx in range(num_blocks):
        block = frame[blk_idx * 7:(blk_idx + 1) * 7]
        is_valid, err_pos, corrected_nibble = check_hamming_block(block)
        corrected_data.append(corrected_nibble)
        if not is_valid:
            all_valid = False
            global_pos = blk_idx * 7 + (err_pos - 1)
            errors.append({
                "block_index": blk_idx,
                "local_bit": err_pos,
                "global_bit_index": global_pos
            })

    details = {
        "is_valid": all_valid,
        "num_blocks": num_blocks,
        "detected_errors": errors,
        "corrected_data": "".join(corrected_data)
    }

    return all_valid, details
