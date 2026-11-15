"""Hamming (7,4) Single-Bit Error Correction & Detection Code.

Implements Forward Error Correction (FEC) using the classical Hamming (7,4) code.
Every 4-bit data nibble (d1, d2, d3, d4) is encoded into a 7-bit block by computing
three parity bits (p1, p2, p4) under even parity.

Bit positions in each 7-bit block (1-indexed):
  Position 1: p1  (binary 001) - Parity for positions with 1 in bit 0: {1, 3, 5, 7}
  Position 2: p2  (binary 010) - Parity for positions with 1 in bit 1: {2, 3, 6, 7}
  Position 3: d1  (binary 011) - Data bit 1
  Position 4: p4  (binary 100) - Parity for positions with 1 in bit 2: {4, 5, 6, 7}
  Position 5: d2  (binary 101) - Data bit 2
  Position 6: d3  (binary 110) - Data bit 3
  Position 7: d4  (binary 111) - Data bit 4

Parity equations (Even Parity):
  p1 = d1 ^ d2 ^ d4   (positions 3, 5, 7)
  p2 = d1 ^ d3 ^ d4   (positions 3, 6, 7)
  p4 = d2 ^ d3 ^ d4   (positions 5, 6, 7)

Syndrome equations at receiver:
  s1 = b1 ^ b3 ^ b5 ^ b7
  s2 = b2 ^ b3 ^ b6 ^ b7
  s4 = b4 ^ b5 ^ b6 ^ b7
  Error position = s1*1 + s2*2 + s4*4 (0 indicates no error)

DCN Characteristics:
- Minimum Hamming distance d_min = 3.
- Forward Error Correction (FEC): Corrects any single-bit error (100%) without ARQ.
- Detects 2-bit errors, but standard (7,4) miscorrects a double error (SECDED requires
  an 8th overall parity bit).
- Redundancy: 3 check bits per 4 data bits (75% overhead).
"""

from typing import Tuple, Dict, Any, List, Optional


def validate_binary(data: str) -> None:
    """Validate that the string consists only of '0' and '1' bits."""
    if not data or not all(c in "01" for c in data):
        raise ValueError(f"Input must be a non-empty binary string of '0' and '1', got: '{data}'")


def pad_to_nibble_boundary(data: str) -> Tuple[str, int]:
    """Pad binary data with trailing zeros so length is a multiple of 4 bits."""
    validate_binary(data)
    rem = len(data) % 4
    if rem != 0:
        pad_count = 4 - rem
        return data + ("0" * pad_count), pad_count
    return data, 0


def encode_74_block(nibble: str) -> str:
    """Encode a 4-bit nibble into a 7-bit Hamming codeword."""
    if len(nibble) != 4 or not all(c in "01" for c in nibble):
        raise ValueError(f"Nibble must be exactly 4 binary bits, got: '{nibble}'")

    d1, d2, d3, d4 = int(nibble[0]), int(nibble[1]), int(nibble[2]), int(nibble[3])

    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p4 = d2 ^ d3 ^ d4

    # 1-indexed: b1=p1, b2=p2, b3=d1, b4=p4, b5=d2, b6=d3, b7=d4
    codeword = f"{p1}{p2}{d1}{p4}{d2}{d3}{d4}"
    return codeword


def decode_74_block(block: str) -> Tuple[str, str, Dict[str, Any]]:
    """Decode a 7-bit Hamming block, detecting and correcting any single-bit error.

    Args:
        block: 7-bit received binary string.

    Returns:
        tuple (corrected_7bit_block, extracted_4bit_data, diagnostic_dict)
    """
    if len(block) != 7 or not all(c in "01" for c in block):
        raise ValueError(f"Block must be exactly 7 binary bits, got: '{block}'")

    bits = [int(c) for c in block]
    b1, b2, b3, b4, b5, b6, b7 = bits

    # Calculate syndrome bits
    s1 = b1 ^ b3 ^ b5 ^ b7
    s2 = b2 ^ b3 ^ b6 ^ b7
    s4 = b4 ^ b5 ^ b6 ^ b7

    syndrome_int = s1 * 1 + s2 * 2 + s4 * 4
    syndrome_bin = f"{s4}{s2}{s1}"

    corrected_bits = list(bits)
    error_detected = (syndrome_int != 0)
    error_pos_1based = syndrome_int if error_detected else None

    if error_detected and 1 <= syndrome_int <= 7:
        # Invert the corrupted bit at index (syndrome_int - 1)
        corrected_bits[syndrome_int - 1] ^= 1

    corrected_block_str = "".join(str(b) for b in corrected_bits)

    # Extract 4 data bits: b3, b5, b6, b7
    extracted_data = f"{corrected_bits[2]}{corrected_bits[4]}{corrected_bits[5]}{corrected_bits[6]}"

    diag = {
        "received_block": block,
        "syndrome_bin": syndrome_bin,
        "syndrome_int": syndrome_int,
        "error_detected": error_detected,
        "error_position": error_pos_1based,
        "corrected_block": corrected_block_str,
        "extracted_data": extracted_data
    }

    return corrected_block_str, extracted_data, diag


def hamming_encode(data_bits: str) -> str:
    """Split payload into 4-bit nibbles (zero-padded if needed) and encode each to 7 bits.

    Args:
        data_bits: Binary string payload.

    Returns:
        Full coded bitstring (length = 7 * number_of_nibbles).
    """
    padded_data, _ = pad_to_nibble_boundary(data_bits)
    blocks = [padded_data[i:i + 4] for i in range(0, len(padded_data), 4)]
    encoded_blocks = [encode_74_block(nibble) for nibble in blocks]
    return "".join(encoded_blocks)


def hamming_decode(
    received_bits: str,
    original_payload_len: Optional[int] = None
) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Decode received 7-bit blocks, locating and correcting single bit errors per block.

    Args:
        received_bits: Received binary bitstring (multiple of 7 bits).
        original_payload_len: Optional length to trim padding from extracted data.

    Returns:
        tuple (corrected_bits, extracted_data_bits, per_block_info_list)
    """
    validate_binary(received_bits)
    if len(received_bits) % 7 != 0:
        raise ValueError(
            f"Received bitstring length ({len(received_bits)}) must be a multiple of 7 for Hamming (7,4)."
        )

    num_blocks = len(received_bits) // 7
    corrected_blocks = []
    extracted_data_list = []
    block_info = []

    for i in range(num_blocks):
        blk = received_bits[i * 7:(i + 1) * 7]
        corr_blk, data_nibble, diag = decode_74_block(blk)
        diag["block_index"] = i
        corrected_blocks.append(corr_blk)
        extracted_data_list.append(data_nibble)
        block_info.append(diag)

    full_corrected = "".join(corrected_blocks)
    full_data = "".join(extracted_data_list)

    if original_payload_len is not None and original_payload_len <= len(full_data):
        full_data = full_data[:original_payload_len]

    return full_corrected, full_data, block_info


def format_hamming_working(data: str) -> str:
    """Format readable step-by-step Hamming (7,4) calculation for educational display."""
    validate_binary(data)
    padded_data, pad_count = pad_to_nibble_boundary(data)
    nibbles = [padded_data[i:i + 4] for i in range(0, len(padded_data), 4)]

    lines = [
        "=" * 68,
        " HAMMING (7,4) FORWARD ERROR CORRECTION (FEC) WORKING",
        "=" * 68,
        f" Original Data Bits   : {data} ({len(data)} bits)",
        f" Nibble Padding Added : {pad_count} zero bit(s) -> Padded: {padded_data}",
        f" Number of 4-bit Blocks: {len(nibbles)} block(s)",
        f" Code Parameters      : (n=7, k=4), Redundancy r=3 bits/block (75% overhead)",
        f" Hamming Distance     : d_min = 3 (Corrects 1 bit error, detects up to 2)",
        "-" * 68,
        " Bit Position Mapping (1-indexed, powers of 2 are parity positions):",
        "   Bit 1: p1  [covers {1, 3, 5, 7} -> p1 = d1 ^ d2 ^ d4]",
        "   Bit 2: p2  [covers {2, 3, 6, 7} -> p2 = d1 ^ d3 ^ d4]",
        "   Bit 3: d1  (Data bit 1)",
        "   Bit 4: p4  [covers {4, 5, 6, 7} -> p4 = d2 ^ d3 ^ d4]",
        "   Bit 5: d2  (Data bit 2)",
        "   Bit 6: d3  (Data bit 3)",
        "   Bit 7: d4  (Data bit 4)",
        "-" * 68
    ]

    encoded_blocks = []
    for idx, nib in enumerate(nibbles):
        d1, d2, d3, d4 = int(nib[0]), int(nib[1]), int(nib[2]), int(nib[3])
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p4 = d2 ^ d3 ^ d4
        codeword = f"{p1}{p2}{d1}{p4}{d2}{d3}{d4}"
        encoded_blocks.append(codeword)

        lines.append(f" Block {idx + 1}: Data Nibble = {nib} (d1={d1}, d2={d2}, d3={d3}, d4={d4})")
        lines.append(f"   p1 = {d1} ^ {d2} ^ {d4} = {p1}")
        lines.append(f"   p2 = {d1} ^ {d3} ^ {d4} = {p2}")
        lines.append(f"   p4 = {d2} ^ {d3} ^ {d4} = {p4}")
        lines.append(f"   Codeword [p1 p2 d1 p4 d2 d3 d4] = {codeword}")

    total_encoded = "".join(encoded_blocks)
    lines.append("-" * 68)
    lines.append(f" Transmitted Frame    : {total_encoded} ({len(total_encoded)} bits)")
    lines.append(f" Total Redundant Bits : {len(total_encoded) - len(data)} bit(s)")
    lines.append(" Receiver Syndrome Decode Rule:")
    lines.append("   s1 = b1 ^ b3 ^ b5 ^ b7,  s2 = b2 ^ b3 ^ b6 ^ b7,  s4 = b4 ^ b5 ^ b6 ^ b7")
    lines.append("   Error Position = s1*1 + s2*2 + s4*4 (0 = Clean; 1-7 = Invert bit to correct)")
    lines.append("=" * 68)

    return "\n".join(lines)
